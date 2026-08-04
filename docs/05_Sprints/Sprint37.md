# Sprint 037: xMins v0 — weight recommendations by expected minutes

**Dates:** 2026-08-04
**Status:** ✅ Complete (3/3 stories, retro done)
**Capacity:** ~2–3 working sessions (a gate + a small engine + wiring at the decision edge)
**Carried Over:** None (Sprint 036 closed clean)

> **Direction (owner):** *"Build xMins v0."* The highest-value deferred item — the *"assumes they
> play"* caveat under every captain / transfer / analyse answer. Assessed in Sprint 036 (US-108):
> a **lightweight, FPL-native v0** (no ML) that estimates expected minutes and **weights xP by it**,
> so nailed-on starters outrank rotation risks. The full probabilistic ML model stays Phase 5.

---

### 🔎 Verified at planning (the standing lesson — and it caught a design bug)

Probed the live DB before shaping this — and the Backlog's first-draft formula was wrong:

- **`chance_of_playing` is populated preseason** — `0` for 41 injured, `75` for 19 doubtful, `None`
  (→ assume 100%) for the rest; status counts 508 `a` / 31 `i` / 19 `d` / 7 `u` / 3 `s`. **The primary
  signal is live now.** ✅
- **`starts` is unreliable before 2022/23** — every season 2007/08–2021/22 has `starts = 0` (FPL didn't
  send the stat; the same trap as `expected_*` in ADR-027). Only **`minutes`** is reliable across
  seasons. ⚠️ **So the Backlog's "minutes / starts ratio" would divide by garbage.** **Corrected:** use
  a **minutes *share*** = `minutes / (38 × 90)` ∈ [0, 1] — minutes-only.
- **`history_past` backfill is partial** (~164 / ~568 players; Haaland/B.Fernandes have no rows yet).
  ⚠️ So xMins must **degrade gracefully** (no history → treat as nailed-on, weight 1.0), and we should
  **broaden the backfill** (idempotent, `history --backfill`) so the minutes signal actually fires.
- **Clean integration seam:** `player_xp` already has a **binary** `is_available` gate (unavailable →
  xP 0). xMins v0 is simply the **continuous** version of that gate — a weight ∈ [0, 1]. Applied at the
  **decision edge** (captain/transfer/analyse/`ask`), leaving the raw `xp` command a pure *"if they
  play"* number. *Generic core, policy at the edge.*

---

### 🧭 What's new — realism at the decision edge

Every recommendation so far quietly assumes 90 minutes. xMins v0 estimates how likely that is —
`chance_of_playing%` × a player's historical share of a full season's minutes — and **scales xP by it
in the decision layer**. A fringe player who's *available* but played 25% of last season's minutes no
longer ranks like a nailed-on starter. The raw `xp` view stays unchanged (the honest ceiling); the
realism lives where decisions are made. Lightweight, FPL-native, no ML, no new dependency.

---

### 🎯 Sprint Goal

**Objective:** A pure `availability_weight(player, history) → [0, 1]` (= `chance_factor` ×
`historical_minutes_share`, minutes-only, graceful fallbacks); a `minutes_weight` hook on `player_xp`;
wired into the decision commands so rankings weight xP by expected minutes, with the weight **shown**
and a `--no-xmins` escape hatch. The raw `xp` command stays a pure *"assumes they play"* number.

#### Success Criteria
- [ ] Approach agreed (**ADR-038**) before code — the formula, the fallbacks, **not** using `starts`,
      the `minutes_weight` hook, and the on/off policy (default-on at the decision edge)
- [ ] `availability_weight(player, history)` (pure): `chance_factor` (chance% /100; `None`→1.0; 0→0.0)
      × `minutes_share` (recency-weighted `minutes/(38×90)`, clamped [0,1]; **no history → 1.0**;
      **no `starts`, no 900-min gate** — a small sample means *low* minutes, which is the point)
- [ ] `player_xp` gains an optional `minutes_weight` callable — when passed, xP (and per-GW) scale by
      the weight; when absent, **behaviour is byte-identical** (existing 313 stay green)
- [ ] Wired into **captain / transfer / analyse / `ask`** (default-on) with a **visible weight**
      (an `xMins%` or `Mins` column/annotation) and a **`--no-xmins`** opt-out
