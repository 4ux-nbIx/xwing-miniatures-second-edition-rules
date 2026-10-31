# X-Wing Rules Reference converter

A source-specific Python converter for `Rules Reference v1.4.6-1.pdf`.
It converts physical pages 2–23: Introduction and Glossary. The cover is omitted,
and conversion stops before `APPENDIX: EXAMPLES` on page 24.

## Install and run

Use Python 3.10 or newer:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python convert_rules.py
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell.
On Linux systems without `ensurepip`, install the matching Python venv package.
If a mounted filesystem rejects symlinks, use `python -m venv --copies .venv`;
some systems also require creating `.venv/lib64` as a directory first.

Open `converted/html/index.html` in a browser or `converted/markdown/index.md` in a
Markdown viewer. Both formats contain section descriptions and linked tables of
contents, preserving source order. Each rule has its own file under its section
folder, with a section-prefixed kebab-case filename:

```text
converted/
  markdown/
    index.md
    introduction/
      introduction-golden-rules.md
      ...
    glossary/
      glossary-abilities.md
      ...
  html/
    index.html
    style.css
    Rules Reference v1.4.6-1.pdf
    assets/
      page-frame.png
      page-02-pilot-and-ship-abilities.png
      ...
    introduction/
      introduction-golden-rules.html
      ...
    glossary/
      glossary-abilities.html
      ...
    vendor/xwing-miniatures-font/
      xwing-miniatures.css
      xwing-miniatures.ttf
      LICENSE
  assets/
    page-02-pilot-and-ship-abilities.png
    ...
```

Each format has 3 Introduction rules and 149 Glossary rules. HTML includes copies
of all 44 illustration crops and the source PDF, alongside its frame, styles, and
icon font. Copy `converted/html/` anywhere and open `index.html`; all generated
file links stay inside that folder, including appendix links to the bundled PDF.
Markdown uses the sibling `converted/assets/` folder and the original source PDF.
Keep those files together when moving Markdown output. Rerunning replaces
the generated files. Existing output from earlier versions stays outside the new indexes; old links may be stale.
To choose another output directory:

```sh
python convert_rules.py "Rules Reference v1.4.6-1.pdf" -o converted-review
python -m unittest discover -s tests -v
```

`-o` now accepts a directory, rather than the previous preview's Markdown filename.
The `converted/` tree is ignored by Git according to the repository's `.gitignore`.

## Preserved structure

- Document part headings and their introductory paragraphs appear in the index.
  Each rule file starts with a level 1 heading and keeps its subsections beneath it.
- The left column precedes the right column. Rules and paragraphs continue across
  columns and pages. Borders, copyright footers, and printed page numbers are omitted.
- Paragraphs, bold text, numbered lists, and nested bullets are retained. Lettered
  substeps retain their original labels as nested bullets, such as `- **a.**`.
- Green references link to rule files or subsection anchors. Explicit aliases
  handle inflections and terms such as `destroyed`, which targets `DESTROYING SHIPS`.
  References to appendices outside the conversion link to the relative source PDF
  with `#page=N`. HTML links to its bundled PDF; Markdown links to the original.
  Page navigation depends on viewer support.
- In Markdown, custom `X-WingIcons` characters become textual tags such as `[focus]`, `[hit]`,
  `[charge]`, and `[bank-left]`. `SYMBOLS` contains all 62 mappings used in this scope.
- Composite illustrations, diagrams, tokens, and captions are 216 dpi PNG crops.
  Their internal text is excluded from the Markdown body. Overlapping body text
  remains in Markdown and is removed from a temporary PDF page before rendering
  crop margins, retaining the underlying artwork.
- Unknown custom symbols, unresolved green references, or a missing appendix
  boundary stop conversion before generated files are replaced.

## HTML styling and icons

HTML uses condensed sans-serif body text, heavy geometric headings, source text
colors, and green rule links. Local font stacks approximate Eurostile and Bank
Gothic; those commercial fonts are not bundled. Layout adapts to narrow screens
and printing. Each rule links back to the HTML index.

Every HTML page uses graphical margins extracted from the PDF's physical page 3.
Only its full-page background image is rendered, clipped to the visible page area;
rules, copyright text, and page numbers are excluded. CSS `border-image` applies
the extracted `html/assets/page-frame.png` as a nine-slice frame. Each corner uses
590×530 source pixels, preserving the diagonal lines at the top right and bottom
left. Corners scale uniformly with the rim; only the middle edges stretch around
the full content height. A decorative layer behind the text keeps the large
corners from covering content or adding excess padding. The border is
30 pixels wide on desktop and 20 pixels on narrow screens. The center stays white.

Inline tags such as `[bank-left]` become accessible icons using
[geordanr/xwing-miniatures-font](https://github.com/geordanr/xwing-miniatures-font).
The icon font, CSS, and MIT license are bundled locally, so conversion and viewing
need no network access. Upstream has no hyperdrive or threat glyph; those two
symbols retain their readable tags. Markdown always retains all textual tags.

Vendored assets are pinned to upstream commit
`2664d8e9efffd4f1f7a0feac08a21bd123ce3c8a`. The CSS includes only the icon portion;
the unused ship font is omitted. `web/style.css` supplies document styling.
Python-Markdown renders the existing paragraph and list structure into HTML.

## Verification and limits

Tests cover every generated local link, image, and explicit subsection anchor;
section/file naming; the appendix boundary; continuations across pages; list
structure; failure without replacing existing output; and preservation of all
1,917 nonempty source body lines. Overview pages and illustration crops were
visually reviewed during implementation. These checks establish extraction
coverage, not a word-for-word editorial review of the whole rulebook.

Fonts, colors, margins, spacing thresholds, aliases, and crop coordinates are
calibrated to this specific edition. A different PDF requires inspection and
updated calibration. Illustration text remains raster content rather than
searchable Markdown. No OCR or model downloads are needed.

PyMuPDF is available under AGPL or a commercial license. Review the appropriate
license before distributing the converter as part of another product.
