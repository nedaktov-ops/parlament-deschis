---
id: GITHUB-TOOLING-INVENTORY-2026-11-22
type: research
title: "GitHub tooling inventory — visual inspection, content/design, semantic understanding"
description: "Consolidated 13-category inventory of 85 distinct GitHub repositories assembled across three research rounds on website inspection, design, and content understanding."
status: active
authority: unverified
tags: [type/research, lifecycle/active, domain/research]
source_paths: []
created: 2026-11-22
updated: 2026-11-22
source_commit: 618849a
verified: 2026-11-22
---

# GitHub tooling inventory — 2026-11-22

Consolidates three research rounds into one index: (1) tools that visually inspect
a website and suggest improvements, (2) leading repositories in website content
and design, and (3) tools that understand what a website is about and what it
contains. Companions: [RESEARCH-LOG](RESEARCH-LOG.md) for provenance conventions,
[SOURCE-RESEARCH](SOURCE-RESEARCH.md) for source dispositions, and
[START-HERE](../00-START/START-HERE.md) for the vault entry point.

## Provenance and limits

- **VERIFIED 2026-11-22:** star counts and repository names were read from the
  GitHub REST API and live GitHub repository pages on 2026-11-22. Some counts in
  the tables are rounded as originally reported; the day's figures are
  approximate and change continuously.
