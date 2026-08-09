# Architectural Decision Record: A fixture-context DefCon magnifier

**Decision ID:** ADR-097
**Date:** 2026-08-28 (design gate) · **refined + built 2026-08-30 (Sprint 129)**
**Status:** Accepted — **refined to the "delta" approach + built wired-dormant (`DEFCON_MAGNIFIER_WEIGHT = 0`);
calibrate at GW1 on real DefCon returns.**
**Superseded By / Replaces:** extends the **one xP metric** (`decision_xp`/`player_xp`, ADR-041) with a
**fixture magnifier on the DefCon points *already in the baseline*** — a **modelling** change, not a lens
(ADR-057 still governs crowd/price/media). Builds on the DefCon reliability lens (ADR-018), the clean-sheet
solidity lens (ADR-019), the FDR/Elo strength model (ADR-004/005/010), and mirrors the **no-double-count**
insight from the set-piece term (ADR-096). No betting odds (deferred, ADR-093 — a proxy suffices).

> **⚠️ Refinement (Sprint 129 build).** The original gate proposed *adding* a new **DefCon-xP component**. Building
> it surfaced the double-counting trap: a player's historical baseline (`total_points`) **already includes** their
> DefCon points. So the build instead **re-weights the DefCon portion already in the baseline by fixture** — a
> **delta** `defcon_pts_per_match × (magnifier − 1)`, which is **0 at a neutral magnifier** (naturally dormant, no
> double-count). §1–§2 of the Decision below are updated to this delta approach; everything else stands.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

**Owner idea:** a transferred player won't return the same at a new team, and **defensive contribution (DefCon)
points depend on the fixture**. FPL awards **2 pts/match** for clearing a defensive-actions threshold (DEF 10,
MID/FWD 12 CBIT[+recoveries]; ADR-018). A player defends **more** when their team is **under pressure** (a strong
opponent, a clean sheet *unlikely*) → more actions → more likely to clear the threshold; **less** when their team
dominates a weak opponent. The owner's worked examples (using clean-sheet odds as the opposition-strength proxy):

- **Spurs v Coventry** — Spurs' clean sheet ~evens (likely) → Sensei's DefCon **less** likely → magnifier ~**0.5–0.75**.
- **Arsenal v Spurs** — Spurs' clean sheet ~3/1 (unlikely) → Sensei's DefCon **more** likely → magnifier ~**1.25–1.5**.

**Verified from the code + data:**
- `defcon_per90` is populated (**363/573** players, last-season rate); `defcon_reliability` (ADR-018) already
  ranks by `per90 − threshold`. `xgc` is stored; `defensive_solidity` (ADR-019) ranks clean-sheet prospect by
  xGC/90. FDR/Elo give per-fixture opponent strength. → **a clean-sheet-probability *proxy* exists without
  betting odds.**
- **⚠️ The baseline ALREADY includes DefCon points.** `decision_xp` uses a `total_points`-based rate, and
  `total_points` covers defensive-contribution points. So *adding* a separate DefCon-xP component would
  **double-count** — instead the magnifier **re-weights the DefCon share already in the baseline** (the delta,
  above). No new "component" is added to the total; only its fixture *distribution* is adjusted.
- **⚠️ A key subtlety — clean sheets and DefCon pull opposite ways.** Clean-sheet points (4 pts, DEF/GK) are
  **more** likely vs a *weak* opponent; DefCon points (2 pts, all outfield) are **more** likely vs a *strong*
  one. So the same "clean-sheet proxy" magnifies the two components **inversely** — they must not share one
  multiplier.
- **⚠️ The transferred-player problem** is the ADR-096 double-counting issue again: `defcon_per90` reflects the
  player's **old team's** defensive share, so a mover to a stronger/weaker side is mis-priced at the **team**
  level — the fixture magnifier addresses the *opponent*, not the *new team's* baseline share.

#### Decision Drivers
- **Model a real, fixture-dependent effect** the owner correctly identified.
- **No betting odds** — use the FDR/xGC/Elo proxy (odds are auth-walled + a lens→xP line, ADR-093).
- **Don't conflate clean-sheet and DefCon** — they respond oppositely to opponent strength.
- **Calibrate on real data** — DefCon is a new-season scoring element; magnitudes need GW1+ returns.
- **Ship safely** — wired-dormant + an invariance pin (the ADR-096 pattern), auditable when active.
- **One xP metric** (ADR-041); a **modelling** change, not a lens (ADR-057).

---

### ✅ Decision

**Re-weight the DefCon points already in the baseline by fixture — a delta, gated by `DEFCON_MAGNIFIER_WEIGHT`
(default 0), wired-dormant + auditable; calibrate at GW1. Built this sprint (US-318/319).**

**1. The DefCon points per match (the portion to re-weight).** `defcon_points_per_match(player) ≈ 2 · P(clear
threshold)`, where `P(clear)` maps `defcon_per90` vs the position `THRESHOLD` (DEF 10 · MID/FWD 12; ADR-018) to a
probability (`clamp(0.5 + (per90 − threshold) / DEFCON_P_SCALE, 0, 1)`; GK/no-data → 0). This estimates the DefCon
share the baseline already prices — it is **not added** to xP; it is what the magnifier scales.

