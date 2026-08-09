# Sprint 126: A gated set-piece xP term (wired-dormant, calibrate at GW1)

**Dates:** 2026-08-27 (planned)
**Status:** 📝 Planned (0/2 stories · 1 ADR)
**Capacity:** ~¾ session (a **modelling** change to the one xP metric — an ADR gate + a careful, tested term)
**Carried Over:** none

> **Direction (owner):** the deferred **set-piece xP boost** — penalty/corner/FK takers have a real scoring
> edge; reflect it in `decision_xp`. The one genuine *analytics* improvement left (a "understand `decision_xp`"
> arc), so it's **ADR-gated**; ship it **wired-dormant** and calibrate at GW1.

---

### 🔎 Verified at planning (on real data + the code)

- **The data is there** (ADR-081): `penalties_order` / `corners_order` / `freekicks_order` are ingested;
  `crowd.set_piece_flags` already flags #1 takers (⚽/🚩/🎯) as a *display lens*.
- **Where a term slots:** `decision_xp → player_xp` builds a per-90 **rate** (a trusted ≥900-min **baseline**,
  else a shrunk **fallback**, else current `ppg`), then blends **form** into that rate, then xP = weight · rate ·
  Σ fixture-multipliers. A set-piece term is naturally a **rate adjustment**, exactly like the form blend.
- **⚠️ The key modelling insight — double-counting.** The baseline rate is the player's **historical pp90**,
  which **already includes their past penalty/set-piece points**. So a blanket boost **double-counts** for an
  established taker. The boost is genuinely *new* information only where the history *doesn't* capture the current
  duty — i.e. the **fallback/current** rate tiers (new signings, role changes, young players), **not** the trusted
  `hist` tier. → **the term applies only to non-`hist` tiers.**
- **The precedent to mirror:** `FORM_WEIGHT = 0` (ADR-060) — a rate term **wired dormant**, pinned by an
  invariance test (weight 0 → xP byte-identical), flipped + calibrated at GW1. The set-piece term follows the
  same shape (`SET_PIECE_WEIGHT = 0.0`).
- **This is a *modelling* change, not a lens.** ADR-057's "signals never touch `decision_xp`" governs *lenses*
  (crowd/price/media); a set-piece **xP** term legitimately alters the metric (like form/xMins) — a different
  category, recorded as such.

---

### 🎯 Sprint Goal

**Objective:** a principled, **gated** set-piece term in the one `decision_xp` recipe — restricted to the rate
tier where it doesn't double-count, **off by default** (no change today; an invariance test pins it), and made
**transparent** (the contribution is explainable + grounded when active). Calibrate the weight at GW1.

#### Success Criteria
- [ ] **ADR-096 (the gate)** — record: the term = a **rate bonus** from set-piece duties (pens > corners/FK),
      applied **only to the fallback/current tiers** (avoids double-counting the `hist` baseline);
      `SET_PIECE_WEIGHT = 0.0` **wired-dormant** (ADR-060 pattern); a **modelling** change (not a lens, ADR-057);
      the invariance-at-0 pin; the GW1 calibration/backtest plan; the honest limits.
- [ ] **US-313 (the term)** — a pure `set_piece_bonus(player) -> float` (from `penalties_order`/`corners_order`/
      `freekicks_order`) + `config.SET_PIECE_WEIGHT` + the wiring in `player_xp` (rate += `SET_PIECE_WEIGHT ·
      bonus`, **non-`hist` tiers only**). Tests: **weight 0 → xP byte-identical** (the ADR-041/060 invariant); a
      positive weight **lifts a fallback-tier pen taker** and **leaves a `hist`-tier taker unchanged**; a
      non-taker unchanged.
- [ ] **US-314 (make it auditable)** — when active, the set-piece contribution is **explainable + grounded**: the
      explanation reasons gain a "⚽ on penalties — a set-piece xP edge (+X)" line and the number enters the
      **facts** so a narrated figure still verifies (ADR-037/089); a config/legend note. Dormant → nothing shown
      (no change).
- [ ] **No unintended drift** — with `SET_PIECE_WEIGHT = 0` the existing **794** stay green (xP unchanged
      everywhere); the lens invariance tests (crowd/price) still hold; ruff clean.
- [ ] Docs: PROJECT_STATUS, Architecture, README, Help, Backlog, ADR-index (+ADR-096).

---

### 🧭 Design sketch

**ADR-096.** The term is a **conservative, tier-restricted rate bonus**, gated by `SET_PIECE_WEIGHT` (default 0).
Rationale recorded: pens carry the most value (a penalty ≈ high xG), corners/FK less; the baseline already prices
an established taker's duty, so the bonus applies **only** where the rate came from `fallback`/`current` (the
history doesn't capture the role). Dormant now (invariance holds); at GW1, calibrate the weight against real
returns (a small backtest: do boosted picks beat the unboosted for role-changers?). Honest limits: it's a coarse
proxy (no per-team penalty rate), duty can change mid-season, and it must never re-double-count.

**US-313.** `analytics/setpieces.py::set_piece_bonus(player)` → e.g. `PEN·(order1) + SP·(corner1) + SP·(fk1)`
(per-90 rate units; a pure lookup over the order fields, empty-safe). In `player_xp`, after the form blend:
`if SET_PIECE_WEIGHT and rate is not None and rate_source != "hist": rate += SET_PIECE_WEIGHT · set_piece_bonus(p)`.
`config.SET_PIECE_WEIGHT = 0.0` (a documented dormant knob, mirroring `FORM_WEIGHT`). The invariance test locks
"weight 0 → identical xP"; a weight-on test proves the tier restriction.

