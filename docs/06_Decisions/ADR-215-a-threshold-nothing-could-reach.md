# ADR-215 — A threshold nothing could reach

**Date:** 2026-09-20
**Status:** Accepted
**Supersedes:** ADR-092's `PRICE_RISE_PRESSURE` / `PRICE_FALL_PRESSURE`
**Applies:** ADR-210's fix, to the constant it did not look at

---

## Context

`price_prediction` returned **`stable` for all 662 players**, and not because prices were quiet — **269 of
them had moved since the season started.**

`price_pressure` is net transfers per 1% owned, compared against `PRICE_RISE_PRESSURE = PRICE_FALL_PRESSURE =
20_000`. Measured on the live GW5 board:

| | |
|---|---|
| the threshold | **±20,000** |
| highest buying pressure | **+5,760** |
| lowest selling pressure | **−2,660** |

**The bar sat 3.5× above anything that occurs.** The rule could not fire, and had not all season.

### Why nothing caught it

The comment beside the constants said what happened:

> *"Placeholders chosen so nothing fires on flat preseason data (net = 0); calibrated on real net transfers at
> GW1."*

The first half happened. **The second was a plan, written as a comment, that nobody executed** — the same
shape as ADR-212, where four runbooks described a hardening that had already changed underneath them.

Two things then kept it invisible:

⭐⭐ **Every unit test built its input *from* the constants it was checking.** `just_rise = _p(net_in=int(
PRICE_RISE_PRESSURE * own) + own)` passes for any threshold, including one no real player can reach. *A test
that derives its fixture from the thing under test is asking whether the code agrees with itself.*

⭐⭐ **A test was named `test_price_predictor_is_dormant_preseason`.** Dormancy stopped being the preseason
state and became the permanent one, and the name read as confirmation. *A rule that never fires looks exactly
like a rule with nothing to report.*

### It is ADR-210's bug, three ADRs later

⭐⭐ **A fixed bar was the wrong *shape*, not merely the wrong value.** `price_pressure` divides
`transfers_in_event − transfers_out_event` — counters that **reset at every deadline and fill across the
week**. A constant therefore encodes *the hour of the week it was picked*. The numbers above were read **516
hours** before the GW6 deadline, across an international break; the same board the night before would be an
order of magnitude larger.

ADR-210 found exactly this in `EXODUS_PRESSURE` and replaced it with a live percentile. It **did not look at
the price constant**, though both live off the same `net_transfers` two modules apart — and `crowd.py`'s
exodus population is literally built by calling `price_pressure`.

⭐ *A lesson recorded about one number does not check the others.* ADR-209 concluded precisely this about
`TIE_NOISE`. It has now happened twice.

---

## Decision

**The definition stays; the number goes** — ADR-210's treatment, applied to the same quantity.

### 1. Percentiles, and they are not symmetric

⭐ **One constant for both directions assumed a symmetry the data flatly contradicts.** Counted from
`player_history`, which records each player's price per round:

| | rose | fell |
|---|---|---|
| GW1→2 | 1.0% | 1.8% |
| GW2→3 | 2.1% | **16.9%** |
| GW3→4 | 2.8% | **15.3%** |

About **seven times more players fall than rise** — a bad week empties a bandwagon faster than a good one
fills it. So `PRICE_RISE_PERCENTILE = 98` and `PRICE_FALL_PERCENTILE = 15`, which are the observed rates
rather than a taste.

On the live board those cuts are **+2,644** and **−346**, and the rule now names **2.1% rising** and **15.3%
falling** of the eligible population.

### 2. The sign decides *whether*, the percentile decides *how much*

⭐ A distribution always *has* a top 2%, so the percentile alone would name risers in a week when every
player was being sold. Either cut is `None` when its sign is wrong, and `None` means **this direction cannot
fire** — never *"fall back to a default"*, because the default is what produced a dead rule.

### 3. The same population at both ends

⚠️⚠️ **The first version of this fix broke the rule ADR-210 wrote down.** Cuts were taken over players owned
≥1% and then applied to all 662 — so **43 of 72 "fall" flags landed on players nobody owns.** Pressure
divides by ownership, so for a 0.1%-owned player a few thousand sales read as a collapse.

⭐ *A threshold and the thing it judges must be measured in the same population, or it describes a
distribution its subject was never in.* The floor is now applied twice: once to build the population, once
before any player is tested. Below it the answer is **"cannot say"**, not "will not move".

The floor is **imported** from `crowd.py` rather than restated — one definition of who counts, over one
quantity.

### 4. Bound once, to the whole board

`price_prediction` now takes its cuts as a **required argument**, and `price_detector(players)` binds them.

⚠️ **Three call sites were passing a filtered list**: the squad page passes **fifteen players**, the pool
page passes a filtered page, `ask` passes the fit-players-only pool. A percentile over fifteen would flag
your worst two every week forever, whatever the league was doing.

⭐ Required, not optional, for ADR-181's reason: *a call site that forgets raises, rather than quietly
falling back to a number nobody calibrated.*

---

## What this does not fix

⚠️ **The percentiles are observed rates, not a calibration.** The real question — *what pressure actually
preceded a price change?* — needs pressure readings paired with the move that followed. **That is exactly
what ADR-210's `player_transfer_flow` log collects, and it currently holds one reading.**

📅 **Re-measure once the log spans a few deadlines** (earliest meaningful: after GW8, ≥2026-10-26). At that
point the percentiles stop being inferred from how often prices move and start being measured against what
moved them.

⭐ Worth stating plainly: this replaces *a number that could not be right* with *a definition that is
defensible and still unproven*. That is a real improvement and not the end of the work.

## Consequences

**Good:** a feature that has been silently dead all season now works, on every surface that shows it. The
threshold re-reads the board, so it cannot rot with the calendar the way a constant does.

**Cost:** four call sites changed and one signature became required. That is deliberate — the alternative is
an optional argument, which is how ADR-181's bug happened.

**Watch:** ⚠️ 15% of the eligible board is now flagged as falling, which is ~29 players. If that reads as
noise on the Players page, the answer is a **stricter percentile**, not a constant.