- **NOT PROVEN against a repo source:** the curated roles, "leading" judgments,
  maintenance statuses (for example "seeking maintainer", "archived on
  22 Apr 2026"), and last-push dates taken from third-party articles. Resolver:
  re-query `https://api.github.com/repos/<owner>/<repo>` after the
  unauthenticated rate-limit reset, and re-read each repository README.
- This is an **external** research artifact: no repo path in
  [SOURCE-MAP](../00-START/SOURCE-MAP.md) is authoritative for it. The note is
  registered as row 31 of that map with status `unverified` and an external
  resolver; it does not become a canonical project note by being indexed.

## Master index

| Part | Category | Entries |
|---|---|---:|
| I | 1. Browser "eyes": render, screenshot, inspect | 5 |
| I | 2. Auditors that emit concrete fixes | 6 |
| I | 3. Visual regression and diffing | 7 |
| I | 4. Behavioral / visual analytics | 2 |
| II | 5. Site frameworks and content platforms | 7 (+4 contenders) |
| II | 6. Design systems and UI component libraries | 7 (+2 contenders) |
| II | 7. Design and canvas tools | 4 |
| II | 8. Icons, fonts and visual assets | 6 (+1 contender) |
| II | 9. CSS, styling and motion | 6 |
| III | 10. URL → LLM-ready readers | 5 |
| III | 11. AI browser agents that interpret pages | 3 |
| III | 12. Main-content and document extraction | 5 |
| III | 13. Metadata, semantics and crawling plumbing | 7 |
| IV | Adjacent, excluded or caveated | 8 |
| | **Distinct repositories (excluding 1 cross-reference)** | **85** |

---

# Part I — Visual inspection and improvement (20)

## 1. Browser "eyes": render, screenshot, inspect

| Repository | Stars | Role |
|---|---:|---|
| [microsoft/playwright](https://github.com/microsoft/playwright) | 100.8k | Browser automation; native `toHaveScreenshot`, traces, three engines |
| [puppeteer/puppeteer](https://github.com/puppeteer/puppeteer) | 95.9k | Google's headless Chrome API; engine under much screenshot tooling |
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | 58.8k | Official DevTools for agents — screenshots, DOM/CSS, console |
| [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 40.0k | Official MCP server; accessibility snapshots and screenshots |
| [AgentDeskAI/browser-tools-mcp](https://github.com/AgentDeskAI/browser-tools-mcp) | 7.3k | Screenshots and browser logs inside Cursor-style IDEs |

## 2. Auditors that emit concrete fixes

| Repository | Stars | Role |
|---|---:|---|
| [GoogleChrome/lighthouse](https://github.com/GoogleChrome/lighthouse) | 31.2k | Performance, accessibility, SEO, best practices plus remediation guidance |
| [stylelint/stylelint](https://github.com/stylelint/stylelint) | 11.6k | CSS linter with autofix |
| [dequelabs/axe-core](https://github.com/dequelabs/axe-core) | 7.9k | Industry-standard accessibility rules engine; zero-false-positive policy |
| [sitespeedio/sitespeed.io](https://github.com/sitespeedio/sitespeed.io) | 5.1k | Deep web-performance analysis with budgets |
| [pa11y/pa11y](https://github.com/pa11y/pa11y) | 4.6k | CLI accessibility tester (HTML CodeSniffer plus axe), CI exit codes |
| [webhintio/hint](https://github.com/webhintio/hint) | 3.7k | Mozilla-origin web hinting engine; last push 2026-07 (NOT PROVEN) |

## 3. Visual regression and diffing

| Repository | Stars | Role |
|---|---:|---|
| [garris/BackstopJS](https://github.com/garris/BackstopJS) | 7.2k | URL-based visual regression with approval report; seeking maintainer (NOT PROVEN) |
| [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) | 7.0k | The pixel-diff primitive used across the ecosystem |
| [rsmbl/Resemble.js](https://github.com/rsmbl/Resemble.js) | 4.6k | Perceptual image comparison; last push 2024 (NOT PROVEN) |
| [americanexpress/jest-image-snapshot](https://github.com/americanexpress/jest-image-snapshot) | 3.9k | Screenshot as a Jest assertion |
| [dmtrKovalenko/odiff](https://github.com/dmtrKovalenko/odiff) | 3.3k | SIMD-first fast image comparison |
| [oblador/loki](https://github.com/oblador/loki) | 1.9k | Storybook visual regression, including React Native |
| [argos-ci/argos](https://github.com/argos-ci/argos) | 666 | Open-source visual regression with PR review UI and ARIA snapshots |

## 4. Behavioral / visual analytics

| Repository | Stars | Role |
|---|---:|---|
| [PostHog/posthog](https://github.com/PostHog/posthog) | 41.0k | Session replay and heatmaps |
| [openreplay/openreplay](https://github.com/openreplay/openreplay) | 13.2k | Self-hostable session replay and cobrowsing |

---

# Part II — Website content and design (30 core + 7 contenders)

## 5. Site frameworks and content platforms

| Repository | Stars | Role |
|---|---:|---|
| [vercel/next.js](https://github.com/vercel/next.js) | 144.0k | Dominant React site and app framework |
| [strapi/strapi](https://github.com/strapi/strapi) | 73.5k | Leading open-source headless CMS |
| [facebook/docusaurus](https://github.com/facebook/docusaurus) | 66.8k | Documentation-site generator |
| [withastro/astro](https://github.com/withastro/astro) | 64.1k | Framework for content-driven sites |
| [nuxt/nuxt](https://github.com/nuxt/nuxt) | 61.1k | Leading Vue site and app framework |
| [TryGhost/Ghost](https://github.com/TryGhost/Ghost) | 55.9k | Independent publishing and newsletters |
| [payloadcms/payload](https://github.com/payloadcms/payload) | 46.0k | Code-first headless CMS |

Close contenders: [gatsbyjs/gatsby](https://github.com/gatsbyjs/gatsby) 55.9k ·
[directus/directus](https://github.com/directus/directus) 38.6k ·
[mdx-js/mdx](https://github.com/mdx-js/mdx) 19.9k ·
[vuejs/vitepress](https://github.com/vuejs/vitepress) 18.5k

## 6. Design systems and UI component libraries

| Repository | Stars | Role |
|---|---:|---|
| [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | 128.7k | Copy-in composable accessible components |
| [ant-design/ant-design](https://github.com/ant-design/ant-design) | 100.3k | Enterprise React design language |
| [mui/material-ui](https://github.com/mui/material-ui) | 99.4k | Canonical Material Design for React |
| [tailwindlabs/tailwindcss](https://github.com/tailwindlabs/tailwindcss) | 98.7k | Utility-first CSS framework |
| [storybookjs/storybook](https://github.com/storybookjs/storybook) | 91.7k | UI component workshop; cross-referenced from Part I |
| [saadeghi/daisyui](https://github.com/saadeghi/daisyui) | 42.9k | Most popular Tailwind component library |
| [radix-ui/primitives](https://github.com/radix-ui/primitives) | 19.5k | Accessible unstyled primitives under shadcn |

Close contenders: [chakra-ui/chakra-ui](https://github.com/chakra-ui/chakra-ui) 40.7k ·
[heroui-inc/heroui](https://github.com/heroui-inc/heroui) 31.3k

## 7. Design and canvas tools

| Repository | Stars | Role |
|---|---:|---|
| [excalidraw/excalidraw](https://github.com/excalidraw/excalidraw) | 136.1k | Hand-drawn-style whiteboard, embeddable |
| [penpot/penpot](https://github.com/penpot/penpot) | 62.6k | Leading open-source Figma alternative |
| [tldraw/tldraw](https://github.com/tldraw/tldraw) | 51.5k | Infinite-canvas React SDK |
| [jgraph/drawio](https://github.com/jgraph/drawio) | 9.5k | Client-side diagramming editor |

## 8. Icons, fonts and visual assets

| Repository | Stars | Role |
|---|---:|---|
| [FortAwesome/Font-Awesome](https://github.com/FortAwesome/Font-Awesome) | 77.0k | Iconic SVG/font/CSS toolkit |
| [simple-icons/simple-icons](https://github.com/simple-icons/simple-icons) | 26.3k | CC0 brand-logo SVGs |
| [lucide-icons/lucide](https://github.com/lucide-icons/lucide) | 25.9k | Community icon toolkit; modern React default |
| [tabler/tabler-icons](https://github.com/tabler/tabler-icons) | 22.8k | 6,500+ MIT SVG icons |
| [google/fonts](https://github.com/google/fonts) | 20.8k | Source of Google Fonts |
| [rsms/inter](https://github.com/rsms/inter) | 20.1k | Default modern UI typeface; last push 2024 (NOT PROVEN) |

Close contender: [vercel/geist-font](https://github.com/vercel/geist-font) 3.8k

## 9. CSS, styling and motion

| Repository | Stars | Role |
|---|---:|---|
| [animate-css/animate.css](https://github.com/animate-css/animate.css) | 83.1k | Cross-browser CSS animations; last push 2024 (NOT PROVEN) |
| [styled-components/styled-components](https://github.com/styled-components/styled-components) | 41.1k | CSS-in-JS pioneer |
| [framer/motion](https://github.com/framer/motion) | 35.4k | Leading React animation library |
| [greensock/GSAP](https://github.com/greensock/GSAP) | 31.1k | Professional web animation standard |
| [postcss/postcss](https://github.com/postcss/postcss) | 29.0k | Plugin ecosystem under modern CSS tooling |
| [sass/dart-sass](https://github.com/sass/dart-sass) | 4.2k | Reference Sass implementation |

---

# Part III — Semantic content understanding (20)

## 10. URL → LLM-ready readers

| Repository | Stars | Role |
|---|---:|---|
| [firecrawl/firecrawl](https://github.com/firecrawl/firecrawl) | 206.6k | Scrape, crawl, map and search to Markdown or schema JSON |
| [microsoft/markitdown](https://github.com/microsoft/markitdown) | 197.7k | File and document to Markdown for LLMs |
| [unclecode/crawl4ai](https://github.com/unclecode/crawl4ai) | 87.7k | Self-hosted LLM-friendly crawler |
| [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) | 32.9k | Plain-English, LLM-driven extraction graphs |
| [jina-ai/reader](https://github.com/jina-ai/reader) | 12.3k | `r.jina.ai/<url>` to LLM-friendly Markdown |

## 11. AI browser agents that interpret pages

| Repository | Stars | Role |
|---|---:|---|
| [browser-use/browser-use](https://github.com/browser-use/browser-use) | 121.7k | LLM drives a real browser toward a goal |
| [browserbase/stagehand](https://github.com/browserbase/stagehand) | 26.1k | Playwright determinism plus LLM reasoning |
| [Skyvern-AI/skyvern](https://github.com/Skyvern-AI/skyvern) | 23.5k | Vision and LLM agent for unconventional DOMs |

## 12. Main-content and document extraction

| Repository | Stars | Role |
|---|---:|---|
| [unstructured-io/unstructured](https://github.com/unstructured-io/unstructured) | 15.8k | Pages and documents to structured LLM-ingestible elements |
| [codelucas/newspaper](https://github.com/codelucas/newspaper) | 15.2k | Article text, headline, author, date, keywords |
| [mozilla/readability](https://github.com/mozilla/readability) | 11.6k | Firefox Reader View article extractor |
| [adbar/trafilatura](https://github.com/adbar/trafilatura) | 7.2k | Main text plus metadata; benchmark leader |
| [apache/tika](https://github.com/apache/tika) | 4.2k | 1,000+ file types to text, metadata and Markdown |

## 13. Metadata, semantics and crawling plumbing

| Repository | Stars | Role |
|---|---:|---|
| [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) | 104.9k | Adaptive selectors, stealth fetchers, spiders |
| [scrapy/scrapy](https://github.com/scrapy/scrapy) | 65.5k | Mature Python crawling framework |
| [cheeriojs/cheerio](https://github.com/cheeriojs/cheerio) | 30.6k | jQuery-style HTML parsing in TypeScript |
| [apify/crawlee](https://github.com/apify/crawlee) | 26.5k | Node.js crawling with proxy rotation |
| [UKPLab/sentence-transformers](https://github.com/UKPLab/sentence-transformers) | 19.3k | Embeddings for topic and classification semantics |
| [microlinkhq/metascraper](https://github.com/microlinkhq/metascraper) | 2.8k | Open Graph metadata: title, description, author, media |
| [scrapinghub/article-extraction-benchmark](https://github.com/scrapinghub/article-extraction-benchmark) | 378 | Reference dataset for comparing extractors |

---

# Part IV — Adjacent, excluded or caveated (8)

| Repository | Status / reason |
|---|---|
| [abi/screenshot-to-code](https://github.com/abi/screenshot-to-code) | 81.4k — converts screenshots to code; adjacent, not a site auditor |
| [percy/cli](https://github.com/percy/cli) | 86 stars — open-source repo is only an uploader for hosted Percy |
| Chromatic (Storybook team) | Hosted SaaS; no meaningful open-source core |
| Applitools | Hosted enterprise visual AI; no open-source core |
| [lost-pixel/lost-pixel](https://github.com/lost-pixel/lost-pixel) | Archived 2026-04-22 per third-party report (NOT PROVEN) |
| BBC/Wraith | Archived 2026-01-16 per third-party report (NOT PROVEN) |
| [YellowLabTools/YellowLabTools](https://github.com/YellowLabTools/YellowLabTools) | 2.5k — last push 2024 (NOT PROVEN) |
| [html-validate/html-validate](https://github.com/html-validate/html-validate) | 19-star GitLab mirror |

---

## Cross-cutting notes

- Only categories 2 and 10–12 inherently explain content; categories 1, 3, 4
  and 13 surface evidence that a human or agent interprets.
- Licence flags to check before adoption: `firecrawl/firecrawl` and
  `Skyvern-AI/skyvern` are AGPL-3.0; `dequelabs/axe-core` is MPL-2.0;
  `pa11y/pa11y` is LGPL-3.0. The ReaderLM-v2 model associated with
  `jina-ai/reader` is reported as CC-BY-NC (NOT PROVEN against the model card).
- Stale but reputable: `animate-css/animate.css`, `rsms/inter`,
  `rsmbl/Resemble.js`, `YellowLabTools/YellowLabTools`, `webhintio/hint`.
- No duplicate counting: Storybook appears once (category 6); Playwright and
  Puppeteer appear once (category 1) although scrapers depend on them.

## Vault write-back status

- [x] New hand-written note created in `50-RESEARCH/`; no generated file edited.
- [x] Frontmatter follows the required schema; `tags` has three values; links
      are relative Markdown outside the tables; no wikilinks.
- [ ] `python3 scripts/vault_sync.py` **not run**: `--check` reported
      pre-existing drift in all five `_generated/*` notes before this note was
      created, and those files are already staged with user work. Regenerating
      would overwrite that staged work. Resolver: the vault owner, after the
      staged tree is settled, re-run the generator and the `--check` gate.
- [x] Inbound link added from [RESEARCH-LOG](RESEARCH-LOG.md) (dated entry) and
      row 31 added to [SOURCE-MAP](../00-START/SOURCE-MAP.md); both notes had
      their `updated` field bumped to 2026-11-22.
- [ ] Not added to the [START-HERE](../00-START/START-HERE.md) note index:
      that note already carries staged edits unrelated to this inventory.
      Resolver: the vault owner, when the staged tree is settled.
- [ ] No commit made: the working tree contains extensive pre-existing staged
      changes unrelated to this inventory.
