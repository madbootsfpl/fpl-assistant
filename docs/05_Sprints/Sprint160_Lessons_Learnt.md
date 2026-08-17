# Lessons Learned

**Sprint:** Sprint 160 — UX Sprint A (brand & copy consistency polish)

**Dates:** 2026-08-17

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

The first slice of the app-wide UX/style review (`docs/00_Project/UX_Style_Audit.md`), scoped from the owner's
smoke-test batch: brand-purple Home callouts + icon-led bullets + de-jargon; **rename "Ask Maddie" → "Maddie
Explains"** (the "Ask" verb implied a chatbot); vibrant Fixtures FDR colours + the difficulty digit; consistent
Help-section icons; and the cheap audit "honesty" fixes (dead caption, stale Feedback picker, terminal-command
empty-states). Display/copy only — no ADR.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Repo-wide rename discipline.** A page rename ripples to the filename (sidebar label), title/config/boot, the
  Home teaser `page_link`, docs and the tests that name the page — plus a call on which references are *live*
  (update) vs *historical record* (leave). Swept it cleanly in one pass.
- **Self-contained brand HTML for a Streamlit gap.** `st.info` can't be recoloured, so the purple callouts are a
  small inline-CSS box — the same ADR-084 pattern used for the cards.

## New Skills Acquired

- **Contrast is a pair.** "More vibrant" only cleared accessibility because each FDR band carries its own text
  colour; vibrancy alone fails AA. This is exactly what a semantic `GOOD/WARN/BAD` token (+ `_FG`) should encode —
  a concrete input into Sprint B.
- **Bundle honesty fixes with visual work.** The dead pointer, stale picker and "run refresh" copy were near-free
  to fix alongside the owner's batch and each restored a bit of the "shows its working" trust.

---

# What Went Well ✅

- One cohesive, low-risk batch (13 files, display/copy) landed green (+3 tests → 1001, ruff clean).
- The audit turned a vague "do a UX pass" into a concrete, owner-triaged worklist; Sprint A cleared the cheapest,
  highest-trust slice.

# What Was Tricky ⚠️

- The page rename touched ~a dozen test references and a `git mv`; caught by the suite, swept in one go.
- Removing the dead caption orphaned the `cloud_store` import (ruff F401) — a reminder that deleting the last use of
  a symbol means pruning its import.

# Process / Meta 🛠️ _(for Tony)_

# Personal Reflections 💭 _(for Tony)_
