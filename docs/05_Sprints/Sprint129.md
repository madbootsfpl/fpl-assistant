# Sprint 129: Build the DefCon opposition magnifier (wired-dormant) + persistence review

**Dates:** 2026-08-30 (planned)
**Status:** 📝 Planned (0/2 stories · 1 ADR refinement)
**Capacity:** ~¾–1 session (a **modelling** build on `decision_xp` — the careful one; wired-dormant)
**Carried Over:** the ADR-097 design gate (now being built, with a refined approach)

> **Direction (owner):** *review* team persistence across devices + the DefCon magnifier, then **build the DefCon
> magnifier** (wired-dormant, calibrate at GW1). Persistence review below; the sprint's work is the DefCon build.

---

### 🔎 Review + verified at planning

**Team persistence across devices (ADR-094, built Sprint 124) — ✅ done + dormant; owner-activated.**
`cloud_store.py` (`is_configured`/`save_squad`/`load_squad`/`delete_squad`/`clean_handle`) + the My-Squad
**"☁ Save / Load across devices"** expander (handle · Save/Load/Clear · a privacy caption) are complete; 10
cloud tests green. It's **off until the owner sets `FPL_STORE_URL`/`FPL_STORE_KEY`** (a Supabase project +
the `squads` table, `docs/CLOUD_SQUADS.md`). **No build needed** — a status note; the optional polish (a "handle
taken?" hint / a suffix suggestion) stays deferred.

**DefCon magnifier — the review sharpened the design.** The build surfaced the crux: **a player's historical
baseline already includes the DefCon points they earned** (`total_points` covers defensive contributions), so
adding a *separate* DefCon-xP component would **double-count** (the same trap as set-pieces). **Refined approach:
the magnifier re-weights the DefCon portion *already in the baseline* by fixture — a delta**
`defcon_pts_per_match × (magnifier − 1)`, which is **0 when the magnifier is neutral** → naturally wired-dormant
(invariance holds). Verified inputs: `defcon_per90` is real (363/573 players); `THRESHOLD` = DEF 10 · MID/FWD 12
(GK excluded); `player_xp` already has the **per-fixture difficulty** `d` in its multiplier loop (the magnifier
input) — so no new fixture plumbing. Clean-sheet proxy = **FDR difficulty** (strong opponent → high difficulty →
more defending → higher magnifier), **no betting odds** (ADR-093/097).

---

### 🎯 Sprint Goal

**Objective:** a **double-counting-safe** DefCon fixture magnifier in the one `decision_xp` recipe — a **delta**
on the DefCon portion already priced in the baseline, **off by default** (`DEFCON_MAGNIFIER_WEIGHT = 0` → every
xP byte-identical; an invariance test pins it), and **auditable** (`defcon_xp` on the row + a grounded reason).
Calibrate the P(clear) mapping + the magnifier band at GW1.

#### Success Criteria
- [ ] **ADR-097 refinement (gate → built)** — record the **delta** approach (re-weight the DefCon portion in the
      baseline, don't add a new component → no double-counting); the P(clear-threshold) model + the FDR
      clean-sheet proxy; `DEFCON_MAGNIFIER_WEIGHT` dormant + invariance-pinned; a *modelling* change (not a lens);
      GW1 calibration. Mark ADR-097 **built**.
- [ ] **US-318 (the pure DefCon-magnifier analytics)** — `analytics/defcon_xp.py`:
      `defcon_points_per_match(player)` → `2 · P(clear)` from `defcon_per90` vs the position `THRESHOLD` (0 for
      GK/ineligible/no data; a documented, GW1-calibratable P-mapping) + `defcon_magnifier(difficulty)` → a
      clamped fixture multiplier (weak opp / low difficulty → ~0.5–0.75; strong / high → ~1.25–1.5; the owner's
      band). Pure + unit-tested.
- [ ] **US-319 (wire the delta into `decision_xp`, dormant + auditable)** — `config.DEFCON_MAGNIFIER_WEIGHT = 0.0`;
      in `player_xp`, add per-fixture `defcon_pts_per_match · w · (defcon_magnifier(d) − 1)` (minutes-weighted)
      to xp — **`w = 0` → 0 delta → xP byte-identical**; a `defcon_xp` field on the row (the net delta; 0
      dormant); a weight-aware explanation reason ("🛡 DefCon fixture edge (+X)") when active.
- [ ] **No unintended drift** — with the weight 0 the existing **811** stay green (xP unchanged everywhere); the
      lens invariance (crowd/price) holds; ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Backlog, ADR-index (ADR-097 built); a persistence status note.

---

### 🧭 Design sketch

**ADR-097 refinement.** The magnifier is a **delta on the DefCon portion already in the baseline**, not a new
component — this is what makes it double-counting-safe and dormant-by-default (delta 0 at neutral magnifier).
Everything else (the FDR clean-sheet proxy, the opposite-direction caveat vs clean sheets, the transferred-player
note, GW1 calibration) stands.

**US-318.** `analytics/defcon_xp.py`:
- `defcon_points_per_match(player) -> float`: threshold from `THRESHOLD[position]` (GK/None → 0); `P(clear) =
  clamp(0.5 + (defcon_per90 − threshold) / DEFCON_P_SCALE, 0, 1)` (a simple, documented, GW1-tunable mapping);
  return `2 · P(clear)`. Empty-safe (no `defcon_per90` → 0).
- `defcon_magnifier(difficulty) -> float`: map FDR difficulty ∈ [1,5] → a multiplier ∈ [`DEFCON_MAG_LO`,
  `DEFCON_MAG_HI`] (e.g. `0.5 + (difficulty − 1) · 0.25` → 1@diff-3), clamped; `None` difficulty → 1.0 (neutral).

**US-319.** In `player_xp`, after the base xp: for the eligible player, `defcon_pm = defcon_points_per_match(p)`;
`defcon_delta = Σ_fixtures weight · defcon_pm · set_piece_weight-style w · (defcon_magnifier(d) − 1)` over the
horizon's per-fixture difficulties `d`; `xp = round(base + defcon_delta, 1)`; record `defcon_xp = round(defcon_
delta, 1)`. `config.DEFCON_MAGNIFIER_WEIGHT` gates it (0 → delta 0 → invariance). `decision_xp` passes the
weight. The explanation gains a weight-aware `🛡 DefCon fixture edge (+X)` reason when `defcon_xp` ≠ 0 (grounded,
ADR-037/089); dormant → nothing added (byte-identical).

**Deferred:** the **GW1 calibration** (`DEFCON_P_SCALE`, the magnifier band, the weight on real returns); a
separate **clean-sheet-xP** magnifier (opposite direction); a **team-share** adjustment for transfers; an
Elo/xGC proxy refinement beyond FDR; the **persistence handle-taken hint** (optional polish).

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-097 | **Refine → the delta approach** (re-weight the baseline's DefCon portion; no double-count). | High | ✅ Done | gate |
| US-318 | **The pure DefCon-magnifier analytics** — `defcon_points_per_match` + `defcon_magnifier`. | High | ✅ Done | ~⅓ session |
| US-319 | **Wire the delta into `decision_xp`** — dormant + invariance + auditable. | High | ⬜ To do | ~½ session |

---

### 🧑‍💻 Owner runbook action (you — persistence, ~10 min, £0)

- **Activate cross-device squads:** create a free Supabase project + the `squads` table + the two secrets
  (`FPL_STORE_URL`/`FPL_STORE_KEY`), per `docs/CLOUD_SQUADS.md` → the "☁ Save / Load across devices" expander
  appears. Nothing to build.

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `defcon_points_per_match` (P(clear) from the rate; 0 for GK/no-data) + `defcon_magnifier`
   (band + clamp; neutral on unknown) are unit-tested; with `DEFCON_MAGNIFIER_WEIGHT = 0` **every xP is
   byte-identical** to today (the invariant); a positive weight lifts a reliable DefCon earner's xP for a **hard**
   fixture and trims it for an **easy** one; `defcon_xp` on the row is 0 dormant / the net delta when active; the
   explanation shows the edge only when active (grounded). Existing **811** stay green; crowd/price lens
   invariance holds; ruff clean. No `.save(`.
2. **Manual smoke** — with the weight temporarily set, a nailed DEF vs a strong opponent gains xP (magnifier > 1),
   vs a weak one loses a little (< 1); the `ask`/explanation cites the 🛡 edge (verified ✓); reset to 0 → exactly
   as before.
3. **Docs updated** — ADR-097 (built) + the index; PROJECT_STATUS, Architecture, README, Backlog.

---

### 📝 Session Progress Log

- **ADR-097 refinement (gate → built)** — refined `docs/06_Decisions/ADR-097-defcon-opposition-magnifier.md` from
  the original "add a DefCon-xP component" to the **delta approach**: the baseline already includes a player's
  DefCon points, so the magnifier **re-weights the DefCon portion already priced in** — `defcon_pts_per_match ×
  (magnifier − 1)`, **0 at neutral → no double-count, dormant by default**. Updated the Status (built wired-dormant
  this sprint, `DEFCON_MAGNIFIER_WEIGHT = 0`; calibrate GW1), the Context (the baseline-includes-DefCon note
  replacing the "prerequisite component"), Decision §1–§2 (the P(clear) portion + the delta formula) + §4 (the
  knob), and the follow-ups (built + the GW1 calibration/backtest). Added a **Refinement** banner. Updated the ADR
  index row. No code (gate) — suite unchanged at **811**.
- **US-318 (the pure DefCon-magnifier analytics)** — added `analytics/defcon_xp.py`:
  `defcon_points_per_match(player)` → `2 · clamp(0.5 + (defcon_per90 − THRESHOLD[pos]) / DEFCON_P_SCALE, 0, 1)`
  (0–2; 0 for GK/ineligible/no `defcon_per90`) + `defcon_magnifier(difficulty)` → the FDR-difficulty → band map
  (`DEFCON_MAG_LO 0.5` … `DEFCON_MAG_HI 1.5`; neutral 1.0 at mid/unknown; clamped). `DEFCON_P_SCALE 10.0` +
  the band are documented, GW1-calibratable constants. Exported both. Probe: DEF per90 15→2.0 / 10→1.0 / 5→0.0;
  MID/FWD threshold 12; GK→0. Magnifier: diff 1→0.5, 3→1.0, 5→1.5, None→1.0, 6→1.5 (clamped). +5 unit tests.
  ruff clean. **816** total. (US-319 wires the delta into `player_xp`, gated by `DEFCON_MAGNIFIER_WEIGHT`.)

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
