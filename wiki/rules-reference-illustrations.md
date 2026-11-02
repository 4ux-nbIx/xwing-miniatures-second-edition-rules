---
type: Guide
title: Rules Reference Illustrations
description: Isolated PDF content for 78 illustrations, Appendix stat bars and anatomies, captions, inherited graphics state, and transparent PNGs.
sources:
  - id: converter
    resource: convert_rules.py
    title: Illustration mapping and output generation
  - id: artwork
    resource: pdf_artwork.py
    title: Isolated marked-content rendering
  - id: checks
    resource: tests/test_convert_rules.py
    title: Illustration and caption regression checks
  - id: group-trial
    resource: experiments/extract_object_groups.py
    title: Original two-image trial
  - id: styling
    resource: web/style.css
    title: HTML figure and caption styling
generated:
  by: process:project-wiki-publish
  at: 2026-11-02T20:46:09.333Z
---
# Rules Reference Illustrations

## Object groups and composite exceptions

The converter produces 78 illustration assets for physical pages 2–29 of Rules Reference v1.4.6-1. `FIGURE_GROUPS` maps all 78 illustrations to source marked-content IDs (MCIDs). `pdf_artwork.py` isolates those groups in temporary in-memory PDF pages, excluding surrounding page prose and backgrounds. Original raster images, vector paths, clipping paths, soft masks, native form calls, and source paint order are retained. The copied page restores its DeviceCMYK transparency group, which `insert_pdf` omits. The source PDF is never saved or modified.[^converter][^artwork]

`COMPOSITE_FIGURES` keeps labels inside the isolated artwork for page 2's Pilot and Ship Abilities example and page 4's Turret Arcs illustration, named Single turret arc indicator and ID tokens in the mapping. Page 2 includes MCIDs 84–88; page 4 includes MCIDs 495–502. Their labels are interleaved with artwork rather than confined below it, so they do not become separate captions. Text coverage and source-render comparisons verify the embedded wording and visual fidelity.[^converter][^checks]

Multi-panel artwork stays grouped in one image. All artwork renders at 216 dpi with alpha transparency. Only fully transparent margins are trimmed, with one pixel of padding. Artwork can extend beyond the original caption/crop bounds, including the second player marker and Jam token. Page 24’s unmarked queue graphics are explicitly clipped to their diagram bounds. Caption positions must not truncate graphics.[^artwork][^converter]

All illustration bytes are rendered before generated output is written. Missing or ambiguous MCIDs and empty artwork raise errors; there is no page-crop fallback. A missing-group regression check confirms existing output stays unchanged.[^artwork][^converter][^checks]

## Diagram annotations and nested groups

- Preserve bounded `Artifact` marked-content groups whose source BBox center falls within the configured illustration bounds. These include page 20's sideslip arrows and dashed placement lines, and page 21's cyan bank/sideslip arrow.[^artwork]
- Page 20 MCIDs 4117 and 4125 are text groups containing the check and cross glyphs. `FIGURE_GROUPS` includes them explicitly as artwork.[^converter]
- Page 23's Victory Counters Figure MCID 4675 contains nested `PlacedPDF` marked content. Its matching `EMC` closes the group; the first nested `EMC` does not.[^artwork]
- Adjacent groups can share `q`/`Q` clipping scopes. Keep source order and balance the combined stream's outer scopes. The helper is calibrated to this PDF's markup and operator layout, not a general PDF parser.[^artwork]
- Skipped captions can carry a closing `Q` or inherited font/color settings needed by later artwork. Replay non-painting graphics stack, font, graphics-state resource, and color changes from source gaps while omitting prose and path painting. Page 20's left-sideslip arrow otherwise stays inside a preceding ship's clip and disappears, even when its Artifact is selected. Embedded composite labels also require inherited font state.[^artwork][^checks]

## Appendix artwork

`APPENDIX_FIGURES` adds 34 images. Remote stat bars and placement diagrams keep their embedded numbers and check/cross glyphs. Page 29’s two anatomy images retain all labels and cyan callout lines; device/deploy captions remain separate searchable text.[^converter][^checks]

Page 24’s queue boxes are painted outside marked-content groups. `unmarked=True` retains unmarked graphics while dropping unwanted marked text, replaying inherited text spacing and graphics state, and removing full-page background forms. Rendering clips this mode to the calibrated diagram bounds, then trims transparent margins. Other figures retain the existing group-only rendering path.[^artwork][^converter]

## Separate captions

`figure_content` identifies 7–8.1-point EurostileLTStd-Cn caption lines within the configured `FIGURES` bounds. It joins centered wrapped lines across PDF blocks and keeps adjacent captions separate. Markdown renders italic caption paragraphs below images; HTML uses italic `figure`/`figcaption` content. Bold emphasis and symbol tags are retained. Printed card text, diagram numbers, and check/cross glyphs stay in the graphics.[^converter]

When visible caption text is inside an isolated native group, text-only redaction removes it from the temporary page while retaining raster and vector artwork. The nested Victory Counters group requires this treatment. Captions remain searchable in both generated text formats. Keep each output's `assets/` directory with its section folders and index.[^artwork][^converter]

## Figure placement

- Figure reading order uses the configured bounds' horizontal center to select the left or right column at x=306. The page 23 Victory Counters bounds start at x=300 but belong in the right column. Using the left edge would place the image in the continuing Tractor rule.[^converter]
- Insertion anchors in `FIGURES` must follow the owning heading. The page 13 Fuse Marker anchor is y=292, after its heading at y=278.13. Its former y=265 anchor attached deferred artwork to Fully Execute.[^converter]
- To place artwork immediately after a heading, the anchor must also precede the first body line. Page 13's Ion token anchor is y=273, between the heading's bottom at y=272.48 and prose at y=273.24. Otherwise paragraph deferral places the image after the opening paragraph.[^converter]

HTML figures float right when both trimmed PNG dimensions are strictly below 155 pixels. The figure width uses the native PNG width, capped at 45% of available width. At viewport widths up to 40rem, figure width is 70% of native width and the cap is 31.5%, reducing both dimensions by 30%; captions wrap below the image inside the float using italic text at .8em. Larger figures retain block placement. Subsection headings clear right floats, and `main` contains them.[^converter][^styling]

A small HTML figure deferred until an unindented paragraph ends is inserted before that paragraph so its text can wrap. Markdown retains the extraction order. On physical page 17, First Player Marker, Position Marker, and the primary weapon card crop qualify; player markers and the range diagram remain blocks.[^converter]

## Original two-image trial

Run `.venv/bin/python experiments/extract_object_groups.py` from the repository root. This standalone trial writes transparent 216 dpi PNGs under `experiments/object-groups/`: `agility.png` (105×131) and `double-turret-arc-indicator.png` (198×182). It selects physical page 3 Figure MCID 296 and page 4 Figure MCID 503, retaining clipping paths, form calls, soft masks, and graphics states. Built-in assertions check retained card text, absent captions, transparent margins, and unchanged source PDF bytes. The trial retains its original bounds; production rendering additionally trims fully transparent margins.[^group-trial][^artwork]

[^converter]: `FIGURES`, `FIGURE_GROUPS`, `COMPOSITE_FIGURES`, `figure_content`, `extract_blocks`, `render_blocks`, and `convert`.
[^artwork]: `figure_stream`, `isolate_figure`, and `render_figure`.
[^checks]: `ConversionTests`, object-group coverage, caption preservation, composite comparisons, and failure preservation.
[^group-trial]: `FIGURES`, `extract_group`, and `main`.
[^styling]: HTML stylesheet, figure, figure-right, figcaption, heading clearing, and main containment.
