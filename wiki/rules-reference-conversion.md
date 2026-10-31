---
type: Guide
title: Rules Reference Conversion
description: Convert Introduction and Glossary into separate Markdown and offline HTML trees, preserving symbols, local references, and cropped artwork.
sources:
  - id: converter
    resource: convert_rules.py
    title: Rules Reference converter
  - id: readme
    resource: README.md
    title: Conversion workflow and fidelity limits
  - id: checks
    resource: tests/test_convert_rules.py
    title: Introduction and Glossary conversion checks
  - id: ignore
    resource: .gitignore
    title: Generated output exclusion
  - id: styling
    resource: web/style.css
    title: HTML document styling
  - id: icon-font
    resource: https://github.com/geordanr/xwing-miniatures-font/tree/2664d8e9efffd4f1f7a0feac08a21bd123ce3c8a
    title: Pinned X-Wing Miniatures Font
generated:
  by: process:project-wiki-publish
  at: 2026-10-31T18:06:26.019Z
---
# Rules Reference Conversion

## Workflow and coverage

Use the Python/PyMuPDF converter for `Rules Reference v1.4.6-1.pdf`. It converts physical pages 2–23: Introduction and Glossary. The cover is omitted, and conversion stops before APPENDIX: EXAMPLES on page 24. Installation and invocation commands live in [README](../README.md).[^readme]

Running `python convert_rules.py` produces `markdown/index.md` and `docs/index.html` in the current directory. Each format has 3 Introduction rules and 149 Glossary rules. Both formats retain section folders, for example `markdown/glossary/glossary-actions.md` and `docs/glossary/glossary-actions.html`. Both formats bundle 44 crops in their own `assets/` folder and a copy of the source PDF. Each index retains section descriptions and linked TOCs in source order. Subsections remain inside their rule files. The Python `convert` function returns the Markdown index path.[^converter]

The `-o` argument accepts a parent directory for `docs/` and `markdown/`, defaulting to the current directory. For example, `-o converted-review` writes `converted-review/docs/` and `converted-review/markdown/`. Rerunning overwrites generated files. Older output remains outside the new indexes and may have stale links; conversion does not delete it. The repository ignores `/markdown/` and legacy `/converted/`; `/docs/` is not ignored and can be tracked by Git.[^readme][^ignore]

## Structure and continuations

The left column precedes the right. Font styles identify document parts, rule blocks, and subsections. Rules and paragraphs continue across columns and pages. Paragraphs, bold runs, numbered lists, and nested bullets are retained. Alphabetic substeps retain their original labels as nested bullets, such as `- **a.**`. Borders are excluded from extracted text and Markdown; HTML uses an extracted decorative frame. Footer copyright text and printed page numbers are excluded.[^converter]

Across page and column boundaries, a return to the unindented body margin ends an active list item. Body margins are x=36 in the left column and x=312 in the right, with one point tolerance. Indented list continuations still merge. This keeps Tractor's boost bullet separate from the following “This move cannot cause” paragraph on page 23.[^converter]

Unmarked paragraphs inside numbered steps retain four-space Markdown indentation when they start at least 12.5 points from the column body margin. This recognizes the source's 13.5-point substep margin with one point tolerance. Headings and new unmarked paragraphs outside this margin clear numbered context. Attack step 4's hit/miss paragraph remains inside the step as a separate paragraph following substep b.[^converter]

Figure placement waits until an enclosing paragraph is complete, preventing side artwork from splitting prose. Regular-font body text includes the smaller position-marker prose as well as the usual 8.5-point text. Extraction placeholders and control artifacts are removed without changing the printed wording.[^converter]

## Symbols and rule references

The 62 scoped `X-WingIcons` mappings produce textual tags such as `[barrel-roll]`, `[hit]`, `[critical-hit]`, `[charge]`, and `[bank-left]`. Unknown custom symbols, unresolved green references, or a missing appendix boundary stop conversion before generated files are replaced.[^converter]

Green text marks rule references. Wrapped spans merge into one link, and explicit aliases handle inflections and descriptive phrases. References within the converted scope link to local rule files or explicit subsection anchors. The text `destroyed` targets `DESTROYING SHIPS`.[^converter]

References outside the scope link to a bundled source PDF with `#page=N`: generic Appendix to page 24, individual device entries to 25, Squad Building to 43, Huge Ships to 44, and Environment Cards to 49. Both formats bundle the PDF under its original filename inside their own output folder. Page navigation depends on the PDF viewer.[^converter]

## Composite illustrations

Explicit 216 dpi PNG crops retain illustrations, diagrams, token artwork, and captions. Embedded image bounds cannot define these crops reliably because PDF clipping masks make the bounds larger than the displayed artwork. Diagram and caption text stay in the images rather than duplicating in the Markdown body.[^converter]

Figure reading order uses the crop's horizontal center to select the left or right column at x=306. Crop margins can cross the gutter: the page 23 victory counters crop starts at x=300 but belongs beneath VICTORY COUNTERS in the right column. Using its left edge would place it in the continuing Tractor rule.[^converter]

