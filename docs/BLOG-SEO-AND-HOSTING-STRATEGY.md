# Blog, SEO, Donations, and Free-Hosting Strategy

**Status:** Red-team revision — strategy only; implementation has not started
**Prepared:** 2026-11-14
**Scope:** Add an original bilingual blog to Parlament Deschis, make its pages
search- and share-friendly, include a trustworthy donation path, and document a
zero-cost static-hosting option without disrupting the current Vercel/Render
deployment.

## Executive recommendation

1. Keep the existing React/Vite application and Render API. Do not migrate the
   application framework or database as part of this feature.
2. Publish 30 distinct, evidence-led articles in Romanian and English. Treat
   Romanian as the primary editorial language and have English versions
   reviewed rather than relying on unreviewed machine translation.
3. Use a single version-controlled content source and generate crawlable,
   static HTML for the blog index and every language/article URL as part of the
   frontend build. Keep the React app's navigation and presentation consistent
   with those pages.
4. Add clean language-specific URLs, canonical and reciprocal `hreflang`
   links, JSON-LD `BlogPosting` markup, a root sitemap, robots rules, and
   metadata that is present in the initial HTML. Do not rely on client-side
   metadata alone.
5. Keep Vercel as the canonical production host for the first release. It is
   already working and already provides a free provider hostname; switching
   to `*.pages.dev` changes the public hostname but does not provide ownership
   of a custom domain or improve the current API dependency. Evaluate
   Cloudflare Pages as a preview/contingency host, not as an automatic
   production migration.
6. Do not publish a donation button until the recipient type and account URL
   are known and the exact payment flow has passed eligibility, checkout,
   payout, fee, and disclosure checks. GitHub Sponsors is a credible candidate
   because GitHub lists Romania as a supported recipient region and allows
   sponsors from any region, but the recipient must qualify as an open-source
   contributor and the checkout language must be tested. Stripe, Ko-fi, and
   PayPal remain conditional candidates, not confirmed solutions.

This plan does not promise search rankings, AI citations, uptime, or a
completely free custom domain. A `pages.dev` hostname is a free provider
subdomain; owning a custom domain generally requires registration and renewal
fees.

## Project facts and constraints

- The frontend is a bilingual React 18/Vite SPA with TanStack Router,
  Tailwind CSS, and i18next. The frontend build is `npm run build` in
  `frontend/`.
- The existing route shell and navigation are in
  [`frontend/src/router.tsx`](../frontend/src/router.tsx). Global metadata is
  currently limited to the title in [`frontend/index.html`](../frontend/index.html).
- Vercel serves the static frontend and rewrites `/api/*` to Render, as
  configured in [`vercel.json`](../vercel.json). The Vite development server
  proxies `/api` and `/snapshots` to the local API in
  [`frontend/vite.config.ts`](../frontend/vite.config.ts).
- FastAPI CORS currently allows only local development origins in
  [`backend/main.py`](../backend/main.py). A direct browser call from
  `pages.dev` to Render would therefore need a deliberate CORS change. A
  same-origin Pages Function proxy avoids relying on permissive CORS.
- The project documents source attribution and data limitations in
  [`docs/METHODOLOGY.md`](METHODOLOGY.md) and
  [`docs/API.md`](API.md). The blog must reinforce, not overstate, those
  guarantees.
- There is no existing blog, sitemap, robots file, static article generator,
  or global canonical/OG metadata in the inspected frontend.
- The production hostname already in use is `parlament-deschis.vercel.app`.
  Moving to `parlament-deschis.pages.dev` (if available) changes every
  absolute URL and requires a host/site move; a provider subdomain is not a
  transferable custom domain.
- This revision changes documentation only; no feature implementation or
  provider settings have been changed.

## Red-team findings and decisions

| Assumption challenged | Failure if left unchecked | Revised decision / control |
| --- | --- | --- |
| A new free host is automatically better | The existing Vercel host already works; a `pages.dev` migration adds URL, routing, and indexing risk without removing Render or changing the data pipeline | Keep Vercel production/canonical. Treat Cloudflare as an optional preview until a specific operational benefit justifies the move |
| “Static generation” guarantees indexable pages | A catch-all SPA rewrite can still return the generic app shell; social crawlers may never run client JS; a bad deploy can return 200 for missing article slugs | Verify real HTTP response bodies/status on each host, require full article HTML before JS, and require true 404s for unknown blog slugs |
| A Pages Function proxy affects only API routes | Cloudflare invokes Functions on all requests by default unless `_routes.json` narrows invocation; static traffic can unintentionally consume the daily Function quota | Generate `_routes.json` that invokes only `/api` and `/snapshots` paths; test that HTML/assets bypass Functions and quota |
| A proxy alone makes the API safe/reliable | An overly broad proxy could expose arbitrary upstream paths; API quota or Render cold starts still fail; query strings/methods/cache behavior can be corrupted | Fixed upstream only; preserve required request semantics; no arbitrary URL forwarding; no API caching by default; test cold start, failure, and quota assumptions |
| Thirty posts automatically create SEO value | Thin, repetitive, machine-translated, or search-first pages can harm trust and may fit Google's scaled-content/doorway abuse patterns | Treat 30 as a count requirement, not a word-count or keyword target. Every post needs a distinct reader purpose, sources, human review, and a pass/fail quality gate |
| Structured data guarantees rich results or GEO | Google may ignore markup, not index a page, or show a different snippet; there is no special AI markup requirement | Use accurate markup only as page description; prioritize useful crawlable content and make no visibility guarantees |
| “Stripe supports Romania” means this project may collect donations | Country availability does not establish account approval, legal treatment, or support for the exact political-transparency funding use | Require explicit provider eligibility confirmation and recipient/account review before choosing Stripe |
| A robots.txt disallow prevents preview indexing | Crawlers cannot fetch a blocked page to see its `noindex`; URLs may still be discovered/indexed without snippets | Protect previews with Cloudflare Access when practical; otherwise send `X-Robots-Tag: noindex`/meta and do not disallow those URLs |
| A sitemap/citation link is proof of discovery or source quality | Submitted URLs can remain unindexed, and source URLs can move or be taken down | Use Search Console URL inspection, dated source titles/access dates, and a manual source-health report; never let a transient third-party outage silently erase evidence |
| Localized pages can share one canonical | Canonicalizing English to Romanian can suppress the translation and conflict with `hreflang` | Each language page self-canonicalizes and links reciprocally to the other language; sitemap, canonical, and internal links must agree |
| A reader can infer current status from an evergreen article | Parliamentary records can change after publication; a historical chart or stale dataset may be misread as live | Timestamp data claims, link to dated views/sources, show release freshness, and define an editorial review trigger |
| An external payment link is just a button | Readers may mistake a private project for a charity, assume tax deductibility, or send money to an unrelated account | Identify the real recipient, purpose, fees/third-party provider, and non-charity status where applicable; verify ownership and account URL before publication |
| “International” means every donor can pay from every country | Providers, card issuers, sanctions rules, currencies, and recipient onboarding impose geographic/payment-method limits | No provider should be described as universally un-geofenced. Define representative eligible markets, disclose provider limitations, and avoid promising acceptance everywhere |
| A public-record claim has no personal/legal risk | A wrong date, identity match, or inference about motive/finances can mislead readers and harm a person | Cite evidence per claim, keep identity resolution auditable, require a second review for person-specific claims, and publish a correction path |
| Static blog generation makes every app route SEO-ready | The existing Vercel catch-all serves the React shell for application paths; a root canonical inserted into that shell could incorrectly canonicalize party/person/chamber routes to `/` | Scope initial SEO guarantees to generated blog/editorial pages. Do not add a generic root canonical to the SPA shell; plan route-specific dashboard SEO as a separate audit |

