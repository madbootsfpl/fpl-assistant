# Lessons Learned

**Sprint:** Sprint 072 — Player Stats page + pagination (Players & Trending)

**Dates:** 2026-08-06

**Version:** 1.0

> Factual sections are filled in below. Fields marked _(for Tony)_ are personal
> reflections left blank on purpose — they only mean something in your own words.

---

# Sprint Goal

Close three tester gaps in the web: bring the CLI's stat views (over/under · DefCon · clean sheets · xG)
into a **Player Stats** page, let **Players** page through *all* players (+ sort by team/position), and let
**Trending's** four boards page past 30 — all by reusing the existing analytics and one shared paginator.

---

# Knowledge Compounded 📈

## Skills Strengthened

- Surfacing existing analytics through a new web page without touching the engine.
- Building one small reusable helper (`paginate`) and applying it across pages.
- Renaming/reordering Streamlit multipage pages and keeping the AppTest refs in step.

### New Skills Acquired

- A **stateless paginator** (a page selectbox of range labels) is simpler than a "Next" button (which needs
  session state) and is trivially unit-testable via a pure `page_labels`.
- Streamlit **tab bodies all execute** on every run, so a per-tab paginator needs a **unique `key`** to keep
  page state from colliding.

---

# What Went Well ✅

- **Real-data-first** confirmed the stat commands are already rich (season-to-date = last season's carryover
  preseason), so the Player Stats page was useful immediately — no GW1 gating, an honest caption instead.
- **Reuse, not rebuild** — the page calls the same `over_under`/`defcon_reliability`/`defensive_solidity`
  the CLI does; one `paginate` helper serves three pages.
- **Guardrails paid off** — the test suite caught a `sqlite3.Row`-vs-dict crash on the Players sort; **ruff**
  caught a leftover `count` (F821) in Trending after the slider was removed.

---

# Challenges Encountered ⚠️

| Issue | Cause | Resolution |
|--------|-------|------------|
| Team/position sort crashed the Players table | that path returned raw `sqlite3.Row`s (no `.get`, no computed `value`) | Normalise through `rank_players` first, then re-sort the dicts |
| Trending crashed after removing the slider | the buzz board still referenced `count` | ruff F821 caught it → `limit=len(players)` (show all mentioned) |
| Player Stats rows have no player `id` | the stat analytics return web_name/team, not `id` | Use **team badges** (by `team`), not per-player photos — no analytics change |
| Placing Player Stats at 2 shifts every later page | sidebar order is filename-coupled | `git mv` renumber (9 pages) + a scripted remap of the AppTest refs; a test run catches misses |
| Per-tab page state could collide | tab bodies all execute each run | Each caller passes a unique `paginate(key=…)` |

---

# Technical Lessons 🧠

| Topic | What I Learned |
|--------|----------------|
| Reuse the analytics | A stat "page" is just a renderer over the CLI's functions — zero engine change, zero drift |
| Stateless pagination | A page selectbox (range labels) beats a Next button for simplicity + testability |
| Unique keys in tabs | Streamlit executes every tab body; per-tab widgets need distinct keys |
| Row vs dict | `rank_players` returns dicts (with `value`); raw `get_players()` rows are `sqlite3.Row` (no `.get`) — normalise before display |
| ruff as a safety net | Removing a widget can orphan a variable; the linter flags the dangling reference |

---

# Development Lessons 💻

- Probe the source (the CLI commands) before building UI — it told me the stats were season-to-date and
  useful now.
- Build the shared helper first, then let each story reuse it — small, consistent stories.
- Trust the test + lint gates on refactors (renumber, slider removal) — they caught both regressions.

---

# AI Collaboration Lessons 🤖

- The owner's steer — **all four stat tabs**, **Player Stats at position 2** — set a concrete target; the
  real-data probe then de-risked it (the stats already populate).

### Notes _(for Tony)_

---

# Decisions Made 📋

| ADR | Decision | Status |
|------|----------|--------|
| ADR-063 | **Player Stats page + pagination** — a new **Player Stats** page (Over/under · DefCon · Clean sheets · xG) reusing the stat analytics (no engine change; season-to-date, team badges), placed at sidebar **position 2** (renumber); a shared **`paginate`** helper so **Players** (page all + sort team/position) and **Trending** (four boards page past 30) see everything; no server writes | Accepted |

---

# Mistakes Made (and Why They're Valuable) 😊 _(for Tony)_

---

# Things That Surprised Me 💡 _(for Tony)_

---

# Improvements for Next Sprint 🚀

## Project Improvements

- Sidebar order is filename-coupled, so every insert cascades — if the page list keeps growing, the
  `st.navigation`/`st.Page` API would let labels + order be declared in one place (a future refactor).
  Open items: pronoun-aware chat, a team-level squad-fixtures view, the tech-debt sweep (PuLP 4.0 + shared
  squad renderer), and — post-GW1 — the Data Hardening flip + calibration and the crowd/form-vs-xP backtest.

## Personal Improvements _(for Tony)_

## Workflow Improvements

- Keep the real-data gate before building; reuse the analytics behind new pages; lean on ruff + AppTest
  when refactoring (they caught both bugs this sprint).

---

# Key Commands Learned

```text
python -m src.web_streamlit        # Player Stats is now the 2nd sidebar page; Players/Trending page through all
python -m pytest tests/test_paginate.py -q   # the pure page_labels helper
```

---

# New Terminology 📖

| Term | Meaning |
|------|---------|
| Paginator | The shared web control (a page selectbox + "Showing X–Y of N") that pages through a long list |
| Season-to-date stats | Cumulative-season fields (xG/DefCon/minutes) — preseason these are last season's carryover |
| Stateless pagination | Paging via a selectbox of range labels (no session-state cursor) |
| Filename-coupled order | Streamlit's sidebar order/labels come from the page filename, so inserts cascade |

---

# Resources Worth Keeping 🔗

| Resource | Why It Was Useful |
|----------|-------------------|
| ADR-063 | The Player Stats + pagination design (and the badges-not-photos / renumber notes) |
| `src/web_streamlit/paginate.py` | The shared paginator (`page_labels` + `paginate`) |
| `pages/2_Player_Stats.py` | The stat views (reusing `over_under`/`defcon_reliability`/`defensive_solidity`/xGI) |

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

- US-203 Player Stats page — Over/under · DefCon · Clean sheets · xG (reused analytics; paginated; at
  sidebar position 2) + the shared `paginate` helper
- US-204 Players — page through all + sort by team / position
- US-205 Trending — the four boards page past 30

**Stories Carried Forward:**

- None.

**Overall Satisfaction (1–10):** ___ _(for Tony)_

**Time Invested:** ___ _(for Tony)_

**Version After Sprint:** v0.0.1

---

> **Remember:** The purpose of this document is not to record what the software did. It is
> to record what *you learned* while building it.
