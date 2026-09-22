# ADR-246 — The formation rule stays where it lives

**Date:** 2026-09-22
**Status:** Accepted
**From:** tester feedback — *"Should also have Substitute option"*
**Builds on:** ADR-014/022 (`XI_FLEX`, `legal_xi_issues`), ADR-241 (`Draft.swap`), ADR-244

---

## Context

The player sheet could make a captain and start a transfer. It could not do the free, reversible thing a
manager does most: **change two players' places**.

The interesting part is not the gesture, it is the rule. FPL's formation limits — one keeper, 3–5
defenders, 2–5 midfielders, 1–3 forwards — decide which swaps are legal, and ⭐ **a client that offered
"any bench player" would propose squads FPL rejects.**

## Decision

**The server says who is legal; the client renders the list.**

`my-team` gains `swaps: [{id, benched, with: [ids]}]`, computed by `legal_xi_issues` — the same validator
that already guards every declared bench.

⭐⭐⭐ **Working the rule out again in Dart would be a second implementation of something the engine owns**,
and ADR-151→156 is this project's record of exactly that: one fact re-taught to six surfaces one at a time,
every gap found by the owner using the product.

⭐ It is computed by **trying** each swap rather than by reasoning about it — a dozen candidates per player
and a list check is cheap, and a derived rule is the thing that drifts. *Ask the validator; do not
re-derive what it knows.*

**On the sheet, "Bench him…" / "Bring him on…" sits above "Transfer…".** ⚠️ *Order on a list of actions is
a recommendation whether or not it was meant as one*, and one of these is free and reversible while the
other costs points.

**Only legal partners appear.** Greying out the rest would invite a manager to wonder what he did wrong,
when the answer is *"nothing — FPL would not allow it"*.

**The incoming player takes the outgoing one's place in the bench order.** FPL substitutes in bench order,
so appending would quietly demote him to last — ⚠️ *a change the manager did not ask for, hidden inside one
he did.*

## What building it found

⚠️⚠️ **The first version offered a goalkeeper a swap with a forward.** It removed the wrong player when
simulating the swap and built a **twelve-man XI** — and `legal_xi_issues` validated it happily, because it
checks position *ranges* and not the size of the list. ⭐ **A validator answers the question it was asked,
and "is this eleven" was never asked.**

⚠️ The fix added a `len(after) == 11` guard, and a mutation then proved the guard **could not fire**: with
the swap logic correct, one out and one in makes eleven by construction. It was removed. ⭐ *An unreachable
guard is not defence in depth, it is a comment that looks like code.* The size is asserted in the test,
where it can fail.

⚠️ **One test skipped itself** because the fixture XI happened to carry two forwards, so the *"you cannot
bench your only striker"* case was never exercised. It now builds a bench that leaves exactly one. ⭐ *A
test that skips when the data is uninteresting reports coverage it does not have.*

⭐ And the suite needed a test for the **converse**: "everything offered is legal" is satisfied by a
function that offers nothing. *Checking what was allowed says nothing about what was left out.*

## Also in this change

**The price line under a shirt no longer wraps.** `£12.0m · TOT (H)` under a long name spilled onto a
second line, making one card taller than its neighbours and pushing the row out of alignment — ⭐ *a card
that changes height with its contents stops being a grid.* Shrunk to fit rather than truncated: the price
and the opponent are both the point of the line.

## Verification

* **5 Python tests** including the exhaustive property (every offered swap makes a legal eleven) **and its
  converse** (every legal swap is offered), plus keepers, the lone forward, and no-declared-bench.
* **5 Dart tests**: the keeper pair, the bench slot, the fifteen untouched, armbands surviving (ADR-241's
  failure, guarded here too), and a two-starter pair changing nothing.
* **5/5 mutations killed** after the dead guard was removed: an inverted swap; no legality check at all;
  nothing offered; and the bench flag inverted.