### Real-world implementation patterns worth adapting

These are patterns to learn from, not material to copy or proof that the same
outcomes are guaranteed here:

- **TheyWorkForYou / mySociety** describes its independence, mission, data
  sources, and how its service differs from official parliamentary sources.
  Its FAQ also acknowledges that a source stopped maintaining a list and
  consequently the related data could no longer be kept current. This models
  clear provenance and visible limitations. Its support links sit in the
  context of a named operating organization and stated funding status. Its FAQ
  also points readers to an explanation for removing some comparative MP
  statistics; the lesson is to publish only measures with defensible scope
  and interpretation. mySociety reports substantial reach for the service
  on its own site; treat that as organization-reported context, not an
  independent forecast for Parlament Deschis.
- **GitHub Sponsors** is a viable open-source-specific candidate to evaluate:
  GitHub documents that sponsors may be from any region, Romania is currently
  listed as a supported recipient region, personal-account sponsorship has
  no GitHub fee, and organization sponsorship can incur fees up to 6%. This
  does not establish that this owner will qualify or that its checkout is
  Romanian.
- **Google Search Central** describes JavaScript discovery as separate crawl,
  render, and index steps and notes that server-side/pre-rendered HTML also
  helps users and bots that do not execute JavaScript. It warns against
  scaled content made mainly to attract search traffic.
- **Cloudflare Pages** serves a matching static HTML file when available and
  otherwise uses SPA fallback behavior when no root `404.html` exists. Its
  Functions routing docs require `_routes.json` to control which requests
  invoke a Function. Therefore static article paths and unknown paths must be
  tested separately from existing client-side dashboard routes.
- **Google's site-move guidance** distinguishes moving hosting without changing
  URLs from changing the host/domain. Moving from the existing `vercel.app`
  hostname to `pages.dev` is a visible URL change; it calls for URL mapping,
  redirects where possible, Search Console monitoring, and patience while
  pages are recrawled. A free hostname change is not an SEO upgrade by itself.

The project-specific lesson is to explain provenance and limitations as
prominently as features; keep one real operating/author identity; provide a
correction route; and publish distinct, researched answers rather than
treating post count or schema as a growth hack.

### Non-negotiable release blockers

**P0 — block public launch:** inaccurate or unsourced claims; no real recipient
identity for a support link; empty-shell article HTML; incorrect
canonical/language pairing; wrong or missing article body; a 200 soft 404 for
unknown blog slugs; preview/duplicate-host pages accidentally indexable; or
regression in the existing dashboard/API.

**P1 — block Cloudflare promotion, not the Vercel blog launch:** no explicit
Function route allowlist; API proxy not verified against Render; no preview
noindex/access protection; no working rollback; or a `pages.dev` migration
without URL mapping and Search Console monitoring.

**P2 — defer if time/credits are limited:** RSS/Atom, new analytics, comments,
CMS/editor UI, extra donation widgets, link-shortener features, and a
production host move without a measured benefit.

### Editorial boundary: what the platform does and does not show

Parlament Deschis tracks dated parliamentary memberships, affiliations, and
documented political movements. It is **not** a real-time physical-location
tracker, attendance system, payroll database, expense ledger, campaign-finance
database, or proof that a movement caused a particular public cost.

The requested themes about public money and knowing “where MPs are at all
times” must be handled transparently:

- Explain that the site shows recorded parliamentary affiliations and
  membership history, not an MP's physical whereabouts.
- Explain that the current data does not calculate the pay or public cost of
  each movement. Any financial analysis would need separately sourced,
  dated, and methodologically reviewed records.
- Put citations next to factual claims and record the source title, relevant
  date, and access date. Where the app shows a historical date, link to that
  date explicitly rather than implying the chart is a live status.
- Never infer motive, wrongdoing, extra pay, or a financial consequence from a
  party/group change alone.
- Label known date gaps, source coverage, stale releases, and uncertain
  interpretations. Distinguish “zero” from “not available.”

This framing protects readers and the project's credibility while still
explaining why transparent, traceable public records matter.

## Options considered

### Blog rendering and content architecture

