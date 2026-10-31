"""Convert Rules Reference v1.4.6-1 through the glossary, before APPENDIX: EXAMPLES."""

import argparse
from dataclasses import dataclass, field
from itertools import groupby
from html import escape
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

import pymupdf
import markdown


SOURCE = Path("Rules Reference v1.4.6-1.pdf")
TEXT_FLAGS = pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES
REFERENCE_COLOR = 0x0F864C
STOP_SECTION = "APPENDIX: EXAMPLES"
SYMBOLS = {
    "\U000f2040": "[focus]", "\U000f2041": "[lock]",
    "\U000f2042": "[barrel-roll]", "\U000f2043": "[boost]",
    "\U000f2044": "[evade]", "\U000f2045": "[cloak]",
    "\U000f2047": "[reinforce]", "\U000f2048": "[coordinate]",
    "\U000f2049": "[jam]", "\U000f204a": "[slam]",
    "\U000f204b": "[talent]", "\U000f204c": "[sensor]",
    "\U000f204d": "[cannon]", "\U000f204e": "[turret]",
    "\U000f204f": "[torpedo]", "\U000f2050": "[missile]",
    "\U000f2052": "[crew]", "\U000f2054": "[astromech]",
    "\U000f2056": "[payload]", "\U000f2058": "[illicit]",
    "\U000f2059": "[modification]", "\U000f205a": "[title]",
    "\U000f205b": "[tech]", "\U000f205c": "[turn-left]",
    "\U000f205d": "[bank-left]", "\U000f205e": "[straight]",
    "\U000f205f": "[bank-right]", "\U000f2060": "[turn-right]",
    "\U000f2061": "[stationary]", "\U000f2062": "[tallon-roll-left]",
    "\U000f2063": "[segnors-loop-left]", "\U000f2064": "[koiogran-turn]",
    "\U000f2065": "[segnors-loop-right]", "\U000f2066": "[tallon-roll-right]",
    "\U000f2067": "[hit]", "\U000f2068": "[critical-hit]",
    "\U000f206a": "[energy]", "\U000f206b": "[rotate]",
    "\U000f206c": "[reverse-straight]", "\U000f206d": "[reverse-bank-right]",
    "\U000f206e": "[reverse-bank-left]", "\U000f2221": "[configuration]",
    "\U000f2222": "[force-power]", "\U000f2223": "[reload]",
    "\U000f2224": "[linked-action]", "\U000f2225": "[calculate]",
    "\U000f2226": "[gunner]", "\U000f2227": "[full-front-arc]",
    "\U000f2228": "[full-rear-arc]", "\U000f2229": "[bullseye-arc]",
    "\U000f222a": "[rear-arc]", "\U000f222b": "[front-arc]",
    "\U000f222c": "[double-turret-arc]", "\U000f222d": "[turret-arc]",
    "\U000f222e": "[charge]", "\U000f222f": "[force]",
    "\U000f2400": "[left-arc]", "\U000f2401": "[right-arc]",
    "\U000f2402": "[tactical-relay]", "\U000f2408": "[shield]",
    "\U000f2409": "[threat]", "\U000f2500": "[hyperdrive]",
}

