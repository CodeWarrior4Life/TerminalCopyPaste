# Publish Project Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the `publish-project` skill and update `new-project` to capture distribution/monetization decisions upfront.

**Architecture:** Two skill files -- one modified (`new-project/SKILL.md`), one created (`publish-project/SKILL.md`). The publish skill is a 10-phase orchestrator that reads distribution config from `CLAUDE.md` and references `application-deployment` for infrastructure/legal/SEO details rather than duplicating them. Each phase has mode gates (Launch/Update/Beta).

**Tech Stack:** Markdown skill files, Claude Code skill system at `~/.claude/skills/`

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `~/.claude/skills/new-project/SKILL.md` | Modify | Add Distribution & Monetization question block after step 6 |
| `~/.claude/skills/publish-project/SKILL.md` | Create | Full 10-phase publish orchestrator |

---

### Task 1: Update `new-project` -- Add Distribution & Monetization Block

**Files:**
- Modify: `~/.claude/skills/new-project/SKILL.md` (after step 6, before step 7)

- [ ] **Step 1: Read current skill and identify insertion point**

Read `~/.claude/skills/new-project/SKILL.md`. The new questions go after step 6 ("Ask: CLAUDE.md template?") and before step 7 ("Show full plan"). This means current steps 7-9 become steps 8-10.

- [ ] **Step 2: Insert Distribution & Monetization questions**

After step 6 in the `## Flow` section, add a new step 7:

```markdown
7. **Ask: Distribution & Monetization?**
   Present these questions one at a time (multiple choice):

   a. **App type?**
      - Browser extension
      - Desktop app
      - Web app
      - CLI tool
      - Library/package
      - Mobile app

   b. **Target platforms?** (multi-select)
      - Windows
      - macOS
      - Linux
      - Web
      - Chrome / Firefox / Edge / Opera (for extensions)

   c. **Monetization model?**
      - Free / open-source (default)
      - Freemium (free tier + paid features)
      - Paid (purchase required)
      - Donation-ware

   d. **License?**
      - MIT (default)
      - Apache 2.0
      - BSL (with auto-convert period -- ask duration)
      - GPL v3
      - Proprietary

   e. **Distribution channels?** (multi-select, auto-suggested based on app type)
      - GitHub Releases (default for desktop/CLI)
      - Browser extension stores (default for extensions)
      - Docker Hub (suggested for web apps)
      - PyPI / npm (suggested for libraries)
      - Cloudflare R2 (suggested for paid desktop apps)
      - Direct download

   f. **Update mechanism?** (auto-suggested based on app type + monetization)
      - Store-managed (default for extensions)
      - Manual download (default for free desktop)
      - Auto-update with entitlement (default for paid desktop -- full Worker + signed artifact pipeline)
      - Package manager (`pip install --upgrade` / `npm update`)
```

- [ ] **Step 3: Add CLAUDE.md template section for Distribution block**

In step 8d (previously 7d, the CLAUDE.md creation step), add the Distribution block to the template. After the existing Vault Identity section:

```markdown
   Add a `## Distribution` section to CLAUDE.md with the answers:
   ```
   ## Distribution
   - **Type:** {app type}
   - **Platforms:** {comma-separated platforms}
   - **Monetization:** {model}
   - **License:** {license name and details}
   - **Channels:** {comma-separated channels}
   - **Updates:** {mechanism}
   ```
```

- [ ] **Step 4: Renumber subsequent steps**

Renumber old steps 7, 8, 9 to 8, 9, 10. Update any internal references.

- [ ] **Step 5: Verify the skill parses correctly**

Read the modified file back and confirm:
- Step numbering is sequential 1-10
- Distribution questions appear as step 7
- CLAUDE.md template includes `## Distribution` block
- No broken references to old step numbers

- [ ] **Step 6: Commit**

```bash
git add ~/.claude/skills/new-project/SKILL.md
git commit -m "feat(new-project): add distribution & monetization questions"
```

---

### Task 2: Create `publish-project` -- Frontmatter, Header, and Mode Detection

**Files:**
- Create: `~/.claude/skills/publish-project/SKILL.md`

- [ ] **Step 1: Create skill directory**

```bash
mkdir -p ~/.claude/skills/publish-project
```

- [ ] **Step 2: Write frontmatter, header, standing rules, and mode detection**

Write the opening of `~/.claude/skills/publish-project/SKILL.md`:

```markdown
---
name: publish-project
description: Full product publish pipeline -- launch (1.0.0), update (1.x.x+), or beta (0.x.0b). Handles assets, marketing copy, infrastructure, store submissions, update mechanisms, and promotional posts.
triggers:
  - "publish project"
  - "publish product"
  - "launch product"
  - "release product"
  - "push release"
  - "publish update"
---

# /publish-project -- Product Publish Pipeline

Orchestrates the full product publish lifecycle: assets, copy, infrastructure, legal, landing page, store submissions, update mechanisms, and promotional posts.

**Modes:** Launch (1.0.0) | Update (1.x.x+) | Beta (0.x.0b)

## Prerequisites

1. Read the project's `CLAUDE.md` for `## Distribution` block. If missing, ask the user the distribution questions from `/new-project` step 7 and write the block before proceeding.
2. Read `machine_config.md` for paths.
3. Read `application-deployment` skill for infrastructure/legal/SEO reference: `~/.claude/skills/application-deployment/SKILL.md`

## Mode Detection

Determine the publish mode from the version being published:

| Pattern | Mode | Phases |
|---------|------|--------|
| `1.0.0` | **Launch** | All 10 phases |
| `1.x.x+` (any post-1.0 release) | **Update** | Phases 1, 3 (changelog only), 7, 9 (light), 10 (smoke) |
| `0.x.0b` or any `b`/`beta`/`rc` suffix | **Beta** | Phases 1, 7 (pre-release only) |

**Ask the user:**
1. "What version are you publishing?" (suggest based on git tags)
2. Confirm detected mode: "This looks like a [Launch/Update/Beta]. Correct?"

## Phase Matrix

| # | Phase | Launch | Update | Beta |
|---|-------|--------|--------|------|
| 1 | Pre-flight | YES | YES | YES |
| 2 | Assets | YES | skip | skip |
| 3 | Copy | YES | changelog + social | skip |
| 4 | Infrastructure | YES | skip | skip |
| 5 | Legal | YES | skip | skip |
| 6 | Landing page + SEO | YES | skip | skip |
| 7 | Submit | YES | YES | YES (pre-release) |
| 8 | Update mechanism | YES | skip | skip |
| 9 | Promote | YES | light social | skip |
| 10 | Post-launch verify | YES | smoke test | skip |

---
```

- [ ] **Step 3: Verify file created**

```bash
cat ~/.claude/skills/publish-project/SKILL.md | head -20
```

Expected: frontmatter with `name: publish-project` and description visible.

- [ ] **Step 4: Commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): create skill with frontmatter and mode detection" --allow-empty
```

Note: If `~/.claude/` is not a git repo, skip git commands for skill files. The vault copy serves as version control.

---

### Task 3: Phase 1 -- Pre-flight

**Files:**
- Modify: `~/.claude/skills/publish-project/SKILL.md` (append)

- [ ] **Step 1: Append Phase 1 content**

Append to `~/.claude/skills/publish-project/SKILL.md`:

```markdown
## Phase 1: Pre-flight (All Modes)

### 1.1 Read Distribution Config

Parse the `## Distribution` block from the project's `CLAUDE.md`:

```
Type: {type}
Platforms: {platforms}
Monetization: {monetization}
License: {license}
Channels: {channels}
Updates: {update_mechanism}
```

If the block is missing, stop and ask the user the distribution questions. Write the block to `CLAUDE.md` before proceeding.

### 1.2 Validate Build State

1. Run the project's test suite. If tests fail, stop -- do not publish broken code.
2. Check for uncommitted changes: `git status --porcelain`. If dirty, stop and ask user to commit or stash.
3. Check current version tag: `git describe --tags --abbrev=0`. Confirm it matches the intended publish version.

### 1.3 Credential Check

Based on the distribution config, verify credentials are available. Check all three credential locations:
1. `~/.claude/memory/credentials.md`
2. Project memory credentials
3. Repo `.credentials.md`

**Required credentials by channel:**

| Channel | Credential | Where to get it |
|---------|-----------|-----------------|
| GitHub Releases | `gh` CLI authenticated | `gh auth login` |
| Chrome Web Store | CHROME_EXTENSION_ID, CHROME_CLIENT_ID, CHROME_CLIENT_SECRET, CHROME_REFRESH_TOKEN | Google Cloud Console OAuth + Chrome Developer Dashboard |
| Firefox AMO | FIREFOX_JWT_ISSUER, FIREFOX_JWT_SECRET | AMO API credentials page |
| Edge Add-ons | EDGE_PRODUCT_ID, EDGE_CLIENT_ID, EDGE_CLIENT_SECRET, EDGE_ACCESS_TOKEN_URL | Azure AD app registration |
| Stripe | STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY, STRIPE_WEBHOOK_SECRET | Stripe Dashboard > Developers > API keys |
| Cloudflare | CF_ACCOUNT_ID, CF_API_TOKEN | Cloudflare Dashboard |
| Recraft | RECRAFT_API_TOKEN | Recraft dashboard |

**For each missing credential:**
- Flag as blocker
- Provide the exact URL and steps to obtain it
- Create a ticket via `create_ticket` if the setup requires multiple steps