- [ ] Broaden `history --backfill` coverage so the minutes signal fires; graceful where history is absent
- [ ] Tests (weight maths + fallbacks; `player_xp` unchanged without the hook; a rotation risk is
      demoted) + **live smoke** on TS (a fringe player drops; nailed-on holds; the ✓ trust line still
      verifies)
- [ ] Docs: ADR-038 + index, Architecture, Handbook/README, PROJECT_STATUS; Backlog/Roadmap (v0 → done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-109 | **Gate.** xMins v0 design (**ADR-038**): the formula (`chance_factor` × recency-weighted **minutes share**, minutes-only — **no `starts`**, no 900-min gate); fallbacks (no history / `chance None` → 1.0; `chance 0` → 0); the `minutes_weight` hook on `player_xp`; **policy** (default-on at the decision edge, `--no-xmins` opt-out; raw `xp` stays pure). Pressure-test on real data | Critical | ✅ Done | 0.5 session |
| US-110 | **The engine** — `src/analytics/minutes.py`: `availability_weight(player, history)` (pure); `player_xp` gains an optional `minutes_weight` callable (xP + per-GW scale by it; absent → unchanged). Unit-tested | High | ✅ Done | 1 session |
| US-111 | **Wire into the decision edge** — captain / transfer / analyse / `ask` pass the weight (default-on), show it (an `xMins`/`Mins` column or annotation), honour `--no-xmins`; broaden the backfill so it fires. Tests + live smoke + docs | High | ✅ Done | 1–1.5 sessions |

#### Technical Tasks & Maintenance
- [ ] ADR-038 recorded + added to the ADR index — _US-109_
- [ ] Update Architecture changelog (xMins v0 at the decision edge) — _US-110/111_
- [ ] Update Handbook/README (recommendations now weight xP by expected minutes) — _US-111_
- [ ] Backlog + Roadmap: mark **xMins v0 done**; the full ML model remains Phase 5 — _US-111_
- [ ] Update PROJECT_STATUS — _US-111_

---

### ✅ Definition of Done (this sprint)

The standard 3-part DoD:
1. **Automated tests pass** — weight maths + fallbacks; `player_xp` unchanged without the hook; a
   rotation risk is demoted; existing **313** stay green; no new dependency.
2. **Manual smoke test done** — on TS with xMins on, a fringe/rotation player's effective xP drops
   while nailed-on starters hold; `--no-xmins` reproduces today's numbers; `ask` still shows ✓.
3. **Documentation updated & checked** — ADR-038 + index, Architecture, Handbook, README, Backlog +
   Roadmap (v0 done), sprint board + PROJECT_STATUS.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| `availability_weight` (chance% × minutes share) | The full probabilistic ML model (congestion / European / rotation profiles) — Phase 5 |
| A `minutes_weight` hook on `player_xp` | Mutating the raw `xp` command's default output |
| Wiring at the decision edge + a visible weight + `--no-xmins` | In-season per-GW minutes blending (post-GW1, Data Hardening) |
| Broadening the history backfill | `starts`-based signals (unreliable pre-2022/23) |

**External Dependencies:** FPL `chance_of_playing_next_round` (stored as `chance`) + `history_past`
`minutes` — both already ingested; a fuller `history --backfill` broadens coverage.

---

### ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation Strategy |
|---|---|---|
| **`starts` unreliable** (planning finding) | High (would corrupt the weight) | **Minutes-only** share; `starts` explicitly unused (ADR-038) |
| Partial history → weight defaults to 1.0 for many | Med | Broaden the backfill; **no history → nailed-on** is the honest fallback (never *penalise* the unknown) |
| Blast radius — changes every recommendation's numbers | Med | Policy at the **edge** only (raw `xp` untouched); **`--no-xmins`** reproduces today; the weight is **shown**, not hidden |
| Over-penalising a genuine starter after one injury-hit season | Med | Recency-weighted over ≥1 season + clamp; a *soft* multiplier, not a gate; visible so it's checkable |
| Cameo-season absurdity (the Sprint 026 trap) | Low | xMins *wants* low minutes → low weight (the opposite failure mode to the pp90 rate); **no 900-min gate** here — stated in ADR-038 |

---

### 🗝️ Gating decision (US-109 → ADR-038)

Settle before code — the data is already pressure-tested. Proposed (confirm/redirect at "start US-109"):

1. **The weight.** `availability_weight = chance_factor × minutes_share`, each ∈ [0, 1]:
   - `chance_factor` = `chance_of_playing_next_round / 100`; **`None` → 1.0** (FPL's "no news, assume
     available"); an injured/suspended 0 → 0.0.
   - `minutes_share` = recency-weighted mean of `minutes / (38 × 90)` over the recent seasons we hold,
     clamped to [0, 1]. **Minutes-only — `starts` is unused** (unreliable pre-2022/23). **No 900-min
     gate** (unlike the xP *rate* baseline — here small minutes *should* lower the weight). **No history
     → 1.0** (treat unknowns as nailed-on; never penalise absence of data).
2. **The hook.** `player_xp(..., minutes_weight=None)` — a callable `player → [0,1]`; when passed, the
   xP total and every per-GW cell scale by it; when absent, output is **byte-identical** to today.
3. **Policy at the edge.** **Default-on** in captain / transfer / analyse / `ask` (they're
   *decisions* — realism belongs there); the raw **`xp`** command stays a pure *"assumes they play"*
   number. A **`--no-xmins`** flag reproduces today's numbers. The weight is **shown** (a column /
   annotation), never silent.
4. **Honest scope.** It's `chance% × historical minutes share`, not a per-fixture probability — say so.
   The full model (schedule/European congestion, rotation profiles) remains Phase 5.

**Worked example (to run at the gate on TS):** confirm a nailed-on premium (weight ≈ 1.0) holds its
rank while an *available-but-fringe* squad player (low minutes share) is demoted; injured (`chance 0`)
→ weight 0; a no-history player → weight = `chance_factor` (unchanged if fit).

---

### 📝 Session Progress Log

- **US-109 (gate) ✅** — Recorded **ADR-038**. The design was **pressure-tested on the live DB first**,
  and the probe corrected the Backlog's first-draft formula:
  - **`starts` is all-zeros before 2022/23** → the "minutes/starts ratio" would break; **corrected to
    a minutes *share*** = `minutes/(38×90)`, **minutes-only**.
  - **`chance_factor` validated:** injured (Timber/Saliba, chance 0) → **0.00**; **suspended**
    (Christie/Fofana, chance `None`, status `s`) → **0.00** *(so the guard keys on **status**, not just
    chance)*; doubtful (Tielemans, 75) → **0.75**.
  - **`minutes_share` sensible** where history exists (Kelleher 0.62, João Pedro 0.68, Truffert 0.99);
    the 10 un-backfilled TS players → 1.0.
  - **Coverage measured: 170/568 (29%)** have any history → **broaden the backfill in US-111**, and
    **no history → 1.0** (never penalise the unknown).
  Settled: `availability_weight = chance_factor × minutes_share` (no `starts`, **no 900-min gate** — low
  minutes *should* lower the weight); a `minutes_weight` hook on `player_xp` (absent → byte-identical);
  **default-on at the decision edge** (`captain`/`transfer`/`analyse`/`ask`) with **`--no-xmins`** and a
  visible weight, the raw **`xp`** staying pure. Honest scope stated (role-change + coverage limits →
  Phase 5). ADR-038 added to the index.
- **US-110 (the engine) ✅** — New `src/analytics/minutes.py`: `chance_factor(player)`,
  `minutes_share(history)`, `availability_weight(player, history)` — all pure, exported from the
  analytics package. `player_xp` gains an optional `minutes_weight` callable — when passed, the xP
  total and every per-GW cell scale by the weight, and the result carries `minutes_weight`; **when
  absent, byte-identical** to today (the raw `xp` view stays pure). **19 unit tests** (chance
  None→1.0 / status i·s·u→0 / doubtful→fraction; minutes share capped, recency-weighted, last-k-only,
  no-history→None, no 900-min gate; the weight product; the `player_xp` hook scales + is unchanged
  without it) → suite **313 → 332**; ruff clean; no new dependency. **Real-data composition check:**
  with the hook, Kelleher 19.6 → 12.1 (0.62) and João Pedro 28.7 → 19.5 (0.68) are demoted while
  Haaland/B.Fernandes hold (no history → 1.0 — the coverage gap US-111 addresses via backfill).
- **US-111 (wire into the decision edge) ✅** — A shared `minutes_weight_from_history(history_by_code)`
  closure; `captain`/`transfer`/`analyse`/`ask` pass it **default-on** (the raw `xp` command untouched),
  with a **`--no-xmins`** opt-out on the three commands. Per Tony's steer, the weight is **shown as
  expected minutes** (`expected_minutes = round(weight × 90)`): an `xMins` column in captain + analyse,
  a footer note on transfer; `--no-xmins` drops the column and reproduces the raw table.
  `captain_picks` + `analyse_squad` thread the weight (`weight_by_id`); `ask` reuses them (analyse
  table shows the column, ✓ trust line intact). **Backfill broadened 29% → 87%** (499/568; the rest are
  genuinely new players → 1.0). **+11 tests** (weight closure + `expected_minutes`; captain demotion +
  column; analyse column + carry; `--no-xmins` parses) → suite **332 → 343**; ruff clean; no new
  dependency. **Live smoke on TS:** captain re-ranks (raw Haaland 6.9 #1 → weighted B.Fernandes tops,
  Haaland 74 mins); analyse projects 278 → 209 with Ampadu flagged at **41 mins**; transfer now targets
  Ampadu for removal; `ask` captain + analyse stay grounded (✓); `--no-xmins` reproduces the raw numbers.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories. **US-109** — ADR-038, the design pressure-tested (and corrected)
  on live data. **US-110** — `analytics/minutes.py` (`chance_factor`, `minutes_share`,
  `availability_weight`) + a `minutes_weight` hook on `player_xp` (byte-identical without it).
  **US-111** — wired **default-on** into captain/transfer/analyse/`ask`, shown **as expected minutes**
  with a `--no-xmins` opt-out; the raw `xp` command untouched; backfill broadened 29% → 87%. Tests
  313 → **343**; one ADR; **no new dependency**.
* **Carried Forward:** None. The full probabilistic model is Phase 5 (post-GW1).
* **Key Artifacts / Decisions:** ADR-038; `availability_weight` + `minutes_weight_from_history` +
  `expected_minutes`; the `minutes_weight` hook; `--no-xmins`; the `xMins` column (captain/analyse).

#### Retrospective
* **What Went Well?**
  - **Planning caught a real bug before code — twice.** The live probe proved `starts` is all-zeros
    pre-2022/23 (so the Backlog's "minutes/starts ratio" would have divided by garbage → corrected to a
    minutes *share*), and that suspended players carry `chance = None` (so the availability guard must
    key on *status*). The standing lesson paid for itself again.
  - **Policy at the edge kept the blast radius tiny.** xMins is the continuous version of a gate that
    already existed; the raw `xp` view is byte-identical and every prior test stayed green.
  - **It visibly changes recommendations** — captain re-ranks, analyse projects a truer 209 (Ampadu at
    41 mins), transfer targets the rotation risk. And the ✓ trust line held, so `ask` stays grounded.
  - **Tony's "show minutes, not 0.65" made it land** — `56`/`80`/`74` reads instantly; the fraction
    wouldn't have.
* **What Could Be Improved?**
  - **Role change is the honest v0 limit** — Haaland's history (past injuries) weights him to 74 mins,
    demoting him below B.Fernandes for captaincy. Defensible, but debatable for a nailed-on premium;
    `--no-xmins` is the escape hatch and Phase 5 (in-season minutes) is the real fix.
  - **Coverage still isn't 100%** — 87% after the backfill; genuinely new players sit at 1.0 (honest,
    but they get no rotation signal until they have history).
* **Lessons Learned?**
  - Verify a data assumption on the real table before you build on it — `starts` looked fine and wasn't.
  - Generalise the seam you already have (a binary gate → a [0,1] weight) rather than bolting on a
    parallel path; the default-off hook makes the change provably safe.
  - Show a model's number in the unit the user thinks in (minutes), and give them the off-switch.
* **Action Items for Next:**
  - [ ] (Backlog) The full probabilistic xMins (congestion / European / rotation profiles) — Phase 5,
    post-GW1; needs in-season per-GW minutes + external fixture data.
  - [ ] Consider a gentle floor/telemetry on the role-change case once in-season data lands.
  - [ ] Keep the gate + 3-part DoD.

---

**Proposed follow-on:** owner to steer — more Phase 4, the web UI (Phase 2), or wait for GW1 to do Data
Hardening (which also feeds the full Phase-5 xMins). All live.

**Completion Date:** 2026-08-04
**Final Notes:** The "assumes they play" caveat under every recommendation is now addressed at the
decision edge — visibly, reversibly, and grounded. Instruct-free realism: the analytics still decide,
the numbers just got more honest. Sprint outcome: **Successful** — 3/3 stories, zero roll-over, DoD
held (37th).
