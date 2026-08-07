# Sprint 095: Set-piece takers & the differential lens

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~1 session (ingest two set-piece fields + a Players "Set pieces" view)
**Carried Over:** none

> **Direction (owner, feature request):**
> *"Set Piece & Ownership Data: clear info on who takes **penalties, corners, and free-kicks** for each team,
> plus **ownership combinations** to find high-performing, **low-ownership differential** picks."*

---

### 🔎 Verified at planning (real data — a live fetch)

- **The data is in the FPL API and reachable.** `bootstrap-static` elements carry `penalties_order`,
  `corners_and_indirect_freekicks_order`, `direct_freekicks_order` (an integer per player: 1 = first-choice).
  Live examples: **Saka** pen 1 · corners 6 · FK 2; **Buendía** pen 1 · FK 1.
- **Half is already ingested.** `penalties_order` + `selected_by` are stored; **the corner/FK orders are
  not** — two new fields. Storage has an **automatic light migration** (`_migrate` ALTERs in missing columns
  on open), so the schema addition is low-friction; a `refresh` populates them (the seed then via `reseed`).
- **The differential lens already exists** — `crowd_flags` (💎 ≤5% owned), the differential shortlist
  (ADR-061), and `value` (xP/£m). So "low-ownership differential" = surfacing set-piece duty **alongside**
  `Own%` + `Val/£m`, filterable — not a new metric.

---

### 🎯 Sprint Goal

**Objective:** see who takes **penalties · corners · free-kicks** for each team, and find **low-ownership
set-piece takers** (a strong differential signal) — a new **Set pieces** view on the Players tab, plus a
compact flag on the Pool. Display-only over freshly-ingested fields; no scoring change.

#### Success Criteria
- [ ] **US-249 (ingest set-piece orders, ADR-081)** — add `corners_order`
      (`corners_and_indirect_freekicks_order`) + `freekicks_order` (`direct_freekicks_order`) to the `Player`
      model + `from_api` + the storage schema/upsert/`get_players` (the `_migrate` path adds the columns).
      A pure **`set_piece_flags(player)`** helper (⚽ pens · 🚩 corners · 🎯 FK for the **first-choice**
      taker). `refresh` + `reseed` to populate real data. Tests use synthetic + a storage round-trip.
- [ ] **US-250 (the Set pieces view + Pool flag)** — a **"Set pieces"** option on the Players segmented
      control: a board (Player · Team · Pos · **Pen** · **Corners** · **FK** order + **Own%** · **Val/£m**),
      through the shared filter (team/position), sortable — so a user can find **low-own** takers; a caption
      frames the **differential** angle. The set-piece flags also show on the **Pool** (a compact column).
- [ ] **No drift** — display-only; `decision_xp`/the analytics unchanged; existing **640** stay green; ruff
      clean.
- [ ] Docs: ADR-081 + index, Architecture, PROJECT_STATUS, README.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-249 | **Ingest set-piece orders** — corners/FK order fields + `set_piece_flags`; refresh + reseed. ADR-081. | High | ⬜ To do | ~½ session |
| US-250 | **Set pieces view + Pool flag** — a Players "Set pieces" board (takers + ownership + value, filterable) + the flag on the Pool. | High | ⬜ To do | ~½ session |

---

### 🧭 Design sketch

**US-249 (ADR-081).** `models/player.py`: `corners_order` / `freekicks_order` (+ `from_api` mapping from the
API's long names). `storage.py`: add to the column dict (auto-migrated), the CREATE TABLE, the
INSERT/upsert, `save_players`, and `get_players`' SELECT. `analytics/crowd.py::set_piece_flags(player)` →
`["⚽ pens","🚩 corners","🎯 FK"]` for each duty where the order is **1** (empty-safe). Then `python app.py
refresh` → `reseed` to populate `fpl.db`/`seed.db`.

**US-250.** `views/players.py`: `render_set_pieces(players, sel, badges)` — filter, then a `_board` of
Player/Team/Pos + Pen/Corners/FK (the order ints, blank if none) + Own% + Val/£m, sorted (e.g. pen-takers
first), with a caption on the low-ownership-differential angle + per-column tooltips. Add **"Set pieces"** to
`pages/1_Players.py`'s segmented control. On the **Pool**, add a compact `set_piece_flags`-based column.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `from_api` maps the corner/FK orders; a storage round-trip persists them;
   `set_piece_flags` returns the right flags for a first-choice taker (and none otherwise); the Set-pieces
   view renders a board with the order columns; the Pool shows the flag. Existing **640** stay green.
2. **Manual smoke** (data refreshed) — Players → Set pieces lists each team's pen/corner/FK takers; filtering
   to a team shows its takers; a low-own penalty taker stands out; the Pool shows a ⚽/🚩/🎯 flag.
3. **Docs updated** — ADR-081 + index, Architecture, PROJECT_STATUS, README.

---

### 📝 Session Progress Log

**US-249 — Ingest set-piece orders (ADR-081).** ✅ Done.
- `models/player.py`: added `corners_order` / `freekicks_order` fields + `from_api` mapping from the API's
  long names (`corners_and_indirect_freekicks_order` / `direct_freekicks_order`).
- `storage.py`: added both to the `_MIGRATIONS` column dict (auto-ALTERed in on open), the CREATE TABLE, the
  UPSERT (INSERT list + placeholders + ON CONFLICT SET), and the `save_players` tuple. `get_players` uses
  `SELECT p.*` → picks them up automatically.
- `analytics/crowd.py`: `set_piece_flags(player)` → `⚽ pens` / `🚩 corners` / `🎯 FK` for each order == 1
  (empty-safe, display-only); exported from `analytics`.
- **Tests (+5):** `from_api` maps the orders (+ absent → None); a storage round-trip persists them;
  `set_piece_flags` flags a first-choice taker and ignores non-first-choice / absent. **645** green, ruff clean.
- **Real data (`refresh` + `reseed`):** 573 players; **38** first-choice takers. Differential lens works —
  e.g. **Buendía** / **Wood** are low-own (≤5%) penalty takers; **B.Fernandes** is pens + FK. seed.db updated.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