| Option | Benefits | Trade-offs | Decision |
| --- | --- | --- | --- |
| React-only pages with `document.title`/meta updates | Smallest initial change; fits current router | Crawlers and social preview bots may receive only the SPA shell; metadata depends on JavaScript execution | Reject as the only SEO solution |
| Replace the application with an SSR framework or CMS | Mature rendering/editorial workflows; SSR across the whole site | Broad migration, new operational dependencies, more risk to the working dashboard, and unnecessary for 30 mostly static posts | Defer unless the site later needs a full editorial CMS or server rendering |
| Build-time static generation from one article manifest | Crawlable HTML, fast static delivery, no runtime database or CMS, compatible with Vite and either host | Requires a small generator and build-output checks; content editing is Git-based | **Recommend** |

Use one content manifest and one server/build-time HTML template as the source
of each blog document. Do not build a React article renderer and a separate,
independently maintained static renderer that can drift. The generated files
are the blog UI; use ordinary anchor navigation between the React dashboard
and generated pages. Reuse the site's visual language through a small shared
stylesheet or proven build output, not by requiring the app bundle to replace
article content after first paint.

Generate actual route files for `/blog/`, `/blog/<slug>/`, `/en/blog/`, and
`/en/blog/<slug>/`, plus a bilingual editorial-standards/corrections page.
The initial HTTP response must contain visible article text, title,
description, same-language canonical URL, reciprocal language links, and
accurate structured data. Verify the built files are served before the SPA
catch-all on Vercel and Cloudflare. Do not rely on an empty shell, client-side
`document.title`, or a social crawler executing JavaScript.

Generate a real not-found response for an unknown blog slug. Many static SPA
hosts return the application root with HTTP 200 for unknown paths; this is a
soft-404 risk. Test status and body on each target host and add explicit
host-level handling if necessary. Preserve the existing SPA fallback for
dashboard routes.

This static strategy makes the blog and editorial policy pages crawlable; it
does **not** make all existing dashboard routes fully SEO-ready. The current
SPA route shell, query-driven date/chamber views, and data-dependent person or
party pages need their own route-specific metadata/rendering audit. Do not put
a single root canonical or `noindex` tag in the shared `index.html` without
proving how it affects every application route. Keep those routes out of the
blog sitemap until their indexing and canonical rules are deliberately
defined.

**Required architecture spike before building all posts:** deploy one sample
article, the index, an unknown blog slug, and `/traseism` to a Vercel preview.
Request each URL directly and check both status and body. Repeat on a
Cloudflare preview if that host remains under consideration. A root
`404.html` is not a harmless fix on Cloudflare Pages: it changes the default
SPA fallback behavior, so it can break direct dashboard-route loads. If a
host needs a route-specific Function to produce a true blog 404, include the
blog route's worst-case traffic in the Function quota budget. Do not choose
the route shape or commit to the host before this test passes.

Keep the posts in a simple reviewed source format (JSON or TypeScript data
with a clearly typed schema); do not introduce a CMS or a paid service for
this first release. Define title, slug, language, description, author,
publication/review dates, category, sections, cited sources, related posts,
and donation-panel copy. Reject missing or duplicate slugs, empty sources,
and missing language variants at build time. Constrain slugs to lowercase
ASCII words separated by single hyphens; never use unchecked content as an
output filesystem path.

### Hosting and API routing

| Option | No-cost fit | API compatibility | Assessment |
| --- | --- | --- | --- |
| Keep Vercel | Already configured and working; free provider hostname | Existing `/api/*` rewrite to Render works | **Recommend as production/canonical default**; least risk and no current need to change hosts |
| Cloudflare Pages plus `pages.dev` | Free static assets, provider hostname, GitHub builds/previews | New host changes URLs; API proxy requires careful route exclusions; preview routes are public by default | **Optional preview/contingency**; migrate only for a documented benefit |
| GitHub Pages | Free static hosting and a `github.io` hostname | Static-only; no same-origin API proxy, so current API/CORS behavior must change | Viable fallback only if the API can be called cross-origin safely |
| Netlify or another free host | May offer static hosting and functions | Free-tier terms, build credits, and function limits vary and change | Not selected; avoid adding another quota/billing model without a need |

Cloudflare Pages is appropriate for the static UI and generated blog, not a
replacement for the Render API or its data pipeline. Its current documentation
lists 500 builds/month, 20,000 files/site, and a 25 MiB per-file limit on the
Free plan. Static asset requests are free and unlimited. Pages Function
requests count against Workers Free usage (currently 100,000 requests/day,
with a 10 ms CPU limit per invocation). These quotas and terms can change.
Critically, once a Functions directory exists, Pages invokes Functions on all
requests by default unless `_routes.json` excludes non-function paths. Generate
the route file into the build output with inclusion limited to `/api`,
`/api/*`, `/snapshots`, and `/snapshots/*`; confirm static HTML, JS, CSS,
images, sitemap, and robots are not Function invocations.

**API decision for the migration:** Prefer a narrow same-origin Pages Function
that proxies only `/api/*` and `/snapshots/*` to
`https://parlament-deschis.onrender.com`, preserving method, query string,
request body, relevant headers, status, and response body. Do not proxy
arbitrary user-supplied URLs. Measure or estimate API volume before launch;
if the Functions quota is a concern, compare a narrowly allowlisted Render
CORS configuration plus an explicit frontend API base URL. Never broaden CORS
to `*` with credentials. Do not cache API responses by default. Test GET,
HEAD/OPTIONS if used, query parameters, error statuses, Render wake-up delays,
and static-route bypass. The existing Vercel rewrite is not automatically
applied by Cloudflare.

### Donation paths

No donation provider can be wired responsibly without an account-specific
URL. Candidate comparison:

