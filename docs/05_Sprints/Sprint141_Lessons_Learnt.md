# Lessons Learned

**Sprint:** Sprint 141 — MADBOOTS: the rebrand (badge · wordmark · tagline · disclaimer)

**Dates:** 2026-08-10 → 2026-08-11 *(planned 2026-08-10; parked pending art; built 2026-08-11)*

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Rebrand the product **FPL Assistant → MADBOOTS** (tagline *Fantasy Football, Calculated.*) across every surface a
user sees — the wordmark, the tagline, and the **MB badge** as the favicon + small mark — folded in as **accents**
on the current light/theme-aware app (approach B), with a single `brand.py` source of truth. Keep the internal
`fpl-assistant` package + `FPL_*` secrets unchanged.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Preview on real assets before wiring** — a faithful Artifact preview (the real badge in the Home header / beta
  gate / card band) got owner sign-off *before* a single page was touched (ADR-103, the visual-preview habit).
- **One source of truth** — `brand.py` (`NAME`/`TAGLINE`/`page_config`/`wordmark_html`/`badge_*`/`DISCLAIMER`) so
  the name/mark live in one place, not ~19 hardcodes.

### New Skills Acquired

- **Separate the visible rebrand from the invisible plumbing.** The name lives in ~19 user-facing spots (a cheap,
  safe swap) but the `FPL_*` secrets + the `fpl-assistant` package/repo are load-bearing (renaming `FPL_*` breaks
  every deploy secret). Rebrand what users see; leave the plumbing — a deliberate, recorded split (ADR-103).
- **A detailed mascot and a small icon are two different jobs.** The AI mascot wouldn't survive shrinking to a
  favicon (lost teeth, muddy colours); a clean transparent **badge** is the small mark, the illustration a deferred
  big-surface hero. The "get the art right, don't rush" call (owner) was the right one — it produced a mark that
  actually renders to ~32px.
- **Colour can do a word-break.** Dropping the space → **MADBOOTS** (one word) works because the two-tone MAD-purple/
  BOOTS-orange split reads the break — and it aligns the display name with the one-word domain/handle.
