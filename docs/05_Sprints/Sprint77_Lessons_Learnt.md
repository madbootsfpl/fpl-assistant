# Lessons Learned

**Sprint:** Sprint 077 — Team-scoped player multiselect

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Make the filter's **Player** multiselect usable: scope its options to the selected team(s)/position(s)
instead of listing all ~570 names — from one edit to the shared filter.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Making a dependent widget (Player options depend on Team/Position) work with Streamlit's top-to-bottom
  rerun model — no callbacks needed.
- De-risking the one tricky case (a stale selection when options shrink) with a prototype at planning.

### New Skills Acquired

- Streamlit **tolerates** a `session_state` multiselect value that's no longer an option (it drops it, no
  exception) — but an explicit **prune** makes the behaviour predictable (no lingering/resurrecting pick).

---

# What Went Well ✅

- **One edit, three pages** — scoping the Player options in the shared `filter_controls` reached Players,
  Player Stats and Trending at once (the shared-component payoff again).
- **Prototype-first** — a throwaway AppTest at planning proved the shrink case is safe, so the build had no
  surprises.
- **Provably scoped** — a test asserts a team narrows the options to that team's players; the smoke showed
  555 → 28 → 15.
- **Zero logic change** — `apply` (the AND predicate) is untouched; scoping only limits *what you can pick*.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| A picked player could fall out of scope on a team change | options depend on the team selection | Streamlit drops it (no crash); we also **prune** the stored value for predictability |
| Where to compute the scope | the Player widget renders after Team/Position | Read `team_sel`/`pos_sel` (already rendered) and recompute the names each run |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Dependent widgets | A later widget can depend on an earlier one's value directly — Streamlit's rerun makes it reactive |
| Stale selections | `session_state` values not in `options` are dropped, not fatal — prune anyway for predictability |
| Shared-component leverage | Scoping in `filter_controls` fixed all three consumers with one change |

---

# Development Lessons 💻

- Prototype the one risky interaction before building — it turned a "will this crash?" into a known-safe.
- Keep the pure logic (`apply`) untouched; make the change purely about what the widget offers.

---

# AI Collaboration Lessons 🤖

- The owner's one-liner ("team-scoped player multiselect") was a precise, small ask that mapped to a single
  shared-filter edit.

### Notes _(for Tony)_

---

# Decisions Made 📋

_No new ADR — refines **ADR-064** (the shared player filter): the Player options are scoped by the selected
team ∧ position._

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Open items: pronoun-aware chat, a team-level squad-fixtures view, and — post-GW1 (2026-08-21) — the Data
  Hardening flip + calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep prototyping the one risky UI interaction at planning; keep investing in shared components.

---

# Key Commands Learned

```text
python -m pytest tests/test_web_streamlit.py -k "player_multiselect or filter" -q   # the scoping + filter tests
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Dependent widget | A widget whose options/value depend on another widget rendered before it |
| Scoped options | A dropdown's choices narrowed by the current selection (here: team ∧ position) |
| Pruning a selection | Dropping stored values that are no longer valid options, for predictable state |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-064 | The shared player filter this refines |
| `src/web_streamlit/filters.py` | `filter_controls` — now with team/position-scoped Player options |

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

- US-213 Team-scoped player multiselect — the Player options are scoped by the selected team ∧ position in
  the shared filter (Players · Player Stats · Trending)

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