**2. A fixture magnifier from a clean-sheet proxy → a delta.** Per fixture, `defcon_magnifier(difficulty)` maps
the player's **FDR difficulty** (a clean-sheet-probability proxy — strong opponent = high difficulty = more
defending) to a multiplier in the owner's band (~**0.5–1.5**; neutral at mid-difficulty), **no betting odds**.
The effect on xP is a **delta**, not a replacement:
`defcon_delta = Σ_fixtures weight · defcon_points_per_match · DEFCON_MAGNIFIER_WEIGHT · (magnifier(d) − 1)`,
added to xp. At `magnifier = 1` (or weight 0) the delta is **0** → xP unchanged (no double-count, dormant).
*(A clean-sheet-xP magnifier would take the **opposite** direction — CS more likely vs weak opponents — a
separate multiplier, deferred.)*

**3. The transferred-player caution.** The fixture magnifier fixes the *opponent* context, not the *new team's*
baseline defensive share. Recorded as a known limit; a **team-level defensive-share adjustment** (scale
`defcon_per90` by the new team's expected possession/defensive load vs the old) is a **deferred** extension —
mirroring the ADR-096 "history doesn't capture the new context" guard.

**4. Wired-dormant + auditable.** `config.DEFCON_MAGNIFIER_WEIGHT = 0` (like `SET_PIECE_WEIGHT`) → the delta is 0
and `decision_xp` is byte-identical until turned on (an invariance test pins it). When active, the net delta is a
grounded number (a `defcon_xp` field on the row + a weight-aware "🛡 DefCon fixture edge (+X)" explanation reason),
so a narrated figure verifies (ADR-037/089).

**5. A modelling change, not a lens.** It alters `decision_xp` (like form/xMins/set-pieces); ADR-057's lens rule
(crowd/price/media never touch xP) is unchanged and stays tested.

**6. GW1 calibration.** At GW1+: fit the `P(clear)` mapping and the magnifier band to **real DefCon returns**
(do magnified picks beat the flat ones?), and set the weights. Preseason there's no in-season DefCon data to fit
— hence the gate.

---

### 🔀 Alternatives Considered

- **Use betting clean-sheet odds directly.** Rejected — auth-walled + crosses the lens→xP line (ADR-093); the
  FDR/xGC/Elo proxy captures the same opposition-strength signal from data we already ingest.
- **One shared "clean-sheet" multiplier for all defensive points.** Rejected — clean-sheet and DefCon points move
  **oppositely** vs opponent strength; a single multiplier would help one and hurt the other.
- **A flat DefCon-xP with no magnifier.** A reasonable first step, but it misses the owner's core insight (the
  fixture *is* the signal); the magnifier is the point.
- **Build it now (preseason).** Rejected — no in-season DefCon returns to calibrate the mapping or the band;
  guessed magnitudes could worsen picks. Gate now, build + calibrate at GW1.
- **Ignore the transferred-player effect.** Rejected as a *silent* omission — recorded as a known limit with a
  deferred team-share adjustment, so the magnifier isn't over-claimed.

---

### 🧭 Consequences

**Positive**
- A principled way to reward the owner's insight (DefCon rises vs strong opposition), from **data we already
  have** (no odds), kept **auditable** and **off by default** until calibrated.
- Names the two traps up front — the **opposite-direction** clean-sheet/DefCon effect and the
  **transferred-player** baseline — so the eventual build avoids them.
- Stays inside one xP metric (ADR-041) and the wired-dormant precedent (ADR-096); the lens invariant holds.

**Negative / risks (mitigations)**
- **A proxy, not odds** — the clean-sheet probability is modelled, not market-implied. *Mitigation:* it's the
  same strength signal FDR uses; calibrate the band at GW1; a proxy avoids the odds ToS/lens problems.
- **DefCon-xP modelling is itself new** (a `P(clear)` mapping from a per-90 rate). *Mitigation:* tier-aware +
  gated + GW1-calibrated; ship dormant.
- **The transferred-player effect is only partly addressed** (opponent, not new-team share). *Mitigation:*
  documented; a team-share adjustment is a named deferred extension.
- **New-season data dependency.** *Mitigation:* the whole thing is gated to GW1 by design.

---

### 🧾 Status & follow-ups

- **Built wired-dormant (Sprint 129, US-318/319):** `analytics/defcon_xp.py` (`defcon_points_per_match` +
  `defcon_magnifier`) + the **delta** wired into `player_xp` behind `config.DEFCON_MAGNIFIER_WEIGHT = 0` (an
  invariance test pins "weight 0 → xP byte-identical"); `defcon_xp` on the row + a weight-aware "🛡 DefCon fixture
  edge" reason.
- **GW1 calibration:** set `DEFCON_MAGNIFIER_WEIGHT`, tune `DEFCON_P_SCALE` (the P(clear) mapping) + the magnifier
  band, and **backtest** on real DefCon returns (do magnified DefCon defenders beat the flat ones vs strong
  opponents?).
- **Deferred:** a team-level defensive-share adjustment for transfers; a separate clean-sheet-xP magnifier (the
  opposite direction); an Elo/xGC proxy refinement beyond FDR; a betting-odds input (unnecessary — the proxy
  suffices).
