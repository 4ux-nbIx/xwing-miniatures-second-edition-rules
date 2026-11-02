---
type: Guide
title: Rules Reference PWA
description: Phone installation, relative app identity, generated icons, offline rule caching, and update behavior for the GitHub Pages site.
sources:
  - id: converter
    resource: convert_rules.py
    title: HTML and service worker generation
  - id: manifest
    resource: web/manifest.webmanifest
    title: App identity and icons
  - id: registration
    resource: web/pwa.js
    title: Worker registration
  - id: worker
    resource: web/sw.js
    title: Scoped offline cache
  - id: readme
    resource: README.md
    title: Install on a phone
generated:
  by: process:project-wiki-publish
  at: 2026-11-02T21:19:02.150Z
---
# Rules Reference PWA

## Installation and assets

The generated `docs/` site supports standalone installation through a web app manifest. Every HTML page links to the manifest, favicon, Apple touch icon, and registration script. Relative identity, start URL, scope, and asset paths support repository subpaths and custom domains. The source artwork is `web/icons/icon.png`, preserved from the supplied 129×129 transparent PNG. It serves as the preferred favicon. The 192px and 512px manifest icons, 180px Apple touch icon, and 32px `web/favicon.ico` derive from it; larger sizes are upscaled. Manifest icons use purpose `any` because the artwork extends to the edges without a maskable safe area.[^converter][^manifest][^readme]

Deploy `docs/` through GitHub Pages over HTTPS. Android Chrome offers **Install app** or **Add to Home screen** in its menu. In iPhone/iPad Safari, use **Share**, then **Add to Home Screen**; enable **Open as Web App** when offered. Opening local HTML files still works, but installation and service workers require HTTPS or localhost. Preview with `python -m http.server --directory docs` and open `http://localhost:8000`.[^readme]

PWA source assets live in `web/` and are copied during conversion. Change the source assets and regenerate rather than editing only `docs/`. Worker registration resolves from the script URL, including on nested rule pages; file URLs skip registration.[^converter][^registration]

## Offline cache and updates

The first online visit downloads the Introduction, Glossary, illustrations, styles, and fonts as an atomic offline bundle. **The 74 MB source PDF is excluded; appendix links require a connection.** Browser storage eviction can remove offline content; revisit online to restore it.[^converter][^worker][^readme]

Conversion hashes generated HTML, non-PDF assets, and the worker template into a cache version. Cache names include the registration scope. The worker handles only same-origin GET requests within its scope, maps the scope root to the cached index, and sends uncached requests to the network.[^converter][^worker]

Updates download a complete bundle and wait until existing app windows and site tabs close. Reopen to use the new version. Activation deletes only older caches belonging to this app scope and claims clients.[^worker][^readme]

[^converter]: `html_document` and `convert`.
[^manifest]: Relative app identity, standalone display, and icon entries.
[^registration]: Script-relative service worker URL and protocol guard.
[^worker]: Install, activate, and fetch handlers.
[^readme]: Install on a phone.
