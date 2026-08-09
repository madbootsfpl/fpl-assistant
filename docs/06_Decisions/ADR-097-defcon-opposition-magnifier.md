# Architectural Decision Record: A fixture-context DefCon magnifier (design gate)

**Decision ID:** ADR-097
**Date:** 2026-08-28
**Status:** Accepted — **design gate only; no code. Build at GW1 (needs real DefCon returns to calibrate).**
**Superseded By / Replaces:** would extend the **one xP metric** (`decision_xp`/`player_xp`, ADR-041) with a
**DefCon-xP component + a fixture magnifier** — a **modelling** change to the rate, not a lens (ADR-057 still
governs crowd/price/media). Builds on the DefCon reliability lens (ADR-018), the clean-sheet solidity lens
(ADR-019), the FDR/Elo strength model (ADR-004/005/010), and mirrors the **tier-guard** insight from the
set-piece term (ADR-096). No betting odds (deferred, ADR-093 — a proxy suffices).
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
- **⚠️ DefCon points are NOT in `decision_xp` today** — the recipe uses a total-points-based rate. So a magnifier
  has **nothing to scale yet**: a **DefCon-xP component is a prerequisite**.
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

**Adopt (as a design) a DefCon-xP component in the one recipe, scaled by a fixture magnifier derived from a
clean-sheet *proxy* (FDR/xGC/Elo) — wired-dormant, calibrated at GW1. This ADR is the gate; no code ships now.**

**1. A DefCon-xP component (the prerequisite).** Model per-match DefCon points as `≈ 2 · P(clear threshold)`,
where `P(clear)` maps a player's `defcon_per90` vs their position threshold (ADR-018) to a probability (a
reliable clearer → high P). Summed over the horizon fixtures, tier-aware like the scoring rate (a low-minutes
sample is untrusted). This is the number the magnifier scales.

**2. A fixture magnifier from a clean-sheet proxy.** Per fixture, a **clean-sheet probability proxy**
`cs_prob(team, opponent)` from the strength model (opponent attacking strength via FDR/Elo, team solidity via
xGC) — **no betting odds**. The DefCon magnifier is **inverse** to `cs_prob` (defend more when a clean sheet is
unlikely), clamped to a sane band (the owner's ~**0.5–1.5**): `defcon_xp' = defcon_xp · clamp(m(cs_prob),
0.5, 1.5)`. *(If/when a clean-sheet-xP component is modelled, it takes the **opposite** magnifier — CS more
likely vs weak opponents — so the two are separate multipliers.)*

**3. The transferred-player caution.** The fixture magnifier fixes the *opponent* context, not the *new team's*
baseline defensive share. Recorded as a known limit; a **team-level defensive-share adjustment** (scale
`defcon_per90` by the new team's expected possession/defensive load vs the old) is a **deferred** extension —
mirroring the ADR-096 "history doesn't capture the new context" guard.

**4. Wired-dormant + auditable.** A `DEFCON_XP_WEIGHT` / `DEFCON_MAGNIFIER` knob at neutral (like
`SET_PIECE_WEIGHT`), so `decision_xp` is byte-identical until turned on (an invariance test pins it). When
active, the DefCon component + the applied magnifier are exposed as grounded numbers (a `defcon_xp` field + an
explanation reason), so a narrated figure verifies (ADR-037/089).

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

- **Accepted as a design gate — no code.** The build is a future (GW1) sprint, gated on this ADR.
- **Build (GW1):** a DefCon-xP component (from `defcon_per90` → `P(clear)`); the `cs_prob` proxy (FDR/xGC/Elo);
  the inverse magnifier (clamped ~0.5–1.5), `DEFCON_*` knobs dormant + an invariance test; `defcon_xp` on the row
  + a grounded reason; then calibrate the mapping/band/weights on real DefCon returns.
- **Deferred:** a team-level defensive-share adjustment for transfers; a separate clean-sheet-xP component (with
  the opposite magnifier); a betting-odds input (still unnecessary given the proxy).