### 1.4 Pre-flight Report

Present a summary:

```
PUBLISH PRE-FLIGHT: {project name} v{version} ({mode})

Distribution: {type} | {platforms} | {monetization}
Channels: {channels}

[READY]   GitHub CLI authenticated
[READY]   Tests passing (X tests, 0 failures)
[READY]   Working tree clean
[MISSING] Chrome Web Store credentials -- see setup instructions below
[SKIP]    Stripe (free/open-source project)

Phases to execute: 1, 2, 3, 7, 8, 9, 10
Blockers: 1 (Chrome Web Store credentials)
```

If blockers exist, ask user: "Resolve blockers before continuing, or skip those channels?"

---
```

- [ ] **Step 2: Verify appended correctly**

Read the file and confirm Phase 1 section is present after the Phase Matrix.

- [ ] **Step 3: Commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): add Phase 1 pre-flight"
```

---

### Task 4: Phase 2 -- Assets

**Files:**
- Modify: `~/.claude/skills/publish-project/SKILL.md` (append)

- [ ] **Step 1: Append Phase 2 content**

Append to `~/.claude/skills/publish-project/SKILL.md`:

```markdown
## Phase 2: Assets (Launch Only)

### 2.1 Icon Generation

**Step 1: Compose the Recraft prompt.**

Use the brand style guide from `application-deployment` Phase 5:

- Colors: dark purple `#190E24` (background), teal `#46C3AC` (primary accent), gold `#F6B256` (secondary accent), white `#F4F4F3` (details)
- Style: flat, minimal, geometric, no gradients, no text
- Canvas: 1024x1024, icon content fills 85-90%

Compose a prompt describing the product's core metaphor. Example:

```
Flat app icon, [PRODUCT METAPHOR]. Minimal geometric shapes, no text, no gradients.
Dark purple background, teal for [PRIMARY ELEMENT], gold for [SECONDARY ELEMENT],
white accents for fine details. Rounded square icon shape, clean edges, centered composition.
```

**Step 2: Present the prompt and ask the user:**

> "Here's the Recraft prompt I'd use to generate the icon:
>
> `{prompt}`
>
> Should I call the Recraft API to generate it, or do you want to generate it yourself and bring back the file?"

**If user says generate:**

Call the Recraft API per `application-deployment` Phase 5.2. Use `recraftv4_vector` model for best quality. Download the SVG immediately (URLs expire in ~24h):

```bash
curl -sL "{generated_url}" -o assets/{product}-original.svg
```

**If user says DIY:** Wait for them to provide the SVG file path.

### 2.2 SVG Post-Processing

Per `application-deployment` Phase 5.3:

1. Fix viewBox to ensure icon content fills 85-90% of canvas
2. Remove unwanted text elements
3. Strip white corner overlays or decorative artifacts
4. Normalize viewBox attribute

Create a **tray icon variant** (for desktop apps): remove the background path elements, then adjust viewBox to crop to content bounds with 5% padding. Save as `assets/{product}-tray-icon.svg`.

### 2.3 PNG + ICO Generation

Render SVGs to PNGs at all required sizes: 16, 24, 32, 48, 64, 128, 256, 512, 1024px.

**Method:** Use a local HTTP server + browser canvas rendering (Cairo is unreliable on Windows), then POST base64 data to a Python receiver. Convert PNGs to multi-size ICO files using Pillow.

**Required ICO files:**
- `assets/{product}-icon.ico` -- full icon with background (7 sizes: 16-256)
- `assets/{product}-tray-icon.ico` -- transparent tray icon (7 sizes: 16-256) -- desktop apps only

**PNG directories:**
- `assets/{product}-icon/` -- full icon PNGs at all 9 sizes
- `assets/{product}-tray-icon/` -- tray icon PNGs at all 9 sizes (desktop apps only)

### 2.4 Favicon

Copy the 32x32 PNG as `assets/favicon.png`. For ICO favicon, use the 16+32px sizes from the icon ICO.

### 2.5 Social Preview Image

Generate an Open Graph image (1200x630) combining:
- Product icon (centered or left-aligned)
- Product name + tagline text
- Brand background color

Save as `assets/{product}-og.png`.

### 2.6 Save Asset Prompt to Vault

Create a vault note at `02_Projects/{project}/` documenting:
- The Recraft prompt used
- File locations
- Notes on any manual adjustments made

Save the prompt to `assets/icon-prompt.md` in the repo as well.

---
```

- [ ] **Step 2: Verify and commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): add Phase 2 assets"
```

---

### Task 5: Phase 3 -- Copy

**Files:**
- Modify: `~/.claude/skills/publish-project/SKILL.md` (append)

- [ ] **Step 1: Append Phase 3 content**

Append to `~/.claude/skills/publish-project/SKILL.md`:

