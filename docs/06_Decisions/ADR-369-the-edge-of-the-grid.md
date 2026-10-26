# ADR-369 — The edge of the grid

**Date:** 2026-10-26
**Status:** Accepted — **the decline stands**
**Closes:** the pre-registration gap ADR-367 recorded and declined to exploit
**No production code changed.**

---

## Context

ADR-367 declined Phase 1 and named one thing the rule had not anticipated:

> `k = 1` is the **edge of the grid** ADR-204 tested (1, 2, 3, 5, 8). A finer search below 1 might clear
> +1 SE. 🔴 **I have not run it, deliberately.**

The owner asked for it to be run. ⭐ That is the right way round: *the gap was reported rather than
quietly exploited, and the person whose decision it is decided.*

## The finer grid

Minutes accuracy improves **monotonically** as `k` falls — board MAE 25.7 → **16.1** at k = 0.1, a 37.5%
improvement, and better on owned players too (20.0 vs 22.0). ⚠️ The best value is the **smallest one
tested**, which is a boundary solution: with eight gameweeks in hand the historical term is close to pure
cost for predicting minutes.

The gate, at full precision — ⚠️ *because the decision lives in the third decimal*:

| k | ρ gain | SE | ≥ 1 SE? | hit@20 | falls? |
|---|---|---|---|---|---|
| **0.1** | +0.0392 | **+1.006** | **YES** | 0.18 | **YES** |
| 0.25 | +0.0371 | +0.952 | no | 0.19 | no |
| 0.5 | +0.0361 | +0.926 | no | 0.20 | no |
| 0.75 | +0.0340 | +0.872 | no | 0.21 | no |
| 1 | +0.0331 | +0.849 | no | 0.21 | no |

## 🔴 The decline stands, for two independent reasons

**1. Exactly one value clears, by 0.006 SE** — and §B0 requires the gain *"across ≥2 adjacent values"*.
The next value along is +0.952. ⭐ *One point on a curve touching a threshold is what the adjacency clause
was written to refuse.*

**2. That same value is the one where hit@20 falls** — 0.19 → **0.18**, and §B0's primary is stated as
*"+1 SE, across ≥2 adjacent values, MAE and hit@20 not falling."*

⚠️⚠️ And the re-fit procedure itself selects it: `k` is re-fitted on **board-wide MAE**, which is minimised
at k = 0.1 — the one value that fails the secondary conditions. *The parameter the method picks is the
parameter the gate rejects.*

## ⭐⭐ The finding: the two criteria disagree about which way `k` should go

As `k` falls, **ρ rises and hit@20 falls**: 0.21 at k = 1, 0.18 at k = 0.1. They move in opposite
directions across the whole sub-1 range.

⭐ Whole-board rank correlation wants last season thrown away; the **top twenty** does not — and the top
twenty is the only part a recommendation reads (ADR-204's own words). *A single `k` cannot satisfy both,
which is a more useful thing to know than whether one of them scraped a bar.*

📌 That is a real argument for a **different shape of model** rather than a better constant — and it is
the kind of thing the next season's gate should be written around, not this one's.

## Consequences

✅ **The gap is closed empirically.** ADR-367's decline no longer rests on a search that was not run.

📌 The harness keeps the wider grid **and the extra precision**: at GW8 the best value printed as
*"+1.0 SE"* at three decimals and was +1.006, while the next printed identically and was +0.952.
⭐ *A rounded number at a threshold is a number that has already decided for you.*
