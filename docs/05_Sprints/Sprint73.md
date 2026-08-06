# Sprint 073: Rich filters on Players & Player Stats (+ a useful graph)

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (edge/UI — no analytics change)
**Carried Over:** none

> **Direction (owner, tester feedback):**
> 1. **Player Stats tab** — needs a **filter**: by player(s) / team / position, or any combination
>    (multi-select on all three).
> 2. **Players tab** — the same rich filter (multi player/team/position); and the **top graph isn't adding
>    value** — replace it (owner's call: a **top-15 bar** of the filtered players by the sort metric).

---

### 🔎 Verified at planning (real data)

- **20 teams**; both surfaces have the fields a filter needs — Players rows carry `team`/`position`/
  `web_name`/`price`; the stat-analytic rows carry `team`/`position`/`web_name` (no `price`, so **max-price
  is a Players-only control**). So one shared filter works across both.
- **AND semantics** — a player passes if it matches **every non-empty** dimension (teams ∧ positions ∧
  players); an empty dimension is "any". Intuitive and lets combinations narrow.
- **Altair is bundled** with Streamlit — a horizontal bar with `sort="-x"` gives a properly **rank-ordered**
  top-15 (st.bar_chart doesn't guarantee value order); web-only, no new dependency.

---

### 🎯 Sprint Goal

**Objective:** a single reusable **player filter** (multi team / position / player, AND-combinable) on both
**Player Stats** and **Players**, and swap the Players scatter for a filter-responsive **top-15 bar** — all
edge-only, no analytics change.

#### Success Criteria
- [x] Approach agreed (**ADR-064**) — a shared `filter_controls` / `apply` (Team · Position · Player
      multiselects + optional max-price; AND); applied to Player Stats (all tabs) and Players; the Players
      scatter → a top-15 bar (Altair, rank-ordered) of the **filtered** set by the sort metric
- [x] **US-206 (Player Stats filter)** — the shared filter above the four tabs; each tab filters its
      analytic rows (by team/position/player) before pagination; the "season-to-date" caption stays. The
      shared `web_streamlit/filters.py` helper built here
- [x] **US-207 (Players filter + graph)** — adopt the shared filter (adds **team** + **player** to the
      existing position; keeps **max-price**); **removed the price-vs-points scatter**, added a **top-15
      horizontal bar** of the filtered players by the current sort metric (points / value); the table +
      pagination + team/position sort stay
- [x] **No analytics change** — the web writes nothing server-side (guardrail holds); existing tests stay
      green — **578** (+7)
- [ ] Docs: ADR-064 + index ✅; Architecture, README (web section), PROJECT_STATUS, Feedback_Log (resolved)
      _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-206 | **Player Stats filter** — a shared Team / Position / Player multiselect filter (AND) above the four tabs, applied to each analytic before pagination; builds `web_streamlit/filters.py`. ADR-064. | High | ✅ Done | ~½ session |
| US-207 | **Players filter + graph** — adopt the shared filter (team + player added, max-price kept); replace the scatter with a top-15 bar of the filtered set by the sort metric. ADR-064. | High | ✅ Done | ~½ session |

---

### 🧭 Design sketch (to settle in ADR-064)

**Shared filter (`web_streamlit/filters.py`, built in US-206).**
```
filter_controls(players, *, key, with_price=False) -> dict     # renders the multiselects; returns `sel`
apply(rows, sel) -> list                                       # keep rows matching every non-empty dim (AND)
```
`filter_controls` renders **Team** (options = distinct `team` short names), **Position** (GK/DEF/MID/FWD),
**Player** (options = `web_name`s) multiselects — each keyed off `key` so Players & Player Stats don't
collide — plus an optional **Max price** slider (`with_price`). `apply` keeps a row when
`(not teams or r["team"] in teams) and (not positions or r["position"] in positions) and (not players or
r["web_name"] in players)` and (price present ⇒ `r["price"] <= max_price`). Empty dim = "any".

**Player Stats (US-206).** `sel = filter_controls(players, key="stats")` once above `st.tabs(...)`; each tab
does `apply(analytic_rows, sel)` before `paginate`. The season-to-date caption stays.

**Players (US-207).** `sel = filter_controls(rows, key="players", with_price=True)` (replaces the position
multiselect + max-price slider); `filtered = apply(rows, sel)`; sort (points/value/team/position as today);
**drop the scatter**; render a **top-15 bar** — `altair` `mark_bar()` with `y=Player (sort="-x")`,
`x=<metric>` over the top 15 filtered by the sort metric (points → Pts, value → Val/£m; else Pts) — then the
paginated table. The bar updates live with the filter.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — AppTest: Player Stats renders the filter + narrows a tab when a team is chosen; Players
   filters by team/player and shows a (vega) bar chart, not the old scatter; the paginated table + sort
   still work; the web-writes-nothing guardrail holds. Existing **571** stay green.
2. **Manual smoke** — on the live app: on Player Stats pick a team + position → every tab narrows; on
   Players pick two teams + a position → the table + the top-15 bar both narrow.
3. **Docs updated** — ADR-064 + index, Architecture, README, PROJECT_STATUS, Feedback_Log (resolved).

---

### 📝 Session Progress Log

- **US-206 ✅ (gate + build)** — Recorded **ADR-064** (+ index; covers US-207). New shared
  `web_streamlit/filters.py`: `filter_controls(players, *, key, with_price=False)` renders **Team ·
  Position · Player** multiselects (+ optional Max-price), namespaced by `key`; `apply(rows, sel)` keeps
  rows matching **every non-empty** dimension (AND), tolerant of `sqlite3.Row` **and** dict rows (a `_get`
  helper) and no-op on price when a row has none. Wired into `pages/2_Player_Stats.py`: `filter_controls(
  players, key="stats")` once above the four tabs; each tab runs `apply(analytic_rows, sel)` before
  paginating. Tests (+6 → **577**): `apply` (empty=all · single dim · **AND** combine · player dim + price ·
  Row tolerance) + an AppTest (Team=ARS narrows every board to ARS-only). **Smoke (real DB):** 3 filter
  multiselects; over/under 50 → **6** after ARS ∧ DEF (teams={ARS}, pos={DEF}), no exception. No analytics
  change. ruff clean. _US-207 (Players filter + the scatter→top-15-bar) next._

- **US-207 ✅ (build)** — Players adopts the shared filter (`filter_controls(rows, key="players",
  with_price=True)` — **Team + Player added** to Position, max-price kept) + a separate sort selectbox;
  `filtered = apply(rows, sel)`. The **price-vs-points scatter is gone**, replaced by a filter-responsive
  **top-15 horizontal bar** (Altair `mark_bar`, `y=Player sort="-x"`) of the strongest filtered players by
  the sort metric (points → Pts, value → Val/£m); the paginated table + team/position sort stay. Two test
  fixes: the filter multiselect indices shifted (Position is now `[1]`, Team `[0]`), and the scatter test →
  a top-15-bar assertion; +1 test (filter by team narrows the table). A tooltip bug (a bare `Player` field
  with `alt.Data` needs an explicit `:N` type) was **caught by the AppTest** and fixed; used the current
  `width="stretch"` (not the deprecated `use_container_width`). **578** green, ruff clean. **Smoke (real
  DB):** table 50 → **6** after (ARS|LIV) ∧ FWD, the bar present + responsive. No analytics change.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — both tester items shipped: a rich **Team · Position · Player** filter
(AND-combinable) on **Player Stats** *and* **Players**, and the dead price-vs-points scatter replaced by a
filter-responsive **top-15 bar**. One shared `filters.py` serves both pages; **no analytics change**.

**What went well** — building the filter **once** (`filter_controls` + `apply`) and reusing it kept both
stories to ~half a session and the UX consistent. The pure `apply` (AND across non-empty dims, Row/dict
tolerant) was easy to unit-test exhaustively, and the AppTests proved the wiring narrows real boards. The
**AppTest caught a real Altair gotcha** — a bare tooltip field with `alt.Data` needs an explicit `:N` type —
before it could reach the live app.

**What to watch / lessons** — the **player multiselect lists ~570 names** (searchable); a team-scoped
variant (only players from the chosen teams) is a noted follow-up if it feels unwieldy. `alt.Data(values=…)`
(non-DataFrame) needs **explicit encoding types** on *every* field, tooltips included. And prefer the
current `width="stretch"` over the deprecated `use_container_width` for new chart calls.

**Lessons captured:** `docs/05_Sprints/Sprint73_Lessons_Learnt.md`.
