# Sprint 125: History polish — a coloured Δ£ + cross-player comparison

**Dates:** 2026-08-26
**Status:** ✅ Complete (2/2 stories)
**Capacity:** ~½ session (two display touches on the web History view — real past-season data, no setup)
**Carried Over:** none

> **Direction:** the History follow-ups flagged in Sprint 118's retro — the web History view's **Δ£** is a plain
> number (no up/down cue), and you can only look at **one** player at a time. Both are display-only and work on
> real past-season data today (unlike the GW1-gated rolling-form sparkline).

---

### 🔎 Verified at planning (on real data)

- **The web History view** (`views/players.py::render_history`): a single-player `st.selectbox` → a **season
  `st.dataframe`** (Season · Pts · Mins · Starts · Pts/90 · xGI · xGC · £ start · £ end · **Δ£**) + a per-GW
  `st.line_chart` (empty preseason → a "fills at GW1" caption). `player_history` supplies the seasons.
- **Real data now:** e.g. **Saka → 8 past seasons** with real `points` + `change` (Δ£) values (`+0.2 / −0.4 / …`)
  — so both a **coloured Δ£** and a **cross-player season overlay** have genuine data today (the per-GW sparkline
  stays GW1-gated).
- **The pattern to reuse:** the Fixtures ticker already colours cells via a pandas Styler; a simpler, preview-
  matching option for Δ£ is an **emoji-in-a-string** (`+0.5 🟢 / −0.3 🔴`) — no Styler, easy to test.
- **No analytics change** — `player_history` is untouched; US-312 adds one small **pure** merge helper
  (`align_seasons`) in `analytics/history.py`; the rendering stays in the view.

---

### 🎯 Sprint Goal

**Objective:** the web History view reads better and compares — a **coloured Δ£** (rise vs fall at a glance) and
an optional **second player** overlaid (season points + a side-by-side table). Display only; the history
assembler + analytics untouched.

#### Success Criteria
- [x] **US-311 (a coloured Δ£)** — on the season table, show Δ£ with an up/down cue: **🟢 for a rise, 🔴 for a
      fall** (e.g. `+0.5 🟢` / `−0.3 🔴`; flat/None → a plain dash). Matches the approved preview.
- [x] **US-312 (cross-player comparison)** — a **"Compare with (optional)"** selectbox (excludes the primary
      player); when set, an aligned **season table** (Season · *A* Pts · *B* Pts, outer-joined on season) + a
      **line chart overlaying both players' season points**. No selection → the current single-player view is
      byte-unchanged.
- [x] **No drift** — display only; `player_history`/`decision_xp` unchanged; the read-only guardrail holds;
      existing **791** stay green (**794** with +3); ruff clean.
- [x] Docs: PROJECT_STATUS, Architecture, README, Backlog (extends **ADR-027/060/069**; no new ADR — display).
      _(Help has no History line; no genuine Feedback_Log item — this traces to Sprint 118's retro.)_

---

### 🧭 Design sketch

**US-311.** In the season-table build, replace the numeric `Δ£` with a formatted string:
`f"{change:+.1f} {'🟢' if change > 0 else '🔴' if change < 0 else ''}".strip()` (None → `"—"`). Δ£ becomes a text
column (drop its `NumberColumn`); the other columns keep their `column_config`. A test asserts a rising season's
Δ£ cell carries 🟢 and a falling one 🔴.

**US-312.** Add a pure `analytics/history.py::align_seasons(hist_a, hist_b, *, key="points")` → a list of
`{"season", "a", "b"}` outer-joined on the season label (missing → None), newest-or-oldest-consistent order.
In the view: a second `st.selectbox("Compare with (optional)", [—] + others)`; when a player is picked, a second
`player_history` read → `align_seasons` → a **season table** (`Season` · `<A name>` · `<B name>`, Pts) and a
`st.line_chart` of both season-points series (a DataFrame indexed by season). The single-player table + per-GW
chart still render for the primary player; the comparison is **additive** below.

**Deferred:** a rolling-**form sparkline** overlay (per-GW — GW1-gated); comparing >2 players (a table gets busy —
2 is the useful case); a stat picker for the overlay (Pts is the headline; xGI/Pts-90 could follow).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-311 | **A coloured Δ£** — 🟢 rise / 🔴 fall on the History season table. | High | ✅ Done | ~¼ session |
| US-312 | **Cross-player History comparison** — a 2nd player overlaid (season table + chart). | High | ✅ Done | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the History season table's Δ£ carries 🟢 on a rise / 🔴 on a fall (`align_seasons` unit-tested
   for the outer join + None-fill; a page AppTest for the compare selectbox → a second table renders). Existing
   **791** stay green. No `.save(` / no analytics change.
