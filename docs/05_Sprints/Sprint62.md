# Sprint 062: Two UI feature requests — a Fixtures ticker + a My Squad pitch view

**Dates:** 2026-08-06
**Status:** ✅ Complete (2/2 stories; retro done)
**Capacity:** ~2 working sessions (a fixture-ticker grid + weeks selector; a formation card-grid; docs)
**Carried Over:** None (Sprint 061 shipped US-184; US-185 deferred → GW1)

> **Direction (owner, from tester/owner notes + two reference images):**
> 1. **Fixtures** — *select the number of weeks* to view difficulty, and display as a **fixture ticker**
>    (teams × gameweeks, colour-coded by difficulty) like the attached screenshot.
> 2. **My Squad** — display as a **pitch / formation** layout (per the attached screenshot), **keeping the
>    information we already have**.
> Owner's call: **robustness first** → a **formation card-grid** (native Streamlit), not a custom-CSS pitch.

---

### 🔎 Verified at planning (data is ready; both work now, not GW1-gated)

- **The ticker data exists.** `team_schedule(upcoming, team)` returns per-GW `{event, opponent, venue
  (H/A), difficulty 1–5}` — exactly one ticker row; `team_fdr(upcoming, next_n)` gives per-team
  `avg_difficulty` (for sorting easiest→hardest). **GW1–8 are loaded**, so a 1–8 week selector has data.
- **The pitch data exists.** Each squad player has a photo (`code`), position, price, xP (`decision_xp`),
  and a **next opponent** via `team_schedule(upcoming, player_team)[0]`; the captain via `captain_id`.
- **Not GW1-gated.** Fixture **difficulty + opponents are live now** (fixtures are loaded), so the ticker
  colours + the pitch opponents render immediately (unlike the momentum trends).
- **No core change, no ADR.** Both are **web-UI renderings over existing analytics** (like Sprint 054/055);
  `decision_xp` and the engine are untouched. Design settled at planning (robust card-grid; difficulty
  colour bands).

---

### 🧭 What's new — two views testers asked for

**Fixtures** becomes a **fixture ticker**: pick how many weeks (1–8); teams are rows, gameweeks are columns,
each cell the opponent + (H/A) shaded green (easy) → red (hard); sorted easiest-first. **My Squad** gains a
**pitch view**: the XI laid out by position (GK/DEF/MID/FWD) + the bench, each a card with photo · name · £ ·
xP · next opponent · **(C)** — the same info, arranged like a team sheet — with the edit controls beneath.

---

### 🎯 Sprint Goal

**Objective:** ship the two requested views — a **weeks-selectable fixture-ticker grid** on Fixtures, and a
**formation card-grid** on My Squad (keeping all current info + edit controls) — as robust, native-Streamlit
renderings over existing data. No core/xP change.

#### Success Criteria
- [ ] **Fixtures ticker** — a teams × GW grid; each cell = opponent + (H/A), **colour-coded by difficulty**
      (1–2 green · 3 amber · 4–5 red); a team badge/name row header; sorted by avg difficulty (easiest first)
- [ ] **Weeks selector** — choose **1–8** gameweeks to show (default 6); the grid + sort update live
- [ ] **My Squad pitch view** — the XI by position rows (GK/DEF/MID/FWD) + a bench row; each a card with
      **photo · name (+ (C)) · £ · xP · next opponent (H/A)**; the legality banner + edit controls
      (rename / swap / bench / download) kept beneath
- [ ] **Robust** — native `st.columns`/`st.container` + a pandas Styler for the grid; no hand-rolled HTML/CSS
      pitch; light/dark themeable; renders headlessly under `AppTest`
- [ ] **No core/xP change** — reuse `team_schedule` / `team_fdr` / `decision_xp`; the invariance test holds
- [ ] Tests — the ticker renders with N columns + reacts to the selector; the pitch view renders the XI +
      bench with (C); existing **501** stay green
- [ ] Docs: Architecture, Handbook/README note, PROJECT_STATUS (no ADR — UI over the settled edge)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-186 | **Fixtures ticker + weeks selector** — a teams × GW grid (opponent + H/A per cell, colour-coded by difficulty) via a pandas Styler; a **1–8 weeks** selector; sort easiest-first (reuse `team_schedule` / `team_fdr`). Replaces the current table/bar. Tests + smoke | High | ✅ Done | 1 session |
| US-187 | **My Squad pitch view** — a formation **card-grid** (GK/DEF/MID/FWD rows + bench) of player cards (photo · name (+ (C)) · £ · xP · next opponent), keeping the legality banner + edit controls; native `st.columns`/`st.container`. Tests + smoke | High | ✅ Done | 1 session |

#### Technical Tasks & Maintenance
- [x] `fixture_ticker` builder (analytics, pure + tested) — team rows × GW cells; page renders via a Styler — _US-186_
- [x] A `pitch`/formation renderer helper in the Streamlit edge (position rows + bench) — _US-187_
- [x] Reuse `team_schedule` for a player's next opponent (My Squad) — _US-187_
- [x] Architecture/Home/PROJECT_STATUS — _US-187_

---

### ✅ Definition of Done (this sprint)

1. **Automated tests pass** — the Fixtures ticker renders a grid, respects the weeks selector, and colours
   cells; the My Squad pitch view lays out the XI + bench with the captain marked; a test still asserts
   `decision_xp` is unchanged; existing **501** stay green.
2. **Manual smoke test done** — Fixtures shows the ticker, the selector changes the columns, colours read
   green→red; My Squad shows the formation with photos + (C) + opponent, and the edit controls still work.