# Crop composites, including captions; embedded image bounds ignore PDF clipping masks.
# Entries contain (rectangle, description, insertion y). Side artwork follows its heading.
FIGURES = {
    2: [((312, 288, 576, 405), "Pilot and ship abilities", 288)],
    3: [((528, 561, 576, 627), "Agility value on a ship card", 589)],
    4: [((110, 273, 217, 377), "Standard arcs", 273),
        ((110, 505, 218, 609), "Bullseye arc", 505),
        ((392, 56, 485, 153), "Full front and rear arcs", 56),
        ((380, 372, 506, 506), "Single turret arc indicator and ID tokens", 372),
        ((520, 543, 589, 617), "Double turret arc indicator", 612)],
    6: [((30, 180, 305, 259), "Small ship barrel roll positions", 180),
        ((30, 279, 305, 359), "Medium or large ship barrel roll", 279)],
    7: [((33, 185, 107, 269), "Blazer Bomb", 185),
        ((310, 149, 581, 273), "Boost positions", 149),
        ((528, 610, 581, 666), "Calculate token", 630)],
    8: [((235, 630, 291, 676), "Recurring charge symbol", 630),
        ((231, 688, 297, 738), "Negative recurring charge symbol", 688)],
    9: [((253, 31, 305, 86), "Cloak token", 47.5)],
    10: [((231, 78, 306, 170), "Damage cards", 78),
         ((252, 616, 305, 674), "Deplete token", 632)],
    11: [((175, 281, 305, 388), "X-wing dials front and back", 302),
         ((531, 376, 584, 430), "Disarm token", 394)],
    12: [((258, 703, 309, 760), "Evade token", 719.5),
         ((535, 626, 588, 680), "Focus token", 644)],
    13: [((257, 275, 309, 337), "Fuse marker", 292),
         ((542, 33, 581, 98), "Hull value on a ship card", 47.5),
         ((534, 259, 590, 321), "Ion token", 273)],
    14: [((253, 159, 305, 214), "Jam token", 175.2)],
    16: [((94, 431, 284, 518), "Obstructed attack", 431)],
    17: [((31, 168, 161, 247), "Player markers", 168),
         ((242, 258, 307, 335), "First player marker", 264),
         ((253, 434, 310, 504), "Position marker", 450),
         ((247, 510, 312, 575), "Primary weapon on a ship card", 521),
         ((359, 75, 531, 233), "Within and beyond range 1", 75)],
    18: [((253, 89, 301, 138), "Ordnance icon", 47.5),
         ((241, 168, 304, 222), "Fore reinforce token", 186.5),
         ((241, 222, 304, 274), "Aft reinforce token", 222),
         ((34, 316, 264, 473), "Reinforce example", 316)],
    19: [((69, 167, 267, 310), "Relocating a remote forward", 167)],
    20: [((449, 236, 584, 332), "A left sideslip", 236),
         ((323, 397, 590, 510), "Correct and incorrect sideslip placement", 397)],
    21: [((40, 81, 305, 264), "Bank compared with sideslip", 81),
         ((253, 690, 306, 738), "Ordnance icon", 699),
         ((533, 640, 586, 696), "Strain token", 656)],
    22: [((257, 31, 309, 84), "Stress token", 47.5),
         ((531, 567, 584, 632), "Tractor token", 588)],
    23: [((300, 68, 388, 133), "Victory counters", 47.5)],
}

# Printed cross-references include inflections and descriptive phrases, not only headings.
RULE_ALIASES = {}
for destination, variants in {
    "abilities": ["ability"], "actions": ["action"],
    "arc": ["arcs"], "attack": ["attacks"], "attack range": ["attack ranges"],
    "barrel roll": ["barrel rolls", "barrel rolling"],
    "boost": ["boosts", "boosting"], "cancel": ["canceling"],
    "charges": ["charge", "charge limit"], "force charge": ["force capacity"],
    "condition cards": ["condition"], "coordinate": ["coordinates"],
    "decloak": ["decloaking", "decloaks"], "deplete": ["deplete token"],
    "destroying ships": ["destroyed"], "device": ["devices", "dropping and launching devices"],
    "dock": ["docked"], "deploy": ["deploys"], "disarmed": ["disarm"],
    "drop": ["dropped"], "engagement phase": ["engagement phases"],
    "fail": ["fails"], "flee": ["flees", "fled"], "hit": ["hits"],
    "id marker": ["id markers"], "initiative": ["initiative order"],
    "jam": ["jams"], "launch": ["launched"], "linked action": ["linked actions"],
    "lock": ["locks"], "maneuver": ["maneuvers"], "miss": ["misses"],
    "dice modification": ["modifying dice"], "move": ["moves"],
    "move through": ["moving through", "moved through"], "objects": ["object"],
    "obstacles": ["obstacle"], "overlap": ["overlapped", "overlapping"],
    "partially execute": ["partially executing", "partially executes", "partially executes a maneuver"],
    "primary weapon": ["primary"], "range": ["range 0", "range 4–5"],
    "recurring charges": ["recurring charge icon"],
    "negative recurring charges": ["negative recurring charge icon"],
    "removed from the game": ["removed"], "upgrade cards": ["restriction", "upgrade"],
    "ship": ["ships"], "ship sizes": ["size", "medium or large ship"],
    "ship type": ["ship’s type"], "slam": ["slams"],
    "special weapon": ["special", "special weapons"], "strain": ["strain token"],
    "stress": ["stress token", "stressed"], "suffer damage": ["suffers damage"],
    "system phase": ["system"], "tokens": ["token"], "winning the game": ["wins"],
}.items():
    RULE_ALIASES.update(dict.fromkeys(variants, destination))
