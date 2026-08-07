# Lessons Learned

**Sprint:** Sprint 085 — Availability flags in the player tables

**Dates:** 2026-08-07

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Surface injury / doubt / suspension flags in the web player tables (the Players Pool + the four stat boards)
the way the squad/captain views already warn — so *"is this player fit?"* is answerable at a glance, without
switching to the News tab.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Adding a cross-table display convention **without touching the analytics** — a shared helper + a view-side
  lookup.
- Extending a shared renderer (`_board`) with one optional parameter so every caller inherits the feature
  consistently.

### New Skills Acquired

- When a downstream layer has dropped a field (the trimmed stat dicts lack `status`), you can **rejoin from
  the full list the view already holds** instead of widening the analytics return shape.
- A **glance-able emoji column** needs a legend + a header tooltip to be self-explanatory — and its
  vocabulary must not collide with other emoji signals in the same table (crowd flags, rating circles).

---

# What Went Well ✅

- **Reused ingested data** (`status`/`chance`, ADR-023) — no new fetch, no analytics change; a pure display
  helper (`availability_flag`) beside `crowd_flags`.
- **One refactor, four boards** — `_board(flag=…)` inserts the Fit column + tooltip + legend in a single
  place; xG flagged its raw rows directly, the three trimmed boards via a `(web_name, team)` lookup.
- **Guarded the vocabulary** — a test asserts the availability emojis don't overlap the crowd/rating emojis.
- 613 → 617 tests; ruff + CI-parity green; seed.db kept clean.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| The stat boards had no `status` to flag | `over_under`/`defcon`/`defensive_solidity` return trimmed dicts | Rejoin from the full `players` list each render func already receives (`_fit_lookup`) — no analytics change |
| Risk of the flag blurring with other signals | crowd flags + rating circles already use emoji | Chose distinct emojis (🚑🚫⛔❓ vs 🟢🟡🟠🔴 / 🟦💎🔥) + a test guarding it |
| Emoji-only is cryptic | no per-cell hover in `st.dataframe` (ADR-072) | A legend caption + a header tooltip + the News tab for detail |
| Keeping four boards consistent | four separate render funcs | One `_board(flag=…)` path adds the column/tooltip/legend uniformly |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Rejoin, don't widen | A view can recover a dropped field from a list it already has, sparing an analytics change |
| Extend the shared renderer | An optional `flag=` on `_board` gives every board the feature identically |
| Distinct emoji vocab | Availability, crowd, and rating signals must stay visually separable in one row |
| Display helper placement | `availability_flag` sits with `crowd_flags` (the display-flags home), keeping analytics pure |

---

# Development Lessons 💻

- Prefer the smallest change that reaches the goal: a display helper + a view lookup beat editing analytics
  return shapes and their tests.
- Put a new signal where its siblings live (flags with flags) so the codebase stays legible.
- A glance feature needs its legend — ship the explanation with the emoji.

---

# AI Collaboration Lessons 🤖

- The owner's pick (availability flags) was a clean, self-contained backlog item that fit preseason (60
  flagged players today) and needed no gated data — a good "quiet week" choice that still adds real value.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-074 | **Availability flags in the player tables** — `availability_flag(player)` (🚑/🚫/⛔/❓, blank = available) in `analytics/crowd.py`; a compact **Fit** column + a shared legend on the Pool and the four stat boards; the trimmed boards look the flag up from the full `players` list (no analytics change); display-only, distinct from the rating circles; no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- **Reseed the deploy** (`python app.py reseed` → commit → push) so testers see Sprints 081–085 on fresh
  data — the Cloud seed is still the 570-player snapshot.
- Possible: the **Fit** flag on the CLI ranking views (`table`/`xg`) too; a chance% on the doubtful (❓) flag.
- Post-**GW1 (2026-08-21)**: the Data Hardening flip + xP calibration.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the "reuse ingested data + a view-side lookup" pattern for surfacing existing fields in new places.

---

# Key Commands Learned

```text
python -m src.web_streamlit      # Players → the Pool + every stat board show a Fit column (🚑/🚫/⛔/❓)
python -m pytest tests/test_crowd.py -q -k availability   # the availability_flag unit tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Availability / Fit flag | A one-emoji injury/doubt/suspension marker in the player tables |
| `_fit_lookup` | A `(web_name, team) → flag` map built from the full players list for the trimmed boards |
| Distinct emoji vocab | Keeping availability, crowd, and rating emojis non-overlapping so a row reads cleanly |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-074 | The availability-flag decision + the "rejoin, don't widen" rationale |
| `src/analytics/crowd.py` | `availability_flag` + `AVAILABILITY_LEGEND` (beside `crowd_flags`) |
| `src/web_streamlit/views/players.py` | `_board(flag=…)` + `_fit_lookup` |

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

- US-228 Availability flag helper + Pool — `availability_flag` (🚑/🚫/⛔/❓) + a Fit column + legend on the
  Players Pool (ADR-074)
- US-229 Fit column on the four stat boards (over/under · DefCon · clean sheets · xG) via `_board(flag=…)`

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
