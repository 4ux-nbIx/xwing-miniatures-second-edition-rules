"""Isolate marked figure groups in the calibrated Rules Reference PDF."""

import re

import pymupdf


def figure_stream(page, mcids, bounds=None, unmarked=False):
    """Retain nested marked content, clipping paths, and original graphics states."""
    source = page.read_contents()
    groups = []
    for mcid in mcids:
        marker = rb"/\w+\s*<<[^<>]*?/MCID\s+" + str(mcid).encode("ascii") + rb"\s*>>\s*BDC"
        starts = list(re.finditer(marker, source))
        if len(starts) != 1:
            raise ValueError(f"Expected one Figure MCID {mcid} on page {page.number + 1}")
        groups.append(starts[0].end())
    if bounds is not None:
        for marker in re.finditer(rb"/Artifact\s*<<\s*/BBox\s*\[([^]]+)\][^<>]*>>\s*BDC", source):
            rect = pymupdf.Rect([float(v) for v in marker[1].split()]) * page.transformation_matrix
            if pymupdf.Rect(bounds).contains((rect.tl + rect.br) / 2):
                groups.append(marker.end())
    streams = []
    cursor = 0
    states = (rb"(?m)^[qQ](?=\s|$)|/\w+\s+[-.\d]+\s+Tf|/\w+\s+gs|"
              rb"(?:[-.\d]+\s+){1,4}(?:[kKgG]|rg|RG)\b")
    for start in sorted(groups):
        # Skipped captions can close an artwork clip or set the font/color inherited
        # by a later label. Replay state changes, excluding text and path painting.
        for state in re.finditer(states, source[cursor:start]):
            operator = state[0]
            streams.append(b"BT " + operator + b" ET" if operator.endswith(b"Tf") else operator)
        depth = 1
        for token in re.finditer(rb"\b(BDC|BMC|EMC)\b", source[start:]):
            depth += -1 if token[1] == b"EMC" else 1
            if depth == 0:
                group = source[start:start + token.start()].strip()
                cursor = start + token.end()
                break
        else:
            raise ValueError("Unclosed figure marked content")
        streams.append(group)
    if unmarked:
        # Page 24 paints queue boxes outside marked content. Keep those graphics;
        # replay only state from unwanted text groups, then clip to the diagram.
        states += rb"|[-.\d]+\s+(?:Tc|Tw|Tz|TL|Tr|Ts)\b"
        streams, cursor = [], 0
        selected = set(groups)
        for marker in re.finditer(rb"/\w+\s*(?:<<[^<>]*>>\s*)?B[DM]C", source):
            if marker.start() < cursor:
                continue
            streams.append(source[cursor:marker.start()])
            depth = 1
            for token in re.finditer(rb"\b(BDC|BMC|EMC)\b", source[marker.end():]):
                depth += -1 if token[1] == b"EMC" else 1
                if depth == 0:
                    end = marker.end() + token.end()
                    break
            else:
                raise ValueError("Unclosed figure marked content")
            content = source[marker.end():end - 3]
            if marker.end() in selected:
                streams.append(content)
            else:
                for state in re.finditer(states, content):
                    operator = state[0]
                    streams.append(b"BT " + operator + b" ET" if re.search(rb"(?:Tf|Tc|Tw|Tz|TL|Tr|Ts)$", operator) else operator)
            cursor = end
        streams.append(source[cursor:])
        # Full-page forms contain the decorative page background and copyright.
        group = b"\n".join(streams)
        for _, name, parent, box in page.get_xobjects():
            if parent == 0 and pymupdf.Rect(box).contains(page.rect):
                group = group.replace(b"/" + name.encode("ascii") + b" Do", b"")
    else:
        group = b"\n".join(streams)
    # Adjacent groups can share a clipping scope. Keep their source order and balance
    # only the combined stream's outer scopes, which originally ended in page prose.
    depth = minimum = 0
    # In this PDF, graphics stack operators start lines. Avoid matching card text.
    for token in re.finditer(rb"(?m)^([qQ])(?=\s|$)", group):
        depth += 1 if token[1] == b"q" else -1
        minimum = min(minimum, depth)
    return b"q\n" * (1 - minimum) + group + b"\nQ" * (1 + depth - minimum)


def isolate_figure(document, page_number, mcids, bounds=None, caption_rects=(), unmarked=False):
    """Return an in-memory PDF containing only the requested figure groups."""
    isolated = pymupdf.open()
    try:
        isolated.insert_pdf(document, from_page=page_number - 1, to_page=page_number - 1)
        page = isolated[0]
        group = figure_stream(page, mcids, bounds, unmarked=unmarked)
        contents = page.get_contents()[0]
        isolated.update_stream(contents, group)
        page.set_contents(contents)
        # insert_pdf omits this source page group; retain its color blending space.
        isolated.xref_set_key(page.xref, "Group", "<</CS /DeviceCMYK /S /Transparency /Type /Group>>")
        caption_rects = [rect for rect in caption_rects if page.get_text(clip=pymupdf.Rect(rect)).strip()]
        if caption_rects:
            for rect in caption_rects:
                page.add_redact_annot(rect, fill=None, cross_out=False)
            page.apply_redactions(images=0, graphics=0, text=0)
        return isolated
    except Exception:
        isolated.close()
        raise


def render_figure(document, page_number, mcids, bounds, caption_rects=(), unmarked=False):
    """Render isolated artwork at 216 dpi and trim only fully transparent margins."""
    with isolate_figure(document, page_number, mcids, bounds, caption_rects, unmarked=unmarked) as isolated:
        page = isolated[0]
        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=bounds if unmarked else None, alpha=True)
        alpha = pixmap.samples[3::4]
        left, top, right, bottom = pixmap.width, pixmap.height, 0, 0
        for y in range(pixmap.height):
            row = alpha[y * pixmap.width:(y + 1) * pixmap.width]
            if row.strip(b"\0"):
                left = min(left, pixmap.width - len(row.lstrip(b"\0")))
                right = max(right, len(row.rstrip(b"\0")))
                top, bottom = min(top, y), y + 1
        if right == 0:
            raise ValueError(f"Empty artwork on page {page_number}: {mcids}")
        clip = pymupdf.Rect(left - 1 + pixmap.x, top - 1 + pixmap.y, right + 1 + pixmap.x, bottom + 1 + pixmap.y) / 3
        return page.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=clip, alpha=True).tobytes("png")
