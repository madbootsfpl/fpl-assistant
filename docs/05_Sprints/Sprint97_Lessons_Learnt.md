# Lessons Learned

**Sprint:** Sprint 097 — Set-piece attributes on My Squad (parity with Trends)

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Every player in **My Squad** shows their **set-piece attributes** (⚽ pens · 🚩 corners · 🎯 FK) — a line on
the pitch card and a **"Set"** column in the squad tables, exactly parallel to how **Trends** is shown.
Display-only; reuses `set_piece_flags`.

---

# Knowledge Compounded 📈

## Skills Strengthened

- **Display-only features over existing data** — reuse a pure flag helper (`set_piece_flags`) as a caption /
  column; no analytics, no ingest, tiny blast radius.
- **Consistency by mirroring** — when a tester says "like it does for X", find every place X is shown and add
  the parallel there, so the new thing can't look half-finished.

### New Skills Acquired

- The Squads tab shows "Trends" in **two shapes** — a **pitch-card caption** (`pitch.py::_card`) and a
  **table column** through the shared `render_player_table` — so "like Trends" meant touching both, not one.
- A shared legend belongs next to its sibling: moving `SET_PIECE_LEGEND` into `analytics/crowd.py` beside
  `AVAILABILITY_LEGEND` removed a duplicate and let both the Players page and the Squads tables import it.
- `render_player_table` was help-less; adding an optional `help=` (threaded to the existing
  `column_config(..., help=…)`) gave text columns like "Set" a tooltip with no caller churn.

---

# What Went Well ✅

- **Pure display** — `set_piece_flags` + the ingested order fields already existed (Sprint 095), so this was
  one caption line + one column per table; the analytics/xP never moved.
- **Followed the tester's frame** — mapped "like Trends" onto the exact two surfaces Trends uses.
- **A tidy refactor fell out** — the shared legend + `help=` on the table renderer.
- **Deterministic test** — the pitch test asserts the flag **count equals** the squad's owned takers, so it
  can't pass on an empty render.
- 658 → 659 tests (+2 assertions on existing); ruff + CI-parity green.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| "like Trends" is ambiguous | Trends shows in a card caption *and* a table column | Add the set-piece equivalent to both surfaces |
| A weak "≥1" pitch test | the demo squad's takers aren't fixed in the test | Assert the caption count *equals* the selected squad's owned takers |
| Transfer "In set" looked empty | preseason there are no positive-gain swaps | Drive a bank in the test so the swap table (with "In set") renders |
| Duplicate legend | `SET_PIECE_LEGEND` lived only in `views/players.py` | Move it to `analytics/crowd.py` + export; both views import it |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Two Trends surfaces | Pitch caption + table column — parity means both |
| Shared legend home | Next to `AVAILABILITY_LEGEND` in `crowd.py`, imported by all callers |
| Optional `help=` | A tiny renderer param gives text columns tooltips without caller churn |
| Count-equals tests | Assert the exact count, not "≥1", so an empty render fails |

---

# Development Lessons 💻

- Reuse the existing pure helper as a view element; don't add logic for a display ask.
- When adding a parallel column/line, put the shared constant where its sibling lives — it prevents drift.
- Make display tests deterministic against the rendered data (count-equals), not tolerant.

---

# AI Collaboration Lessons 🤖

- A one-line tester request ("show set-piece attributes like Trends") decomposed cleanly into: the pitch card
  + the four tables that carry Trends. Naming the surfaces up front (in the plan) kept the scope honest and
  the result consistent.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — display-only, extends **ADR-081** (set-piece takers) exactly as `crowd_flags` is displayed._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **AI Chat Assistant** (owner intake) — still needs a grounded-vs-free-form design/ADR + a willing LLM.
- **Elite Manager Comparison** — GW1-gated (per-manager picks unlock 2026-08-21).
- **Chip Strategy — the gated half:** DGW/BGW detection (in-season) + mini-league position (leagues API, GW1).
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration; the Price Change Predictor lights up.
- Backlog still open: persisted chat context; season countdown / deadline banner; server-side squad persistence.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep decomposing a tester ask onto the *exact* existing surfaces — it's the cheapest path to a consistent UI.

---

# Key Commands Learned

```text
python -m src.web_streamlit   # Squads → My Squad: each card shows ⚽/🚩/🎯 under Trends;
                              # Build/Health/Captain tables show a Set column; Transfer shows In set
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Set-piece attributes | The first-choice pen/corner/FK duty flags (⚽/🚩/🎯) for a player |
| Trends parity | Showing a new signal wherever the Trends signal already appears |
| Display-only lens | A view over ingested fields that never changes the grounded xP |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-081 | The set-piece ingest + `set_piece_flags` this sprint surfaces |
| `src/web_streamlit/pitch.py` (`_card`) | The pitch-card caption (Trends + set pieces) |
| `src/web_streamlit/views/squads.py` | The squad tables' "Set" / "In set" columns |

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

- US-253 Set-piece line on the My Squad pitch cards — a `set_piece_flags` caption, parallel to Trends (ADR-081)
- US-254 "Set" column on the squad tables — Build/Health/Captain + "In set" on Transfer; shared legend + `help=`

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
