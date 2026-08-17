# Lessons Learned

**Sprint:** Sprint 162 — UX Sprint C (naming & onboarding)

**Dates:** 2026-08-17

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

The onboarding/consistency slice of the UX audit: a single clear primary action on Home (US-398); the Ask page
reading like a chat rather than a terminal (US-399); and News speaking the same availability vocabulary as every
other surface (US-400). Display/copy — with one contained engine-shared change (`render_ask` markdown mode).
*(The audit's "sidebar icon labels" item was dropped — the owner reviewed the sidebar and said "leave as is".)*

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Verify the assumption before building.** The audit's "render Ask as markdown" looked like a one-liner; reading
  `render_ask` revealed monospace-aligned plan tables (shared with the CLI) that plain markdown would break. The
  five-minute check changed the whole approach.
- **Opt-in mode over a fork.** `render_ask(..., markdown=False)` keeps the CLI/FastAPI byte-identical while the web
  opts in — one renderer, no divergence.

## New Skills Acquired

- **Fence the aligned part, prose the rest.** The clean way to make a mixed prose+table answer read as chat *and*
  stay aligned: wrap only the table in a ``` fence; markdown handles the rest. Reusable wherever CLI-shaped text
  meets a rich web surface.

---

# What Went Well ✅

- Small, coherent batch landed green (+2 tests → 1005, ruff clean); the Ask change is genuinely nicer without
  risking the CLI.
- Home now has an obvious first action — the thing a first-time signed-in user was missing.

# What Was Tricky ⚠️

- The `my-team → my squad` rename rippled into the Help page (which quotes the Ask example) and its test — a
  reminder to grep a renamed string everywhere it's echoed, not just at its source.
- Getting the Ask tests right meant confirming (by probe) that a fenced block inside `st.markdown` surfaces as one
  `at.markdown` element, not `at.code` — then re-pointing the assertions.

# Process / Meta 🛠️ _(for Tony)_

# Personal Reflections 💭 _(for Tony)_
