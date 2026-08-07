# Sprint 097: Set-piece attributes on My Squad (parity with Trends)

**Dates:** 2026-08-07 (planned)
**Status:** 📝 Planned (0/2 stories)
**Capacity:** ~½ session (display-only — reuses `set_piece_flags` from Sprint 095)
**Carried Over:** none

> **Direction (tester feedback):**
> *"MySquad: Each selected player in my squad should show player **Set Piece Attributes**, like it does for
> showing **Trends**."*

---

### 🔎 Verified at planning (real data — the demo squad)

- **`set_piece_flags` already exists** (Sprint 095, ADR-081) — a pure, empty-safe `player → [⚽ pens · 🚩
  corners · 🎯 FK]` for the first-choice taker. The owned squad rows already carry `penalties_order` /
  `corners_order` / `freekicks_order` (ingested + reseeded), so **no ingest / analytics change** is needed.
- **"Trends" is shown in two shapes** across the Squads tab, so "like Trends" means both:
  1. **My Squad pitch cards** — `web_streamlit/pitch.py::_card` shows `crowd_flags(player)` as a caption line.
  2. **Squad tables** — `render_build` (×2), `render_health`, `render_transfer` (the incoming buy), and
     `render_captain` each add a **"Trends"** column (`" ".join(crowd_flags(p))`) via the shared
     `web_streamlit/tables.py::render_player_table`.
- **Real check (RoboTS):** 4 of 15 own a set-piece duty — **B.Fernandes** (⚽🎯), **Mateta** (⚽),
  **Gibbs-White** (🎯), **Rice** (🎯) — so the cards/columns show meaningful, non-empty flags.
- **No new ADR** — this is display-only and extends **ADR-081** exactly as `crowd_flags` is displayed; the
  analytics/xP are untouched.

---

### 🎯 Sprint Goal

**Objective:** every player in **My Squad** shows their **set-piece attributes** (⚽ pens · 🚩 corners · 🎯
FK) — a line on the pitch card and a **"Set"** column in the squad tables, exactly parallel to how **Trends**
is shown today. Display-only; reuses `set_piece_flags`.

#### Success Criteria
- [ ] **US-253 (pitch cards)** — `pitch.py::_card` shows a **set-piece caption line** (from
      `set_piece_flags`) beneath the Trends line, for any owned player who's a first-choice taker (nothing
      when they take none — empty-safe, like Trends).
- [ ] **US-254 (squad tables)** — a **"Set"** column (parallel to **"Trends"**) on every squad table that
      shows Trends: `render_build` (the build 15 + the formation-preview XI), `render_health`,
      `render_transfer` (the incoming buy → "In set", next to "In trends"), `render_captain`. Move
      `SET_PIECE_LEGEND` to `analytics/crowd.py` (next to `AVAILABILITY_LEGEND`) so both the Players page and
      the Squads tables reuse it; thread an optional `help=` into `render_player_table` so "Set" carries the
      legend tooltip.
- [ ] **No drift** — display-only; `set_piece_flags`/`decision_xp`/the analytics unchanged; existing **658**
      stay green (any column-set assertions updated); ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help (My Squad now shows set-piece attributes).

---

### 🧭 Design sketch

**US-253.** `pitch.py`: import `set_piece_flags`; in `_card`, after the `crowd_flags` caption add
`sp = set_piece_flags(player); if sp: st.caption(" ".join(sp))`. One caption line, empty-safe — the same shape
as the Trends line. (My Squad is the only pitch surface today; the change is at the card, so it's automatic.)

**US-254.** Move `SET_PIECE_LEGEND` from `views/players.py` → `analytics/crowd.py` (export it alongside
`AVAILABILITY_LEGEND`); `players.py` imports it from there (no behaviour change). Add an optional `help=None`
param to `render_player_table` (threaded to the existing `column_config(..., help=…)`). In `squads.py`, next to
each `"Trends": " ".join(crowd_flags(p))`, add `"Set": " ".join(set_piece_flags(p))`, and pass
`help={"Set": SET_PIECE_LEGEND}` to `render_player_table`. For `render_transfer`, add an **"In set"** column
beside "In trends" (the incoming buy's flags).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-253 | **Set-piece line on the My Squad pitch cards** — a `set_piece_flags` caption beneath Trends. | High | ⬜ To do | ~¼ session |
| US-254 | **"Set" column on the squad tables** — parity with "Trends" on Build/Health/Transfer/Captain; shared `SET_PIECE_LEGEND` + `render_player_table(help=…)`. | High | ⬜ To do | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — the My Squad pitch shows a set-piece flag for a taker (AppTest caption scan on the demo
   squad); a squad table exposes a **"Set"** column; `set_piece_flags` stays empty-safe. Existing **658** stay
   green (update any exact column-set assertions).
2. **Manual smoke** — Squads → My Squad: B.Fernandes' card shows ⚽🎯 under his Trends; the Build/Health/Captain
   tables show a Set column; a player with no set-piece duty shows nothing (no clutter).
3. **Docs updated** — PROJECT_STATUS, Architecture, README, Help.

---

### 📝 Session Progress Log

**US-253 — Set-piece line on the My Squad pitch cards (ADR-081).** ✅ Done.
- `web_streamlit/pitch.py::_card`: after the `crowd_flags` (Trends) caption, add a `set_piece_flags` caption
  line (⚽ pens · 🚩 corners · 🎯 FK) — empty-safe (nothing for a non-taker), exactly parallel to Trends.
  Docstring updated. My Squad is the only pitch surface, so the change is automatic there.
- **Tests (+1):** the My Squad pitch shows a set-piece caption for **each** owned first-choice taker — the
  count matches the selected squad's takers exactly (deterministic AppTest against the picker's squad).
  **659** green, ruff clean.
- **Manual smoke (RoboTS):** 4 cards show flags — B.Fernandes ⚽🎯, Gibbs-White 🎯, Rice 🎯, Mateta ⚽; the
  other 11 show nothing (no clutter).

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
