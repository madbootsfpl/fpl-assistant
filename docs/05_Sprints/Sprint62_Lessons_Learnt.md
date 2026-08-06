# Lessons Learned

**Sprint:** Sprint 062 — Two UI feature requests: a Fixtures ticker + a My Squad pitch view

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Ship two owner/tester-requested views (from reference screenshots): a **Fixtures ticker** (teams ×
gameweeks, colour-coded by difficulty, with a weeks selector) and a **My Squad pitch/formation** layout
(keeping the existing info) — robustly, over existing data, with no core/xP change.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Reproducing a screenshot's layout from data we already had (no new analytics/source).
- Keeping data-shaping in the pure core (unit-tested) and presentation/colour at the edge.
- Choosing robustness over pixel-fidelity when the trade-off favours maintainability.

### New Skills Acquired

- Colour-coding a grid with a **pandas Styler** rendered by `st.dataframe` (per-cell background from a
  parallel difficulty frame), combined with `column_config` for an image column.
- Building a "pitch" with native `st.columns`/`st.container` position rows (no custom HTML/CSS).

---

# What Went Well ✅

- **No new analytics needed** — `fixture_ticker` just reshaped `team_fdr`/`team_schedule`; the pitch reused
  `crowd_flags` + `team_schedule`. The screenshots mapped onto existing data.
- **Clean core/edge split** — the ticker's grid data is a pure, tested function; the colouring/layout is
  edge-only.
- **Robustness-first paid off** — the pitch is a native card-grid (themeable, headless-testable), not a
  fragile custom-CSS pitch; the owner's call kept it maintainable.
- **Both work now** — unlike the deferred trends intent, difficulty/opponents are live, so these deliver
  immediately.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Per-cell grid colours in Streamlit | `st.dataframe` doesn't colour cells directly | A pandas **Styler** (a same-shaped CSS frame keyed off a parallel difficulty frame) |
| A "pitch" look without heavy HTML/CSS | A literal shirt-on-green pitch is fragile in Streamlit | A native card-grid in position rows — approximates the layout, stays robust (owner's call) |
| My Squad tests assumed a dataframe | The pitch replaced the table | Narrowed the image-table test to the table tabs; added a pitch-layout test |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Screenshot → existing data | A requested view often needs reshaping, not new data — check the payload first |
| Styler for grids | `st.dataframe(df.style.apply(..., axis=None))` colours cells; pairs with `column_config` |
| Native pitch | Position rows of `st.container` cards capture the formation without custom CSS |
| Pure core, edge render | Grid *shape* is testable core; colour/layout is edge — keeps logic verifiable |

---

# Development Lessons 💻

- Look at the data before scoping a "new" view — much of it is reshaping.
- Prefer a robust approximation over a fragile pixel-match unless fidelity is the point.
- When a view changes shape (table → pitch), update the tests to the new reality rather than forcing the old.

---

# AI Collaboration Lessons 🤖

- The owner's reference images made the target unambiguous; viewing them up front set the exact scope.
- The "robustness first" call resolved the one real fork (card-grid vs custom-CSS pitch) cleanly.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — both stories are UI over the settled edge (reuse `team_fdr`/`team_schedule`/`crowd_flags`),
like Sprint 054/055._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **GW1 (~2026-08-21):** the deferred **trends `ask` intent (US-185)** + threshold calibration + **Data
  Hardening** (per-GW history/form). Meanwhile: triage **tester feedback** (Sprint 059 loop). Optional
  later: a full custom-CSS pitch if the exact FPL look is wanted (with the robustness trade-off).

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the core/edge split (pure data-shaping + edge render); keep matching requests to existing data.

---

# Key Commands Learned

```text
python -m pytest tests/test_fdr.py tests/test_web_streamlit.py -q   # ticker + pitch tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Fixture ticker | A teams × gameweeks grid, each cell an opponent + venue, colour-coded by difficulty |
| pandas Styler | A pandas object carrying per-cell CSS; `st.dataframe` renders its background colours |
| Formation card-grid | A native-Streamlit "pitch": position rows of player cards + a bench row |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| `src/analytics/fdr.py` (`fixture_ticker`) | The pure teams × GW grid builder |
| `src/web_streamlit/pitch.py` | The reusable formation card-grid renderer |
| The reference screenshots (local) | The exact layout targets for both views |

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

- US-186 Fixtures ticker grid + a 1–8 weeks selector (colour-coded difficulty)
- US-187 My Squad pitch / formation card-grid (keeps info + edit controls)

**Stories Carried Forward:**

- None new (GW1 markers: US-185 trends intent + calibration + Data Hardening)

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