EXTERNAL_RULES = {
    "appendix": 24, "appendix: huge ships": 44,
    "appendix: environment cards": 49, "squad building": 43,
    "individual entries": 25,
}


@dataclass
class Block:
    kind: str
    spans: list = field(default_factory=list)
    page: int = 0
    prefix: str = ""
    figure: tuple | None = None

    @property
    def text(self):
        return "".join(s["text"] for s in self.spans).replace("\ufffc", "").strip()


def heading_level(spans):
    """Use the source's three heading styles, not capitalization."""
    if any(s["font"] == "KimberleyBl-Regular" and s["size"] >= 17 for s in spans):
        return 1
    if any(s["font"] == "EurostileLTStd-Bold" and s["size"] >= 10.5 for s in spans):
        return 2
    letters = [s for s in spans if s["font"] != "X-WingIcons" and s["text"].strip()]
    if letters and all(s["font"] == "EurostileLTStd-Bold-SC70" for s in letters) and max(s["size"] for s in letters) >= 9.5:
        return 3
    if letters and all(s["font"] == "EurostileLTStd-Bold" for s in letters):
        text = "".join(s["text"] for s in letters)
        if text.isupper() and re.fullmatch(r"[A-Z ]+", text):
            return 3
    return 0


def title_key(text):
    return text.split("(")[0].replace("\ufffc", "").strip().rstrip(".").casefold()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.casefold().replace("’", "")).strip("-")


def translated(span):
    text = span["text"].replace("\u00ad", "").replace("\ufffc", "").replace("\x07", "")
    if span["font"] == "X-WingIcons":
        unknown = set(text) - SYMBOLS.keys() - set(" ")
        if unknown:
            codes = ", ".join(f"U+{ord(c):04X}" for c in sorted(unknown))
            raise ValueError(f"Unmapped X-WingIcons character(s): {codes}")
        return "".join(SYMBOLS.get(c, c) for c in text)
    if any(0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c) <= 0x10FFFD or c == "\ufffd" for c in text):
        raise ValueError(f"Unmapped character in font {span['font']}")
    return text


def body_line(spans):
    return any(s["font"] == "EurostileLTStd-Cn" and 8.2 <= s["size"] <= 8.6 for s in spans)


def relative_url(target, current):
    path, _, anchor = target.partition("#")
    relative = Path(os.path.relpath(path, Path(current).parent)).as_posix()
    return quote(relative) + ("#" + anchor if anchor else "")


