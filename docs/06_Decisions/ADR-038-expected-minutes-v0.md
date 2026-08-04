# Architectural Decision Record: Expected minutes (xMins) v0 — weight recommendations by playing time

**Decision ID:** ADR-038
**Date:** 2026-08-04
**Status:** Accepted
**Superseded By / Replaces:** Generalises the binary `is_available` gate (ADR-006) into a continuous
weight; the lightweight first step of the two-step xMins plan (Sprint 036, US-108). The full
probabilistic model remains Roadmap Phase 5.
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Every recommendation so far — `captain`, `transfer`, `analyse`, and `ask` — quietly assumes a player
plays the full 90 minutes. xP is a per-90 rate projected over a fixture horizon; a player who is
*available* but only a rotation option is ranked exactly like a nailed-on starter. "Assumes they play"
is the standing caveat under the whole decision layer, and rotation/minutes is the single biggest
source of FPL variance.

xMins **v0** is the lightweight, FPL-native fix: estimate a player's **expected minutes** from data we
already hold, express it as a weight ∈ [0, 1], and **scale xP by it at the decision edge** so nailed-on
starters outrank rotation risks. No machine learning, no new dependency.

#### A planning probe pressure-tested the design on real data — and corrected it

1. **`chance_of_playing` is populated preseason.** `0` for 41 injured, `75` for 19 doubtful, `None`
   (→ assume 100%) for the rest; status counts 508 `a` / 31 `i` / 19 `d` / 7 `u` / 3 `s`. The primary
   signal is live now. On a worked example: J.Timber/Saliba (`i`, chance 0) → factor **0.00**;
   Christie/Fofana (`s`, chance **None**) → **0.00** *(suspended players carry no 0 chance — so the
   guard must key on **status**, not just chance)*; Tielemans (`d`, 75) → **0.75**.
2. **`starts` is unreliable before 2022/23.** Every season 2007/08–2021/22 has `starts = 0` (FPL didn't
   send the stat — the same trap as `expected_*` in ADR-027). **So the original Backlog sketch ("minutes
   / starts ratio") would divide by garbage.** Corrected: use a **minutes *share*** = `minutes / (38 ×
   90)` — **minutes-only**, the one field reliable across every season.
3. **History coverage is partial** — only **170 / 568 players (29 %)** have any `history_past`. So the
   weight must **degrade gracefully** (no history → 1.0, nailed-on) and the backfill should be broadened
   so the signal actually fires (US-111). Worked example on TS: Kelleher 0.62, João Pedro 0.68,
   Truffert 0.99 where history exists; the 10 un-backfilled players default to 1.0.

#### Decision Drivers
- **More correct by default** — realism where decisions are made.
- **Lightweight & FPL-native** — data we already hold; no ML, no new dependency (the project's ethos).
- **Generic core, policy at the edge** — the raw `xp` view stays a pure "if they play" number.
- **Honest & visible** — show the weight; state exactly what it is (and isn't).
- **Robust to the known traps** — no `starts`; graceful on missing history; the cameo-minutes case
  helps here rather than hurting.

---

### ✅ Decision

**1. The weight.** A pure `availability_weight(player, history) → [0, 1]`:

```
availability_weight = chance_factor × minutes_share
```

- **`chance_factor`** = `chance_of_playing_next_round / 100`, clamped [0, 1]; **`None` → 1.0** (FPL's
  "no news, assume available"). **Guard on status first:** `i` (injured) / `s` (suspended) / `u`
  (unavailable) → **0.0** — suspended players show `chance = None`, so status is the reliable gate.
- **`minutes_share`** = a **recency-weighted** mean of `minutes / (38 × 90)` over the recent seasons we
  hold (newer seasons weigh more), clamped [0, 1]. **Minutes-only — `starts` is unused** (unreliable
  pre-2022/23). **No history → 1.0** (treat the unknown as nailed-on; never *penalise* absent data).
- **No 900-minute gate.** Unlike the xP *rate* baseline (ADR-028), where a tiny sample invents an
  absurd per-90 rate, here small minutes *should* lower the weight — that is the signal, not noise.

**2. The hook.** `player_xp(..., minutes_weight=None)` gains an optional callable `player → [0, 1]`.
When passed, the xP total **and every per-GW cell** scale by it; when absent, output is
**byte-identical** to today (every existing test stays green). This subsumes the binary `is_available`
gate as its continuous generalisation.

**3. Policy at the edge.** xMins is **default-on** in the *decision* commands — `captain`, `transfer`,
`analyse`, and `ask` — because realism belongs where recommendations are made. The raw **`xp`** command
stays a pure *"assumes they play"* number (the honest ceiling, still comparable). A **`--no-xmins`**
flag reproduces today's numbers. The weight is **shown** (a column / annotation), never silent.

**4. Honest scope.** It is `chance% × historical minutes share`, **not** a per-fixture minutes
probability. Two limits are stated plainly:
- **Role change** — a player who has *moved into* a starting role is under-weighted by his historical
  share (e.g. a former understudy) until in-season minutes arrive.
- **Coverage** — where we hold no history, the weight is just `chance_factor`.
Both are resolved by the **full probabilistic model** (schedule/European congestion, rotation profiles,
in-season minutes) — **Roadmap Phase 5**, gated on post-GW1 data.

---

### 🔀 Alternatives Considered

- **Minutes / starts ratio (the original Backlog sketch).** Rejected at planning — `starts` is
  all-zeros before 2022/23, so the ratio is undefined/garbage for most historical seasons.
- **Mutate the raw `xp` command to be xMins-weighted by default.** Rejected — it would change the one
  clean "if they play" number and blast the change across every view. Policy belongs at the edge.
- **A binary "likely starter?" flag** (keep the existing gate, just widen it). Rejected — throws away
  the gradient; a 60 %-minutes squad player and a 95 %-minutes starter are meaningfully different.
- **Apply the 900-minute gate here too** (as the rate baseline does). Rejected — it would *ignore* the
  low-minutes players xMins exists to demote.
- **Opt-in `--xmins` (default off).** Rejected as the default — being correct-by-default matters more
  than preserving preseason numbers nobody has acted on; `--no-xmins` covers the escape hatch.

---

### 🧭 Consequences

**Positive**
- Rotation risks stop out-ranking nailed-on starters; injured/suspended players are zeroed continuously
  rather than by a separate gate.
- The realism is **visible** and **reversible** (`--no-xmins`), and the raw analytics are untouched.
- Reuses stored data (`chance`, `history_past.minutes`); no ML, no new dependency.

**Negative / risks (mitigations)**
- **Partial coverage** dilutes the signal → broaden the backfill (US-111); no-history → 1.0 is honest.
- **Role change** mis-prices a player who changed role → recency weighting + a *soft* multiplier +
  visibility; fully fixed only by in-season data (Phase 5).
- **Blast radius** across recommendations → confined to the decision edge; `--no-xmins` reproduces today.

---

### 📊 Validation

Prototyped on the live DB before code (worked example above): `chance_factor` correctly zeros
injured/suspended and halves the doubtful; `minutes_share` is sensible where history exists
(Kelleher 0.62, João Pedro 0.68, Truffert 0.99); missing history degrades to 1.0. Coverage measured at
29 % → backfill broadened in US-111. Acceptance for the sprint: on TS with xMins on, a fringe/rotation
player's effective xP drops while nailed-on starters hold, `--no-xmins` reproduces today's numbers, and
`ask` still shows the ✓ trust line.