| Candidate | Advantages | Open checks before selection |
| --- | --- | --- |
| GitHub Sponsors | GitHub currently lists Romania as a supported recipient region; sponsors can be in any region; an open-source sponsorship is contextually aligned; no GitHub fee for personal-account sponsorships, organization fees up to 6% | Owner must qualify as an open-source contributor, complete payout onboarding, and confirm whether GitHub's checkout language/payment UX meets the Romanian-user requirement |
| Stripe Payment Link | Stripe lists Romania among supported business countries and says businesses in supported countries can accept global payments; hosted checkout avoids collecting card data in this app | Stripe is a processor, not a donation platform. Confirm exact project/fundraising use is permitted, account approval, recipient type, checkout language, variable-amount setup, payout, fees, and tax/accounting |
| Ko-fi | Familiar creator-facing page and one-off/recurring support model | Official country-help page could not be fetched in this research; verify Romanian creator onboarding/payout, donor checkout/language, processor eligibility, and fees in the actual account |
| PayPal | Potentially familiar cross-border hosted payment option | Verify Romanian account features, donation-link availability, donor checkout, payout, fees, language, and policy for this recipient in the actual account |
| Open Collective or similar | May provide a hosted funding ledger and expense transparency where its legal/host structure fits | Confirm Romania eligibility, fiscal-host arrangements, fees, terms, and legal-entity requirements |

Country coverage is not proof that an individual account or political/public
interest funding use case will be approved. Stripe's restricted-business
policy says it does not restrict service based on political viewpoint, while
also reserving legal, banking-partner, and business-use restrictions; get
provider confirmation for this exact recipient and use. No provider can
promise every donor in every country can pay. Test Romania plus representative
EU and non-EU donor locations, document supported methods/currencies and
known exclusions, and do not market the provider as “un-geofenced.” Fees,
currency conversion, identity checks, and taxes mean that payment processing
is not literally free. Use “Support the project” rather than
legal/tax-loaded “charitable donation” language unless the recipient's status
and local obligations have been confirmed. Do not state that gifts are
tax-deductible or that the project is a charity without evidence.

**Selection gate:** The owner supplies the exact public URL and confirms they
control the receiving account. Before displaying it, test the hosted checkout
from Romania, another EU country, and a non-EU market with real test-mode
flows where available; confirm recipient onboarding and payout eligibility,
identify platform and currency fees, verify Romanian and English checkout
behavior, record supported payment methods and exclusions, and publish a
short, truthful explanation of the actual recipient and how funds support the
project.
Prefer ordinary external links over third-party payment widgets or scripts;
this is simpler, more private, and keeps payment handling off the project
site. Check platform acceptable-use terms before using payment links in a
political-transparency context. Until all gates pass, do not show a dead,
generic, or placeholder donation button.

## Editorial and SEO plan

### Audience and content principles

Write for Romanian citizens, journalists, educators, researchers, and
international readers trying to understand Romanian parliamentary movement
records. The goal is to explain the data and its limits, not to persuade
readers toward a party or politician.

Each article should:

1. Answer one well-defined reader question in the opening, using plain
   language and defining Romanian institutional terms.
2. Explain the evidence and method; cite sources close to factual statements,
   link to the relevant dashboard view, and identify source title/access date
   when a parliamentary record is likely to move.
3. Separate documented facts, interpretation, and unknowns. Include “what
   this data can/cannot establish” where the topic could invite overclaiming.
4. Provide author/editor identity that is real and approved by the project
   owner. Do not invent a named expert, credentials, endorsements, or
   firsthand experience.
5. Show a genuine publication and review date. Update the date only after a
   substantive review; do not make automated date changes to look fresh.
6. Link to a small number of genuinely related articles and relevant
   dashboard pages. Avoid keyword stuffing, doorway pages, repetitive
   boilerplate, and unsupported promises about transparency or impact.
7. Be original and useful in both languages. Have a fluent human review the
   English version, parliamentary terminology, and source links.
8. End with a clearly separated support-project panel only after a working
   donation destination and transparent disclosure have been approved.
9. Pass a documented editorial scorecard for accuracy, distinct reader
   intent, source quality, clarity, language review, and non-misleading
   framing. There is no SEO-mandated minimum or magic word count; do not pad
   an article to hit one.
10. Have a visible correction route, review trigger, and change history.
    Keep open comments off in the first release to avoid adding moderation,
    privacy, and spam risks without a demonstrated reader need.
11. Write original prose, cite instead of copying source text, honor the
    data/code licenses, and use only project-owned or appropriately licensed
    images. The project's CC-BY data license does not automatically grant
    rights to every third-party image or source document.

Google's current guidance says there are no special AI Overview/AI Mode
optimizations or additional AI-specific structured data requirements. The
same fundamentals apply: crawlable pages, useful original content, internal
links, good page experience, and markup that matches visible content. No
markup or writing style guarantees indexing, ranking, rich results, or
generative-search citations. A 30-post target is not a justification for
releasing thin drafts: all 30 must pass the same quality bar before being
indexable. Do not target near-identical queries with separate pages;
distinguish overlapping briefs by reader task, link related pieces, and merge
or reframe any pair that cannot answer different questions.

### Proposed 30-article editorial map

These are distinct article briefs, not 30 keyword-swapped versions of the
same post. Final titles and search phrasing should be checked against actual
reader questions and Search Console after launch.

