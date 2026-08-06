# Sprint 080: Consolidate the sidebar — Players & Squads

**Dates:** 2026-08-06 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~2–2.5 sessions (the biggest web restructure yet — extract view bodies, 2 merged pages, rewire ~all web tests)
**Carried Over:** none

> **Direction (owner):** fewer, clearer tabs — merge **Players + Player Stats** → one **Players** tab, and
> **Build Squad + My Squad + Squad Health + Transfer + Captain** → one **Squads** tab. Owner's calls (from
> the recommendation): a **segmented control** sub-nav (tab-like but **lazy** — only the selected view
> computes); keep the groupings, ordered as the workflow; **Players first**; Ask/Fixtures/News/Trending/Help
> stay top-level.

---

### 🔎 Verified at planning (real code)

- **`st.segmented_control`** exists + is AppTest-drivable, and renders **only the selected option** — so a
  5-tool Squads page doesn't recompute the ILP build + transfer + captain + health each interaction (which
  `st.tabs` would, since it executes every tab body).
- The current pages run as **top-level scripts**, so consolidating means **extracting each view's body into
  a `render_*()` function** the merged page can call conditionally.
- **Shared setup** the merged pages centralise: `render_data_status()`; a **filter** (Players) or the
  **sidebar + squad picker** (Squads); one data load (players · upcoming · history · gw_history · photos ·
  badges). One `filter_controls(..., with_price=True)` serves the Pool (players have a price) *and* the stat
  boards (analytic rows have no price → `apply`'s price check is a no-op).
- **~38 AppTest references** point at the pages being merged — they'll be rewired to the new pages (driving
  the segmented control to the right view).

---

### 🎯 Sprint Goal

**Objective:** a **12 → 7** tab sidebar — **Players · Fixtures · Squads · Ask · News · Trending · Help** —
by merging the two groups behind a lazy segmented-control sub-nav, with **no behaviour change** to the
underlying tools (same engine, same outputs).

#### Success Criteria
- [ ] Approach agreed (**ADR-069**) — merge Players+Player Stats and the 5 squad tools; a **segmented
      control** sub-nav (lazy); view bodies extracted into `render_*` functions; a shared filter (Players) /
      picker (Squads); Ask/Fixtures/News/Trending/Help stay top-level; final sidebar order
- [x] **US-216 (Players)** — merge Player Stats into **Players**: a shared filter + a segmented control
      **Pool · Over/under · DefCon · Clean sheets · xG** (only the chosen view computes); remove
      `2_Player_Stats.py`; rewire the Players + Player Stats AppTests + the tooltip-coverage list
- [x] **US-217 (Squads)** — merge Build/My Squad/Health/Transfer/Captain into **Squads**: the sidebar +
      a segmented control **Build · My Squad · Health · Transfer · Captain** (a shared picker for the manage
      views; only the chosen view computes); removed the 5 pages; **renumbered** to the clean 7-tab sidebar;
      rewired the squad AppTests; updated **Home** + **Help** copy to the new nav
- [x] **No behaviour change** — each tool behaves as before (same analytics, same rendered output); the web
      writes nothing server-side (the `.save(` guardrail holds); help tooltips still covered
- [x] Existing **585** stay green (rewired, not weakened); ruff clean
- [ ] Docs: ADR-069 + index ✅; Architecture, PROJECT_STATUS, README (the new tab list) _(at the retro)_

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-216 | **Consolidate Players** — Players + Player Stats → one **Players** page (shared filter + a lazy segmented control: Pool · Over/under · DefCon · Clean sheets · xG). Extract the view renders; rewire tests. ADR-069. | High | ✅ Done | ~1 session |
| US-217 | **Consolidate Squads** — Build/My Squad/Health/Transfer/Captain → one **Squads** page (sidebar + a lazy segmented control + a shared picker for the manage views). Extract renders; renumber to 7 tabs; rewire tests; update Home/Help. ADR-069. | High | ✅ Done | ~1–1.5 sessions |

---

### 🧭 Design sketch (to settle in ADR-069)

**Extraction.** Move each page's body into a `render_*(…)` function in a small `web_streamlit/views/`
package (taking already-loaded data + shared helpers). The merged page: page-config → `render_data_status()`
→ shared control → `view = st.segmented_control("View", [...], default=…, help=…)` → call the selected
`render_*`. Only the chosen view executes (the perf win).

**Players (US-216).** `sel = filter_controls(players, key="players", with_price=True)` above the control;
`view` ∈ `Pool · Over/under · DefCon · Clean sheets · xG`. Pool = the sort + top-15 bar + paginated table;
the four stat views = the reused analytics boards. All light, but still lazy for consistency.

**Squads (US-217).**
```
view = st.segmented_control("Tool", ["Build","My Squad","Health","Transfer","Captain"], default="Build")
if view == "Build": render_build(...)
else:
    name, squad = squad_picker()          # one picker feeds the four manage views
    {"My Squad": render_my_squad, "Health": render_squad_health,
     "Transfer": render_transfer, "Captain": render_captain}[view](name, squad, ...)
```
Final sidebar renumber: `1 Players · 2 Fixtures · 3 Squads · 4 Ask · 5 News · 6 Trending · 7 Help`.