Insertion anchors in `FIGURES` must follow the owning heading. An anchor before that heading can attach deferred artwork to the preceding rule. The page 13 Fuse Marker anchor is y=292, after its heading at y=278.13; the former y=265 anchor placed it in Fully Execute.[^converter]

To place artwork immediately after a heading, its insertion anchor must also precede the first body line. Otherwise paragraph deferral places it after the opening paragraph. The page 13 Ion token anchor is y=273, between the heading's bottom at y=272.48 and prose at y=273.24.[^converter]

Nearby prose is removed from a temporary PDF page before rendering overlapping crop margins. Underlying raster and vector artwork is retained; the original PDF is not saved or modified. Keep the generated asset directory with the section folders and index. Illustration text remains raster content rather than searchable Markdown.[^converter]

## HTML styling and icons

For phone installation, app icons, and offline caching, see [Rules Reference PWA](rules-reference-pwa.md).

Both generated output folders are self-contained. Copy `docs/` alone and open `index.html`, or copy `markdown/` alone and open `index.md`. All generated local links stay inside the respective folder. HTML includes stylesheets, frame image, icon font, and font license. Crops are rendered once in `markdown/assets/` and copied into `docs/assets/`. Relocation regression checks copy each format to a separate directory and validate local references and anchors; HTML checks also cover CSS resources. Bundled PDFs and illustration copies are compared by bytes.[^converter][^checks]

HTML uses Python-Markdown to render the extracted paragraphs and lists. Inline emphasis, source text colors, green references, and subsection anchors are retained. Each page links to the HTML index. `web/style.css` supplies responsive and print layouts, condensed sans-serif body text, and heavy geometric headings. Local font stacks approximate Eurostile and Bank Gothic; commercial source fonts are not bundled.[^converter][^styling]

The bundled X-Wing Miniatures Font is pinned to commit `2664d8e9efffd4f1f7a0feac08a21bd123ce3c8a`. Its TTF, icon-only CSS, and MIT license are copied from `web/vendor/xwing-miniatures-font/` into HTML output. HTML renders 60 of the 62 symbol tags with accessible icon labels. Upstream has no hyperdrive or threat glyph, so `[hyperdrive]` and `[threat]` remain readable text. Markdown retains all textual tags. Conversion and viewing need no network access after dependencies are installed.[^converter][^icon-font]

## HTML graphical margins

Every HTML document uses `docs/assets/page-frame.png`, extracted from physical page 3 at 216 dpi (1836×2376 pixels). A temporary copy retains only the background form's first marked-content artifact, excluding rules, copyright text, and page numbers. Rendering clips bleed to the visible page. Keep the original image transformation and graphics state, and restore the CMYK transparency group omitted by `insert_pdf`; raw image extraction and reinsertion changes rendered colors. The source PDF is not modified. Missing margin artwork stops conversion before replacing generated files.[^converter]

CSS `border-image` uses 530-pixel vertical slices and 590-pixel horizontal slices, retaining the full 590×530 source-pixel corner regions containing diagonal graphics. Corners scale uniformly at the same ratio as the 90-pixel source rim: 1/3 on desktop and 2/9 on narrow screens. Only middle edge sections stretch around document content. A noninteractive pseudo-element behind the rules holds the frame so large corner interiors neither cover text nor add excess padding. The content border remains 30 CSS pixels wide, reduced to 20 pixels at viewport widths up to 40rem. Short pages fill the viewport minus desktop margins. The frame remains separate from Markdown and the 44 illustration crops.[^styling]

The margin regression check compares sampled top and side pixels with the rendered source PDF and confirms the frame interior is white. Existing illustration preservation checks remain applicable.[^checks]

## Verification and limits

Run `python -m unittest discover -s tests -v`. Checks cover section and file naming, all 626 generated link/image references and explicit anchors, the appendix boundary, paragraph continuations, numbered and nested lists, symbol tags, illustration placement, and failure without replacing existing output. Every one of the 1,917 nonempty regular-font source body lines is checked against generated text. An illustration preservation check compares the bank/sideslip crop against its original rendered region.[^checks]

These checks establish extraction coverage, not a complete editorial review. Fonts, colors, margins, aliases, and crop coordinates are calibrated to this edition; a different PDF requires inspection and updated calibration. The appendices remain outside the conversion scope.[^readme]

[^converter]: Converter, `FIGURES`, `SYMBOLS`, `RULE_ALIASES`, `EXTERNAL_RULES`, `translated`, `inline_text`, `extract_blocks`, `organize`, and `convert`.
[^readme]: README, Install and run, Preserved structure, and Verification and limits.
[^checks]: ConversionTests.
[^ignore]: Generated output exclusion in `.gitignore`.
[^styling]: HTML stylesheet, font stacks, colors, responsive and print rules.
[^icon-font]: Pinned upstream README, dist icon CSS, font, and MIT license; accessed 2026-10-31.
