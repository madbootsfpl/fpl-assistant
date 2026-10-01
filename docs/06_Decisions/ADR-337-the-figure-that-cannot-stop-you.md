# ADR-337 — The figure that is supposed to stop you

*Five planned changes, and "£1.0m In the bank" never moved.*

**Date:** 2026-10-01
**Status:** Accepted
**Fixes:** the draft path added around ADR-244 · **Touches:** ADR-226 (over budget is a warning, not a block)
**From:** the owner, with four screenshots — *"I can make a transfer and have no idea if I have enough
funds to do same"*, against FFH showing `£-8.1m in bank` in red

---

## What was wrong

`my_team` accepts `draft_player_ids` and rebuilds the answer around the planned fifteen. It kept FPL's
`bank` untouched, with this comment:

> ⭐⭐ **The draft replaces the fifteen and nothing else.** Name, bank, deadline and armbands still come
> from FPL — **a draft that invented its own bank would let a manager plan a move he cannot pay for**

🔴 **The principle is right and the conclusion is backwards.** Holding FPL's bank is *precisely* what let
a manager plan a move he could not pay for, because the number never moved to say otherwise.
⭐⭐⭐ *The figure that is supposed to stop you cannot stop you if it never moves.*

⚠️⚠️ **And a test asserted it, arguing from the same sentence.** `test_a_draft_keeps_fpls_money_and_deadline`
pinned `bank == 2.5` across a swap, with the comment repeated verbatim in its docstring. ⭐ *A test written
from the same sentence as the code cannot disagree with it* — the same shape as ADR-327's three tests that
agreed with an off-by-one.

The per-swap check in `replacements` (ADR-226) was working all along — but it tests **one** swap against
the **original** bank, so five changes never accumulated.

## Decision

The bank follows the fifteen: `bank − (cost(draft) − cost(base))`, at today's prices. `cost` follows
them too — it is *"what the fifteen price at today"*, so it has to be **this** fifteen.

The client shows it **red** and relabels to *"Over budget"* the moment it goes negative, which is the
only state that changes a decision.

### ⚠️ It is an estimate, and the screen says so

FPL pays back only **half** of a player's rise since you bought him, and the public API publishes no
selling price — `entry/{id}/event/{gw}/picks/` carries the squad's aggregate `bank` and `value` and
nothing per player. So the estimate errs **optimistic**: it can tell you about money you will not get.

⭐⭐ *An estimate that flatters the reader about money is the one kind that has to admit it* — hence
`bank_is_estimated` and the "(est.)" on the label. Using today's prices is also the convention this
codebase already had: `replacements` has budgeted with `out["price"] + bank` since ADR-226.

### ⭐ Value does not move, and that is correct

The owner reported both figures as frozen. FPL's `value` **includes** the bank, so a transfer only moves
money between the two and the total is invariant. He was right that the bank was broken and right that
value looked frozen; only one of them was a bug. A test asserts the invariant rather than the constant,
so the reason survives.

## Verified

3,034 Python and 527 Dart tests, the new ones driving the **endpoint** against the real store. Four
mutations, all caught: holding FPL's bank, subtracting on a cheaper plan too, never colouring the bank
red, never saying "est.".

⚠️ **Two fixture faults found while writing them**, both the same family as ADR-336's:

* A first draft asserted arithmetic computed **inside the test** and never called `my_team`. *A test that
  recomputes the answer tests the recomputation.*
* Swapping an XI player and appending the arrival to the bench leaves it **five deep**, and the optimiser
  raises on that — so the fixture was testing the validator. The swap stays inside the bench now.

## Consequences

**Good:** a planned squad you cannot afford says so, in the place the eye already goes, in red.

**Costs:** ⚠️ the headline figure is now sometimes an estimate, and "est." is a weaker promise than the
app usually makes. That is honest rather than ideal, and the alternative — a number that is always FPL's
and always wrong while planning — is worse.

⚠️ **Open:** the exact selling price needs FPL's authenticated `my-team` endpoint, which needs a login the
app does not have and does not want. Until then the error is bounded by half the rise since purchase, per
sold player, and is invisible to us.
