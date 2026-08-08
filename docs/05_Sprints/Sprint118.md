# Sprint 118: History on the web (+ a price column)

**Dates:** 2026-08-19 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (enrich the history assembler + a web view — display only)
**Carried Over:** none

> **Direction (owner):** keep going on the backlog — **complete the Sprint-117 history feature on the web**: a
> player-history view reachable from Players, plus the per-season **price / price-change** column (the cost
> units are verified now).

---

### 🔎 Verified at planning (on real data)

- **The price/cost units are £m.** `player_history_past.start_cost`/`end_cost` are already **£m** (Haaland
  *2024/25 £15.0m → £14.9m · 2025/26 £14.0m → £14.7m*) — the ingest converts tenths → £m (the ingestion test
  pins `115 → 11.5`). So a **£start→end** (and the ± change) column is safe to add now.
- **The web slots into the existing Players sub-nav.** The Players page already switches views with a
  **`st.segmented_control`** (Pool · Set pieces · Over/under · DefCon · Clean sheets · xG) — a **"History"**
  option fits cleanly. History is **per-player** (pick one), so the view needs an on-demand history fetch
  (a short-lived `Storage` for the selected player's `get_history_past`/`get_history`).
- **The engine is done.** `analytics.player_history` + the accessors already exist (US-295); the web view
  reuses them, rendered natively (a `st.dataframe` season table + a per-GW **line chart**) rather than the mono
  block. Past seasons are real now; the per-GW trend fills at GW1.

---

### 🎯 Sprint Goal

**Objective:** a player's history is a first-class **web** view (season table + per-GW trend + price), and the
CLI/Ask history gains the **price column** too. Display only — reuses `analytics.player_history`; the
analytics/xP untouched.

#### Success Criteria
- [ ] **US-297 (a price column in the history)** — `analytics/history.py::player_history` season rows gain
      `start_cost` · `end_cost` · `change` (all £m; empty-safe); `ui/history.py::render_player_history` shows a
      **£** column (`start→end`) so the CLI + `ask "X's history"` include it. No analytics change.
- [ ] **US-298 (history on the web)** — a **"History"** view on the **Players** page (added to the segmented
      control): a **player selectbox** → `player_history` rendered as a **season `st.dataframe`** (Season · Pts ·
      Mins · Starts · Pts/90 · xGI · xGC · £start→end) + a per-GW **`st.line_chart`** (points by GW) when data
      exists, else a *"per-GW form fills at GW1"* caption; degrades to a "run `history --backfill`" note when a
      player has none. Display-only; no server writes.
- [ ] **No drift** — a read-view/lens only; `decision_xp`/the analytics unchanged; the read-only web guardrail
      holds; existing **762** stay green (+ price / web-history tests); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Backlog (extends **ADR-027/060** (history) +
      **ADR-069** (the Players sub-nav) — noted; no new ADR).

---

### 🧭 Design sketch

**US-297.** `player_history` season dicts gain `start_cost`/`end_cost` (from the rows, already £m) + `change`
(`round(end - start, 1)`); `render_player_history`'s `_SEASON_COLS` gains a `Col("£", …)` showing
`{start}→{end}` (e.g. `14.0→14.7`). The Ask/CLI history answers inherit it. Empty-safe (missing cost → "—").

**US-298.** `web_streamlit/views/players.py::render_history(rows, photos, badges)` — a `st.selectbox` of player
names (from the filtered/sorted `rows`); on a pick, open a short-lived `Storage`, fetch the player's history,
build `player_history`, and render: a **season `st.dataframe`** (formatted via the shared `column_config`) + a
**`st.line_chart`** of per-GW points (only when per-GW rows exist), else a caption noting it fills at GW1; a
photo/badge header. The Players page gains `"History"` in the segmented control + an `elif view == "History":`
branch. A test drives the view via AppTest (season table renders; the GW1 note shows preseason).

**Deferred:** a rolling-form sparkline beyond the raw per-GW line; cross-player history comparison; a standalone
History **tab** (the Players sub-view is enough).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-297 | **A price column in the history** — `£start→end` (+ change) in `player_history` + the CLI/Ask renderer. | High | ⬜ To do | ~¼ session |
| US-298 | **History on the web** — a "History" view on Players (player picker → season table + per-GW chart + price). | High | ⬜ To do | ~¾ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `player_history` season rows carry `start_cost`/`end_cost`/`change` (empty-safe); the CLI
   `render_player_history` shows the `£` column (`14.0→14.7`); the Players **History** view renders a season
   dataframe for a real player (AppTest, skip if no seed history) + the "fills at GW1" note when per-GW is empty
   + a "run --backfill" note for a player with none. Existing **762** stay green. No `.save(` / no analytics
   change.
2. **Manual smoke** — `python app.py history Haaland` shows the £ column; Players → **History** → pick Haaland →
   the season table + (preseason) the GW1 caption.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Backlog.

---

### 📝 Session Progress Log

**US-297 — a price column in the history.** ✅ Done.
- `analytics/history.py::player_history` season rows now carry **`start_cost` · `end_cost`** (already £m — the
  ingest converts tenths) **+ `change`** (`round(end − start, 1)`, `None` when a cost is absent — empty-safe).
- `ui/history.py::render_player_history` gained a **£m** column via `_price` → `£{start}→{end}` (or "—"), so
  the CLI + `ask "X's history"` show it. e.g. Haaland: *2022/23 £11.5→12.4 · 2024/25 £15.0→14.9 · 2025/26
  £14.0→14.7*.
- **Tests (+1, 1 extended):** `player_history` carries price + change (a rise +0.3, a fall −0.1, missing → None);
  the renderer shows `£14.0→14.3` and "—" when absent. **763** green, ruff clean.
- **Manual smoke:** `history Haaland` shows the £ column across all four seasons.

_(US-298 next — "start US-298".)_

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
