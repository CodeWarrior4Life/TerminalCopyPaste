# Publish Project Skill Design

**Date:** 2026-04-03
**Status:** Draft
**Scope:** Two skill changes -- `new-project` update + new `publish-project` skill

---

## Problem

Publishing a product is a repeatable, multi-phase process that currently lives as tribal knowledge and scattered skill files. Each project (Extension Janitor, TCP, ABM) has reinvented parts of the pipeline. We need a single skill that orchestrates the full launch lifecycle, with mode awareness for first launch vs updates vs betas.

## Solution

### 1. `new-project` Skill Update

Add a **Distribution & Monetization** question block after existing scaffolding questions. Answers are written to `CLAUDE.md` as a `## Distribution` section that `publish-project` reads at runtime.

**New questions:**

| Question | Options | Default |
|----------|---------|---------|
| App type | browser extension, desktop app, web app, CLI tool, library/package, mobile app | -- |
| Target platforms | Windows, macOS, Linux, web, Chrome/Firefox/Edge/Opera | -- |
| Monetization | free/open-source, freemium, paid, donation-ware | free/open-source |
| License | MIT, Apache 2.0, BSL (with auto-convert), GPL, proprietary | MIT |
| Distribution channels | GitHub Releases, browser stores, app stores, Docker Hub, PyPI/npm, Cloudflare R2, direct download | GitHub Releases |
| Update mechanism | auto-update, manual download, package manager, store-managed | store-managed or manual |

**Output in CLAUDE.md:**

```markdown
## Distribution
- **Type:** desktop app
- **Platforms:** Windows
- **Monetization:** free/open-source
- **License:** BSL 1.1 (4-year auto-convert to MIT)
- **Channels:** GitHub Releases
- **Updates:** manual download
```

### 2. `publish-project` Skill (New)

Lives at `~/.claude/skills/publish-project/SKILL.md` (same location as `new-project` and `application-deployment`). Also stored in the vault skill library for reference. Reads `## Distribution` from the project's `CLAUDE.md` to determine which phases and sub-steps apply.

---

## Publish Modes

Auto-detected from the version tag:

| Mode | Version Pattern | Scope |
|------|----------------|-------|
| **Launch** | `1.0.0` | Full ceremony -- all 10 phases |
| **Update** | `1.x.x+` | Build, tag, push, changelog, store update, light social |
| **Beta** | `0.x.0b` | Tag, build, push to pre-release channel only |

---

## Phase Matrix

| # | Phase | Launch | Update | Beta |
|---|-------|--------|--------|------|
| 1 | Pre-flight | YES | YES | YES |
| 2 | Assets | YES | skip | skip |
| 3 | Copy | YES | changelog + abbreviated social | skip |
| 4 | Infrastructure | YES | skip | skip |
| 5 | Legal | YES | skip | skip |
| 6 | Landing page + SEO | YES | skip | skip |
| 7 | Submit | YES | YES | YES (pre-release) |
| 8 | Update mechanism | YES | skip | skip |
| 9 | Promote | YES | light social | skip |
| 10 | Post-launch verify | YES | smoke test | skip |

---

## Phase Details

### Phase 1: Pre-flight

1. Read `CLAUDE.md` for `## Distribution` block
2. Determine publish mode from version tag (or ask user)
3. Validate build is clean: tests pass, no uncommitted changes, git tag ready
4. Check credential availability for all required channels:
   - Stripe keys (if paid/freemium)
   - Store API tokens (Chrome, Firefox, Edge)
   - Recraft API token (for icon generation)
   - GitHub token (for releases)
   - Cloudflare credentials (if Worker needed)
   - Social account access (X/Twitter, Reddit, etc.)
5. Produce **pre-flight checklist** showing ready/missing/manual items
6. Missing credentials are flagged as blockers with setup instructions

### Phase 2: Assets

1. **App icon** -- compose a Recraft API prompt based on the product description and brand style guide (colors: dark purple `#190E24`, teal `#46C3AC`, gold `#F6B256`, white `#F4F4F3`)
2. **Present the prompt** to the user and ask: "Should I generate this via Recraft API, or do you want to generate it yourself?"
   - If yes: call Recraft API, download SVG immediately (URLs expire in ~24h)
   - If no: wait for user to provide the file
