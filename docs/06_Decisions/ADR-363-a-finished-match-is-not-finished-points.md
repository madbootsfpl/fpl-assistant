# ADR-363 — A finished match is not finished points

**Date:** 2026-10-18
**Status:** Accepted
**Proposed by:** the product owner — *"The key principle is simple: a finished match doesn't necessarily
mean finished fantasy points."*
**Extends:** ADR-346, ADR-356

---

## Context

BPS settles, then it moves. Goals, assists and cards are corrected in the post-match review and the 3-2-1
follows. ADR-356 taught the card to say *Full time* at the whistle and left the bonus unlabelled, on
purpose — *"just stop lying about 90'"*. This is the other half.

The owner's four stages, and what each one is read from. ⭐ **Measured on GW6 and GW7, not assumed:**

| stage | signal | measured |
|---|---|---|
| **live** — the match is on | `started`, not `finished_provisional` | — |
| **pending** — full time, nothing awarded | `finished_provisional`, `bonus` block empty | the whistle flips at full time: 13:37 for Everton–Chelsea (ADR-356) |
| **provisional** — awarded, week open | `bonus` block filled, `finished` false | ⭐⭐ **32 hours after GW7's first kick-off every match had its 3-2-1 and not one was `finished`** |
| **final** — the gameweek is locked | `finished` | GW6: `data_checked = true`, ten finished. GW7: neither |

## 🔴 One correction to the proposal, and it is the load-bearing one

The design read `finished` as *"the post-match update"* and `data_checked` as a later lock. **They are the
same event in this data.** Thirty-two hours on, nine played GW7 fixtures were `finished = false` while
every one of them had already been awarded its bonus.

⭐⭐ So the per-match *"bonus is in"* signal is **the `bonus` block itself**, not a flag — and `finished`
stands in for the gameweek lock, which means **no `bootstrap-static` call is needed** for `data_checked`.

## Decision

**`bonus_status` on every match: `live` · `pending` · `provisional` · `final`.**

⚠️⚠️ **Deliberately independent of the scoreline's state**, which is the owner's principle made into a
field. A match reads *Full time* for a day and a half while its points are still open; folding that into
`finished` is exactly what hid it.

📌 **No new polling and no new fetch**, as asked. Every state is read from the live fixture payload this
module already pulls behind its sixty-second cache (ADR-361), and a settled week asks upstream for
nothing at all.

⭐ The card draws a chip beside the bonus race — *live*, *bonus to come*, *provisional* — and **nothing
once the week is locked**: ⚠️ *a label on every state is a label nobody reads.*

## Consequences

✅ Four mutants, each caught — including *"pending collapses into provisional"*, which claims a bonus
before it exists and is the failure this ADR is about.

🔴 **A test read the live cache, not the code.** The helper builds two states of one gameweek in a single
test, and the second call was served the first's payload from the sixty-second cache — ⭐ *which reads
exactly like the code ignoring the second state.* It clears the cache between calls now.

⏳ **Stage two is the one I could not observe.** Every GW7 match already had its bonus by the time this
was built, so the window between the whistle and the award is handled by construction and has never been
seen. 📌 It is visible on any matchday: a card reading *Full time · bonus to come*.