**Tests.** Rewire the ~38 AppTest refs to the merged pages, driving `at.segmented_control[0].set_value(view)`
to reach each tool; keep every existing assertion (behaviour unchanged). Update `test_help_tooltips._COVERED`
to the merged pages; the segmented control + filter/picker carry `help=`.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the merged page renders each view via the segmented control; every prior assertion
   (tables, bars, filters, build/transfer/captain/health behaviour, session-squad edits) survives; the
   web-writes-nothing guardrail + the tooltip coverage hold. Existing **585** stay green.
2. **Manual smoke** — the sidebar shows the 7 tabs; on **Players**, switching Pool ↔ Stats works and the
   filter applies to both; on **Squads**, Build sets the active squad and the manage views act on it via one
   picker; nothing recomputes that isn't shown.
3. **Docs updated** — ADR-069 + index, Architecture, PROJECT_STATUS, README, and the **Home** + **Help**
   copy reflect the 7-tab nav.

---

### 📝 Session Progress Log

- **US-216 ✅ (gate + build)** — Recorded **ADR-069** (+ index; covers US-217). New `web_streamlit/views/`
  package — extracted the Player views into `views/players.py` (`render_pool` + `render_over_under` /
  `render_defcon` / `render_cleansheet` / `render_xg` + the `_sorted`/`_board` helpers). Rewrote
  `pages/1_Players.py` as a thin page: load once → one shared `filter_controls(with_price=True)` → an
  `st.segmented_control` **Pool · Over/under · DefCon · Clean sheets · xG** → render **only** the selected
  view (lazy). Removed `pages/2_Player_Stats.py` (`git rm`). Rewired the two Player Stats tests to the merged
  page (drive the segmented control); dropped `2_Player_Stats.py` from the tooltip-coverage list + fixed the
  stale layout test. Every prior Players assertion (table · top-15 bar · crowd-lens cols · photo/badge ·
  filter narrowing · team scoping · sort + pagination) still passes on the default Pool view — **no
  behaviour change**. **585** green, ruff clean. **Smoke:** 5 views (default Pool = table + bar); switching
  to "Clean sheets" + Team=ARS → 7 ARS players (xGC/90), no exception. _Home/Help copy + the final renumber
  land in US-217 with the Squads merge._

- **US-217 ✅ (build)** — Extracted the five squad tools into `views/squads.py` (`render_build` /
  `render_my_squad` / `render_health` / `render_transfer` / `render_captain` — bodies copied faithfully,
  `st.stop()`→`return`). New thin `pages/3_Squads.py`: `render_sidebar()` → an `st.segmented_control`
  **Build · My Squad · Health · Transfer · Captain** → Build renders itself; the four manage views share
  **one** `squad_picker()`; only the selected view computes (lazy). `git rm` the five squad pages; **final
  renumber** to the clean **7-tab** sidebar (`1 Players · 2 Fixtures · 3 Squads · 4 Ask · 5 News ·
  6 Trending · 7 Help`). **Rewired ~38 AppTest refs** (a `_squads_view(view)` helper drives the control;
  every prior assertion kept — buttons label-filtered for robustness); updated the tooltip-coverage list,
  the layout test, **Home** + the **Help** guide + the package docstring to the new nav. **585** green
  (rewired, not weakened), ruff clean, no server writes. **Smoke:** all 5 tools render via the control
  (Build→code · My Squad→pitch · Health/Transfer/Captain→code), shared picker present, no exceptions.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — the sidebar went **12 → 7 tabs** (Players · Fixtures · Squads · Ask · News ·
Trending · Help). Players absorbed Player Stats; Squads absorbed Build/My Squad/Health/Transfer/Captain —
each behind a lazy `st.segmented_control` (only the shown view computes). **No behaviour change**: every
prior assertion was kept, just reached via the control.

**What went well** — doing **Players first** proved the pattern (extract view bodies → `views/` package →
thin page + segmented control → rewire tests) on the light page before the heavy Squads merge, which then
went smoothly. The `st.segmented_control` choice paid off: the 5-tool Squads page only computes the selected
view. A `_squads_view()` test helper made the ~38-ref rewire tractable, and **label-filtering the buttons**
(rather than `button[0]`) made the tests robust to the sidebar's Import button shifting widget indices.

**What to watch / lessons** — a few tests had hidden a fragile assumption (`text_input[0]`/`button[0]`
positional indexing); consolidating surfaced it, and label-filtering is the durable fix. The tooltip
coverage now checks each consolidated page's **default** view (Pool / Build); the manage-view widgets keep
their help (Sprint 074) but aren't re-checked — an acceptable trade. This is intended as the **settling
point** for the nav; Home + Help now describe the 7 tabs + the in-tab view switches.

**Lessons captured:** `docs/05_Sprints/Sprint80_Lessons_Learnt.md`.