```markdown
## Phase 3: Copy (Launch: full | Update: changelog + social)

### Prerequisites

Read the Writer DNA profile from the vault before writing any copy:
- Path: `02_Projects/Protocols/Writer Profiles/Writer DNA - Cyril.md`
- All copy uses Cyril's voice unless overridden by "write as {name}" or "no voice styling"

### 3.1 Changelog (All non-Beta modes)

Generate from git history since the last release tag:

```bash
git log $(git describe --tags --abbrev=0 HEAD^)..HEAD --oneline --no-decorate
```

Format per Keep a Changelog (https://keepachangelog.com/):

```markdown
## [{version}] - {YYYY-MM-DD}

### Added
- {new features}

### Changed
- {modifications to existing features}

### Fixed
- {bug fixes}
```

Save to `CHANGELOG.md` in repo root (append at top, below header).

### 3.2 Store Descriptions (Launch only)

Generate for each applicable store based on distribution config channels:

**Chrome Web Store / Edge Add-ons:**
- Summary: max 132 characters, SEO-optimized
- Full description: pain-point-first messaging, feature list, privacy assurance

**Firefox AMO:**
- Same as Chrome but note any Firefox-specific features or limitations

**GitHub repo description:**
- One-liner (max 350 chars) for the repo About section

**PyPI / npm** (if applicable):
- `description` field for pyproject.toml or package.json
- Long description from README

Save all store copy to `marketing/copy.md`.

### 3.3 README (Launch only)

Generate or update `README.md` with:
- Badges: version, license, downloads (shields.io format)
- One-paragraph description (pain-point-first)
- Screenshot or demo GIF
- Installation instructions (per-platform)
- Usage instructions
- Configuration reference
- Contributing section
- License section

### 3.4 Social Posts (Launch: full | Update: abbreviated)

Generate copy for ALL channels regardless of distribution type. Save to `marketing/copy.md`:

**Twitter/X thread (8-tweet format):**
1. Hook tweet (problem statement)
2. Problem amplification
3. Solution introduction
4. Key feature 1
5. Key feature 2
6. Key feature 3
7. Call to action with link
8. Engagement question

**Reddit posts:**
Auto-select 3-4 relevant subreddits based on app type:
- Desktop utility: r/software, r/windows, r/commandline, r/tools
- Browser extension: r/chrome, r/browsers, r/webdev, r/sysadmin
- Web app: r/webdev, r/SaaS, r/selfhosted, r/InternetIsBeautiful
- CLI tool: r/commandline, r/programming, r/devops, r/linux

Each post tailored to the subreddit's culture and rules.

**Hacker News:**
- "Show HN: {Product} - {one-line description}" post
- Opening comment with technical details, motivation, and what's next

**Product Hunt:**
- Tagline (max 60 chars)
- Description (2-3 paragraphs)
- Maker comment

**Dev.to / Hashnode / Medium:**
- Article draft (800-1200 words): problem, journey, solution, technical details, what's next

**For Update mode:** Generate only:
- Single tweet announcing the update with changelog highlights
- Single Reddit post to the most relevant subreddit
- Skip HN, Product Hunt, Dev.to, Medium

### 3.5 Landing Page Copy (Launch only)

Generate copy for the product landing page:

1. **Hero:** Pain-point-first headline + subhead + CTA button text
2. **Problem amplification:** "Here's what's really happening..." section
3. **Solution introduction:** What the product does
4. **Feature highlights:** 3-4 key features with short descriptions
5. **Pricing comparison** (if freemium/paid): Free vs Pro table
6. **FAQ:** 4-6 common questions
7. **Footer CTA:** Final call to action

Save to `marketing/landing-page-copy.md`.

---
```

- [ ] **Step 2: Verify and commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): add Phase 3 copy"
```

---

### Task 6: Phases 4-6 -- Infrastructure, Legal, Landing Page + SEO

**Files:**
- Modify: `~/.claude/skills/publish-project/SKILL.md` (append)

These phases reference `application-deployment` heavily, so the skill content is delegation instructions rather than duplicated details.

- [ ] **Step 1: Append Phases 4, 5, and 6**

Append to `~/.claude/skills/publish-project/SKILL.md`:

```markdown
## Phase 4: Infrastructure (Launch Only)

This phase references `application-deployment` (`~/.claude/skills/application-deployment/SKILL.md`). Read it before executing.

### 4.1 Determine Required Infrastructure

Based on the `## Distribution` config:

| Monetization | Infrastructure Needed |
|-------------|----------------------|
| Free/open-source | CI/CD workflow only |
| Freemium | Stripe + Cloudflare Worker + CI/CD |
| Paid | Stripe + Cloudflare Worker + CI/CD |
| Donation-ware | CI/CD + donation link (no Worker) |

### 4.2 Stripe Setup (Paid/Freemium Only)

