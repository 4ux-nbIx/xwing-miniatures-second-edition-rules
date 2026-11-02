---
type: Guide
title: Rules Reference Conversion
description: Convert pages 2–29 to portable Markdown and offline HTML with individual Appendix cards, local references, symbols, and isolated artwork.
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
  at: 2026-11-02T21:09:09.995Z
---
# Rules Reference Conversion

## Workflow and coverage

Use the Python/PyMuPDF converter for `Rules Reference v1.4.6-1.pdf`. It converts physical pages 2–29: Introduction, Glossary, and Appendix: Examples. The cover is omitted, and conversion stops before the ERRATA heading on physical page 30. Installation and invocation commands live in [README](../README.md).[^readme]

Running `python convert_rules.py` produces `markdown/index.md` and `docs/index.html` in the current directory. Each format has 3 Introduction rules, 149 Glossary rules, and 27 Appendix pages. Both formats retain `introduction/`, `glossary/`, and `appendix-examples/` section folders, for example `markdown/glossary/glossary-actions.md` and `docs/glossary/glossary-actions.html`. Both formats bundle 78 illustration assets in their own `assets/` folder and a copy of the source PDF. Each index retains section descriptions and linked TOCs in source order. Subsections remain inside their rule files. The Python `convert` function returns the Markdown index path.[^converter]

The `-o` argument accepts a parent directory for `docs/` and `markdown/`, defaulting to the current directory. For example, `-o converted-review` writes `converted-review/docs/` and `converted-review/markdown/`. Rerunning overwrites generated files. Older output remains outside the new indexes and may have stale links; conversion does not delete it. The repository ignores `/markdown/` and legacy `/converted/`; `/docs/` is not ignored and can be tracked by Git.[^readme][^ignore]

## Structure and continuations

The left column precedes the right. Font styles identify document parts, rule blocks, and subsections. Rules and paragraphs continue across columns and pages. Paragraphs, bold runs, numbered lists, and nested bullets are retained. Alphabetic substeps retain their original labels as nested bullets, such as `- **a.**`. Borders are excluded from extracted text and Markdown; HTML uses an extracted decorative frame. Original footer copyright text and printed page numbers are excluded during extraction. Markdown omits copyright footers; generated HTML adds the shared notice described below.[^converter]

Across page and column boundaries, a return to the unindented body margin ends an active list item. Body margins are x=36 in the left column and x=312 in the right, with one point tolerance. Indented list continuations still merge. This keeps Tractor's boost bullet separate from the following “This move cannot cause” paragraph on page 23.[^converter]

Unmarked paragraphs inside numbered steps retain four-space Markdown indentation when they start at least 12.5 points from the column body margin. This recognizes the source's 13.5-point substep margin with one point tolerance. Headings and new unmarked paragraphs outside this margin clear numbered context. Attack step 4's hit/miss paragraph remains inside the step as a separate paragraph following substep b.[^converter]

Markdown and large HTML figure placement wait until an enclosing paragraph is complete, preventing side artwork from splitting prose. Regular-font body text includes the smaller position-marker prose as well as the usual 8.5-point text. Extraction placeholders and control artifacts are removed without changing the printed wording.[^converter]

## Appendix panels

`APPENDIX_CARDS` calibrates one independent reading stream per object card on pages 25–28, preserving left-column-before-right-column order. The 21 cards retain searchable text and isolated artwork without decorative borders. Page 29 becomes three device/deploy example pages and two image-based card anatomy pages. Both indexes display one Appendix section with six subsections: Examples, Objects: Bombs and Mines, Objects: Obstacles, Objects: Remotes, Device and Deploying Examples, and Card Anatomies. The 27 individual page URLs and the `appendix-examples` index anchor remain stable. `APPENDIX_GROUPS` and `organize` assign each page to its subsection. `appendix_events` suppresses internal artwork text and original card headings, inserts one title per panel, preserves phase paragraph breaks, and treats “range 0.” as prose rather than a numbered list.[^converter][^checks]

## Symbols and rule references

