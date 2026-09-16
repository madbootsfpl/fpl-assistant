# Architectural Decision Record: The Phase 1 gate — a candidate that works, and does not clear the bar

**Decision ID:** ADR-204
**Date:** 2026-09-17
**Status:** ⏳ **HELD — measured, not shipped. The candidate improves every criterion and fails the
pre-registered one.** Re-decided at the GW8 review with a rule written *below*, before the data exists.
**1832 tests (unchanged), ruff clean. No production code changed.**
**Superseded By / Replaces:** Runs the gate [ADR-202](./ADR-202-the-minutes-baseline.md) set. Re-aims
[ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md)'s concern at a better variable. Would replace
[ADR-173](./ADR-173-minutes-you-have-actually-played.md)'s all-or-nothing rule if it ships.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

ADR-202's premise test was a **false negative**: its substitute forecaster was 15% better on *owned* players
but a dead heat board-wide (24.6 vs 24.5), and the ranking is board-wide. ⭐ *A substitute that is not better
on the population being scored cannot test whether better helps.* The gate it left was specific — **build a
forecaster that is better board-wide, then re-score the ranking.**

It also left a diagnosis, so this had a candidate rather than a guess: the weak part is the **historical
fallback** (32.1 MAE against the in-season term's 20.0 on the *same* players), which `in_season_share` reaches
for whenever a player missed even one completed gameweek — 35–52 of ~190 owned players a round.

---

### 🎯 The candidate: shrinkage instead of a switch

ADR-173's rule is all-or-nothing **by design**: *played every completed gameweek with minutes in each, or fall
back to last season.* That refusal answers a real worry — two gameweeks cannot tell a rested player from one
being phased out.

Shrinkage answers the same worry **continuously** rather than categorically:

```
share = (n · this_season + k · last_season) / (n + k)
```

`k` is the prior strength in gameweeks. At `n = 0` it *is* the historical share, so nothing changes at GW1; it
never craters a nailed starter on one rest, and it never ignores four straight benchings either.

**It clears the gate.** Board-wide minutes accuracy, walk-forward:

| forecaster | board MAE | bias | start call | owned MAE | owned start |
|---|---|---|---|---|---|
| xMins v0 (today) | 24.5 | +11.7 | 73.5% | **24.0** | **70.1%** |
| **blend, k=1** | **20.9** | +4.6 | **78.8%** | 25.0 | 68.5% |
| blend, k=2 | 22.7 | +5.4 | 74.8% | 26.4 | 66.7% |

⚠️ **And it is worse on owned players** — the exact mirror of the substitute it replaced. ⭐ **"MORE ACCURATE"
IS A CLAIM ABOUT A POPULATION, AND TWO FORECASTERS CAN EACH BE MORE ACCURATE THAN THE OTHER.** Neither
candidate dominates; there is no single "better minutes model" here to point at.

---

### 📊 The gate, scored — and the verdict

| weight | ρ | MAE | hit@20 | vs live |
|---|---|---|---|---|
| xMins v0 (today) | 0.605 | 1.23 | 0.17 | — |
| **blend, k=1** | 0.621 | **1.14** | **0.26** | **+0.016 = +0.4 SE** |
| blend, k=2 | 0.617 | 1.14 | 0.25 | +0.011 = +0.3 SE |
| blend, k=3 | 0.613 | 1.15 | 0.25 | +0.007 = +0.2 SE |

**§B0's bar is +1 SE on ρ. This is +0.4 SE. It does not clear, and it is not shipped.**

Every other criterion moves the right way — MAE improves, hit@20 improves, the gain is monotone across three
adjacent values of `k`. **That is not enough.** ⭐ *The bar exists precisely to stop four gameweeks of
movement in the right direction from becoming a change.*

---

### ⭐⭐ The structural finding, recorded and not acted on

hit@20 moved **0.175 → 0.263**: **14 → 21 hits in 80 slots**, +2.1 SE unpaired, and it improved in **all three
rounds where the two forecasters differ at all** (GW1 is identical by construction, `n = 0`). Top-20 mean
return rose **4.11 → 4.94**, +20% per recommendation slot.

Against ADR-202's oracle — perfect minutes reaches hit@20 **0.28** and ρ **0.811** — the blend captures
**93% of the oracle's top-of-board gain on 8% of its ρ gain.**

⭐⭐ **BETTER MINUTES IS WORTH FAR MORE AT THE TOP OF THE BOARD THAN ACROSS IT** — and the top of the board is
the only part a recommendation reads.

⚠️ **This is reported, not used.** ADR-190 declined a term whose `hit@10` rose while ρ fell, on the grounds
that *treating it as the answer would be choosing the metric after seeing the curve*. The same discipline
applies when the secondary is the flattering one — ⭐ *a rule that only binds when it agrees with you is not a
rule.* What it earns is a **pre-registered place in the next decision**, below.

---

### 🔁 What this says about ADR-192

ADR-192 proposed demoting players with **no past seasons**. ADR-202 declined it: ρ fell at every value, and
the one real harm was n = 1.

The blend targets **low observed minutes this season**, whatever the player's history — and the two rules
disagree about who to demote:

| | cold-start players in top 20 | top-20 mean points |
|---|---|---|
| xMins v0 | 1 | 4.11 |
| ADR-192's demotion (0.8) | 0 | 4.26 |
| **blend, k=1** | **3** | **4.94** |

The blend puts **more** no-history players in the top 20 and the recommendations get **better**.
⭐⭐ **THE VARIABLE ADR-192 IDENTIFIED WAS "NO HISTORY"; THE VARIABLE THAT MATTERS IS "NOT PLAYING", AND THEY
ARE NOT THE SAME PLAYERS.** Affengruber had no career *and had just played 90 minutes* — ADR-192's rule
demotes him, the blend does not, and the blend is right. ⭐ *A correct complaint can name the wrong variable,
and the fix aimed at the named variable will underperform the fix aimed at the real one* — by 5× here
(+0.83 vs +0.15 points per top-20 slot).

**ADR-192 stays Proposed and its own remedy is now second choice to this one.**

---

### 📅 The GW8 rule — pre-registered now, before the data exists

⚠️ Written before GW8 is played, because the whole value of a threshold is that it was set without knowing
which side of it the answer falls on.

**Ship the blend if, on ≥8 gameweeks:**
1. **ρ gain ≥ +1 SE** (§B0's existing primary, unchanged), **or**
2. **hit@20 gain ≥ +2 SE *and* ρ does not fall**, with both holding across ≥2 adjacent values of `k`.

Clause 2 is new and it is a **deliberate, argued widening of §B0, not a loophole**: §B0's criteria were
written to decide whether to switch on a **dormant term**, where a whole-board ρ is the right question because
the term touches the whole board. This is a different class of change — **replacing the internal method of a
term that is already on and already earning 2.9 SE** — and ADR-202's oracle decomposition, run *before* this
result existed, already showed the gain concentrating at the top of the board. The reason is independent of
the outcome, which is the only thing that makes it admissible.

⚠️ **`k` must be re-fitted on the 8 gameweeks, not carried over.** It was chosen here by board-wide MAE on the
same four rounds this then scored — ⭐ *a parameter selected on the data it is tested on has already spent
some of its result.*

**If neither clause is met at GW8, Phase 1 is declined for the season** and the ceiling stands as a measured
fact rather than an open question. ⭐ *A decline needs a date the same way a feature does.*

---

### 📊 Consequences

**Good:** the gate is executed rather than deferred, with a real candidate and a real number. Phase 1 is now a
decision waiting on evidence rather than on effort. ADR-192 has a better-aimed successor.

**Costs / limits:**
- ⚠️ **Holding has a price and it should be named:** if the effect is real, eight weeks of recommendations are
  ~0.8 points per top-20 slot worse than they need to be. The alternative is shipping on four gameweeks.
- The blend is worse on owned players. If it ships, that regression ships with it and needs stating.
- GW1 is unchanged by construction (`n = 0`), so three rounds carry the entire result.
- ⚠️ GW4 was anomalous for every forecaster in ADR-202, and it is one of the three.

---

### 🔗 Links

- [ADR-202](./ADR-202-the-minutes-baseline.md) — the baseline, the ceiling, and the gate this runs
- [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — the all-or-nothing rule this would replace
- [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) — the concern, re-aimed
- [ADR-190](./ADR-190-the-gw4-sitting.md) — why the flattering secondary is recorded and not used
- `spikes/204-board-wide-minutes/` — `blend.py` · `blend_on_points.py` · `hit_rate_error.py` · `does_it_fix_192.py`