| # | Romanian-first article brief | Core question / boundary |
| ---: | --- | --- |
| 1 | Cum urmărești parcursul parlamentar al unui ales | Read a dated membership timeline; distinguish identity and mandate records |
| 2 | Ce înseamnă traseismul politic și ce nu înseamnă | Define the term without assuming motive or judging every case alike |
| 3 | Partid, grup parlamentar și statut de independent | Explain affiliation concepts and why they are not interchangeable |
| 4 | Cum se verifică o schimbare de afiliere | Trace a claim to dated, primary-source evidence |
| 5 | Cum citești o cronologie a apartenenței parlamentare | Interpret start/end dates, gaps, and overlapping records cautiously |
| 6 | Componența Parlamentului la o dată anume | Explain an “as of” snapshot and historical date selection |
| 7 | Camera Deputaților și Senatul: ce date comparăm | Explain chamber scope without conflating their records |
| 8 | Legislatură, mandat și afiliere: trei noțiuni diferite | Define time periods and avoid treating them as one event |
| 9 | Cum se citesc intrările, ieșirile și soldul net | Explain aggregate flow measures and their limits |
| 10 | De ce o schimbare poate apărea diferit în surse | Explain publication timing, source updates, and reconciliation |
| 11 | Ce înseamnă acoperire completă, parțială sau indisponibilă | Explain coverage labels; unavailable is not zero |
| 12 | Cum folosim sursele oficiale ale Parlamentului | A practical source-checking guide with source links |
| 13 | Cum se schimbă grupurile parlamentare în timp | Interpret group-size timelines; do not equate group totals with election results |
| 14 | Mai multe schimbări pentru aceeași persoană | Distinguish events, membership periods, and repeated records |
| 15 | Mandate în ambele Camere: ce arată istoricul | Explain recorded cross-chamber careers and date limitations |
| 16 | Ce poate și ce nu poate demonstra o bază de date publică | Data provenance, completeness, and limits of inference |
| 17 | De ce contează sursa și data unei afirmații | Show how readers can cite a dated record rather than a screenshot |
| 18 | Cât de actuale sunt datele de pe Parlament Deschis? | Explain release version, source refresh, and stale-data notices |
| 19 | Cum corectăm o înregistrare și păstrăm istoricul | Responsible correction reports, evidence, and audit trail |
| 20 | De ce datele parlamentare deschise trebuie să fie reutilizabile | Explain open data, attribution, and the project's license |
| 21 | Cum pot folosi cetățenii cronologiile parlamentare | Practical civic use without implying that one chart proves intent |
| 22 | Cum pot jurnaliștii verifica o afirmație despre o afiliere | A repeatable fact-check workflow with linked records |
| 23 | Cum pot profesorii explica schimbările parlamentare | Classroom activity focused on evidence and uncertainty |
| 24 | Ce spune o schimbare de partid despre alegători? | Explain what membership records cannot establish about voter views |
| 25 | De ce nu trebuie să presupunem motivul unei schimbări | Avoid motive attribution absent direct, reliable evidence |
| 26 | Urmărește Parlament Deschis locația fizică a deputaților? | Clearly answer no; affiliation history is not live location or attendance |
| 27 | Cât costă o schimbare de partid? Ce date lipsesc | State that this site does not calculate a movement's cost or compensation |
| 28 | Cum se verifică separat cheltuielile și remunerațiile publice | Explain that financial questions require separate official records and scope |
| 29 | De ce traseismul nu măsoară singur activitatea legislativă | Separate affiliation history from attendance, bills, votes, or performance |
| 30 | Cum contribui la o evidență parlamentară mai bună | Explain source-based corrections and responsible open-source contribution |

Every financial article should say plainly that the current platform does not
attribute expenditure or remuneration to a particular movement. Every
location-related article must correct the misconception that the site tracks
physical whereabouts.

To keep similar briefs distinct rather than publishing keyword variants, keep
these editorial boundaries:

- **#4, #12, #17, #22:** verify one reported affiliation change; locate and
  read official parliamentary sources; cite a date/version correctly; and
  apply a newsroom fact-check workflow, respectively.
- **#5 vs. #6:** read one person's membership timeline vs. interpret the
  aggregate chamber composition on a selected date.
- **#10 vs. #11:** reconcile source disagreement/timing vs. understand
  coverage labels and missingness.
- **#19 vs. #30:** submit a correction with evidence vs. contribute a code,
  documentation, or data improvement to the project.
- **#24 vs. #25:** what membership records cannot reveal about voters vs.
  what they cannot establish about an MP's personal motive.
- **#27 vs. #28:** explain why this platform cannot price a movement vs.
  outline how a separate, properly scoped public-expenditure analysis would
  need to be researched.

If a draft cannot preserve these different tasks, revise or merge the brief
before publication rather than forcing all 30 titles to target a keyword.

### Page structure and technical SEO

- **URLs:** `/blog/` and `/blog/<ascii-slug>/` for Romanian;
  `/en/blog/` and `/en/blog/<ascii-slug>/` for English. Keep URLs stable;
  preserve old URLs with redirects if a slug ever changes.
- **Language:** Set `<html lang="ro">` or `lang="en"`. Each translated page
  lists itself and its reciprocal translation with absolute `hreflang` URLs
  and self-canonicalizes to its own language URL; include `x-default` only if
  a real language-selection/fallback page exists.
- **Metadata:** Unique title and description per article; canonical URL;
  Open Graph and social-card title/description/type/URL; publication and
  review dates where accurate. Do not reuse the app shell's title for all
  articles.
- **Structured data:** JSON-LD `BlogPosting` (or `Article`) with headline,
  description, author/publisher, dates, language, canonical page, and an
  image only when an appropriate real image exists. Markup must match visible
  content; represent the author/publisher only with approved real identities.
  Escape values safely when generating JSON-LD and HTML. Do not add fake
  reviews, ratings, FAQ rich-result markup, or unsupported claims. Validate
  output with Google's Rich Results Test.
- **Navigation/accessibility:** One clear H1, ordered headings, semantic
  `article`, `nav`, and `main` landmarks, descriptive link labels, keyboard
  navigation, visible focus, sufficient contrast, responsive line length,
  and reduced-motion compatibility. If a data chart is embedded, add a text
  explanation and a useful alternative rather than making the image the only
  evidence. Target WCAG 2.2 AA for the blog, with automated checks plus
  manual keyboard, zoom/reflow, and screen-reader spot checks; an automated
  pass alone is not proof of conformance. Keep the existing dark visual
  language while providing comfortable long-form reading.
- **Internal discovery:** Add a Blog entry to the main site navigation, a
  crawlable index linked from each article, breadcrumbs, topic categories,
  and a few relevant cross-links. Avoid JavaScript-only links.
- **Trust page:** Publish a bilingual, crawlable editorial-standards and
  corrections page. Explain who operates the project at the level the owner
  approves, data scope, primary sources, license, author/reviewer policy,
  correction method, limitations, and donation recipient/disclosure if
  enabled. Link it from the blog footer/articles; do not imply government
  affiliation.
- **Support panel:** If enabled, place one modest, consistent panel after the
  article body, not between evidence and conclusions. Explain the actual
  recipient and intended use of funds, identify the third-party payment
  service, and state that support does not buy editorial influence. Do not
  claim funds are used for hosting/development unless that is true. Keep the
  link optional and do not load payment scripts or collect donor data here.
