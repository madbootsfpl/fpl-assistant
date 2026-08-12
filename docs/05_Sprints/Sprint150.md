# Sprint 150: Per-gameweek xP in the player card (ADR-109)

**Dates:** 2026-08-12
**Status:** 🚧 Planned — US-367 + US-368 (ADR-109)
**Capacity:** ~1 short session (card render + pitch threading; no xP math)
**Carried Over:** none

> **Direction (ADR-109):** match the tester's image — under a shirt, a **per-gameweek row** in the card: each of the
> next up-to-3 GWs as a column with **xP on top** + **fixture below** (Mbeumo `5.1` HUL (A) · `6.2` IPS (H) · `4.5`
> EVE (A)) — up to 3 GWs, **no Total** (dropped after previewing — cleaner). Reuses `by_gameweek` (already
> computed) — **display-only, no xP math**.
> One `card_body` change → both the hover popover **and** the ⚙ panel card (ADR-108).

---

### 🔎 Verified at planning (on the code)

- **Data is free:** `decision_xp` returns `by_gameweek` (`{event: xP}`) + `gameweeks`; `render_my_squad` already
  builds `by_gameweek_by_id` (line 276, used only for the captain bonus). `xp_by_id` = the horizon total.
- **Fixtures carry the gameweek:** `team_schedule(upcoming, team)` → per-fixture `{event, opponent, venue,
  difficulty}`. Align xP to fixture by **event number** — exact.
- **`card_body` (ADR-084)** renders the fixture pills (`fixtures=[{opp,home,fdr}]`) + a single Proj-xP chip; used by
  the hover popover (`pitch.py:_kit_html`, compact, **no fixtures passed today**) *and* the ⚙ panel card
  (`render_player_card`). One change hits both.
- **Horizon** 1/2/3/4/5/10 → the card shows the first **up-to-3** GWs (no Total column — owner steer).

---

### 🎯 Sprint Goal

The player card shows a per-GW row (xP over fixture) matching the tester's image — in the ⚙ panel card (all devices)
and the pitch hover popover (desktop) — up to 3 GW columns (no Total), with no xP change and the suite green.

#### Success criteria
- [ ] **US-367 (the per-GW row + the panel card)** — extend `card_body`: when each `fixtures` item carries an `xp`,
      render a **per-GW row** (column = xP bold on top + FDR-tinted `OPP (H/A)` below, up to 3 GWs) instead of the
      plain pills. **No Total column** (owner dropped it after previewing — cleaner; the shirt chip already shows the
      horizon total). **Backward-compatible:** no `xp` on fixtures → today's pills + Proj chip (the Players "Card"
      view unchanged). Build a shared `fixtures_by_id` in `render_my_squad` (`team_schedule` next-3 + `by_gameweek`
      xP per event) and wire the ⚙ **panel card** (`render_player_card`). Tests: the panel card shows a per-GW xP +
      fixture; no Total column.
- [ ] **US-368 (the hover popover)** — thread `fixtures_by_id` through `render_pitch` → `_kit_html` → `card_body` so
      the **card under each shirt** shows the same per-GW row (the exact image). Tests: the pitch markup includes a
      per-GW xP for a kit.
- [ ] **No drift** — display-only; no `decision_xp`/analytics change; ruff clean; the suite green.
- [ ] **Docs** — Help note; PROJECT_STATUS; Architecture; memory. ADR-109 already written (the gate).

---

### 🧭 Design sketch

```
card (hover popover + ⚙ panel):
┌───────────────────────────────┐
│  photo   Team · POS · £8.0     │
│          Mbeumo                │
│     5.1      6.2      4.5      │   ← per-GW row: xP (bold) …
│    HUL(A)   IPS(H)   EVE(A)    │   ← … over fixture (FDR-tinted), up to 3 GWs, no Total
│  [flags: ownership · set-piece]│
└───────────────────────────────┘
```

- `card_body`: new `.plc-gwrow` of `.plc-gwcol` (xP over an FDR-tinted `OPP (H/A)`, up to 3 — no Total). Falls back
  to the current pills when fixtures carry no `xp`.
- `render_my_squad`: `fixtures_by_id[id] = [{opp,home,fdr,xp} …≤3]` via `team_schedule` + `by_gameweek_by_id`; pass to
  `render_pitch` (US-368) and to the panel card (US-367).

**DoD:** tests (per-GW row in the panel card; per-GW in the pitch markup) + a manual smoke (hover a shirt
/ open the panel card → the row matches the image) + docs. **DGW/BGW** = graceful (align by event; a GW1-era polish).

---

### 📋 Sprint Review
*(filled at retro)*

### 🧠 Lessons
*(see `Sprint150_Lessons_Learnt.md` at retro)*