The 63 scoped `X-WingIcons` mappings produce textual tags such as `[barrel-roll]`, `[hit]`, `[critical-hit]`, `[charge]`, and `[bank-left]`. Unknown custom symbols, unresolved green references, or a missing ERRATA boundary stop conversion before generated files are replaced.[^converter]

Green text marks rule references. Wrapped spans merge into one link, and explicit aliases handle inflections and descriptive phrases. References within the converted scope link to local rule files or explicit subsection anchors. The text `destroyed` targets `DESTROYING SHIPS`.[^converter]

Generic Appendix and individual device-entry references link to the local index’s `appendix-examples` anchor. Existing Glossary rules retain link ownership when an Appendix card shares their title. References outside the scope link to a bundled source PDF with `#page=N`: Squad Building to 43, Huge Ships to 44, and Environment Cards to 49. Both formats bundle the PDF under its original filename inside their own output folder. Page navigation depends on the PDF viewer.[^converter]

## Illustrations and captions

The converter renders all 78 illustrations from isolated PDF content as transparent 216 dpi PNGs. Original clipping paths, soft masks, form calls, and diagram annotations are retained. Page 2's pilot/ship abilities example and page 4's single-turret diagram keep embedded labels inside their images. Other captions are separate searchable italic Markdown paragraphs and italic HTML `figure`/`figcaption` content. HTML figures whose trimmed PNG width and height are both below 155 pixels float right with captions underneath, allowing text to wrap beside them. Missing groups stop conversion before generated files are replaced.[^converter][^checks]

See [Rules Reference Illustrations](rules-reference-illustrations.md) for group mappings, annotation preservation, transparent trimming, caption extraction, placement anchors, and the original two-image trial.

## HTML styling and icons

Every generated HTML page, including the index, ends with a semantic footer containing “© & ™ Lucasfilm Ltd. The AMG logo is a ® of Atomic Mass Games.” The centered text uses .625rem, #444 on white, and 1.4 line height. A column flex layout places it at the bottom of short pages and after content on long pages, inside the scrolling region. The footer remains present when printing.[^converter][^styling]

For phone installation, app icons, and offline caching, see [Rules Reference PWA](rules-reference-pwa.md).

Both generated output folders are self-contained. Copy `docs/` alone and open `index.html`, or copy `markdown/` alone and open `index.md`. All generated local links stay inside the respective folder. HTML includes stylesheets, frame image, icon font, and font license. Illustrations are rendered once and written into both `markdown/assets/` and `docs/assets/`. Relocation regression checks copy each format to a separate directory and validate local references and anchors; HTML checks also cover CSS resources. Bundled PDFs and illustration copies are compared by bytes.[^converter][^checks]

HTML uses Python-Markdown to render the extracted paragraphs and lists. Inline emphasis, source text colors, green references, and subsection targets are retained. Subsection IDs are placed directly on h2 headings so empty anchor paragraphs do not add vertical gaps. Pages show a Rules Reference home navigation link above 40rem; the header is hidden at widths up to 40rem and when printing. Rule subsection headings use #004761 and a 1.1em font size (10% above body text). Page titles are black without an underline and use 1.25em (25% above body text); inline font icons use 1.2em, 20% smaller than the vendored 1.5em default. `web/style.css` supplies responsive and print layouts. See [Rules Reference Typography](rules-reference-typography.md) for bundled fonts, PDF measurements, and text spacing.[^converter][^styling]

Font icons use green `#4F8535` for focus, evade, calculate, and reinforce; orange `#C46312` for jam, disarm, and tractor; blue `#287F91` for cloak and shield; red `#C40025` for lock, stress, strain, deplete, ion, geometric arcs, range bonus indicator, and critical markers; golden yellow `#A07800` for charges and recurring-charge symbols; and purple `#875392` for energy and force symbols. Hit and critical-hit result glyphs retain inherited text color. These CSS colors affect font icons; token illustrations remain raster crops.[^styling][^converter]

The bundled X-Wing Miniatures Font is pinned to commit `2664d8e9efffd4f1f7a0feac08a21bd123ce3c8a`. Its TTF, icon-only CSS, and MIT license are copied from `web/vendor/xwing-miniatures-font/` into HTML output. HTML renders 61 of the 63 symbol tags with accessible icon labels. Upstream has no hyperdrive or threat glyph, so `[hyperdrive]` and `[threat]` remain readable text. Markdown retains all textual tags. Conversion and viewing need no network access after dependencies are installed.[^converter][^icon-font]