def inline_text(spans, targets, current, source, html=False):
    """Merge font runs and wrapped references before emitting Markdown."""
    runs = []
    for span in spans:
        text = translated(span)
        style = "bold" if "Bold" in span["font"] else "italic" if "Oblique" in span["font"] else ""
        if html and "Demi" in span["font"]:
            style = "bold"
        runs.append((text, style, span["color"] == REFERENCE_COLOR, span["color"] if html else None))
    output = []
    for (style, reference, color), group in groupby(runs, key=lambda r: r[1:]):
        text = "".join(r[0] for r in group)
        core = text.strip()
        if not core:
            output.append(text)
            continue
        if reference and any(c.isalpha() for c in core):
            # Keep surrounding punctuation outside the link and preserve the printed wording.
            match = re.fullmatch(r'([“"(]*)(.*?)([.,;:”)"!]*)', core)
            before, label, after = match.groups()
            name = RULE_ALIASES.get(label.casefold(), label.casefold())
            if name in targets:
                url = relative_url(str(targets[name]), current)
            elif name in EXTERNAL_RULES:
                url = relative_url(str(source) + f"#page={EXTERNAL_RULES[name]}", current)
            else:
                raise ValueError(f"Cannot resolve rule reference: {core!r}")
            formatted = (f'{escape(before)}<a href="{escape(url, quote=True)}">{escape(label)}</a>{escape(after)}'
                         if html else f"{before}[{label}]({url}){after}")
        elif style:
            marker = "**" if style == "bold" else "*"
            tag = "strong" if style == "bold" else "em"
            formatted = f"<{tag}>{escape(core)}</{tag}>" if html else marker + core + marker
        else:
            formatted = escape(core) if html else core
        if html and color != 0x231F20 and not reference:
            formatted = f'<span style="color: #{color:06x}">{formatted}</span>'
        output.append(text[:len(text) - len(text.lstrip())] + formatted + text[len(text.rstrip()):])
    return "".join(output).strip()


def extract_blocks(document):
    """Keep paragraphs and list items intact across page and column boundaries."""
    events = []
    found_stop = False
    for page in document:
        if page.number == 0:
            continue
        figures = FIGURES.get(page.number + 1, [])
        for block in page.get_text("dict", flags=TEXT_FLAGS)["blocks"]:
            for line in block.get("lines", []):
                rect = pymupdf.Rect(line["bbox"])
                if rect.x0 < 30 or rect.x0 > 590 or rect.y0 < 30 or rect.y0 > 759:
                    continue
                if not "".join(s["text"] for s in line["spans"]).strip():
                    continue
                if not body_line(line["spans"]) and any(pymupdf.Rect(box).contains((rect.tl + rect.br) / 2) for box, _, _ in figures):
                    continue
                events.append((page.number + 1, int(rect.x0 >= 306), rect.y0, line))
        for box, description, anchor in figures:
            # Crop margins can cross the gutter; use the center to identify the column.
            events.append((page.number + 1, int((box[0] + box[2]) / 2 >= 306), anchor, (box, description)))
        if STOP_SECTION in page.get_text():
            found_stop = True
            break
    if not found_stop:
        raise ValueError(f"Missing conversion boundary: {STOP_SECTION}")
    events.sort(key=lambda e: e[:3])
    result, paragraph = [], None
    pending_figures = []
    numbered_list = False
    previous_stream, previous_bottom = None, 0
    for page, column, top, item in events:
        stream = page, column
        if isinstance(item, tuple):
            figure = Block("figure", page=page, figure=item)
            if paragraph:
                pending_figures.append(figure)
            else:
                result.append(figure)
            continue
        spans = [dict(s) for s in item["spans"]]
        text = "".join(s["text"] for s in spans)
        level = heading_level(spans)
        if level == 1 and text.strip() == STOP_SECTION:
            break
        bullet = re.match(r"^([•◊]|[a-z]\.|\d+\.)\s+", text)
        # Across pages/columns, a return to the body margin ends an indented list item.
        list_ended = (stream != previous_stream and paragraph and paragraph.prefix
                      and item["bbox"][0] <= (312 if column else 36) + 1)
        if paragraph and (level or bullet or list_ended or (stream == previous_stream and top - previous_bottom > 4)):
            result.append(paragraph)
            result.extend(pending_figures)
            pending_figures.clear()
            paragraph = None
        if level:
            numbered_list = False
            result.append(Block({1: "section", 2: "rule", 3: "subsection"}[level], spans, page))
        else:
            prefix = ""
            if bullet:
                marker = bullet[1]
                if marker[0].isdigit():
                    numbered_list = True
                prefix = "    - " if marker == "◊" else "- " if marker == "•" else (
                    f"    - **{marker}** " if marker[0].isalpha() else marker + " ")
                # Bullet markers in this source share the first text span.
                remaining = bullet.end()
                for span in spans:
                    amount = min(remaining, len(span["text"]))
                    span["text"] = span["text"][amount:]
                    remaining -= amount
                    if remaining == 0:
                        break
            elif paragraph is None:
                # Unmarked paragraphs at the substep margin still belong to the numbered step.
                numbered_list = numbered_list and item["bbox"][0] >= (312 if column else 36) + 12.5
                if numbered_list:
                    prefix = "    "
            if paragraph is None:
                paragraph = Block("paragraph", spans, page, prefix)
            else:
                last = paragraph.spans[-1]["text"].rstrip()
                paragraph.spans[-1]["text"] = last + ("" if last.endswith("-") else " ")
                paragraph.spans.extend(spans)
        previous_stream = stream
        previous_bottom = item["bbox"][3]
    if paragraph:
        result.append(paragraph)
    result.extend(pending_figures)
    return result


