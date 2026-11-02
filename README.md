# X-Wing Rules Reference converter

A source-specific Python converter for `Rules Reference v1.4.6-1.pdf`.
It converts physical pages 2–29: Introduction, Glossary, and `APPENDIX: EXAMPLES`.
The cover and content from page 30 onward are omitted.

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

Open `docs/index.html` in a browser or `markdown/index.md` in a Markdown viewer.
Both formats contain section descriptions and linked tables of contents in source
order. Both formats retain `introduction/`, `glossary/`, and `appendix-examples/` section folders, with
section-prefixed kebab-case filenames:

```text
markdown/
  index.md
  introduction/
    introduction-golden-rules.md
    ...
  glossary/
    glossary-abilities.md
    ...
  Rules Reference v1.4.6-1.pdf
  assets/
    page-02-pilot-and-ship-abilities.png
    ...
docs/
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
```

Each format has 3 Introduction rules, 149 Glossary rules, and 27 Appendix pages.
The Appendix contains page 24’s extended examples, 21 separate object cards from
pages 25–28, three device/deploy examples, and two card anatomy pages from page 29.
The Appendix index groups its links under Examples, Objects: Bombs and Mines,
Objects: Obstacles, Objects: Remotes, Device and Deploying Examples, and Card
Anatomies. Object cards retain their text and artwork without decorative card borders. Remote
stat bars and card anatomies retain embedded labels as images.
Both folders are self-contained, including all 78 illustration assets and a copy of the source PDF.
Copy either folder anywhere and open its index; all generated file links stay
inside that folder, including links to the remaining sections in the bundled PDF. HTML also
includes its frame, styles, and icon font.

Rerunning replaces generated files. Existing output from earlier versions stays
outside the new indexes; old links may be stale. To choose another parent directory:

```sh
python convert_rules.py "Rules Reference v1.4.6-1.pdf" -o converted-review
python -m unittest discover -s tests -v
```

This writes `converted-review/docs/` and `converted-review/markdown/`.
`-o` accepts a parent directory, defaulting to the current directory.
The generated `markdown/` and legacy `converted/` trees are ignored by Git.
The `docs/` tree can be tracked by Git.

## Preserved structure

- Document part headings and their introductory paragraphs appear in the index.
  Each rule file starts with a level 1 heading and keeps its subsections beneath it.
- The left column precedes the right column. Rules and paragraphs continue across
  columns and pages. Borders, copyright footers, and printed page numbers are omitted.
- Paragraphs, bold text, numbered lists, and nested bullets are retained. Lettered
  substeps retain their original labels as nested bullets, such as `- **a.**`.
- Green references link to rule files or subsection anchors. Explicit aliases
  handle inflections and terms such as `destroyed`, which targets `DESTROYING SHIPS`.
  Appendix references link to the local index. References outside the conversion link to the relative source PDF
  with `#page=N`. Both formats link to their own bundled PDF.
  Page navigation depends on viewer support.
- In Markdown, custom `X-WingIcons` characters become textual tags such as `[focus]`, `[hit]`,
  `[charge]`, and `[bank-left]`. `SYMBOLS` contains all 63 mappings used in this scope.
- Illustrations, diagrams, and tokens are transparent 216 dpi PNGs rendered from
  isolated PDF object groups. Original clipping paths, soft masks, colors, and
  diagram annotations are retained; page backgrounds and nearby prose are excluded.
  Fully transparent margins are trimmed without cutting off artwork. Captions below artwork
  are extracted as italic text in Markdown and HTML, retaining bold emphasis and symbol tags.
  HTML groups images and captions in `figure`/`figcaption` elements. Images whose
  trimmed PNG width and height are both below 155 pixels float right with their
  captions underneath, allowing prose to wrap around them. On screens up to 40rem,
  floating images shrink by 30%. Captions use 80% of the body font size. The page 2
  pilot/ship abilities example and page 4 single-turret diagram retain their embedded
  labels in the isolated artwork instead of extracting them as captions. Printed text and numbers on
  cards and diagrams remain part of the graphics. `FIGURE_GROUPS` maps the source
  marked-content IDs; `pdf_artwork.py` renders them without modifying the source PDF.
  Page 24’s queue diagrams also retain unmarked box graphics and clip to their
  calibrated bounds. Missing groups stop conversion before any generated files are replaced.
- Unknown custom symbols, unresolved green references, or a missing conversion
  boundary (`ERRATA` on physical page 30) stop conversion before generated files are replaced.

## HTML styling and icons

