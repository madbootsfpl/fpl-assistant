# Sprint 072: Player Stats page + pagination (Players & Trending)

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/3 stories)
**Capacity:** ~1–2 sessions (edge/UI — the analytics are untouched)
**Carried Over:** none

> **Direction (owner, tester feedback — 3 items):**
> 1. **CLI stats parity** — bring **Overperf · DefCon · Cleansheet** (and the natural 4th, **xG**) into the
>    web as a **Player Stats** tab.
> 2. **Players tab** — you can only see 50; page through all players (1–50 → next 50) and **sort by team /
>    position** too.
> 3. **Trending tab** — the boards cap at 30; page through all (Most owned · transferred in · transferred
>    out · in form).

---

### 🔎 Verified at planning (real data)

- **The stat commands are rich NOW** — `overperf` (Semenyo 3200 mins, +38.1), `defcon` (DC/90 vs threshold),
  `cleansheet` (xGC/90), `xg` (xG/xA/xGI/xGC) all print full tables on the live DB. They read **season-to-
  date** fields — preseason that's **last season's carryover** (the bootstrap keeps prior aggregates until
  the new season overwrites them). So a stats page is **useful immediately** (a caption notes it's
  season-to-date); no GW1 gating.
- **All reuse existing analytics** — `over_under` / `defcon_reliability` / `defensive_solidity`, and xG =
  players sorted by `xgi` (the CLI's `cmd_xg`). **No analytics change.**
- **The caps are literal** — Players `slider("How many", 5, 50, 20)`; Trending `slider(5, 30, 15)`. Both are
  just display caps to replace with pagination.

---

### 🎯 Sprint Goal

**Objective:** full stat-view parity in the web + see-everything pagination — reusing the same analytics
(no engine change), consistent photos/badges, and one shared paginator.

#### Success Criteria
- [x] Approach agreed (**ADR-063**) — a **Player Stats** page (season-to-date, reuse the analytics) at
      sidebar **position 2**; a shared **paginate** helper; Players gains team/position sort + pagination;
      Trending's 4 boards paginate
- [x] **US-203 (Player Stats page)** — a new `pages/2_Player_Stats.py` with tabs **Over/under · DefCon ·
      Clean sheets · xG**, each an st.dataframe (team badge + the stat columns) paginated; a
      "season-to-date" caption. Placed at **2** (renumbered the rest); the shared `paginate` helper built here
- [x] **US-204 (Players — pagination + sort)** — replace the 50-cap with the paginator (page through all);
      add **team** and **position** to "Sort by" (the scatter still spans all matches)
- [x] **US-205 (Trending — pagination)** — the four crowd boards page through **all** rows (not just 30),
      via the shared paginator (per-board keys); the GW1 "lights up" note unchanged
- [x] **No analytics change** — the web writes nothing server-side (guardrail holds); existing tests stay
      green — **571** (+6)
- [ ] Docs: ADR-063 + index ✅; Architecture, README (web section), PROJECT_STATUS _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-203 | **Player Stats page** — a new page (tabs: Over/under · DefCon · Clean sheets · xG) reusing the stat analytics, paginated, at sidebar position 2 (renumber); + the shared `paginate` helper. ADR-063. | High | ✅ Done | ~1 session |
| US-204 | **Players — pagination + sort** — page through all players (per-page 50) + sort by team / position (on top of points / value). ADR-063. | High | ✅ Done | ~½ session |
| US-205 | **Trending — pagination** — the four boards (owned / in / out / form) page through all rows, via the shared paginator. ADR-063. | High | ✅ Done | ~½ session |

---

### 🧭 Design sketch (to settle in ADR-063)

**Shared paginator (`web_streamlit/paginate.py`, built in US-203).**
```
paginate(rows, *, key, per_page=50) -> list
```
When `len(rows) <= per_page`: a caption "N players", return all. Else: a **page selectbox** with range
labels ("1–50", "51–100", …, keyed) + a caption "Showing X–Y of N"; return `rows[start:end]`. A pure
`page_labels(total, per_page)` helper (for unit tests). Each caller passes a unique `key` (tab-safe).

**Player Stats (`2_Player_Stats.py`).** `st.tabs(["Over/under", "DefCon", "Clean sheets", "xG"])`. Each tab:
run the analytic (`over_under` / `defcon_reliability` / `defensive_solidity`; xG = `sorted(players, key=xgi)`),
render an st.dataframe with photo/badge + the CLI's columns (e.g. over/under: Mins · Actual · Exp · Diff),
`paginate`d. A caption: *"Season-to-date stats — preseason these are last season's totals; ≥900 mins."*
**Placed at sidebar position 2** → renumber: `2_Fixtures`→3, `3_Build_Squad`→4, `4_My_Squad`→5,
`5_Squad_Health`→6, `6_Transfer`→7, `7_Captain`→8, `8_Ask`→9, `9_News`→10, `10_Trending`→11 (via `git mv`);
update the AppTest refs + Home copy.

**Players (`1_Players.py`).** Drop the `How many` slider; `paginate(ranked, key="players", per_page=50)`.
Add `team` / `position` to the **Sort by** selectbox — points/value via `rank_players`, team/position via a
plain sort key. (The st.dataframe headers stay click-sortable too.)

**Trending (`…_Trending.py`).** Fetch each board with a large limit (`trending(players, by, limit=len(players))`)
and `paginate(rows, key=f"trend_{by}", per_page=30)`; keep the GW1-empty note. The buzz board is unchanged
(it lists all mentioned players already).

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `page_labels` unit test; AppTest: the Player Stats page renders each tab + paginates;
   Players pages + sorts by team/position; a Trending board pages past 30; the renumbered pages resolve
   under their new refs; the web-writes-nothing guardrail holds. Existing **565** stay green.
2. **Manual smoke** — on the live app: Player Stats shows the four boards (season-to-date); Players pages
   1–50 → 51–100 and sorts by team; a Trending board pages past 30.
3. **Docs updated** — ADR-063 + index, Architecture, README, PROJECT_STATUS.

---

### 📝 Session Progress Log

- **US-203 ✅ (gate + build)** — Recorded **ADR-063** (+ index; covers US-204/205). New shared
  `web_streamlit/paginate.py` — a pure `page_labels(total, per_page)` ("1–50" / "51–100" / …) + `paginate(
  rows, *, key, per_page)` (a page selectbox + "Showing X–Y of N" caption; ≤per_page → just a count). New
  `pages/2_Player_Stats.py` — `st.tabs(["Over / under-perf", "Defensive Contribution", "Clean sheets",
  "xG / xA / xGI"])`, each reusing the **same** analytics (`over_under` / `defcon_reliability` /
  `defensive_solidity`; xG = players by `xgi`) → an st.dataframe (team **badge** + the CLI's columns),
  `paginate`d per board; a **season-to-date** caption per tab. The analytics rows carry `team` but no `id`,
  so badges (not per-player photos) keep it uniform + change no analytics. **Placed at sidebar position 2**
  → `git mv` renumbered the other 9 pages (Fixtures→3 · Build Squad→4 · My Squad→5 · Squad Health→6 ·
  Transfer→7 · Captain→8 · Ask→9 · News→10 · Trending→11). Updated the ~40 AppTest refs, Home.py, and the
  package docstring. Tests (+4 → **569**): `page_labels` (short/exact/single/empty); the Player Stats page
  (4 tabs render); the layout (Player Stats at 2, old names gone). **Smoke (real DB):** no exception, 4
  tabs · 4 dataframes · 4 page selectboxes, a "1–50" page label + the season-to-date caption present. No
  analytics/data change. ruff clean. _US-204 (Players pagination + sort) and US-205 (Trending pagination),
  reusing `paginate`, next._

- **US-204 ✅ (build)** — Players now **pages through all** matches: dropped the `How many` (5–50) slider,
  added `paginate(ranked, key="players", per_page=50)`; the scatter still spans every match. **Sort by**
  gained **team** and **position** (a helper `_sorted` — points/value via `rank_players`, team/position via
  a plain key then points-desc within the group, using a GK→DEF→MID→FWD order). **Bug caught by the test:**
  the team/position path first returned raw `sqlite3.Row`s (no `.get`, no computed `value`) → crash in the
  table; fixed by normalising through `rank_players` first, then re-sorting the dicts. Tests (+1 → **570**):
  sort-by-team orders the first page + a page control appears + paging past 50 doesn't crash. The existing
  filter test (max-price slider = the only slider now) still holds. ruff clean. _US-205 next._

- **US-205 ✅ (build)** — Trending's `How many` (5–30) slider gone; each of the four boards now fetches
  **all** rows (`trending(players, by, limit=len(players))`) and `paginate(rows, key=f"trend_{by}",
  per_page=30)` — page past 30 on every board. The GW1-empty note (momentum boards preseason) is unchanged;
  the buzz board's stale `count` (from the removed slider) → `limit=len(players)` (show all mentioned — a
  bug **ruff caught** as F821 undefined `count`). Tests (+1 → **571**): the always-populated owned board
  shows a "1–30" page control. **Smoke (real DB):** owned board paginates ("1–30"), momentum boards still
  note "lights up at GW1". ruff clean.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
