---
type: Guide
title: Rules Reference Typography
description: Bundled open fonts, PDF page 2 typography measurements, compact heading hierarchy, and desktop/mobile paragraph and list spacing.
sources:
  - id: typography
    resource: web/vendor/typography/NOTICE.md
    title: Bundled typography provenance
  - id: styling
    resource: web/style.css
    title: Shared typography styles
  - id: converter
    resource: convert_rules.py
    title: HTML generation and offline asset copying
generated:
  by: process:project-wiki-publish
  at: 2026-11-02T20:58:41.257Z
---
# Rules Reference Typography

## Font selection and offline use

Local WOFF2 assets bundle Rajdhani Medium (500) and Bold (700) for body/emphasis, with Exo 2 ExtraBold (800) for headings. These open fonts were selected against the Eurostile Condensed, Bold, and small-cap styles on physical PDF page 2. Subsection headings use small capitals. Both families include SIL Open Font License notices and pinned Google Fonts provenance; commercial PDF fonts are not bundled. Conversion copies these assets into the HTML folder and includes them in the offline cache.[^typography][^styling][^converter]

Source page 2 uses EurostileLTStd-Cn body text (8.5pt), EurostileLTStd-Bold rule headings (11pt), and EurostileLTStd-Bold-SC70 subsections (10pt with smaller capitals). Bank Gothic appears within the card illustration rather than primary rule headings. The bundled alternatives approximate this appearance; fonts and line wrapping are not identical to the PDF.[^typography]

Font source is pinned to Google Fonts commit `6c1dbe27dcf7d817d4b62cec033ba77fa8e2a5ec`. Full glyph sets are converted to WOFF2 using FontTools 4.68.0 and Brotli 1.2.1; Exo 2 is instantiated at weight 800 before conversion. Conversion needs no font-build tools after these assets are bundled.[^typography]

## Heading and paragraph rhythm

Appendix index group headings use h3 with black `#000` text at `.9em`, retaining the shared heading font and weight. Their margins are `.75em` above and `.15em` below.[^styling]

Body line-height is 1.2, matching page 2's 10.2pt baseline advance for 8.5pt text. Paragraph gaps use 1em and list/item gaps use 1.1em, slightly increasing the original PDF-derived gaps for readability. Page titles have .2em bottom margins; subsections have .75em top and .15em bottom margins, with a .2em top margin immediately after a page title. Desktop lists use 1.6em hanging indents. First/last item paragraphs avoid duplicate spacing.[^styling]

Page titles remain black at 1.25em; blue #004761 subsection headings use 1.1em and small capitals. Heading sizes scale with the desktop/mobile body size. Subsection IDs sit directly on h2 headings, avoiding empty anchor paragraphs that otherwise introduce unwanted space.[^styling][^converter]

At widths up to 40rem, paragraph gaps use 1em/3 and list/item gaps use 1.1em/3, retaining the compact mobile rhythm. Mobile hanging indents remain 1.25em; nested lists indent relative to their parent text. See [Rules Reference Conversion](rules-reference-conversion.md) for layout, graphical margins, and conversion workflow.[^styling]

[^typography]: Bundled font provenance, pinned source revision, conversion versions, and adjacent SIL Open Font License notices.
[^styling]: Shared stylesheet, @font-face, heading, paragraph, list, and mobile rules.
[^converter]: HTML wrapper, subsection anchor normalization, web asset copy, and offline bundle generation.