**US-314.** Surface the contribution where the *why* is shown (ADR-089): `explain_captain`/`explain_transfer`
gain a set-piece **xP-edge** reason (with the number) **when the weight is active**, and that number joins the
`facts` (grounding, ADR-037) so a narration citing it verifies ✓. A short legend note. When dormant, no reason is
added (byte-unchanged). *(Set-piece flags already appear as a display lens, ADR-081 — this adds the xP link.)*

**Deferred:** per-team penalty-rate modelling (needs richer data); a mid-season duty-change detector; the GW1
**calibration + backtest** (set the weight on real returns); auto-detecting "newly the taker" beyond the rate
tier.

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| ADR-096 | **Gated set-piece xP term** — tier-restricted rate bonus, wired-dormant (the design gate). | High | ✅ Done | gate |
| US-313 | **The term** — `set_piece_bonus` + `SET_PIECE_WEIGHT` in `player_xp` (non-`hist` tiers); invariance. | High | ✅ Done | ~½ session |
| US-314 | **Make it auditable** — the contribution is explained + grounded when active. | High | ✅ Done | ~¼ session |

---

### ✅ Definition of Done (per feature)

1. **Tests pass** — `set_piece_bonus` scores duties (pens > corners/FK; empty-safe); with `SET_PIECE_WEIGHT = 0`
   every xP is **byte-identical** to today (the invariant); a positive weight lifts a **fallback-tier** pen
   taker's xP and **not** a `hist`-tier taker's; the explanation shows the set-piece xP edge only when active,
   with the number in the facts (grounding verifies). Existing **794** stay green; crowd/price lens invariance
   holds; ruff clean.
2. **Manual smoke** — with `SET_PIECE_WEIGHT` temporarily set, a role-changing pen taker's xP/rank rises and the
   `ask`/explanation cites the ⚽ edge (verified ✓); reset to 0 → everything is exactly as before.
3. **Docs updated** — ADR-096 + the index; PROJECT_STATUS, Architecture, README, Help, Backlog.

---

### 📝 Session Progress Log

- **ADR-096 (gated set-piece xP term — the gate)** — wrote `docs/06_Decisions/ADR-096-gated-set-piece-xp-term.md`
  (Accepted; no code). Records: the term = a **rate bonus** from set-piece duties (pens > corners/FK) added to
  the `player_xp` rate, **gated by `SET_PIECE_WEIGHT` (default 0, wired-dormant — ADR-060 pattern;
  invariance-at-0 pinned)**; the **double-counting insight** → the bonus applies **only to the fallback/current
  tiers** (`rate_source != "hist"`, since the trusted baseline already prices an established taker's pens); a
  **modelling** change (legitimately alters `decision_xp`, distinct from the lens rule ADR-057, which still holds
  for crowd/price/media); **auditable** — the contribution becomes an explanation reason + enters the grounding
  facts when active (ADR-037/089); honest limits (a coarse proxy — no per-team pen rate) + the GW1 calibration/
  backtest plan. Added to the ADR index. No tests/code (design gate) — suite unchanged at **794**.
- **US-313 (the term)** — added a pure `analytics/setpieces.py::set_piece_bonus(player)` (`PENALTY_BONUS=0.30`
  for the #1 pen taker + `SET_PLAY_BONUS=0.10` each for #1 corner/FK; only the #1 duty counts; empty-safe) +
  `config.SET_PIECE_WEIGHT = 0.0` (dormant, mirroring `FORM_WEIGHT`). Wired into `player_xp` **after the form
  blend**: `if set_piece_weight and rate is not None and rate_source != "hist": rate += set_piece_weight ·
  set_piece_bonus(p)` — the **`rate_source != "hist"` guard** is the no-double-count crux; `decision_xp` passes
  `config.SET_PIECE_WEIGHT`. Exported `set_piece_bonus`. **Verified on real data (weight 0.5):** only **3**
  fallback-tier pen takers' xP changed; **all 17 hist-tier pen takers unchanged** (0 double-counted). +7 tests
  (`tests/test_setpieces.py`: the bonus scoring; player_xp dormant-vs-active + the tier guard + non-taker;
  decision_xp invariance + activation). **The full 794 stayed byte-identical at weight 0** (invariance holds);
  ruff clean. **801** total.
- **US-314 (make it auditable)** — `player_xp` rows now carry **`set_piece_xp`** — the term's *share* of the xp
  (`weight · applied_bonus · Σ horizon multipliers`; **0.0 when dormant** or on the `hist` tier), a grounded
  per-player number. `captain_picks` now passes `set_piece_weight=config.SET_PIECE_WEIGHT` (dormant → no-op) so
  captain reflects the term and carries `set_piece_xp` via `**r`. A weight-aware `explain._penalty_reason(set_
  piece_xp)`: active (`>0`) → **"Penalty taker (+X xP set-piece edge)"** (the number is real → a narrated figure
  verifies, ADR-037); dormant/`hist` → the plain lens "Penalty taker" (byte-identical). Wired into
  `explain_captain` (via the pick) + `explain_transfer` (via the buy summary). Smoke: dormant `set_piece_xp` 0 →
  plain reason; active current-tier → `+0.3 xP` edge; hist-tier → 0 (unchanged). +3 tests. The **new row field
  didn't break any of the 801** (no strict-dict test regressed); dormant explanations byte-identical. ruff clean.
  **804** total.

---

### 🏁 Sprint Review & Retrospective

_(to be filled at "run retro and push")_
