# ADR-335 — Price belongs next to the decision

*The predictor was worth trusting (ADR-334). This is where it goes.*

**Date:** 2026-09-30
**Status:** Accepted
**Builds on:** ADR-334 (the recalibration) · ADR-092 · ADR-215 (the percentile over the whole board)
**From:** the owner — *"2 spots of importance … OR do you have a better idea? Lets discuss"*

---

## Context

The owner proposed two homes: actual **and** predicted changes on **My Team → Price**, and a
risers/fallers control on **Players**. Both reasonable. Tracing what already existed changed the shape of
the answer twice.

🔴 **`changedThisGameweek` has been parsed on the device since the endpoint shipped and never rendered.**
`PriceMove` carries it, documents it as *"how much his price has already moved this gameweek"*, and
`_Price` draws the arrow, the current price and net transfers instead. The first half of the owner's ask
was ten lines of Dart and no server work.

⚠️ **And I had told him the predictor surfaced in one place.** It is in four — the Streamlit Players
column, Streamlit Squads, the ask layer and the API. I had grepped for the wrong symbol.

## The design constraint that shaped it

⭐⭐⭐ **A fact and a forecast were about to share one visual language.** `↗ £6.2` reads as *"went up to
£6.2"*; the arrow is a **prediction**, right about 40% of the time. Putting the actual change beside it
would have put two arrows on one card meaning *this happened* and *this might*.

⚠️ *An estimate that looks like a fact is worse than no estimate*, because a reader cannot discount what
they cannot tell apart. So: **the forecast keeps the colour, the fact is plain text.** `price_flag`'s
docstring has drawn that distinction since ADR-140; the UI had not.

## Decision

### 1. The transfer card says when, not just whether — and this is the new part

`explain_transfer` takes optional `cuts` and `out_row`, and adds one line of price timing **after** the
football reasons. All four cases, because the direction of the news depends on which side it lands:

| | buy | sell |
|---|---|---|
| **rising** | *may cost £0.1m more if you wait* | ⚠ you are selling into a rise |
| **falling** | ⚠ wait and he may be cheaper | *ahead of a likely £0.1m drop* |

⭐⭐ **This is where a 40%-precision signal earns its keep.** Being wrong costs **£0.1m, not a bad
transfer** — numbers that are weak for a dashboard and ample beside a decision the reader is already
making. And it reaches someone who would never open a price tab.

⚠️ *"May"*, always. One change is £0.1m and the rule is right about a third of the time; a line that said
*"will"* would be wrong more often than the delay it advises against.

⚠️⚠️ **`cuts` is optional and absent means silent**, never a default. A caller without the whole board
cannot have trustworthy cuts, and ⭐ *no note is a better answer than one taken over fifteen players* —
ADR-215's bug. The guard already existed: `price_thresholds` returns `(None, None)` below twenty, so
passing a squad yields no note rather than a wrong one. A test pins that, so nobody "fixes" the refusal.

### 2. My Team → Price shows what happened, plainly

The card renders `changedThisGameweek` where it showed net transfers, falling back to the transfer count
when the price has not moved yet.

### 3. One line for the squad

`squad_price` on the endpoint: what the squad's value did this week, how many are under pressure each
way, and what the falling ones are **worth**.

⭐ It leads with falls because that is the half the predictor can support — **72% recall against 24%**
(ADR-334). *"One of yours is about to drop"* has evidence behind it; *"four are about to rise"* barely
does. ⚠️ And the £ is what they are worth, not what they would lose: a change is £0.1m each. *The number
that makes you look is the exposure; the number that matters is small, and saying the small one first is
how a feature gets ignored.*

## Verified

3,028 Python and 518 Dart tests. The two Dart claims are checked against their opposite: painting the
fact in the forecast's colour fails, and showing the squad line outside PRICE mode fails.

⚠️ **Two fixture mistakes worth recording**, both of which made a test pass for the wrong reason:

* A board where one player had all the pressure produced **no note at all** — the 95th percentile of
  fifty-nine zeros is zero, and `price_thresholds` refuses a non-positive rise cut. ⭐ *A distribution
  always has a top 5%; only the sign can say there is nothing to be a lot of.*
* A board that was **all buying** has a positive 25th percentile, so there was no fall cut and the fall
  test could not have failed. ⭐ *A fixture that cannot produce the answer is not a fixture.*

The `my-team.json` contract sample was regenerated and its time drift reverted — age, countdown and a
signal id (ADR-327's rule). The remaining diff is the new key and three `direction` values that changed
from `stable`, which is ADR-334's recalibration visible in the contract.

## Consequences

**Good:** price reaches the reader at the moment it matters, on both platforms, and the app stopped
discarding a number it had already fetched.

**Costs:** ⚠️ `explain_transfer` grew two optional arguments and a dependency on the price module. The
optionality is load-bearing rather than convenient, which is the kind of parameter that gets "tidied up"
by someone who has not read why.

⚠️ **Not done, and deliberately:** the Players tab. Mobile has no price movement at all — price is a
max-price filter and nothing else — so that is a real gap, and a **filter** is most of it. A separate
risers/fallers board is a third thing and competes with the Players page for the same job.

⭐ **Still true, and the ceiling on all of this:** it says *whether*, never *when*. That needs the
transfer ramp kept (ADR-334), which is a storage decision.