- **Crawl files:** Generate `/sitemap.xml` from canonical production URLs and
  `/robots.txt` that permits public blog pages and references the sitemap.
  Keep preview deployments out of the index; do not list API endpoints,
  preview hosts, or duplicate hostnames as canonical pages. Use `lastmod`
  only for a substantive update; robots rules are not a canonicalization or
  access-control mechanism.
- **Preview environments:** Apply the same rule to Vercel and Cloudflare
  previews: restrict access where practical or verify a `noindex` response
  header/meta on actual preview URLs. Do not rely on `robots.txt` disallow to
  hide a preview.
- **Sharing:** Create a project-owned article/social cover image in a
  crawler-compatible raster format (PNG/JPEG) and use the same stable
  absolute URL consistently in Open Graph/Twitter metadata and article
  markup. Do not use a remote image without permission or a suitable license.
- **Performance/privacy:** Static content, no mandatory trackers, no remote
  fonts/scripts, and no embedded donation widget in the first release. If
  analytics are later added, choose a privacy-respecting setup and disclose
  it appropriately.
- **Measurement:** Verify the production host in Google Search Console and
  submit the sitemap. Monitor indexing, crawl errors, queries, clicks, and
  performance over time. Do not promise a ranking or GEO outcome.
- **Content safety:** Treat the article manifest as trusted source code but
  still HTML-escape text, validate link schemes, and avoid raw HTML injection.
  Do not collect reader data or embed payment-provider scripts in v1.

## Failure playbook

| Failure | Detection | Safe response |
| --- | --- | --- |
| A blog route serves the SPA shell, empty markup, or the wrong language | Direct `curl`/HTTP checks and “view source” checks on deployed URLs | Block release; fix static-file precedence and build output before requesting indexing |
| Unknown article slug returns HTTP 200 | Negative-route test against the production-like host | Configure a real host-level 404 for blog paths without breaking dashboard SPA routes |
| Canonical, `hreflang`, sitemap, or preview metadata disagree | Build assertions plus Search Console URL inspection | Stop release; derive all URL variants from one configured production origin; remove preview host from public indexes |
| Search Console shows submitted but not indexed | URL inspection, crawl/index reports, rendered HTML and robots checks | Diagnose access, canonical, quality, and internal links; allow recrawl time; do not generate filler articles or repeatedly resubmit unchanged URLs |
| A cited official source moves or disappears | Scheduled/report-only link review and reader correction report | Keep source title, date, and contextual evidence; update the link after verification; use the project's archived evidence only when lawful and clearly labeled |
| Official data refresh fails or the Render API is asleep | Existing health/freshness signal and API error state | Keep the last known-good dataset visible with its date/status; article content remains static; never label stale data as live |
| Pages Function quota is exhausted or static paths invoke it | Function metrics and static-asset request checks | Static blog remains available only if its paths bypass Functions; if a Function is needed for blog 404s, budget those invocations too. Show dashboard API failure clearly; correct `_routes.json` or roll back to Vercel after verification |
| Donation provider rejects, freezes, or changes the account | Provider notice, failed checkout, payout/eligibility review | Remove/disable the CTA promptly; do not silently substitute a different recipient or use personal details without approval |
| A person or reader reports a factual error | Maintainer reviews cited primary records and correction contact | Triage promptly; correct the claim, disclose meaningful changes, and keep an editorial change record; seek qualified advice for legal threats |
| A translation is incomplete or changes the meaning | Bilingual review and reciprocal-link validation | Do not publish the incomplete translation as an alternate; keep the version in draft until reviewed |
| Build output contains unsafe markup or an unapproved payment URL | Generator validation, code review, and link allowlist | Fail the build; permit only approved URL schemes/origins and render article text as escaped content |

This playbook assumes the article site remains static and the API remains
separate. It is not a substitute for provider incident procedures, backups,
legal/accounting advice, or a staffed uptime commitment.

## Staged action plan

### Stage 0 — Owner decisions and evidence preparation

- Confirm whether the 30 posts should launch in both Romanian and English;
  this plan recommends both.
- Approve the project/team author attribution and editorial contact/correction
  route.
- Supply and verify a donation account URL, or explicitly defer donation links
  while retaining a non-transactional support explanation.
- Confirm the intended production canonical host. Keep the current Vercel
  host as the default. Treat `pages.dev` as a URL migration, not merely a
  hosting toggle.
- Decide the real recipient category and account type before choosing a
  payment provider. Confirm whether GitHub Sponsors onboarding is available
  for the owner and whether its checkout meets the Romanian-language need.
- Build an article source sheet from official parliamentary records,
  applicable project documentation, and source citations. Record access
  dates and known limitations.
- Set up the production Search Console property and record a pre-launch
  baseline; this is for monitoring, not a promise of search traffic.

**Gate:** No fake author/credentials, unsupported movement-cost claim, broken
source citation, or unverified donation link.

### Stage 1 — Content model and editorial review

- Create the 30 unique article briefs above as separate source-backed posts.
- Write the Romanian versions first; produce and human-review English
  versions.
- Add titles, summaries, metadata, categories, related links, dates, and
  visible source citations.
- Review every post for factual accuracy, neutrality, readability, duplicate
  content, accessibility, and the location/finance boundaries.
- Assign one distinct reader question to each article; resolve overlap in
  briefs before writing. Do not generate English copy by direct machine
  translation without human editorial review.
- Include a support panel only when Stage 0's donation gate passes.

**Gate:** Exactly 30 distinct article records, each with a reviewed RO and EN
version, sources, a unique stable slug, and a truthful scope statement.

### Stage 2 — Blog UX and static generation

- Add blog index/article layouts consistent with the existing site and
  accessible on mobile, keyboard, and screen readers; use normal links to
  cross between the React dashboard and static blog documents.
- Add a bilingual editorial-standards/corrections page rather than relying
  only on documentation that may not be published with the frontend.
