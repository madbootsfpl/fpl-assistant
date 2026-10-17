# ADR-356 — The referee and the accountant

**Date:** 2026-10-17
**Status:** Accepted
**Asked for:** *"just stop lying about 90'"*
**Extends:** ADR-346 (match scores) · **cites:** ADR-123

---

## Context

FPL publishes **two** finished flags on every fixture, and they mean different things:

| | flips when | call it |
|---|---|---|
| `finished_provisional` | the **whistle** goes | the referee |
| `finished` | **bonus points are confirmed** for the gameweek — hours later, sometimes next day | the accountant |

The scores card read only `finished`. So between the whistle and the bonus, a match sat at
`minutes = 90, finished = false` and the card printed **"90'"** — ⭐⭐ *a match that is over, captioned as
though it were still being played*, for the rest of the afternoon.

### Measured, on the day

The gap was sampled live through GW7's first match, Everton 0-2 Chelsea:

```
13:24  min=90  finished=0  provisional=0      still playing
13:37  min=90  finished=0  provisional=1   ←  the whistle
15:13  min=90  finished=0  provisional=1      ninety-six minutes later, still unsettled
```

⚠️ **Ninety-six minutes and counting** — not a corner case measured in seconds. ⭐ *The window this ADR
exists for is longer than the match that opens it*, and for all of it the old card said `"90'"`.

## ⭐⭐ The project already knew, in a different module

ADR-123 refuses `finished` for the fixture horizon for exactly this reason:

> *"Not `finished`, because FPL holds that flag back until a gameweek's bonus points are confirmed — it
> sets `finished_provisional` at full-time instead. So for the couple of days a gameweek is in flight,
> every played match still reads as unfinished."*

That sentence is in `storage.py`, and the card was written without it. ⚠️ *A fact learned once and
recorded in the module that needed it is not a fact the next module inherits.* This is the third time
this session: ADR-350 cited an ADR naming the fact it needed, and ADR-354's docstring claimed a property
its own gate broke.

## Decision

**Full time is the whistle.** `_status` reports *"Full time"* when **either** flag is set.

📌 `finished` in the payload still means **settled** and is untouched — the card stops mis-captioning
without the API starting to claim the bonus is in.

📌 **No new caption.** The product owner's call: *"just stop lying about 90'"*. The distinction is now
available to any surface that wants it later; nothing says anything new today.

### ⚠️ The flag is read live and deliberately not stored

Storing it would mean a **schema migration** — the step that has bitten twice (ADR-349, and the seed
snapshot before it). What that migration would buy is a better degrade in one case: a failed live fetch
during the provisional window.

⭐ That degrade is **exactly today's behaviour**, so the migration buys a fix for the bug this ADR already
fixes, in the minority of cases where the fetch fails. Not worth a schema change. The flag rides in on the
live merge, which ADR-354 ensures is running for any match inside the 24-hour window — which the
provisional gap always is.

⚠️ Every stored row therefore **lacks the key**, and `sqlite3.Row` raises `IndexError` for a missing one
where a dict returns `None`. The lookup tolerates all three shapes, the `kits._get` convention again.

## Consequences

✅ Four mutants, each caught — including *"caption everything Full time"*, which passes the headline test
and breaks the feature.

📌 **Not done, and not an oversight:** `data_checked` is the gameweek-level settle signal, and it
interacts with ADR-350's *"a played week never changes, so it caches for ever."* ⚠️ Conflating the two is
how that caching gets broken quietly, so it stays a separate question.

📌 **Also not done:** points shown during the provisional window can still change when bonus lands. The
payload now has what a client would need to say so; whether it should is a product decision, not this one.
