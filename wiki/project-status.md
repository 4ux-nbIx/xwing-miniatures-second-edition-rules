---
type: Project Status
title: Project Status
description: Introduction and Glossary coverage, generated output organization, and source-specific fidelity limits.
stale_after: 2026-11-06
generated:
  by: process:project-wiki-publish
  at: 2026-10-31T17:29:27.021Z
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

The source is `Rules Reference v1.4.6-1.pdf`. The Python/PyMuPDF converter produces Introduction and Glossary from physical pages 2–23: an index and 152 rule files per format in `converted/markdown/` and `converted/html/`. Markdown uses 44 crops under `converted/assets/`. HTML is portable, including its own copies of illustrations and the source PDF, plus local styles, frame, and icon assets with approximate source typography.[^converter]

Conversion stops before APPENDIX: EXAMPLES on page 24; the cover and all appendices are excluded. Fonts, symbols, aliases, and crop coordinates are calibrated to this edition. Coverage checks do not establish a complete editorial review.[^readme]

See [Rules Reference Conversion](rules-reference-conversion.md) for installation, output, symbol handling, and reference behavior. Ownership and delivery milestones remain unspecified.

## Review

Review by 2026-11-06. The short review window reflects the initial stage: conversion coverage and fidelity constraints may quickly change.

See [X-Wing Reference Conversion](project.md) for project purpose and scope.

[^converter]: Converter, `extract_blocks`, `organize`, and `convert`.
[^readme]: README, Verification and limits.