- Generate route-specific initial HTML from one content source/template
  during the normal Vite build. Escape text, validate link schemes, and do
  not insert raw HTML from article data.
- Make the generator available to local development as well as clean builds;
  generated files should be reproducible and should not require committing
  duplicate HTML copies.
- Generate self-canonicals, reciprocal language alternates, JSON-LD,
  sitemap, and robots from the same route/content source; use no separate
  hand-maintained URL lists.
- Require the production canonical origin in production builds; do not
  silently publish preview URLs or a stale fallback hostname as canonical.
- Keep RSS/Atom optional until there is a real subscriber need; it is not an
  SEO prerequisite.
- Define host rules for known static articles, unknown article slugs (real
  404), and existing dashboard SPA routes before rollout.

**Gate:** A direct HTTP request to every article route returns the complete
visible article and unique metadata before client JavaScript executes.

### Stage 3 — Verification and release

- Add build-time checks for 30 posts, both languages, unique slugs, required
  metadata/source fields, distinct article intent, valid internal links,
  safe URLs, and valid sitemap URLs.
- Test browser navigation, direct entry/reload, responsive layout, keyboard
  use, dark theme, reduced motion, no-JavaScript readability, and external
  link behavior.
- Fetch every generated URL directly and assert HTTP status, title, H1,
  language, canonical, reciprocal alternates, article text, and structured
  data. Test unknown slugs return 404, not a 200 SPA shell.
- Validate JSON-LD and page metadata; report broken/moved source links for
  editorial review rather than making transient source outages silently
  fail or delete a build. Run frontend typecheck/build and relevant tests.
- Keep Vercel production unchanged until the feature passes its existing
  deployment checks.
- After launch, submit the sitemap in Search Console, inspect representative
  URLs, and monitor indexing/crawl errors and actual queries. Sitemap
  acceptance is not evidence that pages are indexed.

**Gate:** No broken route/source, duplicate canonical, missing language
alternate, invalid schema, placeholder donation destination, or claim that
the site measures physical location or politician-specific costs.

### Stage 4 — Optional Cloudflare Pages preview, not default migration

This is a parallel deployment and rollback plan, not a prerequisite for the
blog. The current recommendation is to publish on Vercel and stop here unless
Cloudflare provides a concrete benefit. Both hosts are static frontends; the
Render API and data pipeline remain dependencies either way.

1. Create/sign in to Cloudflare and open **Workers & Pages**.
2. Choose **Create application → Pages → Connect to Git**, authorize GitHub,
   and select `nedaktov-ops/parlament-deschis`.
3. Select the production branch (`main`). Use root directory `frontend`,
   build command `npm run build`, and output directory `dist`. Confirm the
   lockfile-based install works from this root.
4. Choose an available project name. Cloudflare generates a free
   `<project>.pages.dev` hostname; the exact name is subject to availability.
   This is a provider subdomain, not ownership of a custom domain.
5. If adding a Pages Function, generate `_routes.json` into `dist` with
   inclusion limited to `/api`, `/api/*`, `/snapshots`, and `/snapshots/*`.
   Add `/blog/*` only if a proven route-specific 404 implementation requires
   it, and include that traffic in quota estimates. Verify static pages/assets
   bypass Functions wherever possible. Do not assume that merely placing a
   Function file leaves static requests unmetered.
6. Deploy a preview first. Cloudflare branch previews are public by default;
   protect them with Access where appropriate and otherwise verify
   `X-Robots-Tag: noindex` on actual responses. Do not disallow the preview
   in `robots.txt` as a substitute for noindex. If a separate Cloudflare
   `pages.dev` production mirror is kept while Vercel remains canonical, that
   mirror must also be explicitly non-indexable. Canonical and sitemap
   metadata must still point only to the actual production host.
7. Test the home dashboard and every existing route (including direct entry
   and reload), API health/data routes, snapshot access, both blog indexes,
   all 60 language/article routes, both editorial-policy routes, social
   metadata, sitemap, robots, and an unknown article slug returning a real
   404. Confirm API errors and Render cold starts remain understandable.
8. Review build/Functions quotas and account billing controls. Record
   function invocations separately from unlimited static asset requests and
   define what users see if the daily allowance is exhausted. Never assume
   that the backend moved with the frontend.
9. Keep Vercel production/canonical until the preview has a measurable reason
   to replace it and passes all checks. If migrating to `pages.dev`, this is
   a URL/host move: map old URLs to corresponding new URLs, configure
   permanent redirects from the old host where possible, update canonicals
   and sitemap in one controlled release, verify both hosts in Search
   Console, and monitor both. Do not leave two indexable copies. Expect
   recrawl/reindex time and possible temporary ranking fluctuations.
10. Document and rehearse rollback. Keep the old Vercel deployment and the
    ability to remove redirects; verify the return path before promoting.
    Never change host, article structure, and editorial/content model in the
    same release.

The Cloudflare Git-integration documentation warns that a Git-integrated
Pages project cannot later be switched to Direct Upload. Keep Git integration
if GitHub remains the source of truth. If a custom domain is acquired later,
it can make a host migration less disruptive by keeping the URL constant, but
the domain registration itself is not a free resource.

### Ongoing editorial maintenance

- Review articles when a cited record changes, the dataset methodology/API
  changes, a reader reports an issue, or the project changes its scope.
- Run a lightweight source-link report periodically. Treat a failed link as
  a review task, not permission to remove the claim or silently rewrite it.
- Correct material errors promptly and record the reason/date; update
  `dateModified` only for a substantive change.
- Review Search Console indexing and query data periodically. Improve pages
  where readers' questions are unanswered; do not respond to low traffic by
  producing more near-duplicate content.
- Reconfirm donation-provider eligibility, recipient details, and public
  disclosures before any account or platform change.
- Keep a compact monthly maintenance record: current host, last successful
  data release, outstanding source/correction issues, and donation status.

## Acceptance checklist

- [ ] Blog is discoverable in the main navigation and has an accessible,
  browsable index with topic labels and crawlable article links. Add client-
  side search only if readers need it; it must not replace the static links.