def organize(blocks, output, extension=".md"):
    sections, targets = [], {}
    section = rule = None
    for block in blocks:
        if block.kind == "section":
            section = {"title": block.text, "slug": slug(block.text), "intro": [], "rules": []}
            sections.append(section)
            rule = None
        elif block.kind == "rule":
            if section is None:
                raise ValueError("Rule encountered before a document section")
            name = title_key(block.text)
            path = output / section["slug"] / f"{section['slug']}-{slug(name)}{extension}"
            if isinstance(targets.get(name), Path):
                raise ValueError(f"Duplicate rule: {name}")
            targets[name] = path
            rule = {"title": block, "path": path, "blocks": []}
            section["rules"].append(rule)
        else:
            if section is None:
                raise ValueError("Text encountered before a document section")
            (rule["blocks"] if rule else section["intro"]).append(block)
            if block.kind == "subsection" and rule:
                targets.setdefault(title_key(block.text), str(rule["path"]) + "#" + slug(title_key(block.text)))
    if [s["title"] for s in sections] != ["INTRODUCTION", "GLOSSARY"]:
        raise ValueError("Expected Introduction and Glossary before the examples appendix")
    return sections, targets


def render_blocks(blocks, targets, current, source, root, assets, html=False):
    rendered = []
    list_parent = False
    for block in blocks:
        if block.kind == "figure":
            box, description = block.figure
            name = f"page-{block.page:02d}-{slug(description)}.png"
            asset = root.parent / "markdown" / "assets" / name
            assets[asset] = block.page, box
            linked_asset = root / "assets" / name
            rendered.append(f"![{description}]({relative_url(str(linked_asset), current)})")
        else:
            text = inline_text(block.spans, targets, current, source, html=html)
            if block.kind == "subsection":
                title = text if html else "".join(translated(s) for s in block.spans).strip()
                text = f'<a id="{slug(title_key(block.text))}"></a>\n\n## ' + title
            prefix = block.prefix
            if html:
                # Standalone lettered substeps have no parent list to supply Markdown indentation.
                if prefix.startswith("    ") and not list_parent:
                    prefix = prefix[4:]
                if not block.prefix.startswith("    "):
                    list_parent = bool(block.prefix)
            rendered.append(prefix + text)
    return "\n\n".join(rendered)