HTML uses locally bundled Rajdhani Medium/Bold for condensed body text and
Exo 2 ExtraBold for headings, selected against the Eurostile fonts on PDF page 2.
Both are distributed under the SIL Open Font License; licenses and pinned source
details live in `web/vendor/typography/`. Commercial PDF fonts are not bundled.
Source text colors and green rule links are retained. Layout adapts to narrow screens
and printing. Page titles are black without an underline, and pages omit the
navigation header on narrow screens and when printing. Above 40rem, the header
includes a Rules Reference home link. Rule subsection headings use #004761.
Subsection headings are 10% larger than body text; page titles are 25% larger.
Subsections use small capitals. Body line height is 1.2, matching the PDF's
10.2pt baseline spacing for 8.5pt text. Paragraph gaps use 1em and list gaps
use 1.1em for slightly more breathing room; headings sit close to the text that follows.
Inline icons are 20% smaller and use token-specific colors.
Narrow screens use smaller body text and half the previous page inset.
Mobile paragraph and list gaps use one third of the desktop spacing.
Bullet and numbered lists use native outside markers with a compact 1.25em
hanging indent. Item text and wrapped lines stay to the right of the markers.
Nested lists repeat the same indentation relative to their parent's text edge.

Every HTML page uses graphical margins extracted from the PDF's physical page 3.
Only its full-page background image is rendered, clipped to the visible page area;
rules, copyright text, and page numbers are excluded. CSS `border-image` applies
the extracted `docs/assets/page-frame.png` as a nine-slice frame. Each corner uses
590×530 source pixels, preserving the diagonal lines at the top right and bottom
left. Corners scale uniformly to a 70-pixel artwork height. The visible rim occupies
only 90 of the 530 source pixels, so content clips about 12 pixels from each
edge rather than reserving the entire artwork height.
The frame stays within the viewport; content scrolls inside it and clips at its
inner edges. Desktop layout retains its 70rem maximum width, 30-pixel side inset,
and horizontal content padding. Narrow screens use a 10-pixel side inset.
The center stays white; the surrounding desktop background is #030404.
The frame anchors to the viewport edges rather than using `vh`/`dvh` heights,
avoiding dependence on viewport-unit updates after mobile PWA navigation.
Print layout expands the content so scrolling does not hide printed rules.

Inline tags such as `[bank-left]` become accessible icons using
[geordanr/xwing-miniatures-font](https://github.com/geordanr/xwing-miniatures-font).
The icon font, CSS, and MIT license are bundled locally, so conversion and viewing
need no network access. Upstream has no hyperdrive or threat glyph; those two
symbols retain their readable tags. Markdown always retains all textual tags.

Vendored assets are pinned to upstream commit
`2664d8e9efffd4f1f7a0feac08a21bd123ce3c8a`. The CSS includes only the icon portion;
the unused ship font is omitted. `web/style.css` supplies document styling.
Python-Markdown renders the existing paragraph and list structure into HTML.

## Install on a phone

Deploy `docs/` through GitHub Pages over HTTPS. The site includes a web app
manifest, favicon, Apple touch icon, and maskable 192px and 512px app icons.
Relative URLs support both a repository subpath and a custom domain.

- Android Chrome: open the site and use **Install app** or **Add to Home screen**
  from the browser menu.
- iPhone/iPad Safari: open the site, tap **Share**, then **Add to Home Screen**.
  Enable **Open as Web App** if offered.

Keep the first visit online while the service worker downloads the Introduction,
Glossary, Appendix examples, illustrations, styles, and fonts. These remain available offline after
the download completes. The 74 MB source PDF is excluded from the offline cache;
links to sections outside the converted scope require a connection. Browser storage eviction can remove offline
content; revisit online to restore it.

Each conversion generates a content-versioned service worker. Updates download
as a complete bundle and activate after all open app windows and site tabs close.
Reopen the app to use the new version. Opening HTML directly from disk still
works, but installation and service workers require HTTPS (or localhost for testing).
To preview locally, run `python -m http.server --directory docs`, then open
`http://localhost:8000`. Run service worker checks with `node --test tests/test_pwa.cjs`.

PWA source assets live in `web/` and are copied during conversion. The original
vector icon is `web/icons/icon.svg`; PNG sizes and `web/favicon.ico` derive from it.

## Verification and limits

Tests cover every generated local link, image, and explicit subsection anchor;
section/file naming; the conversion boundary; continuations across pages; list
structure; failure without replacing existing output; and preservation of all
1,917 nonempty Introduction/Glossary source body lines, plus appendix card body text.
Appendix checks cover individual index entries, remote stats, card anatomy labels,
and source-render comparisons for composite artwork. Overview pages and illustration crops were
visually reviewed during implementation. These checks establish extraction
coverage, not a word-for-word editorial review of the whole rulebook.

Fonts, colors, margins, spacing thresholds, aliases, and crop coordinates are
calibrated to this specific edition. A different PDF requires inspection and
updated calibration. Illustration text remains raster content rather than
searchable Markdown. No OCR or model downloads are needed.

PyMuPDF is available under AGPL or a commercial license. Review the appropriate
license before distributing the converter as part of another product.
