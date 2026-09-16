# Architectural Decision Record: A start/bench call gets a margin

**Decision ID:** ADR-194
**Date:** 2026-09-16
**Status:** ✅ **Accepted — built** (2026-09-16). **1793 → 1797 tests, ruff clean.**
**Superseded By / Replaces:** Applies [ADR-144](./ADR-144-captain-margin.md)'s idiom to the one recommendation
surface that never had it. No `decision_xp` change — the XI it fields is unchanged; only what it *claims* about
that choice.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

> **Owner**, on *"Start Thomas over Konsa (higher projected xP: 2.7 vs 2.6)"*: **"Not a chance. Coventry
> shipped 5 goals last week, haven't got a point yet, whereas Arsenal have just shipped a couple. Konsa has
> been solid."**

He is right, and the instructive part is that **he did not need to dispute the number**. A **0.1 xP** gap is
one thirty-fifth of a player's weekly standard deviation (3.51, ADR-161); a *swap's* own spread is wider
still. The model cannot separate those two players — and it said so in the same voice it uses when it can.

#### Every other surface already had a margin

| surface | threshold |
|---|---|
| captain | `WHISKER 0.3` · `CLEAR 1.3` — a 0.2 lead reads *"too close to call"* (ADR-144, re-measured ADR-190) |
| transfers | `TIE_NOISE 2.0` (ADR-189) |
| chips | a 15% relative margin |
| explanation confidence | `_CLEAR_LEAD 0.8` · `_CLEAR_GAIN 3.0` |
| **lineup** | **none — any gap above zero became an instruction** |

Worse, the toss-ups were counted as **Edge**: *"✓ 2 lineup tweaks to bank more points"* presented two coin
flips as an advantage.

---

### 📊 The measurement (`spikes/194-lineup-margin/`)

500 random legal squads at **two seeds** (ADR-183), each given an arbitrary legal declared XI, recording the xP
gap of every swap the plan would actually print:

| | seed 3 | seed 17 |
|---|---|---|
| p25 | 1.00 | 1.10 |
| **median** | **1.80** | **1.80** |
| p75 | 2.80 | 2.90 |
| p90 | 3.67 | 3.70 |
| swaps within 0.3 | **10%** | **10%** |

⭐ **The advice is usually good.** A typical swap is worth 1.8 xP, which is real information, and muting the
lot would be the opposite error. **The fault is the tail:** one call in ten is inside the noise and was
indistinguishable, in tone, from the nine that are not.

---

### 🎯 Decision

**Band the call by the measured quartiles**, exactly as ADR-144 does for the captain:

```
gap < 1.0   (≈p25)  →  "Thomas or Konsa — too close to call (2.7 vs 2.6); your call"
1.0 – 2.8           →  "Start A over B (higher projected xP: … )"
gap ≥ 2.8   (≈p75)  →  "… — a clear gap"
```

**The plan still fields the higher-xP player** — it has to field someone, and the optimiser is unchanged.
What changes is that it stops claiming the choice is knowledge. And a toss-up **no longer counts as Edge**.

⭐ **Handing the call back is not a weaker answer, it is the honest one — and it is literally the mantra.**
*Analytics decide. Logic explains. **You make the call.*** On a 0.1 gap the manager's own information — who
looked fit, who is rotation risk, whose club shipped five last week — is better evidence than the model's. The
product's slogan already said whose decision this is; this surface was the one taking it away on no evidence.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the app stops spending credibility on coin flips, and the Edge block stops counting them.
  A reader who disagrees with a toss-up is now agreeing with the model, not overruling it.
* **Negative:** slightly more text on close calls, and a manager who wants to be told what to do gets a shrug
  one time in ten. That is the correct trade — ⭐ *a confident answer on a coin flip spends trust that a later,
  real recommendation needs.*
* **Risks & Mitigations:**
  - **Risk:** the constants drift by eye. **Mitigation:** a test pins them to the measured quartiles and names
    the spike, the same guard ADR-144's thresholds carry.
  - **Risk:** the distribution moves as the season matures. **Mitigation:** re-measure at the GW10 checkpoint,
    exactly as `CLEAR` moved 1.0 → 1.3 when captain margins widened (ADR-190).

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/explain.py` (`lineup_verdict`, `_lineup_reasons`, `_lineup_edge_count`),
  `tests/test_explain.py`, `spikes/194-lineup-margin/`
* **Action Items:**
  - [x] Measure the distribution at two seeds before choosing anything
  - [x] Band the wording; toss-ups name both players and hand the call back
  - [x] Toss-ups excluded from the Edge count
  - [x] Guards: a toss-up is not an instruction · a real gap is still stated plainly · the bands are the
        measured quartiles · a toss-up is not Edge
  - [x] Mutation-test every guard — four mutants, all red
  - [ ] Re-measure the quartiles at GW10 with the other single-gameweek constants

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A recommendation engine has to decide how sure it is *per surface*, and the surface nobody argued about
> is the one that never got asked.**

The captain call got a margin because it is the loudest decision in FPL and someone pushed back. Transfers got
one because a 1.7-point ranking was separating two defenders (ADR-189). Chips got one. The lineup never did —
not because anyone judged it unnecessary, but because **nobody had ever complained about a start/bench call**,
so the question of how sure it was never arrived.

⭐ The generalisable form: **an unexamined surface inherits the confidence of its loudest neighbour.** Once one
part of an app speaks with measured hedging, the parts that never got measured *sound* measured too — they are
in the same voice, the same block, under the same Confidence score.

---

### 🔗 References & Related Artifacts
- **The idiom:** [ADR-144](./ADR-144-captain-margin.md) · re-measured in [ADR-190](./ADR-190-the-gw4-sitting.md)
- **The same problem in transfers:** [ADR-189](./ADR-189-two-defenders-one-bet.md)
- **The noise floor:** [ADR-161](./ADR-161-head-to-head.md) — one starter's week has sd 3.51
- **The measurement:** `spikes/194-lineup-margin/`
- **Found by:** the owner, on his own squad, third report of the same species
