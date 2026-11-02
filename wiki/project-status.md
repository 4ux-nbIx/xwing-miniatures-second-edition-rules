---
type: Project Status
title: Project Status
description: Introduction, Glossary, and Appendix Examples coverage, generated output organization, and source-specific fidelity limits.
stale_after: 2026-11-06
generated:
  by: process:project-wiki-publish
  at: 2026-11-02T20:46:09.333Z
sources:
  - id: converter
    resource: convert_rules.py
    title: Rules Reference converter
  - id: readme
    resource: README.md
    title: Converter workflow and limitations
---
# Project Status

## Direction

Convert an X-Wing reference PDF to Markdown and styled offline HTML.

## Current State and Constraints

The source is `Rules Reference v1.4.6-1.pdf`. The Python/PyMuPDF converter produces Introduction, Glossary, and Appendix: Examples from physical pages 2–29: an index and 179 rule/example files per format in `markdown/` and `docs/`. Both formats retain `introduction/`, `glossary/`, and `appendix-examples/` section folders. Each output folder is portable, including 78 illustrations and the source PDF. Illustrations use isolated PDF content with transparency. Appendix pages include 21 object cards, three device/deploy examples, two card anatomy images, and page 24’s extended examples. Callout diagrams, remote stat bars, and card anatomies keep embedded labels; other captions render as separate text. HTML also bundles local styles, frame, and icon assets with approximate source typography.[^converter]

Conversion stops before physical page 30’s ERRATA boundary; the cover and pages 30–49 are excluded. Fonts, symbols, aliases, and crop coordinates are calibrated to this edition. Coverage checks do not establish a complete editorial review.[^readme]

See [Rules Reference Conversion](rules-reference-conversion.md) for installation, output, symbol handling, and reference behavior. Ownership and delivery milestones remain unspecified.

## Review

Review by 2026-11-06. The short review window reflects the initial stage: conversion coverage and fidelity constraints may quickly change.

See [X-Wing Reference Conversion](project.md) for project purpose and scope.

[^converter]: Converter, `extract_blocks`, `organize`, and `convert`.
[^readme]: README, Verification and limits.