**Ask the user:**
1. "Subscription or one-time payment?"
2. "What price point?" (suggest $X/month or $X one-time based on app type)
3. "What features are free vs paid?" (define the TIER_CONFIG)

Follow `application-deployment` Phase 2 (Stripe), Phase 2B (Entitlement & Usage), and Phase 2C (Native App Security) as applicable.

Key deliverables:
- Stripe product + price created
- Cloudflare Worker deployed with payment/entitlement/usage endpoints
- TIER_CONFIG defined
- Client-side payment adapter + entitlement caching
- All credentials saved to three locations per standing rules

### 4.3 CI/CD Workflow

Generate `.github/workflows/publish.yml` based on distribution channels:

| Channel Type | Workflow Template |
|-------------|------------------|
| Browser extension stores | `application-deployment` Phase 10 (Chrome/Firefox/Edge publish on tag) |
| GitHub Releases (desktop) | Build executable + create release + upload artifacts on tag |
| Cloudflare R2 (paid desktop) | Build + sign + upload to R2 + update KV metadata on tag |
| Docker Hub | Build image + push on tag |
| PyPI | Build wheel + twine upload on tag |
| npm | npm publish on tag |

### 4.4 DNS & Email (If Needed)

If the product needs its own subdomain or email forwarding, follow `application-deployment` Phase 7.

Flag each infrastructure item as:
- **Automated** -- skill executes it
- **Manual** -- skill provides step-by-step instructions and creates a ticket

---

## Phase 5: Legal (Launch Only, Paid/Freemium)

Skip entirely for free/open-source projects with no data collection.

Follow `application-deployment` Phase 3 for:

### 5.1 Terms of Service

Create on codewarrior4life.com at `extensions/{product}/terms.html` (or appropriate path for non-extensions).

Mandatory provisions per `application-deployment` Phase 3.1:
- Digital delivery / no-refund
- Chargeback waiver
- Trial encouragement
- South Dakota governing law (Codington County)
- Entity: Crossroads Technologies, LLC

### 5.2 Privacy Policy

Create at `extensions/{product}/privacy.html`.

Per `application-deployment` Phase 3.2:
- What IS collected (install ID, billing via Stripe)
- What is NOT collected (explicit section)
- Third-party disclosures (Stripe, Cloudflare)
- Local-only data processing emphasis
- Data retention and deletion

### 5.3 ToS Acceptance Gate

Per `application-deployment` Phase 3.3:
- In-app acceptance required before functionality access
- Version-tracked (`tosVersion` in local storage)
- Stripe checkout: `consent_collection.terms_of_service: 'required'`

---

## Phase 6: Landing Page + SEO (Launch Only)

Follow `application-deployment` Phases 4 and 6.

### 6.1 Product Landing Page

Create on codewarrior4life.com. Use the copy generated in Phase 3.5.

Structure per `application-deployment` Phase 4.1:
1. Hero section (pain-point-first)
2. Problem amplification
3. Solution introduction
4. Feature highlights with icons
5. Pricing table (if paid/freemium)
6. CTA buttons
7. Footer with Terms, Privacy, company links

### 6.2 SEO

Apply to EVERY page per `application-deployment` Phase 6:
- Meta tags (title, description, keywords, canonical)
- Open Graph tags (use the OG image from Phase 2.5)
- Twitter Card tags
- JSON-LD structured data (SoftwareApplication schema)

### 6.3 Website Cards

- Add product card to **crossroadtech.com** products section
- Add product card to **codewarrior4life.com** projects grid
- Update SEO keywords meta tag on both sites

---
```

- [ ] **Step 2: Verify and commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): add Phases 4-6 infrastructure, legal, landing page"
```

---

### Task 7: Phase 7 -- Submit

**Files:**
- Modify: `~/.claude/skills/publish-project/SKILL.md` (append)

- [ ] **Step 1: Append Phase 7 content**

Append to `~/.claude/skills/publish-project/SKILL.md`:

```markdown
## Phase 7: Submit (All Modes)

### 7.1 Git Tag + Push

```bash
git tag -a v{version} -m "Release v{version}"
git push origin v{version}
```

For Beta: use the beta suffix (`v0.2.0b1`).

### 7.2 GitHub Release

```bash
gh release create v{version} \
  --title "v{version}" \
  --notes-file CHANGELOG_EXCERPT.md \
  {artifact_files...}