2. **Manual smoke** — Players → History: pick a player → Δ£ shows 🟢/🔴; pick a second player in **Compare with**
   → a side-by-side season table + an overlaid line chart; clear it → back to the single view.
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help, Feedback_Log, Backlog.

---

### 📝 Session Progress Log

- **US-311 (a coloured Δ£)** — added `views/players.py::_delta_cell(change)` (pure): `+0.5 🟢` (rise) / `−0.4 🔴`
  (fall, a real minus sign) / `0.0` (flat) / `—` (None); the History season table's `Δ£` now uses it (a text
  column). Display only — `player_history` untouched. Smoke: the History table renders Δ£ with 🟢/🔴 (`['+0.4 🟢',
  '+0.2 🟢', '0.0', …]`). +1 unit test (`test_delta_cell_colours_the_price_move`). ruff clean. **792** total.
- **US-312 (cross-player comparison)** — added a pure `analytics/history.py::align_seasons(hist_a, hist_b, *,
  key="points")` (outer-join on the season label → `[{season, a, b}]`, None-fill for a season only one played;
  exported from `analytics`). In `render_history`: a **"Compare with (optional)"** `st.selectbox` (excludes the
  primary, "—" default) → a 2nd on-demand `player_history` read → a **season table** (Season · *A* · *B* points,
  same-name disambiguated by team) + a **`st.line_chart`** overlaying both season-points series. No selection →
  the single-player view is byte-unchanged. Display only. Smoke: compare → a 2nd dataframe `[Season, Haaland,
  A.Becker]` + chart, no exception. +2 unit tests (`align_seasons` outer-join + empty-safe) + the History page
  AppTest extended (Δ£ cue + the compare table). ruff clean. **794** total.

---

### 🏁 Sprint Review & Retrospective

**Outcome:** ✅ both stories shipped — the web History view reads better (a **🟢/🔴 Δ£**) and now **compares** (a
second player overlaid). Display-only on real past-season data; the history assembler + `decision_xp` untouched.
A light, tester-visible win before recruiting.

**Delivered**
- **US-311** — `_delta_cell(change)` → the season table's Δ£ shows an up/down cue (`+0.5 🟢` / `−0.4 🔴` / `0.0` /
  `—`). +1 unit test.
- **US-312** — a pure `align_seasons(hist_a, hist_b, key="points")` (outer-join on the season label, None-fill) +
  a "Compare with (optional)" selectbox → a side-by-side season table + an overlaid season-points line chart.
  +2 unit tests + the History page AppTest extended.

**Verified at planning + build** — real data now (Saka = 8 past seasons with points + `change`), so both the
colour cue and the overlay have genuine data; the per-GW sparkline stays GW1-gated (deferred). Smoke: Δ£ renders
🟢/🔴; compare → a second table (`[Season, Haaland, A.Becker]`) + a chart, no exception.

**Metrics** — 794 tests (791 → +3) · ruff + CI-parity green · 95 ADRs (no new) · 2 stories, ~½ session.

**What went well**
- **A pure helper for the merge** — `align_seasons` (outer-join) is unit-tested in isolation; the view stays a
  thin renderer, matching the "build once, surface many" pattern of the history feature.
- **Additive, non-destructive** — the compare is *below* the single-player view; no selection → byte-unchanged.
- **Matched the approved preview** — the emoji Δ£ (not a Styler) is simple, robust, and exactly what Tony saw.

**Even better if**
- The overlay is **season points** only (the headline) — xGI / Pts-90 could be a stat picker later.
- The per-GW **sparkline** overlay (the richer form comparison) is GW1-gated — this is the season-level version.
- Two-player only — a 3rd would crowd the table; 2 is the useful comparison.

**Deferred / backlog** — a rolling-form **sparkline** overlay (per-GW → GW1); a **stat picker** for the overlay
(xGI/Pts-90); >2-player comparison.

---

### 📌 For Tony

_(sprint-review reflection fields — left blank for you)_

- **Biggest learning this sprint:**
- **Does the compare view help you scan players (1–5):**
- **One thing to change next sprint:**