3. **Documentation updated & checked** — Architecture, Handbook/README note, PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| A fixture-ticker grid + a 1–8 weeks selector | A custom-CSS green pitch with shirt graphics (owner: robustness first) |
| A formation card-grid on My Squad (all current info) | Any core / xP / engine change |
| Reuse `team_schedule` / `team_fdr` / `decision_xp` | New analytics or a new data source |
| Native Streamlit + a pandas Styler | Drag-and-drop lineup editing (a later nicety) |

**External Dependencies:** none (FPL data already loaded). Both render **now** (difficulty/opponents live).

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| A styled grid is fiddly in Streamlit | Med | Use a pandas **Styler** (`st.dataframe` accepts it) for per-cell colours — a known, native path |
| The card-grid drifts from a "pitch" look | Low | Owner chose robustness over pixel-fidelity; position rows + cards capture the layout + all info |
| Colour bands feel off | Low | Map FPL difficulty 1–5 → green/amber/red (few, tunable); mirror the screenshot's palette |
| Regressions on Fixtures/My Squad | Med | Keep the data reuse; `AppTest`s for both; the `decision_xp`-invariance test still guards xP |

---

### 🗝️ Gating note — no new ADR

Both stories are **UI renderings over the settled edge** (reuse `team_schedule`/`team_fdr`/`decision_xp`),
like Sprint 054/055. **No ADR.** The design is settled here: a **weeks-selectable difficulty grid** and a
**robust formation card-grid** (not a custom-CSS pitch — owner's call).

---

### 📝 Session Progress Log

- **US-186 ✅** — **Fixtures ticker + weeks selector.** New pure **`fixture_ticker(fixtures, next_n)`** in
  `src/analytics/fdr.py` (reuses `team_fdr` + `team_schedule`) → `{gameweeks, rows: [{team, avg_difficulty,
  cells: {gw: {opponent, venue, difficulty}|None}}]}`, easiest-run first. The **Fixtures** page rebuilt as
  a **teams × gameweeks grid**: a **1–8 weeks** slider (default 6); each cell = `opponent (H/A)`,
  **colour-shaded by difficulty** (1–2 green · 3 amber · 4–5 red) via a pandas **Styler**; a team-badge
  column; replaces the old table/bar. Data-shaping is core (pure + unit-tested); colours/render at the edge.
  Tests (+2 → **503**): `fixture_ticker` shape/ordering + a blank-GW → None cell; the page renders the grid
  and the weeks slider changes the GW-column count (6 → 3). Smoke: 20 teams, GW1–6, EVE easiest; `ruff`
  clean. Works **now** (difficulty/opponents are live).
- **US-187 ✅** — **My Squad pitch view.** New `src/web_streamlit/pitch.py` `render_pitch(xi, bench, …)` — a
  robust, native **formation card-grid**: position rows (GK/DEF/MID/FWD) via `st.columns` + a bench row,
  each player a bordered card (photo · name (+ **(C)**) · team · £ · xP · **next opponent (H/A)** · crowd
  flags), reusing `crowd_flags`. The **My Squad** page renders it in place of the dataframe (a
  `team_schedule` lookup per owned team gives each card's next fixture); the legality banner + all edit
  controls (rename/swap/bench/download) stay beneath. Owner's call honoured — no custom-CSS pitch, so it's
  themeable + headless-testable. Tests (+1 → **504**): the pitch lays out ≥11 name cards and no dataframe;
  the existing My Squad tests (banner/download/swap/rename/bench) stay green; `test_squad_tabs_show_image_tables`
  narrowed to the table tabs. Smoke: 15 cards, banner + edit controls + download intact; `ruff` clean.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ Successful — both owner-requested views shipped: a **Fixtures ticker** (weeks-selectable,
colour-coded) and a **My Squad pitch** (formation card-grid), robustly and over existing data.

**Delivered**
- **US-186 ✅** — a pure `fixture_ticker` + a teams × GW grid on Fixtures (1–8 weeks selector, difficulty
  colours via a Styler, easiest-first).
- **US-187 ✅** — a `render_pitch` formation card-grid on My Squad (position rows + bench; photo · name ·
  (C) · £ · xP · opponent · flags), keeping the edit controls; native Streamlit, no custom CSS.

**Verification** — 504 tests green (**+3**), `ruff` clean. Smoke: the ticker renders 20 teams × the chosen
weeks and recolours by difficulty; the pitch lays out 15 cards with the captain marked, banner + edit
controls intact. `decision_xp`/engine untouched; the invariance test still holds.

**Carried forward** — none new. The standing markers remain: **GW1 (2026-08-21)** (the deferred trends
intent US-185 + threshold calibration + Data Hardening) and the **tester-feedback loop** (Sprint 059).

**What went well** — matching the screenshots with existing data meant **no new analytics** — `fixture_ticker`
just reshaped `team_fdr`/`team_schedule`, and the pitch reused `crowd_flags` + `team_schedule`. Keeping the
grid's data-shaping pure (core, unit-tested) and the colouring at the edge kept the split clean. The owner's
"robustness first" call made the pitch a native card-grid — themeable and headless-testable — rather than a
fragile custom-CSS pitch.

**What to watch** — the pitch is an *approximation* of the FPL pitch (cards in position rows), not the exact
shirt-on-green look; if that fidelity matters later it's a custom-HTML/CSS follow-up (with the robustness
trade-off noted). The ticker's colour bands are fixed constants — fine, but tunable if the palette needs it.

**Lessons captured:** `docs/05_Sprints/Sprint62_Lessons_Learnt.md`.
