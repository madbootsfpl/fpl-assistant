# ADR-354 — The live path was gated on the pipeline

**Date:** 2026-10-17
**Status:** Accepted
**Found:** in production, during GW7, an hour after the first kick-off
**Extends:** ADR-346 (match scores for a gameweek)

---

## Context

ADR-346 is explicit that the two cases are fetched differently on purpose:

> 🔴 **A finished match is a fact; a match in progress is a feed.** … ⚠️ *The scheduled pipeline fires at
> roughly a fifth of its declared cadence with an 08:00–16:00 hole, so a "live" score behind it would be a
> lie in the product.* **The live path does not go near it.**

At **12:32 UTC on 2026-10-17**, 62 minutes after Everton–Chelsea kicked off, the endpoint answered:

```
gameweek=6  live=False     ← last week's finished results, on a matchday
```

## 🔴🔴 The fetch did not go near the pipeline. The decision to fetch did.

```python
in_flight = any(_started(f) and not f["finished"] for f in stored.values())
if in_flight:
    for raw in _live_fixtures(gameweek, client=client):   # the live path
```

`_started` reads the **stored** flag, and only the hourly refresh writes it. So at kick-off the database
still said *not started*, `in_flight` was False, and the live fetch never happened. `_which_gameweek`
reads the same flag, so the screen did not even select the live week — it fell through to *"the most
recently played"*, which is last Saturday.

⭐⭐ *A guard against depending on something, written in terms of that something.* The docstring's claim
was true of the request and false of the branch that decides whether to make it, and that is the only half
that matters.

⚠️ **Why no test caught it:** every test of the live path sets `started=1` in the database first. ⭐ *The
fixture that makes the live path reachable is the bug*, so each test proved the merge worked and none
proved it ran.

## Decision

**Gate on the clock.** The kick-off time is already stored, weeks in advance — ⭐ the product owner's own
framing: *the fixture is known in advance, but its score and status evolve.* A clock we already have beats
a flag somebody else has to write.

```python
def _playing(f, now=None) -> bool:
    return (_started(f) or _kicked_off(f, now)) and not f["finished"]
```

One predicate now drives both the week selection and the live gate, so the two cannot disagree.

### ⚠️ Bounded at the far end, which the first version was not

Kick-off alone made every fixture the feed never finished — a postponement, an abandonment — count as in
progress **for ever**, polling FPL and holding the screen on a dead week. ⭐ *An unbounded "since" is a
condition that becomes permanently true.* 🔴 Caught by two existing tests going red against the seed,
whose fixtures are months old.

**`LIVE_WINDOW_HOURS = 24`**, and it is sized against **the pipeline, not the match**. A game is over ~2h
after kick-off, but `finished` in the database only flips when the refresh next runs and the observed gaps
reach five hours. ⚠️ *Closing the window before the pipeline catches up would replace a live score with
"not started"* — worse than either truth. Inside the window FPL's own `finished` is read live, so the card
says *Full time* whatever the database thinks.

### 📌 What this deliberately does **not** do

The product owner's stage 2 said *"update `started`, `minutes` and the current score"*. Nothing is
**persisted** live. A writer running every minute during matches is the streaming-infrastructure project
this was meant to avoid; read-through gets the same screen with no new moving parts. The database is
written at full time by the ordinary refresh, exactly as before.

## Consequences

⚠️ **This answer is now clock-dependent, and that has a cost.** `gameweek_scores` takes an injectable
`now`, because the seed holds a whole season and *"nothing has been played"* is only true on a date before
any of it. ⭐ *A test that reads the real clock passes on the day it was written* — this repo has watched
that happen, when `test_xp_board` pinned to "from GW6" went red the week GW6 was played.

✅ Five mutants, each caught, including the two that restore the original bug.

📌 **Unrelated drift, fixed in the same commit because CI could not go green without it:** the
`gameweek-plan` contract sample stopped matching when the clock rolled to GW8 and the engine chose a
different transfer. ⚠️ Regenerating rewrites **all sixteen** samples (~5,000 lines) because they are
rebuilt from whichever database `DB_PATH` resolves to; only `gameweek-plan` had drifted, so only that one
is committed. ⭐ *A regeneration script with no single-sample option turns a one-key change into a
five-thousand-line review.*