def html_document(text, title, current, root):
    body = markdown.markdown(text, extensions=["sane_lists"])
    # Replace symbols only in text, never inside link destinations or attributes.
    parts = re.split(r'(<[^>]+>)', body)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'\[([a-z-]+)\]', html_icon, parts[i])
    stylesheet = relative_url(str(root / "style.css"), current)
    manifest = relative_url(str(root / "manifest.webmanifest"), current)
    favicon = relative_url(str(root / "favicon.ico"), current)
    icon = relative_url(str(root / "icons/icon.svg"), current)
    touch_icon = relative_url(str(root / "icons/apple-touch-icon.png"), current)
    script = relative_url(str(root / "pwa.js"), current)
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<meta name="theme-color" content="#004761">\n'
            f'<link rel="manifest" href="{manifest}">\n'
            f'<link rel="icon" href="{favicon}" sizes="32x32">\n'
            f'<link rel="icon" href="{icon}" type="image/svg+xml">\n'
            f'<link rel="apple-touch-icon" href="{touch_icon}">\n'
            f'<script src="{script}" defer></script>\n'
            f'<title>{escape(title)}</title>\n<link rel="stylesheet" href="{stylesheet}">\n'
            f'</head>\n<body>\n'
            f'<main>{"".join(parts)}</main>\n</body>\n</html>\n')


ICON_ALIASES = {
    "critical-hit": "crit", "payload": "device", "configuration": "config",
    "force": "forcecharge", "linked-action": "linked", "rotate": "rotatearc",
    "stationary": "stop", "koiogran-turn": "kturn", "turret-arc": "singleturretarc",
    "segnors-loop-left": "sloopleft", "segnors-loop-right": "sloopright",
    "tallon-roll-left": "trollleft", "tallon-roll-right": "trollright",
}
WEB = Path(__file__).resolve().parent / "web"


def html_icon(match):
    name = match[1]
    # shortcut: upstream lacks these glyphs; retain labels until the font adds them.
    if f"[{name}]" not in SYMBOLS.values() or name in {"hyperdrive", "threat"}:
        return match[0]
    icon = ICON_ALIASES.get(name, name.replace("-", ""))
    return (f'<i class="xwing-miniatures-font xwing-miniatures-font-{icon}" '
            f'role="img" aria-label="{name}" title="{name}"></i>')


def extract_page_frame(document):
    """Render the page-sized background form without its footer or rule content."""
    with pymupdf.open() as artwork:
        artwork.insert_pdf(document, from_page=2, to_page=2)
        page = artwork[0]
        for xref, name, parent, bbox in page.get_xobjects():
            if parent != 0 or not pymupdf.Rect(bbox).contains(page.rect):
                continue
            background, marker, _ = artwork.xref_stream(xref).partition(b"EMC")
            if not marker or b"/Im0 Do" not in background or b"BT" in background:
                continue
            # The first artifact contains only the frame; the next form adds copyright text.
            artwork.update_stream(xref, background + marker)
            contents = page.get_contents()[0]
            artwork.update_stream(contents, f"q /GS0 gs /{name} Do Q".encode("ascii"))
            page.set_contents(contents)
            # insert_pdf omits the source page's CMYK transparency group.
            artwork.xref_set_key(page.xref, "Group", "<</CS /DeviceCMYK /S /Transparency /Type /Group>>")
            return page.get_pixmap(matrix=pymupdf.Matrix(3, 3)).tobytes("png")
    raise ValueError("Missing full-page margin artwork on physical page 3")


