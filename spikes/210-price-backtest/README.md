# 210 — Does the price predictor work?

`src/analytics/price.py` has shipped since ADR-092 and been recalibrated once (ADR-215). **It had never
been scored against what actually happened.** This is that score.

## Running it

```
python3 spikes/210-price-backtest/fetch.py    # ~4 min, 667 polite requests
python3 spikes/210-price-backtest/score.py
```

`fetch.py` pulls `element-summary/{id}/`, which carries `value`, `selected`, `transfers_in` and
`transfers_out` **per gameweek per player** — everything the rule reads, plus the outcome, from a public
endpoint with no key.

⭐ `score.py` **imports the shipped functions**. A backtest that reimplements the rule measures the
reimplementation, and the whole point was to find out about the real one.

## What it found (GW1–5, 3,216 player-gameweeks)

The rule is real. Forecasting the following week:

| | precision | recall | base rate | lift |
|---|---|---|---|---|
| ▲ rise | 33.3% | 8.9% | 2.3% | **14.4×** |
| ▼ fall | 50.6% | 15.1% | 14.7% | **3.4×** |

⭐⭐ **It is never wrong about direction.** Not once did it call a rise that fell, or a fall that rose.
Every error is *"called a move, nothing happened"* — a conservative signal, not a confused one.

⚠️ But it fired **12 times** for rises across the whole season-to-date, catching 9% of them. That is the
finding: the cut points were far too tight, and the shipped pair was **dominated** (ADR-334).

## Two pairings, and the gap between them matters

* **Same week** — the signal against the change in that same window. The counters are end-of-window, so
  they include transfers made *after* the price moved: the rule marking its own homework. A **ceiling**.
* **Next week** — no hindsight. The claim a ▲ actually makes to a reader.

They come out close (40%/33% precision for rises), which is itself informative: the signal is not
getting most of its apparent skill from hindsight.

## What it cannot tell you

⚠️⚠️ **Nothing about *when*.** Prices move nightly; this data is one point per player per gameweek.
Predicting "rises tonight" needs the **ramp** — net transfers sampled through the week — and
`player_transfer_flow` deliberately keeps only the last reading before each deadline. That is the change
which would unblock a real nightly predictor, and it is a storage decision, not a modelling one.
