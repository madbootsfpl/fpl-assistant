# Sprint 263: A candidate that works, and does not clear the bar

**Dates:** 2026-09-17
**Status:** ⏳ **ADR-204 — measured, not shipped.** 1832 tests (unchanged), ruff clean. No production change.

---

## The job

Run the gate ADR-202 set. Its own premise test had been a **false negative** — the substitute was better on
owned players but a dead heat board-wide, and the ranking is board-wide — so the gate was specific: **build a
forecaster better board-wide, then re-score the ranking.**

ADR-202 also left a diagnosis, so this had a candidate rather than a guess: the weak part is the **historical
fallback**, which the model reaches for whenever a player misses even one completed gameweek.

---

## The candidate

ADR-173's rule is all-or-nothing by design — *played every completed gameweek, or fall back to last season* —
and the worry behind it is real: two gameweeks cannot tell a rested player from one being phased out.

Shrinkage answers that worry **continuously** instead of categorically:

```
share = (n · this_season + k · last_season) / (n + k)
```

At `n = 0` it *is* the historical share, so GW1 is unchanged; it never craters a nailed starter on one rest,
and never ignores four straight benchings either.

**It clears the gate** — board MAE **24.5 → 20.9**, start calls **73.5% → 78.8%**.

⚠️ **And it is worse on owned players** (24.0 → 25.0): the exact mirror of the substitute it replaced.
⭐ **"More accurate" is a claim about a population, and two forecasters can each be more accurate than the
other.** There is no single better minutes model here to point at.

---

## The verdict: it does not clear the bar

| weight | ρ | MAE | hit@20 | vs live |
|---|---|---|---|---|
| xMins v0 | 0.605 | 1.23 | 0.17 | — |
| blend, k=1 | 0.621 | 1.14 | 0.26 | **+0.4 SE** |

**§B0's bar is +1 SE. Not shipped.** Every other criterion improves and the gain is monotone across three
values of `k`. ⭐ *The bar exists precisely to stop four gameweeks of movement in the right direction from
becoming a change.*

---

## ⭐⭐ What is recorded and not acted on

hit@20 went **14 → 21 hits in 80 slots** (+2.1 SE), improving in **all three rounds where the forecasters
differ at all**. Top-20 mean return rose **4.11 → 4.94** — +20% per recommendation slot.

Against ADR-202's oracle, that is **93% of the oracle's top-of-board gain on 8% of its ρ gain.**

⭐⭐ **Better minutes is worth far more at the top of the board than across it** — and the top is the only
part a recommendation reads.

⚠️ ADR-190 declined a term whose `hit@10` rose while ρ fell. The same discipline has to apply when the
secondary is the flattering one: ⭐ *a rule that only binds when it agrees with you is not a rule.*

---

## 🔁 And it re-aims ADR-192

| | cold-start in top 20 | top-20 mean points |
|---|---|---|
| xMins v0 | 1 | 4.11 |
| ADR-192's demotion | 0 | 4.26 |
| **blend** | **3** | **4.94** |

The blend puts **more** no-history players in the top 20 and the recommendations get **better**.

⭐⭐ **The variable ADR-192 identified was "no history"; the variable that matters is "not playing", and they
are not the same players.** Affengruber had no career *and had just played 90 minutes* — ADR-192's rule
demotes him, the blend does not, and the blend is right. ⭐ *A correct complaint can name the wrong variable,
and the fix aimed at the named variable will underperform the fix aimed at the real one* — by 5× here.

---

## 📅 The GW8 rule, written before the data exists

Ship if **ρ ≥ +1 SE**, or **hit@20 ≥ +2 SE with ρ not falling**, both across ≥2 adjacent `k`.

The second clause is a deliberate widening of §B0 with an argued reason: §B0 was written to decide whether to
switch on a **dormant term**, where a whole-board ρ is the right question. This replaces the internal method
of a term already on and already earning 2.9 SE — and the oracle decomposition predicting a top-of-board
concentration was run *before* this result existed. ⭐ **The reason is independent of the outcome, which is
the only thing that makes it admissible.**

⚠️ `k` gets re-fitted at GW8, never carried over: ⭐ *a parameter selected on the data it is tested on has
already spent some of its result.* If neither clause is met, **Phase 1 is declined for the season.**

---

## 💡 The lesson

⭐ **Writing the next decision's rule is the work, when this decision is "not yet".** A hold with no rule is
a hold that gets re-argued from scratch in five weeks, by which point the result will be known and the rule
will be chosen to fit it.

---

## Definition of Done

- ✅ **Tests** — no production code changed, so no new guards; the deliverable is a decision. 1832 passed,
  ruff clean.
- ✅ **Manual smoke** — all four spikes run end to end against live `data/fpl.db`
- ✅ **Docs** — ADR-204 + index row, Roadmap, PROJECT_STATUS, this sprint doc

**Next:** nothing on the ML track until GW8. The queue returns to the product.
