# ADR-318 — Three answers from one call

**Date:** 2026-09-27
**Status:** ✅ **Built.**
**From:** three tester notes — *"Should the build number be in Settings, just for information?"* · *"How
does FFH know how many transfers you have?"* · *"In the historical game views, could you calculate league
position places dropped or increased, red or green text with a 45-degree arrow?"*

---

## The decision

**Two of the three were already paid for.** `get_entry_history` has been called since ADR-234 to find out
which chips are spent. The same response carries `event_transfers` and `overall_rank` per gameweek — ⭐ *a
call worth making once is worth making once.*

## 1 — The build number

⚠️⚠️ **It already existed, and was readable only when an update was available.** `kAppBuild` drives the
update check and appeared in the *"Build 27 is out — yours is 26"* banner. ⭐ *The number that settles "is
this the version with the fix?" was being shown only to people who were already behind* — which is exactly
who does not need it.

Now in Settings under **About**, beside the version.

## 2 — *"How does FFH know how many transfers you have?"*

**Two ways, and the honest answer names both.**

⭐ FPL's **authenticated** `/api/my-team/{id}/` returns `transfers.limit` outright — but it needs the
manager's login. *That is the whole trick, and it is not cleverness, it is a different endpoint.*

⭐⭐ Unauthenticated, it is **derivable**: one free transfer a week, rolling over to a cap of five, minus
the ones spent. `free_transfers_from_history` does that, and against the owner's own season — **zero
transfers in five gameweeks** — it correctly returns **5**.

⚠️⚠️ **Two rules the derivation must not get wrong**, and both are pinned:

- **A hit costs points, not future transfers.** Four moves on one free transfer is a −12, and the next week
  still brings one. The bank floors at zero, never negative.
- **A wildcard or free hit leaves the bank alone.** The chip pays for that week's moves; ⭐ *it does not
  spend the transfers you saved* — which is why the chip list matters here and not only for chip advice.

⚠️⚠️⚠️ **And the blind spot is stated rather than hidden.** `event_transfers` only appears once a gameweek
has ticked over, so moves made *during the current window* are invisible until the deadline passes. So the
number is offered **beside** the control, never instead of it — ⭐ *a derived number presented as fact is
worse than a field.* The Settings caption says so in the app.

📌 That caption used to read *"FPL does not publish this, so the app has to ask."* Half true, and now the
wrong half — ⭐ *a caption explaining a limitation the app no longer has teaches people to distrust the ones
it does.*

## 3 — Rank movement

⚠️⚠️⚠️ **The sign is inverted from the number, and that is why it is computed on the server.** A rank of
**167,946 is better than 292,349** — so a *falling number is a rising position*. ⭐ *Doing that arithmetic
in each client is repeating the trap on each surface*; doing it once means one test, and it is
mutation-tested by flipping the subtraction.

```
GW3 → GW4   463,077 → 167,946    ▲ 295,131   green
GW4 → GW5   167,946 → 292,349    ▼ 124,403   red
```

⭐ A **45° arrow**, as asked, because the movement is a direction before it is a number — ⚠️ *a green
figure alone still has to be read to be understood.*

⚠️ **Null and zero are different, and the client draws them differently.** GW1 has nothing to compare
with, and a failed lookup is unknown — both draw **no arrow**. A rank that genuinely did not move is a
**known** zero, and also draws none. *"We could not check" is not "no movement".*

## Consequences

- ⭐ **One extra FPL call, already being made.** The history lookup now answers three questions instead of
  one, and still degrades to `{}` on failure with every caller unharmed.
- ⚠️ **A layout bug, found by fifteen tests.** The first arrow sat in a `Row` beside the label — and
  *"Overall rank"* plus an arrow plus six digits does not fit a quarter of a phone. It is scaled down like
  the figure above it now: ⭐ *a label that has outgrown its column is a layout bug, not a font size.*
- 📌 **The contract guard earned its keep again**: adding `free_transfers_implied` failed the sample test,
  which is exactly the prompt to check whether a Dart model needed the field. It did.

**2959 Python · 466 Dart.**