def convert(source, output):
    source, output = Path(source), Path(output)
    if output.suffix.lower() == ".md":
        raise ValueError("Output must be a directory; use -o output")
    with pymupdf.open(source) as document:
        if len(document) != 49 or document[1].rect != pymupdf.Rect(0, 0, 612, 792):
            raise ValueError("Expected the 49-page US Letter Rules Reference v1.4.6-1 PDF")
        blocks = extract_blocks(document)
        files, assets = {}, {}
        for format, extension in (("markdown", ".md"), ("docs", ".html")):
            root = output / format
            html = extension == ".html"
            linked_source = root / source.name
            sections, targets = organize(blocks, root, extension)
            index = root / ("index" + extension)
            toc = ["# Rules Reference v1.4.6-1"]
            for section in sections:
                toc.append("## " + section["title"].title())
                intro = render_blocks(section["intro"], targets, index, linked_source, root, assets, html=html)
                if intro:
                    toc.append(intro)
                links = []
                for rule in section["rules"]:
                    title = "".join(translated(s) for s in rule["title"].spans).strip()
                    heading = inline_text(rule["title"].spans, targets, rule["path"], linked_source, html=True) if html else title
                    text = "# " + heading + "\n\n" + render_blocks(rule["blocks"], targets, rule["path"], linked_source, root, assets, html=html) + "\n"
                    files[rule["path"]] = html_document(text, title, rule["path"], root) if html else text
                    links.append(f"- [{escape(title) if html else title}]({relative_url(str(rule['path']), index)})")
                toc.append("\n".join(links))
            text = "\n\n".join(toc) + "\n"
            files[index] = html_document(text, "Rules Reference v1.4.6-1", index, root) if html else text
        # Read web resources before replacing any generated content.
        web_assets = {p.relative_to(WEB): p.read_bytes() for p in WEB.rglob("*") if p.is_file()}
        web_assets[Path("assets/page-frame.png")] = extract_page_frame(document)
        web_assets[Path(source.name)] = source.read_bytes()
        # Render only after text validation, so unmapped symbols cannot replace a good output.
        for asset, (page, box) in assets.items():
            asset.parent.mkdir(parents=True, exist_ok=True)
            pdf_page = document[page - 1]
            clip = pymupdf.Rect(box)
            overlaps = []
            for block in pdf_page.get_text("dict", flags=TEXT_FLAGS)["blocks"]:
                for line in block.get("lines", []):
                    if body_line(line["spans"]):
                        for span in line["spans"]:
                            rect = pymupdf.Rect(span["bbox"]) & clip
                            if not rect.is_empty:
                                overlaps.append(rect)
            if not overlaps:
                pdf_page.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=clip).save(asset)
                continue
            # Remove nearby prose from a temporary page; retain the artwork underneath it.
            with pymupdf.open() as artwork:
                artwork.insert_pdf(document, from_page=page - 1, to_page=page - 1)
                crop_page = artwork[0]
                for rect in overlaps:
                    crop_page.add_redact_annot(rect, fill=None, cross_out=False)
                crop_page.apply_redactions(images=0, graphics=0, text=0)
                crop_page.get_pixmap(matrix=pymupdf.Matrix(3, 3), clip=clip).save(asset)
        for asset in assets:
            web_assets[Path("assets") / asset.name] = asset.read_bytes()
        # Version the offline bundle by content so each deployment installs atomically.
        offline = {p.relative_to(output / "docs").as_posix(): text.encode("utf-8")
                   for p, text in files.items() if p.suffix == ".html"}
        offline.update({p.as_posix(): data for p, data in web_assets.items()
                        if p.suffix != ".pdf" and p.name != "sw.js"})
        digest = hashlib.sha256()
        for name, data in sorted(offline.items()):
            digest.update(name.encode("utf-8") + b"\0" + data)
        digest.update(web_assets[Path("sw.js")])
        worker = web_assets[Path("sw.js")].decode("utf-8")
        worker = worker.replace("__VERSION__", digest.hexdigest()[:16])
        worker = worker.replace("__PRECACHE__", json.dumps(sorted(offline)))
        web_assets[Path("sw.js")] = worker.encode("utf-8")
        for path, text in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for relative, data in web_assets.items():
            path = output / "docs" / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (output / "markdown" / source.name).write_bytes(web_assets[Path(source.name)])
    return output / "markdown" / "index.md"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", type=Path, default=SOURCE)
    parser.add_argument("-o", "--output", type=Path, default=Path("."), help="parent directory for docs/ and markdown/ (default: current directory)")
    args = parser.parse_args()
    try:
        result = convert(args.source, args.output)
    except (OSError, ValueError, pymupdf.FileDataError) as error:
        parser.exit(1, f"Conversion failed: {error}\n")
    print(f"Converted Introduction and Glossary: {result} and {args.output / 'docs' / 'index.html'}")


if __name__ == "__main__":
    main()