- **A wordmark is markdown, not a title — so update the tests that keyed on the title.** Moving Home's brand from an
  `st.title` to a two-tone `st.markdown` wordmark meant the access/analytics "is it unlocked?" checks (which keyed on
  `at.title`) had to detect the brand in `at.markdown` instead. An `aria-label="MADBOOTS"` gave both accessibility
  *and* a stable test hook (the coloured spans aren't a contiguous "MADBOOTS").

---

# What Went Well ✅

- **Owner-approved before wiring** — the real-badge preview de-risked the whole sprint; zero rework on the look.
- **Low-risk by design** — display/asset-only; `brand.py` one source of truth; no engine/xP/secret change; the
  `page_icon` swap made every tab show the badge in one place.
- **Honest scope** — kept the internal identity + `FPL_*` secrets; the repo/domain changeover stayed a separate,
  deliberate backlog item (not silent drift).
- 952 → 958 tests (+6); ruff + CI green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The AI badge wouldn't render small | a detailed mascot traced to a muddy favicon | Owner produced a clean transparent PNG badge; the illustration is a deferred hero |
| ~19 hardcodes vs. DRY | the name is in many visible spots | Introduce `brand.py` (name/tagline/page_config) in US-348; grow it in US-349 |
| Tests keyed on Home's `st.title` | the two-tone wordmark is markdown, not a title | Detect the brand in `at.markdown` via an `aria-label`; update access/analytics |
| Card-band badge weight on the pitch | 15 kits could each embed the badge | The band only renders on the *full* card (compact popover has none) → a 64² data URI, once |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Rebrand scope | Split visible (swap) from invisible/load-bearing (`FPL_*`, package) — rebrand the first, keep the second |
| Mark system | A rich illustration (hero) and a simple icon (favicon) are different assets, designed for different sizes |
| Streamlit favicon | `page_config`'s `page_icon` takes an image path → one place sets the badge on every tab |
| Two-tone wordmark | CSS spans + an `aria-label` = a coloured lockup that's still accessible *and* testable |

---

# Development Lessons 💻

- Get sign-off on the *real* asset in context before wiring — a preview is cheaper than a re-do across 19 surfaces.
- Put the brand behind one module; swapping the name/mark later is then a one-file change.
- When a visual moves from one widget type to another (title → markdown), grep the tests that asserted the old shape.

---

# AI Collaboration Lessons 🤖

- The rebrand is **display/asset-only** — `brand.py` is pure (no Streamlit import); the analytics/decision core, the
  one-xP metric, and the read-only guardrail are untouched. The favicon/wordmark/tagline/disclaimer are accents; the
  engine is unchanged. Honest provenance recorded (AI-origin mark, a raster PNG; vector/redraw deferred).

### Notes _(for Tony)_

---

# Decisions Made 📋

**ADR-103 — the MADBOOTS brand identity.** Rename user-facing surfaces FPL Assistant → **MADBOOTS** (one word;
two-tone colour split), tagline *Fantasy Football, Calculated.*; a mark system (badge = favicon/small, CSS wordmark =
headers, illustration = deferred hero); **approach B** (accents, not a dark reskin); keep the internal `fpl-assistant`
package + `FPL_*` secrets (only `USER_AGENT`/CLI `prog` flip); a not-affiliated disclaimer; honest AI-origin/raster
notes. Built US-348 (the swap + tagline) · US-349 (`brand.py` + the badge favicon + the wordmark) · US-350 (the
disclaimer + the live-doc rebrand). The repo-transfer + `madboots.com` changeover stays a separate bundled backlog
item.

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Owner (browser smoke):** the tab icon is the MB badge; Home shows the badge + two-tone MADBOOTS + tagline; the
  beta gate leads with the badge; a player card's band reads MADBOOTS; the disclaimer footer shows.
- **Owner (the bundled infra changeover — `docs/Backlog.md` "Branding"):** transfer the repo to `madbootsfpl`
  (reconnect Streamlit) + rename the subdomain to `madboots.streamlit.app` + 301-forward `madboots.com`, together.
- **Deferred:** the boots **illustration** hero (a transparent export); a **true-vector SVG** badge + a **designer
  redraw**; a **dark reskin** (approach A); a **madboots.com landing page**; an email/domain migration.
- **GW1 (2026-08-21):** the calibration flip remains the data-gated owner thread.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "preview the real asset, get sign-off, then wire" loop for any visual change.

---

# Key Commands Learned

```text
python -m pytest tests/test_brand.py -q     # the brand source of truth + the "no stray old name" guard
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| MADBOOTS | The product brand (one word; two-tone MAD-purple/BOOTS-orange wordmark) |
| Approach B | Fold the marks in as *accents* on the current light app (vs. A = a full dark reskin) |
| The mark system | Badge (favicon/small) · CSS wordmark (headers) · illustration (deferred hero) |
| `brand.py` | The single source of truth — name/tagline/page_config/wordmark/badge/disclaimer |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `docs/06_Decisions/ADR-103-madboots-brand-identity.md` | The identity decision + the deferred set |
| `src/web_streamlit/brand.py` · `assets/madboots-badge*.png` | The brand module + the badge assets |
| `docs/Backlog.md` "Branding" | The bundled repo-transfer + domain changeover (still to do) |

---

# Questions for Future Me ❓ _(for Tony)_

---

# Confidence Rating 📊 _(for Tony — rate 1–5)_

---

# Overall Sprint Reflection _(for Tony)_

### What am I most pleased with?

### What was the biggest lesson?

### What challenged me the most?

### What am I looking forward to building next?

---

# Summary

**Sprint Outcome:** ☑ Successful ☐ Partially Successful ☐ Needs Follow-up

**Stories Completed:**

- ADR-103 The MADBOOTS brand identity (the gate)
- US-348 The display swap + tagline (`brand.py` name/tagline/page_config; ~19 surfaces; `USER_AGENT`/CLI `prog`)
- US-349 The MB badge favicon on every page + the two-tone CSS wordmark (Home · gate · card band)
- US-350 The not-affiliated disclaimer + the live identity-doc rebrand

**Stories Carried Forward:**

- None. (The illustration hero · a vector/designer redraw · a dark reskin · the repo/domain changeover are recorded
  follow-ups / a bundled backlog item.)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
