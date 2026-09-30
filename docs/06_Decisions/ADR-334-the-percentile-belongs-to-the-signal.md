# ADR-334 — The percentile belongs to the signal, not to the event

*The price predictor had never been scored. It works — and its cut points were set from the wrong thing.*

**Date:** 2026-09-30
**Status:** Accepted
**Recalibrates:** ADR-092 (the predictor), ADR-215 (its first recalibration)
**From:** the owner, on price tracking — *"would be good to have a global pricing / prediction model"*

---

## Context

`price_prediction` has shipped since ADR-092 and been recalibrated once. 🔴 **Nobody had ever checked
whether it was right**, and the data to check it has been public all along: `element-summary/{id}/`
carries `value`, `selected`, `transfers_in` and `transfers_out` per gameweek per player — the rule's own
inputs, plus the outcome.

⭐ *A predictor nobody scores is a claim, not a feature*, and this one is printed next to a player's name
with an arrow beside it.

## What the backtest found

`spikes/210-price-backtest/`, 3,216 player-gameweeks, GW1–5, **importing the shipped functions** rather
than reimplementing them. Forecasting the following week:

| | precision | recall | base rate | lift |
|---|---|---|---|---|
| ▲ rise | 33.3% | 8.9% | 2.3% | **14.4×** |
| ▼ fall | 50.6% | 15.1% | 14.7% | **3.4×** |

⭐⭐ **It is never wrong about direction.** Not once in 3,216 rows did it call a rise that fell or a fall
that rose. Every error is *"called a move, nothing happened"*. `net transfers ÷ ownership` at 14× lift is
not a subtle pattern being teased out — it is a strong signal, conservatively applied.

## The mistake, and it was a good one

ADR-215 set the percentiles **from the observed rates**: rises happen to ~2% of players, so the 98th
percentile; falls to ~15%, so the 15th. Its own words: *"the percentiles below are those observed rates,
not a taste."*

⚠️⚠️ **That is only correct if the signal is perfect.** Matching the cut to the base rate calls exactly as
many moves as actually happen — which spends the entire budget on the very top of the distribution and
never reaches most of what moves. The rule is right about a third of the rises it names, so a bar set at
the event's own rate leaves 91% of rises unnamed.

⭐⭐⭐ **The percentile belongs to the signal's discriminating power, not to the event's base rate.**

## Decision

| | calls | precision | recall |
|---|---|---|---|
| rise @ 98th — was | 12 | 33.3% | 8.0% |
| **rise @ 95th — now** | 30 | **40.0%** | **24.0%** |
| fall @ 15th — was | 85 | 50.6% | 43.4% |
| **fall @ 25th — now** | 141 | 50.4% | **71.7%** |

The shipped pair was **dominated**, not narrowly beaten: rises get better precision *and* three times the
recall; falls hold precision and catch 1.65× as many.

⚠️ **In-sample, over five gameweeks.** The exact percentile is not to be trusted far — what is safe is
that the old point was worse on *both* axes, which tuning noise does not explain. Re-measure when the
season is longer. The definition stays and the number moves, as in ADR-210 and ADR-215.

🔴 **And nothing pinned these constants**, which is how they were wrong for a season and then suboptimal
for another. `test_the_cut_points_are_the_backtested_ones` now fails loudly and names where to re-run the
evidence; `test_the_rise_cut_is_looser_than_the_rate_rises_happen` pins the *reasoning* rather than the
number.

## On the ML experiment

The owner asked whether ADR-204's held candidate could be invoked here. **No, on both counts.** That gate
is about *expected minutes*, and it is a shrinkage estimator rather than a learned model; price is not in
its scope, and the date is the point of it (CLAUDE.md).

⭐ **And it would not help.** FPL's price mechanism is a deterministic threshold on net transfers — there
is nothing to learn, there is a constant we cannot see. A 14× lift from one ratio says the pattern is not
subtle. What is missing is **sampling rate, not model capacity**.

## Consequences

**Good:** three times as many rises named, at better precision, for a two-line change — and for the first
time the arrow has a number behind it.

**Costs:** ⚠️ more false positives in absolute terms (30 rise calls where there were 12), which is the
trade recall always is. Precision went *up*, so each individual arrow is more trustworthy than before.

⚠️ **Open, and it is the real ceiling:** this can say *whether*, never *when*. Prices move nightly and
`player_transfer_flow` keeps one row per player per gameweek, by an explicit ADR-210 decision that was
right for a threshold and is wrong for a forecast. ⭐ *Keeping the ramp is what a nightly predictor needs,
and it is a storage decision rather than a modelling one.*