```

For Beta: add `--prerelease` flag.
For Update: same as Launch.

**Attach artifacts based on distribution type:**
- Desktop app: `.exe`, `.msi`, `.dmg`, `.AppImage` (whichever were built)
- CLI tool: platform-specific binaries
- Library: skip (published to registry instead)
- Browser extension: skip (published to stores via CI/CD)

### 7.3 Store Submissions (Launch + Update, Not Beta)

**If CI/CD is configured** (Phase 4.3):
The tag push triggers the publish workflow automatically. Monitor:

```bash
gh run watch
```

**If first-time submission** (no CI/CD yet):
Provide manual upload instructions per `application-deployment` Phase 9:

- **Chrome Web Store:** Build ZIP, upload at https://chrome.google.com/webstore/devconsole
- **Firefox AMO:** Run Firefox build script, upload at https://addons.mozilla.org/en-US/developers/
- **Edge Add-ons:** Upload Chrome ZIP at https://partner.microsoft.com/en-us/dashboard/microsoftedge/overview
- **Opera:** Upload Chrome ZIP at https://addons.opera.com/developer/

### 7.4 Package Registries (If Applicable)

| Registry | Command |
|----------|---------|
| PyPI | `python -m build && twine upload dist/*` |
| npm | `npm publish` |
| Docker Hub | `docker build -t {user}/{product}:{version} . && docker push {user}/{product}:{version}` |

### 7.5 Cloudflare R2 (Paid Desktop Apps)

For apps using the full updater pipeline:

```bash
# Upload signed artifacts
wrangler r2 object put releases/{version}/{product}-setup.exe --file dist/{product}-setup.exe
wrangler r2 object put releases/{version}/{product}-setup.exe.sig --file dist/{product}-setup.exe.sig

# Update KV metadata
wrangler kv:key put --namespace-id={ns_id} "app:latest_version" \
  '{"latest":"{version}","changelog":"{changelog}","pub_date":"{iso_date}"}'

# Update binary hash for integrity verification (if applicable)
sha256sum dist/{product}-setup.exe
wrangler secret put BINARY_SHA256  # paste the hash
```

### 7.6 Directory Listings (Launch Only)

Provide pre-filled copy and direct submission URLs for:

| Directory | URL | Notes |
|-----------|-----|-------|
| AlternativeTo | https://alternativeto.net/manage/add/ | Tier 1 priority |
| G2 | https://www.g2.com/products/new | Tier 1 priority |
| SourceForge | https://sourceforge.net/create/ | Tier 1 priority |
| Capterra | https://www.capterra.com/vendors/sign-up | Tier 1 priority |
| StackShare | https://stackshare.io/tools/new | Tier 2 |
| TrustRadius | https://www.trustradius.com/ | Tier 2 |
| Crunchbase | https://www.crunchbase.com/add-new | Tier 2 |

Mark each as **manual** with the copy from Phase 3 pre-filled for easy paste.

---
```

- [ ] **Step 2: Verify and commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): add Phase 7 submit"
```

---

### Task 8: Phase 8 -- Update Mechanism

**Files:**
- Modify: `~/.claude/skills/publish-project/SKILL.md` (append)

- [ ] **Step 1: Append Phase 8 content**

Append to `~/.claude/skills/publish-project/SKILL.md`:

```markdown
## Phase 8: Update Mechanism (Launch Only)

Set up end-user update delivery. The mechanism is determined by app type + monetization from the `## Distribution` config.

### Decision Matrix

| Type | Monetization | Mechanism |
|------|-------------|-----------|
| Browser extension | any | Store-managed (nothing to build) |
| Desktop app | free/open-source | Lightweight GitHub check |
| Desktop app | freemium/paid | Full updater pipeline |
| Web app | any | Deploy = update (nothing to build) |
| CLI tool | any | Package manager + version notice |
| Library | any | Package manager (nothing to build) |

### 8.1 Store-Managed (Browser Extensions)

Nothing to implement. Browser extension stores push updates automatically when a new version is published. The CI/CD workflow from Phase 4.3 handles the upload; users receive the update within hours.

### 8.2 Lightweight GitHub Check (Free Desktop Apps)

For apps like TCP. Implement a version check function in the application:

**On application startup:**
1. Read the current version from the app's own metadata (e.g., `__version__` in Python, version in config)
2. Query GitHub Releases API: `GET https://api.github.com/repos/{owner}/{repo}/releases/latest`
3. Compare `tag_name` (strip `v` prefix) against current version using semver
4. If newer version exists:
   - **Desktop with tray (AHK/Windows):** Show a tray tooltip or balloon notification: "TCP v{new} available -- click to download" linking to the release URL
   - **CLI:** Print a one-line notice on startup: "Update available: v{new} (you have v{current}). Download: {url}"
5. Cache the check result for 24 hours to avoid hitting the API on every launch
6. Never block startup -- version check runs async, failure is silent

**Implementation notes:**
- No authentication needed for public repos (60 req/hr rate limit is sufficient for per-user checks)
- For private repos, use a GitHub token or a simple version endpoint
- No auto-install -- user downloads and installs manually

### 8.3 Full Updater Pipeline (Paid/Freemium Desktop Apps)

For apps like ABM using Tauri. This is the most complex mechanism. Reference the ABM implementation as the canonical pattern.

**Worker endpoints to create:**

1. **`GET /version`** -- public version check
   - Request: optional `Authorization: Bearer {jwt}` header
   - Response: `{ latest, download_url, changelog, entitled, entitled_through }`
   - Entitlement logic:
     - Pro users (`paid: true`): entitled to all versions
     - Free users: entitled within `entitled_through` major version window
     - Anonymous: entitled (shows upgrade CTA in frontend)

2. **`GET /update/:target/:current_version`** -- Tauri updater manifest
   - Request: `Authorization: Bearer {jwt}` required
   - Response (if entitled + update available):
     ```json
     {
       "url": "https://worker.dev/update-download/{version}",
       "version": "{version}",
       "signature": "{ed25519_sig_base64}",
       "notes": "{changelog}",
       "pub_date": "{iso_date}"
     }
     ```
   - Response (no update or not entitled): `204 No Content`

3. **`GET /update-download/:version`** -- artifact stream
   - Streams the signed installer from R2

**Frontend components:**

- **UpdateBanner** with three states:
  1. `update_available && entitled` -- blue banner: "Version X available -- Update Now"
  2. `update_available && !entitled` -- amber banner: "Version X available -- Upgrade to Pro"
  3. `dismissed` -- hidden (cached in localStorage, re-appears on next version)

- **Update flow** (when user clicks "Update Now"):
  1. Call Tauri updater `check()` with JWT header
  2. Download + verify Ed25519 signature
  3. Install silently (passive NSIS mode)
  4. Relaunch app

**Backend polling:**
- Version check on startup + every 30 minutes
- Cache response in local database/storage

**Signing setup:**
1. Generate Ed25519 key pair (Tauri CLI: `tauri signer generate`)
2. Embed public key in `tauri.conf.json` under `plugins.updater.pubkey`
3. Build with `createUpdaterArtifacts: true` to generate `.sig` files
4. Store private key securely (never in repo)

**Entitlement rules:**
- Free user registration: `entitled_through = bumpMajor(current_version, 1)`
- Pro users: `paid: true` in KV, unlimited updates
- Check entitlement on both frontend (UI gating) and worker (download gating)

---
```

- [ ] **Step 2: Verify and commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): add Phase 8 update mechanism"
```

---

### Task 9: Phases 9-10 -- Promote and Post-Launch Verify

**Files:**
- Modify: `~/.claude/skills/publish-project/SKILL.md` (append)

- [ ] **Step 1: Append Phases 9 and 10**

Append to `~/.claude/skills/publish-project/SKILL.md`:

```markdown
## Phase 9: Promote (Launch: full | Update: light social)

### 9.1 Website Updates (Launch Only)

- Add/update product card on **crossroadtech.com** products section
- Add/update product card on **codewarrior4life.com** projects grid
- Ensure the landing page from Phase 6 is live and linked

### 9.2 Social Media Posts

Use the copy from Phase 3.4. Post to each channel:

| Channel | Launch | Update | Automation Status |
|---------|--------|--------|-------------------|
| X/Twitter | Full 8-tweet thread | Single announcement tweet | Manual (copy provided) |
| Reddit | 3-4 subreddit posts | 1 post to primary subreddit | Manual (copy provided) |
| Hacker News | "Show HN" post | Skip | Manual (copy provided) |
| Product Hunt | Full listing | Skip | Manual (copy provided) |
| Dev.to | Full article | Skip | Manual (copy provided) |
| Medium | Cross-post from Dev.to | Skip | Manual (copy provided) |
| Hashnode | Cross-post from Dev.to | Skip | Manual (copy provided) |

**Timing guidance:**
- Hacker News: Mon-Wed, 8-10 AM EST for best visibility
- Product Hunt: Tuesday-Thursday launches perform best
- Reddit: varies by subreddit, generally weekday mornings

**For each manual channel:** Present the pre-written copy and the submission URL. Ask user to confirm before proceeding to the next channel.

**Automation hooks:** Each channel entry includes an `automation_status` field. When an API is wired up in the future, flip from `manual` to `automated` and add the API call. The skill structure doesn't change -- only the execution method for that channel.

### 9.3 Directory Submissions (Launch Only)

Use the directory list from Phase 7.6. Work through submissions tier by tier:

**Tier 1 (do first):** AlternativeTo, G2, Capterra, SourceForge
**Tier 2 (do next):** StackShare, TrustRadius, Crunchbase

For each: provide the pre-filled copy and direct URL. These are always manual.

---

## Phase 10: Post-Launch Verify (Launch: full | Update: smoke test)

### 10.1 Endpoint Checks

Verify all live URLs return expected responses:

```bash
# Product page
curl -sI https://codewarrior4life.com/{product-path}/ | head -3

# Terms page (if applicable)
curl -sI https://codewarrior4life.com/{product-path}/terms.html | head -3

# Privacy page (if applicable)
curl -sI https://codewarrior4life.com/{product-path}/privacy.html | head -3

# Worker health (if applicable)
curl -s https://{product}-auth.codewarrior4life.workers.dev/health

# GitHub Release
gh release view v{version}
```

### 10.2 Payment E2E Test (Paid/Freemium, Launch Only)

Per `application-deployment` Phase 11.2:

1. Install the product fresh
2. Accept ToS gate
3. Click upgrade / subscribe
4. Complete Stripe Checkout with test card `4242 4242 4242 4242`
5. Verify subscription activates
6. Open Customer Portal, verify it loads
7. Cancel subscription, verify downgrade
8. Check Stripe Dashboard for events

**Switch to live mode** for real launches. Test mode uses `pk_test_` and `sk_test_` keys.

### 10.3 Update Mechanism Test

- **Store-managed:** Verify store listing shows the correct version
- **Lightweight check:** Run the app, confirm it reports "up to date" (or the correct new version if testing against an older install)
- **Full pipeline:** Call `GET /version` and verify response matches published version. Call `/update/{target}/{old_version}` with a valid JWT and verify manifest is returned.

### 10.4 DNS/SSL Verification (Launch Only)

```bash
nslookup -type=A {domain} 8.8.8.8
nslookup -type=MX {domain} 8.8.8.8
curl -sI https://{domain} | head -5
```

### 10.5 Launch Promo Code (Paid, Launch Only)

Create a launch promo code (e.g., `LAUNCH50` for 50% off first month):
- Via admin panel: `https://{product}-auth.codewarrior4life.workers.dev/admin`
- Or via Stripe Dashboard: Products > Coupons

### 10.6 Update Project Records

1. Update `active-work.md` with deployment status and all live URLs
2. Write vault session note to `02_Projects/{Project Name}/Sessions/`
3. Update project memory files with new credentials, URLs, store listing IDs
4. Add store listing URLs to reference/credential stores

### 10.7 Summary Report

Present a final summary:

```
PUBLISH COMPLETE: {project name} v{version} ({mode})

Live URLs:
  Product page: https://...
  GitHub Release: https://...
  Chrome Web Store: https://...
  (etc.)

Store Submissions:
  [LIVE] GitHub Release
  [PENDING REVIEW] Chrome Web Store (1-3 business days)
  [SUBMITTED] Firefox AMO
  [MANUAL] Opera -- download from GitHub Actions artifacts

Marketing:
  [POSTED] Twitter thread
  [POSTED] Reddit (3 subreddits)
  [MANUAL] Hacker News -- post Monday 8 AM EST
  [MANUAL] Product Hunt -- schedule for Tuesday

Next steps:
  - Monitor store reviews for approval
  - Post to Hacker News on Monday
  - Schedule Product Hunt launch
```

---
```

- [ ] **Step 2: Verify and commit**

```bash
git -C ~ add .claude/skills/publish-project/SKILL.md
git -C ~ commit -m "feat(publish-project): add Phases 9-10 promote and verify"
```

---

### Task 10: Save to Vault + Final Verification

**Files:**
- Vault: `02_Projects/Terminal Copy Paste/Plans/`
- Skill: `~/.claude/skills/publish-project/SKILL.md` (final read-back)

- [ ] **Step 1: Read back the complete skill file**

Read `~/.claude/skills/publish-project/SKILL.md` in full. Verify:
- Frontmatter is valid (name, description, triggers)
- All 10 phases are present
- Phase matrix matches phase content
- No TBDs, TODOs, or placeholders
- All references to `application-deployment` include the file path
- Mode gates (Launch/Update/Beta) are consistent

- [ ] **Step 2: Read back the modified new-project skill**

Read `~/.claude/skills/new-project/SKILL.md`. Verify:
- Steps are numbered 1-10
- Step 7 contains Distribution & Monetization questions
- CLAUDE.md template includes `## Distribution` block

- [ ] **Step 3: Create vault plan note**

Create a vault note at `02_Projects/Terminal Copy Paste/Plans/` with:
- Title: "TCP - Publish Project Skill Implementation Plan"
- Summary of the plan: 10 tasks, 2 skill files (1 new, 1 modified)
- Reference to repo plan file location

- [ ] **Step 4: Register skill in vault skill library**

Use `create_note` to save the complete `publish-project` SKILL.md content as a vault note in the skills area for reference.

- [ ] **Step 5: Final commit**

```bash
cd "G:/My Drive/Projects Merge/TerminalCopyPaste"
git add docs/superpowers/plans/2026-04-03-publish-project-skill.md
git commit -m "docs: publish-project skill implementation plan"
```
