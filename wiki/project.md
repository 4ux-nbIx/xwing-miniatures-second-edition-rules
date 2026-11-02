---
type: Project
title: X-Wing Reference Conversion
description: Convert the X-Wing Rules Reference v1.4.6-1 PDF to structured Markdown and styled offline HTML with source-specific Python extraction.
generated:
  by: process:project-wiki-publish
  at: 2026-11-02T20:46:09.333Z
sources:
  - id: converter
    resource: convert_rules.py
    title: Rules Reference converter
---
# X-Wing Reference Conversion

The project converts an X-Wing reference PDF to Markdown and styled offline HTML.

## Scope

- Input: `Rules Reference v1.4.6-1.pdf`, a 49-page US Letter PDF.
- Output: Markdown and HTML preserving document parts, rule sections, paragraphs, lists, cross-references, and illustrations. Markdown retains textual symbol tags; HTML renders supported symbols with a bundled icon font.

The Python/PyMuPDF converter supports physical pages 2–29: Introduction, Glossary, and APPENDIX: EXAMPLES. It skips the cover and stops before physical page 30. Each format has a sectioned index and one section-prefixed file per rule. HTML is under `docs/` and Markdown under `markdown/`; both retain `introduction/`, `glossary/`, and `appendix-examples/` section folders. Both output folders include their own illustrations and source PDF.[^converter]

See [Rules Reference Conversion](rules-reference-conversion.md) for the workflow and fidelity boundary. Target readers remain unspecified.

See [Project Status](project-status.md) for current direction and constraints.

[^converter]: Converter, `extract_blocks`, `organize`, and `convert`.
