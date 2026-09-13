# Sprint 253: The GW4 sitting (ADR-190)

**Dates:** 2026-09-13
**Status:** ✅ Complete — ADR-190. **1762 tests, ruff clean.** **All four weights stay at 0.**
One constant shipped (`CLEAR` 1.0 → 1.3); one re-measure found impossible as written.

---

## Why it was overdue, and why nobody noticed

The roadmap's *"blocked on gameweeks"* section held **two different gates under one heading**: the
900-minute bar (still real — **0 of 657** clear it, a ~GW10 item) and the ≥4-gameweek bar (lifted at GW4).

**When one of two gates lifts, nothing announces it.** The row still reads *blocked*, and everything filed
under it stays parked. The list's own rule — *"assume this list is stale before you assume the work is
undone"* — was written for precisely this and still did not fire, because re-auditing is something you do on
a schedule and gates lift on theirs.

## The sweeps — four flat lines that are not the same result

```
baseline everywhere: ρ 0.621 · MAE 1.22 · hit@20 0.19 · n=626 · 1 SE = 0.040

FORM_WEIGHT          0.621 → 0.626   ascending    +0.005
SET_PIECE_WEIGHT     0.621 → 0.622   flat         +0.001
DEFCON_MAGNIFIER     0.621 → 0.622   flat         +0.001
CLEAN_SHEET_WEIGHT   0.621 → 0.614   DESCENDING   −0.007
```

Criterion 1 asks for **+0.040**. Nothing moves more than 0.007 in any direction.

## The check that changed the reading

A flat curve means *"no signal"* only if the term reaches the projection. Measured against the same call the
harness makes:

| weight | xP moves (of 657) | max Δ | **ρ(rank at 0, rank at w)** |
|---|---|---|---|
| `FORM_WEIGHT` @0.5 | 291 | 3.10 | **0.98716** |
| `CLEAN_SHEET_WEIGHT` @0.5 | 172 | 1.50 | **0.98095** |
| `DEFCON_MAGNIFIER_WEIGHT` @0.5 | 69 | 0.30 | **0.99977** |
| `SET_PIECE_WEIGHT` @0.5 | **5** | 0.20 | **0.99998** |

A term producing a ranking **0.99998** correlated with the baseline's cannot change that ranking's
correlation with reality by 0.040. For set-piece and DefCon the bar is **unreachable**, not merely unmet —
at GW6, at GW10, at any n.

And for set-piece it is by design. The bonus applies only off the `hist` tier (ADR-096 — a trusted baseline
already prices an established taker's pens, so adding it would double-count). Of **43** #1 duty-holders the
term reaches **9**; `history_by_code` holds only completed seasons, so that 9 is **fixed for the season**.

⚠️ **I nearly measured this wrong.** The first run omitted `gw_history_by_code`, which the harness passes —
and reported `FORM_WEIGHT` moving **0 of 657 players at every value**, i.e. a dead term. It was not dead; my
call was not the harness's call. *A measurement of the mechanism has to make the same call the thing under
test makes, or it measures a different mechanism and does it confidently.*

## Constants, re-measured at two seeds

| constant | GW1 | GW4 | move | outcome |
|---|---|---|---|---|
| `WHISKER` | 0.20 | 0.30 · 0.30 | 0% | keep |
| `CLEAR` | 1.00 | 1.30 · 1.30 | **+30%** | ⚠️ **shipped 1.3** |
| `CONCENTRATED` | 0.35 | 0.374 · 0.370 | +6% | keep |
| `HEAVY` | 0.45 | 0.446 · 0.435 | −2% | keep |

`CLEAR` shipped because §B0 pre-registered it: *ship the new value if it moves ≥20%*. Leads **widened** (max
2.80 → 4.30) as real returns replaced preseason projections, so holding 1.0 would have kept the number and
lost the meaning. `tests/test_captain.py::test_a_clear_lead_reads_as_one` failed on the change — correctly,
its 1.1 example is now *narrow* — and a new assertion pins the 1.0–1.2 band that moved.

⚠️ **My first concentration measurement was an artifact and said so out loud**: p75 and p90 both came back
**0.200**, at both seeds, because I measured *max club share of the 15* and the sampler caps clubs at 3
(3/15 = 0.2). A statistic that returns the same number at two different percentiles is not a distribution.
Re-measured on what `match_concentration` actually computes — a match's share of the XI's gameweek xP — it
gave 0.374/0.370 and 0.446/0.435, and both constants held.

## The one that could not be run at all

`EXODUS_PRESSURE`'s rule says *re-measure on ≥4 gameweeks*. `price_pressure` reads `transfers_in_event` /
`transfers_out_event` — **current-event fields** — and `player_history` stores **no per-round transfer
columns**. The app holds one week of this quantity at a time, so the instruction has no data to run on; what
it produced was a **second single-week sample**, 51% away from the first.

Two samples of a varying quantity that disagree by 51% establish **that it varies**, not a new value. No
constant changed. What the pair *does* show is that a fixed constant is the wrong mechanism: defined as *"the
worst tenth"*, it flags **2 of 190** on this week's distribution. A live percentile would be the worst tenth
every week by construction — proposed and **gated**, not built.

---

## 💡 The lesson

> **A measurement can fail because the thing is absent, or because the instrument cannot see it — and a flat
> curve looks identical either way.**

Four weights, four nearly-identical flat lines, one obvious reading: *no signal, wait for more data.* One
column — how much each term changes the ranking **at all** — splits them into evidence about football and
evidence about the harness. Waiting for GW6 would have produced the same flat lines for two of them while
looking like patience.

The narrower form: **a whole-board metric cannot evaluate a term scoped to a sub-population.** Set-piece
applies to nine players by design and was asked to prove itself in a statistic over 626.

And the one about the method itself: **pre-registering a criterion protects you from choosing the answer
afterwards; it does not protect you from asking a question the instrument cannot answer.** §B0 asked whether
its bar was strict enough. It never asked whether the bar was reachable. Both checks are needed.

---

## Definition of Done

1. **Tests: 1762, unchanged in count** — one threshold test rewritten with the new band pinned, one example
   fixture corrected by the change it was meant to catch.
2. **Manual smoke** — four sweeps run end to end; the liveness table and both constant re-measures run at two
   seeds; full suite + ruff green.
3. **Docs** — ADR-190, `GW1_RUNBOOK` §📉 + the stopping rule, ADR-000 index, PROJECT_STATUS, Roadmap, this
   retro, and `spikes/190-gw4-sitting/constants.py` kept as the harness.
