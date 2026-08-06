# Lessons Learned

**Sprint:** Sprint 073 — Rich filters on Players & Player Stats (+ a useful graph)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Add one shared **Team · Position · Player** filter (AND-combinable) to both **Player Stats** and
**Players**, and replace the Players price-vs-points scatter (which "wasn't adding value") with a
filter-responsive **top-15 bar** — all edge-only, reusing the analytics.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Building one small reusable helper (`filters.py`) and applying it across pages.
- Keeping a pure predicate (`apply`) separate from the Streamlit render (`filter_controls`) so the logic
  is unit-testable.
- Leaning on AppTest to prove real wiring (a chosen team actually narrows the boards).

### New Skills Acquired

- **Altair with `alt.Data(values=…)`** (a non-DataFrame source) needs an **explicit encoding type on every
  field** — including tooltips (`alt.Tooltip("Player:N")`), or `to_dict()` raises.
- A rank-ordered horizontal bar = `y=alt.Y("…:N", sort="-x")` — `st.bar_chart` doesn't guarantee value order.
- Prefer `width="stretch"` over the deprecated `use_container_width` for new chart calls.

---

# What Went Well ✅

- **Reuse** — one `filter_controls`/`apply` served two pages; each story was ~half a session and the UX is
  consistent.
- **Pure + testable** — `apply` (AND across non-empty dims, tolerant of Row **and** dict rows) took thorough
  unit tests; the AppTests confirmed the pages narrow.
- **The graph now earns its place** — a top-15 bar that responds to the filter, instead of a static cloud.
- **AppTest caught the Altair type gotcha** before it hit the live app.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Altair chart raised on render | a bare tooltip field with `alt.Data` has no inferable type | give every field an explicit type (`alt.Tooltip("Player:N")`) |
| Players filter tests broke | the multiselect order changed (now Team `[0]`, Position `[1]`, Player `[2]`) | update the AppTest indices |
| `st.bar_chart` wouldn't rank the bars | it doesn't guarantee value order | Altair `mark_bar` with `y` `sort="-x"` |
| A row could be Row or dict | Players = `sqlite3.Row`, stats = dict | a tolerant `_get` in the filter |
| A deprecation warning on the chart | `use_container_width` is being retired | `width="stretch"` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Filter = controls + predicate | Split the render (`filter_controls`) from the pure `apply` so the logic is testable and reusable |
| AND semantics | "team **and** position" = keep rows matching every non-empty dimension; empty = any |
| Altair typing | `alt.Data(values=…)` needs explicit `:Q`/`:N` on **every** encoding, tooltips included |
| Ranked bars | `sort="-x"` on the `y` channel orders bars by value; `st.bar_chart` won't |
| Widget indices are positional | Reordering controls shifts AppTest indices — update them together |

---

# Development Lessons 💻

- Build the shared helper first, then let each page reuse it — small, consistent stories.
- Unit-test the pure predicate exhaustively; AppTest the wiring — both caught something this sprint.
- Watch framework deprecations on new code (`width="stretch"`).

---

# AI Collaboration Lessons 🤖

- The owner's steer — **replace** the scatter with a **top-15 bar by the sort metric** — turned a vague
  "the graph isn't adding value" into a concrete, buildable deliverable.

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-064 | **Shared player filter** — one `web_streamlit/filters.py` (`filter_controls` + `apply`): Team · Position · Player multiselects (+ optional max-price), **AND**-combinable, Row/dict-tolerant; applied to Player Stats (all tabs) + Players; the Players scatter → a filter-responsive **top-15 bar** (Altair, rank-ordered) by the sort metric; no analytics change, no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- A **team-scoped player** multiselect (only players from the chosen teams) if the ~570-name list feels
  unwieldy. Open items: pronoun-aware chat, a team-level squad-fixtures view, the tech-debt sweep (PuLP 4.0
  + shared squad renderer), and — post-GW1 — the Data Hardening flip + calibration and the crowd/form-vs-xP
  backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep splitting render from pure logic; keep AppTest on the wiring — it caught the Altair type bug.

---

# Key Commands Learned

```text
python -m pytest tests/test_filters.py -q      # the pure `apply` predicate (AND / Row tolerance)
python -m src.web_streamlit                     # Players & Player Stats now share the Team/Position/Player filter
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| AND filter | Keep rows matching every non-empty dimension (team ∧ position ∧ player); empty = any |
| `alt.Data(values=…)` | An inline (non-DataFrame) Altair data source — needs explicit encoding types |
| Ranked bar | A horizontal bar ordered by value (`y` `sort="-x"`) |
| Filter-responsive chart | A graph computed from the filtered set, so it updates as the filter changes |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-064 | The shared-filter design + the scatter→bar decision |
| `src/web_streamlit/filters.py` | `filter_controls` + `apply` (the reusable filter) |
| `pages/1_Players.py` | The top-15 Altair bar (explicit encoding types, `sort="-x"`) |

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

- US-206 Shared player filter (`filters.py`) + the Player Stats filter (Team · Position · Player, AND)
- US-207 Players filter (team + player added) + the scatter → a filter-responsive top-15 bar

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
