# ADR-214 — Most of the remaining boards have nothing in them yet

**Date:** 2026-09-20
**Status:** Accepted
**Follows:** ADR-213 (the pipeline publishes analytics) · Mobile audit §4.1

---

## Context

ADR-213 published the xP board and said the rest of §4.1's list — the stat boards, DNA percentiles, Signals —
*"become mechanical once the pattern exists"*. The next step was to do them.

⭐⭐ **Measuring the populations first turned a six-board sprint into a one-board sprint.** Counted on the
live snapshot at GW5:

| board | rows today | why |
|---|---|---|
| **Team DNA** | **20 teams**, grades A→D, scores 46–87 | ✅ **published** |
| Player DNA | 662 profiles, but `pool_size` is **1 for 584 players and 0 for 78** | 🔴 percentiles are the no-peers default |
| over/under | **0** | needs 900 minutes; the board's maximum is **450** |
| DefCon reliability | **0** | same 900-minute gate |
| worth-noticing / exodus | **0** | nothing classifies yet |
| price predictions | 662 rows, **all `stable`**, 0 flags | see the finding below |
| trending | 10 / 10 / 10 | ⬜ it is `ORDER BY` on a published column |
| headline events | 15 rows | ✅ already its own table |

**The deciding number is 450.** That is the highest minutes total on the board five gameweeks in, and three
of these boards gate at **900**. They are not unfinished; they are **out of season**.

⭐ **Player DNA is the one worth dwelling on, because it does not look empty.** It returns a profile for all
662 players. Every profile is `low_minutes` for 659 of them, the peer pool is one player or none, and the
percentiles come back **50** — a full-looking table carrying no information. ⚠️ *A board that renders
perfectly and says nothing is worse than an empty one, because nothing prompts you to check.*

## Decision

**Publish Team DNA. Decline the rest, with dates.**

Team DNA is published for the same reason xP was: **percentiles require the whole population**, so a client
genuinely cannot compute them. 20 rows, eight axes each, validated before replacing the last good board,
pinned by a test that recomputes and compares.

📅 **Re-measure on or after 2026-11-01** (roughly GW10, when a regular starter passes 900 minutes) for
over/under, DefCon reliability and Player DNA. The check is one line — *does the population contain the
case?* — and it is the third time in a month that question has changed a plan (ADR-195, ADR-202, ADR-208).

⬜ **`trending` is not published at all, and that is not a deferral.** It is `sorted(players, key=…)[:10]` on
columns the pipeline already publishes. ⭐ *Publish a rule; do not publish a sort.* A client ordering rows by
a column it already holds is not a second implementation of anything.

## 🐛 The finding: a threshold nothing can reach

`price_prediction` returns `stable` for **all 662 players**, and it is not because prices are quiet — **269 of
662 have moved since the season started.**

`price_pressure` is `net_transfers / selected_by`, compared against `PRICE_RISE_PRESSURE = 20_000`. Measured
on the live board:

| | |
|---|---|
| threshold | **±20,000** |
| highest buying pressure | **+5,760** (Schuster) |
| lowest selling pressure | **−2,660** (Elanga) |

**The threshold is 3.5× anything that occurs.** The rule cannot fire.

⭐⭐ **This is ADR-210's bug, in a different constant, three ADRs later.** ADR-210 found `EXODUS_PRESSURE =
−8,000` was a fixed threshold on an **accumulating counter** — `transfers_in_event` / `transfers_out_event`
reset at every deadline and fill across the week, so a fixed bar encodes *the hour the calibration ran*
rather than a severity. `price_pressure` divides **those same two counters** by ownership.

And this snapshot was taken **516 hours** from the GW6 deadline — three weeks out, across an international
break, when the counters are nearly empty. The same reading the day before a deadline would be a different
number entirely.

⚠️ **ADR-210 fixed the exodus threshold and did not look at the price one**, though both live off
`net_transfers` and sit two modules apart. ⭐ *A lesson recorded about one number does not check the others* —
which is precisely what ADR-209 concluded about `TIE_NOISE`, and it has now happened again.

📅 **Not fixed here**, because ADR-160 already flagged the price journey as *"thin until prices move, revisit
~GW4"* and it is now GW5 — so this wants the same treatment ADR-210 gave exodus (a live percentile, phase-aware),
not a new constant. Logged as the next candidate after the GW6 sitting.

## Consequences

**Good:** two boards published instead of one guessed-at six. The pattern is proven twice, on two different
shapes (per-player and per-team), which is what makes the remaining four mechanical when they have content.

**Cost:** a mobile client cannot show over/under, DefCon reliability or Player DNA percentiles until those
tables exist. ⚠️ **That is a fact about the season, not a gap in the plan** — the web app cannot show them
either, for exactly the same reason.

**Explicitly not done:** building the tables now and letting them fill up later. It was considered. It would
mean shipping four validators calibrated against an empty population — and a validator that has never seen a
populated board is a guess with a test around it.