## HTML graphical margins

Every HTML document uses `docs/assets/page-frame.png`, extracted from physical page 3 at 216 dpi (1836×2376 pixels). A temporary copy retains only the background form's first marked-content artifact, excluding rules, copyright text, and page numbers. Rendering clips bleed to the visible page. Keep the original image transformation and graphics state, and restore the CMYK transparency group omitted by `insert_pdf`; raw image extraction and reinsertion changes rendered colors. The source PDF is not modified. Missing margin artwork stops conversion before replacing generated files.[^converter]

CSS `border-image` uses 530-pixel vertical slices and 590-pixel horizontal slices, retaining the full 590×530 source-pixel corner regions containing diagonal graphics. Corners scale uniformly to a 70px artwork height. Most of the 530-source-pixel corner slice is white space; the visible rim occupies about 90 source pixels. The content clipping inset therefore uses 70 * 90 / 530, about 11.89px at the top and bottom, independently of artwork height. Only middle edge sections stretch around the viewport. The body frame is fixed to the viewport edges, keeping the frame visible while a focusable, labeled `.page-content` region scrolls and clips navigation and main content inside the frame. Desktop layout retains its 70rem maximum width, 30px side insets, 1rem/1.5rem vertical/horizontal content padding, and 2rem outer margins; outside background is #030404. Desktop frame edges use a 2rem inset; mobile uses zero inset. Frame sizing does not use vh/dvh heights, avoiding dependence on viewport-unit recalculation during PWA navigation. Print restores static body positioning and resets content height and overflow so all rules print. Frame extraction and illustration crops remain unchanged.[^styling][^converter]

At viewport widths up to 40rem, body text uses 1rem instead of the desktop 1.1rem, side insets are 10px, and outer margins are zero. Frame artwork remains 70px high while the top and bottom content clipping insets are about 11.89px. Content padding is .375rem. Paragraph gaps use 1em/3 and list/item gaps use 1.1em/3, preserving one-third desktop spacing. Bullet and numbered lists have zero inline margins and 1.25em inline-start padding with native outside markers. Item text and wrapped lines remain indented to the right of the markers. Nested lists repeat this hanging indent relative to their parent text edge. First item paragraphs retain block flow with zero top margin.[^styling]

The margin regression check compares sampled top and side pixels with the rendered source PDF and confirms the frame interior is white. Existing illustration preservation checks remain applicable.[^checks]

## Verification and limits

Run `python -m unittest discover -s tests -v`. Checks cover section and file naming, all generated link/image references and explicit anchors, the ERRATA boundary, paragraph continuations, numbered and nested lists, symbol tags, illustration placement, and failure without replacing existing output. Every one of the 1,917 nonempty regular-font source body lines is checked against generated text. Caption checks cover source text, wrapped and adjacent captions, emphasis, symbols, and HTML figure markup. Artwork checks cover all 78 transparent images, embedded composite wording and visual fidelity, native check/cross glyphs, both cyan arrows, and missing-group failure without replacing output.[^checks]

These checks establish extraction coverage, not a complete editorial review. Fonts, colors, margins, aliases, and crop coordinates are calibrated to this edition; a different PDF requires inspection and updated calibration. Content from physical page 30 onward remains outside the conversion scope.[^readme]

[^converter]: Converter, `FIGURES`, `COMPOSITE_FIGURES`, `figure_content`, `render_blocks`, `SYMBOLS`, `RULE_ALIASES`, `EXTERNAL_RULES`, `translated`, `inline_text`, `extract_blocks`, `organize`, and `convert`.
[^readme]: README, Install and run, Preserved structure, and Verification and limits.
[^checks]: ConversionTests.
[^ignore]: Generated output exclusion in `.gitignore`.
[^styling]: HTML stylesheet, font stacks, colors, responsive and print rules.
[^icon-font]: Pinned upstream README, dist icon CSS, font, and MIT license; accessed 2026-10-31.