3. **Post-process SVG**: fix viewBox, remove unwanted elements, ensure icon fills 85-90% of canvas
4. **Generate PNG icon pack**: 16, 24, 32, 48, 64, 128, 256, 512, 1024px
5. **Generate ICO files**: multi-size for Windows (tray icon variant without background + full icon with background)
6. **Favicon**: cropped/scaled variant for web presence
7. **Store listing graphics**: screenshots, promotional tiles (per store size requirements)
8. **Social preview image**: Open Graph / Twitter Card image
9. Save all assets to `assets/` in repo + vault note documenting the prompt

### Phase 3: Copy

Generate marketing and listing copy for **all** channels using the Writer DNA profile from the vault:

- **Store descriptions** -- Chrome Web Store, Firefox AMO, Edge, Opera, GitHub repo description, PyPI/npm listing (whichever apply per distribution config)
- **README** -- badges, install instructions, feature highlights, screenshots
- **Changelog** -- from git history since last release, formatted per Keep a Changelog
- **Social posts:**
  - Twitter/X thread (8-tweet format)
  - Reddit posts (auto-select relevant subreddits based on app type)
  - Hacker News "Show HN" post with opening comment
  - Dev.to / Hashnode / Medium article draft
- **Product Hunt** -- tagline, description, maker comment
- **Landing page copy** -- hero (pain-point-first), features, FAQ, CTA, pricing comparison

All copy uses pain-point-first messaging pattern: `[Symptom] -> [Hidden cause] -> [Solution]`

Saved to `marketing/` in repo. For **Update** mode, only changelog + abbreviated social posts.

### Phase 4: Infrastructure

References `application-deployment` skill phases. Based on distribution config:

- **Stripe** (if paid/freemium):
  - Ask: subscription or one-time payment?
  - Ask: what features are gated? (free vs paid partition)
  - Create product, price, webhook, customer portal
  - Set up TIER_CONFIG with entitlement manifest
  - Build Cloudflare Worker with payment/entitlement/usage endpoints
- **CI/CD** -- generate GitHub Actions workflow matching the project's channel type:
  - Browser extension: Chrome/Firefox/Edge store publish on version tag
  - Desktop app: PyInstaller/Tauri build + GitHub Release + R2 upload
  - Web app: deploy on push
  - Library: PyPI/npm publish
- **DNS/Email** -- subdomain or email forwarding setup if needed (ImprovMX)
- **Cloudflare Worker** -- auth/entitlement endpoint for paid apps

Each item flagged as **automated** (skill does it) or **manual** (step-by-step instructions provided). Manual items tracked as tickets.

### Phase 5: Legal

References `application-deployment` Phase 3:

- **Terms of Service** -- on codewarrior4life.com, includes digital delivery/no-refund, chargeback waiver, trial encouragement, SD governing law
- **Privacy Policy** -- what is/isn't collected, third-party disclosures, data retention
- **ToS acceptance gate** -- in-app, version-tracked, must accept before use
- **Stripe Checkout consent** -- `consent_collection.terms_of_service: 'required'`

Skip for free/open-source projects with no data collection.

### Phase 6: Landing Page + SEO

References `application-deployment` Phases 4 + 6:

- Product landing page on codewarrior4life.com:
  - Hero (pain-point-first), problem amplification, solution, features, pricing, CTA, footer
- SEO meta tags on every page (title, description, keywords, canonical)
- Open Graph + Twitter Card tags
- JSON-LD structured data (SoftwareApplication schema)
- Favicon in HTML head
- Add product card to crossroadtech.com products section

### Phase 7: Submit

Build and push artifacts to all applicable channels:

- **Git** -- tag version, push tag
- **GitHub Release** -- create release with changelog + attached artifacts
- **Store submissions** -- trigger CI/CD workflow or provide manual upload instructions for first-time submissions
- **Package registries** -- PyPI, npm, Docker Hub (if applicable)
- **Cloudflare R2** -- signed binary upload + KV metadata update (for self-distributed apps)
- **Directory listings** (launch only) -- AlternativeTo, G2, SourceForge, Capterra, etc. Pre-filled copy + direct URLs.

For **Update** mode: tag + push + trigger CI only.
For **Beta**: pre-release flag on GitHub Release, no store submissions.

### Phase 8: Update Mechanism

Set up end-user update delivery based on app type and monetization:

#### Store-managed (browser extensions)
Nothing to build. Stores handle updates automatically.

#### Lightweight (standalone desktop, free)
For apps like TCP:
- On-launch version check against GitHub Releases API
- Compare current version vs latest release tag
- If newer version exists: show system tray notification (Windows) or CLI message with download link
- No auto-install, no entitlement gating
- Implementation: Python function in core, called at startup

#### Full updater pipeline (desktop, paid/freemium)
For apps like ABM with Tauri:
- **Worker endpoints:**
  - `GET /version` -- returns latest version, changelog, entitlement status
  - `GET /update/:target/:current_version` -- Tauri updater manifest (JWT required)
  - `GET /update-download/:version` -- streams signed artifact from R2
- **Entitlement rules:**
  - Free users: entitled to one major version of updates
  - Pro users: unlimited updates
  - Anonymous: no in-app update
- **Frontend components:**
  - UpdateBanner with three states: entitled (update now), not entitled (upgrade to Pro), dismissed
  - Progress callback during download
  - Automatic relaunch after install
- **Signing:** Ed25519 key pair, public key embedded in Tauri config, `.sig` file alongside installer in R2
- **Backend polling:** version check on startup + every 30 minutes
- **Install mode:** passive (silent NSIS, no user prompts)

### Phase 9: Promote

Execute the marketing push (Launch mode only):

- **Website updates** -- add/update project card on crossroadtech.com and codewarrior4life.com
- **Social posts** -- post to X/Twitter, Reddit (relevant subreddits), Hacker News (Mon-Wed 8-10 AM EST)
- **Content marketing** -- publish Dev.to / Medium / Hashnode article
- **Product Hunt** -- submit listing with maker comment
- **Community** -- relevant Discord servers, forums, Slack groups
- **Directory listings** -- AlternativeTo, G2, SourceForge, Capterra, StackShare, TrustRadius, Crunchbase

Each channel marked **automated** (API wired up) or **manual** (copy + URL provided). Designed for incremental automation -- as APIs get wired, manual items flip to automated without changing skill structure.

For **Update** mode: abbreviated social post announcing the update only.

### Phase 10: Post-Launch Verify

References `application-deployment` Phase 11:

- **Endpoint checks** -- product page, terms, privacy, worker health, admin panel
- **Payment e2e test** (if paid) -- install, ToS, checkout, subscription activation, portal, cancellation
- **DNS verification** -- A records, MX, TXT, CNAME
- **SSL verification** -- HTTPS enforced, cert valid
- **Store listing live** -- confirm listing appears in each store
- **Update mechanism test** -- verify version check returns correct data
- **Create launch promo code** (if paid) -- via admin panel or Stripe Dashboard

For **Update** mode: smoke test only (endpoints up, new version visible).

---

## Relationship to Existing Skills

| Skill | Role |
|-------|------|
| `new-project` | Asks distribution/monetization questions, writes `## Distribution` to CLAUDE.md |
| `publish-project` | Orchestrates the full publish pipeline, reads distribution config |
| `application-deployment` | Referenced by publish-project for infrastructure/legal/SEO/store phase details |
| `brainstorming` | Used before publish-project to design the product itself |
| `writing-plans` | Creates implementation plan after publish-project design is approved |

---

## Automation Roadmap

Current state: many phases are manual with copy+URL provided. Designed for incremental wiring:

| Channel | Current | Target |
|---------|---------|--------|
| GitHub Releases | automated (gh CLI) | automated |
| Chrome Web Store | CI/CD via GitHub Actions | automated |
| Firefox AMO | CI/CD via GitHub Actions | automated |
| Edge Add-ons | manual | automated (API) |
| Opera | manual | manual (no API) |
| X/Twitter | manual (copy provided) | automated (API) |
| Reddit | manual (copy provided) | automated (API) |
| Hacker News | manual (copy provided) | manual (no API) |
| Product Hunt | manual (copy provided) | automated (API) |
| Dev.to | manual (copy provided) | automated (API) |
| Directory listings | manual (copy + URL) | manual (no APIs) |
| Stripe setup | semi-automated (CLI + dashboard) | automated |
| Cloudflare Worker | automated (wrangler CLI) | automated |

---

## Open Questions

None at this time. Design is ready for implementation planning.