- [ ] Blog passes an accessibility review against WCAG 2.2 AA target checks,
  including keyboard/focus, zoom/reflow, text alternatives, and a screen-
  reader spot check.
- [ ] Exactly 30 original article topics are published in Romanian and
  reviewed English.
- [ ] Each article is primary-source-linked, fact-checked, non-partisan, and
  explicit about relevant data limitations.
- [ ] No copy claims real-time physical tracking or calculates the cost of a
  movement from this platform's data.
- [ ] Direct HTTP requests to all blog routes return the full visible article
  before JavaScript; unique metadata, correct language, same-language
  canonical, reciprocal language links, appropriate schema, and crawlable
  internal links are present.
- [ ] An unknown blog slug returns a true 404, while existing dashboard SPA
  routes still load on direct entry/reload.
- [ ] Sitemap lists only canonical public pages; robots references it; preview
  URLs have a working noindex/protection response and are not listed.
- [ ] No donation link appears until recipient eligibility, account ownership,
  Romania/international checkout, payout, acceptable-use policy, fees, and
  disclosure are verified.
- [ ] If enabled, the same modest support panel appears at the end of each
  article with the verified destination and accurate recipient/use
  disclosure; it does not imply charity status or editorial influence.
- [ ] Existing dashboards, date/chamber routing, Vercel API proxy, Render
  data access, and local development continue to work.
- [ ] If Pages Functions are present, `_routes.json` keeps static page/assets
  outside Function invocation; proxy requests are fixed-origin and tested.
- [ ] Vercel remains canonical unless migration is explicitly approved;
  any host migration has URL mapping, redirects, Search Console monitoring,
  and a tested rollback.
- [ ] Build/test output and post-launch Search Console observations are
  recorded; no ranking or AI-citation guarantee is implied.

## Dependencies and owner inputs

The following are not available in the repository and must not be guessed:

1. The donation account's public URL, display name, owner/recipient identity,
   and confirmation that the owner can receive payouts in Romania.
2. Whether the owner wants donation processing on an individual, nonprofit,
   or other legal/accounting basis.
3. The approved author/editor name and public correction/contact address.
4. Whether to publish all 30 English translations at the same time as the
   Romanian originals.
5. Whether the owner qualifies for GitHub Sponsors as an open-source
   contributor, and whether a non-Romanian checkout UI is acceptable.
6. Approval of Cloudflare as a preview/backup host and, only if migration is
   justified, the desired `pages.dev` project-name choice.

## Research references

Provider documentation was reviewed on 2026-11-14. Quotas, eligibility, and
product terms can change; recheck them at implementation and before migration.

- Google, [AI features and your website](https://developers.google.com/search/docs/appearance/ai-features)
- Google, [JavaScript SEO basics](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)
- Google, [JavaScript troubleshooting and soft 404s](https://developers.google.com/search/docs/crawling-indexing/javascript/fix-search-javascript)
- Google, [Creating helpful, reliable, people-first content](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)
- Google, [Search spam policies](https://developers.google.com/search/docs/essentials/spam-policies)
- Google, [Article structured data](https://developers.google.com/search/docs/appearance/structured-data/article)
- Google, [Structured data policies](https://developers.google.com/search/docs/appearance/structured-data/sd-policies)
- Google, [Localized versions and `hreflang`](https://developers.google.com/search/docs/specialty/international/localized-versions)
- Google, [Canonical URLs](https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls)
- Google, [Build and submit a sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap)
- Google, [Changing hosting without changing URLs](https://developers.google.com/search/docs/crawling-indexing/site-move-no-url-changes)
- Google, [Moving a site with URL changes](https://developers.google.com/search/docs/crawling-indexing/site-move-with-url-changes)
- Google, [Inspect URL status in Search Console](https://support.google.com/webmasters/answer/9012289)
- W3C, [Web Content Accessibility Guidelines (WCAG) 2.2](https://www.w3.org/TR/WCAG22/)
- Cloudflare, [Pages Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/)
- Cloudflare, [Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
- Cloudflare, [Pages serving and SPA/404 behavior](https://developers.cloudflare.com/pages/configuration/serving-pages/)
- Cloudflare, [Pages Functions routing and `_routes.json`](https://developers.cloudflare.com/pages/functions/routing/)
- Cloudflare, [Preview deployments](https://developers.cloudflare.com/pages/configuration/preview-deployments/)
- Cloudflare, [Pages Functions pricing](https://developers.cloudflare.com/pages/functions/pricing/)
- Cloudflare, [Workers pricing and Free plan limits](https://developers.cloudflare.com/workers/platform/pricing/)
- Vercel, [Rewrites](https://vercel.com/docs/routing/rewrites)
- Stripe, [Global availability and supported countries](https://stripe.com/global)
- Stripe, [Restricted and prohibited businesses](https://stripe.com/legal/restricted-businesses)
- GitHub, [GitHub Sponsors: eligibility, regions, and fees](https://docs.github.com/en/sponsors/getting-started-with-github-sponsors/about-github-sponsors)
- TheyWorkForYou, [About the service and its operator](https://www.theyworkforyou.com/about/)
- TheyWorkForYou, [FAQ: data sources and known limitations](https://www.theyworkforyou.com/help/)
- mySociety, [Democracy and TheyWorkForYou](https://www.mysociety.org/democracy/)
- mySociety, [Why some comparative MP statistics were removed](https://www.mysociety.org/2020/11/16/publishing-less-our-current-thinking-about-comparative-statistics/)
- mySociety, [Why some comparative MP statistics were removed](https://www.mysociety.org/2020/11/16/publishing-less-our-current-thinking-about-comparative-statistics/)
- Ko-fi, [Country availability help article](https://help.ko-fi.com/hc/en-us/articles/360007975494-Which-countries-can-I-use-Ko-fi-from) (could not be fetched during research; eligibility remains unverified)
- Project, [Methodology](METHODOLOGY.md), [API documentation](API.md), and [self-sustainability architecture](SELF-SUSTAINABILITY-ARCHITECTURE.md)
