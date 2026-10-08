# ADR-344 — The cap is five, and the marginal move is the question

**Date:** 2026-10-05
**Status:** Accepted
**Reported by:** the owner, from the app — *"USE guide states that max transfers is 3, actual is 5 can roll over"*
**Revises:** ADR-132 (the timing arithmetic), ADR-173 (two moves, not one)

---

## Context

The week's answer told a manager holding three free transfers:

> *"You already hold 3 free transfers, and they do not stack any higher — saving this one would gain you
> nothing."*

⭐ **The 3 was his real count; the hardcoded wrong number was 2:**

```python
if free >= 2:                      # src/analytics/transfer_timing.py
```

That is FPL's rule **until 2024/25**, when two was the cap. ⚠️⚠️ And the contradiction was inside the same
file, twelve lines above:

```python
MAX_SAVED = 5         # free transfers roll over, up to five banked
```

`free_transfer_run()` used `MAX_SAVED` correctly throughout. `bank_or_use()` never heard about it. ⭐⭐ *The
file disagreed with itself, and the half that spoke to the manager was the half that was wrong.* A test
pinned the old rule by name — `test_holding_two_transfers_removes_the_reason_to_wait`.

🔴 **A one-line fix was the wrong fix**, and that is the part worth recording. Changing `free >= 2` to
`free >= MAX_SAVED` drops 2–4 into arithmetic that assumes you hold exactly one — *"Next week you would
have two free transfers, so a second move costs no −4 hit"*. With three banked, next week is four, and the
second move **is already free**. It would have replaced a false reason with a differently false one, and
overstated banking.

## Decision

**Generalise from "the second move" to "the move after your free ones".**

| | before | after |
|---|---|---|
| banking is impossible | `free >= 2` | `free >= MAX_SAVED` (5) |
| what banking costs | the **first** move's gain | the **marginal** move's — `moves[held - 1]` |
| what banking buys | the **second** move free — `moves[1]` | one more free move — `moves[held]` |
| is a hit worth it? | `moves[1]`, only when `free < 2` | `moves[held]`, always |
| moves computed | `max(held, 2)` | `max(held + 1, 2)` below the cap |

⭐ **At `free = 1` every number is identical to before**, which is the test that says this is a
generalisation rather than a rewrite.

### ⭐⭐ Why the marginal move is the right cost

Banking means making `held − 1` moves now instead of `held`. What it costs is the move you drop — the last
of the plan — not the best one, which you make either way.

⚠️ That only works because `suggest_transfer_plan` is **greedy and sequential** (ADR-035/191): each move is
priced on the squad and bank the previous one leaves, so the plan's prefix *is* the `held − 1` plan. ⭐
*Against `suggest_transfers`' disjoint alternatives the same arithmetic would be meaningless* — which is
the trap ADR-191 already caught once on this exact surface.

⚠️ A consequence, visible on real data: the gains are **not monotonic** (+10.30, **+12.40**, +9.50, +8.00).
A sequential marginal gain can exceed its predecessor. "The worst move" and "the last move" are therefore
different things, and it is the **last** one banking drops.

### 🔴 The flaw the prototype caught

A first draft returned *"Nothing on the board improves your squad this week"* whenever there were fewer
moves than transfers held — and **banked** on it. With three transfers and two good moves that sentence is
simply false, and the verdict was wrong. ⭐ *Holding more transfers than there are moves worth making is
the opposite of having nothing to do: it means you are not transfer-constrained at all.* Now its own
branch, with its own wording and its own test.

⭐⭐ **It was found by prototyping the arithmetic against the real move sequence before touching `src/`** —
the gate doing the thing the gate is for.

## What changed for a manager

**Verified on the demo squad at every count 0–5: no verdict changed.** Every move on that board gains
7.3–12.4 against a 4-point hit, so USE wins regardless. What changed is that the reasons became true.

⚠️ **Verdicts do change, and the cases are the ones that should.** Holding two with gains `[10.0, 1.0,
3.0]`, the old code said USE without arithmetic; it is now BANK — drop a 1.0 move so a 3.0 move is free
next week. Holding three with `[5.0, 4.5, 0.5, 4.0]`, likewise.

📌 So the change is **reason-only on a strong board and verdict-changing on a marginal one**, which is the
right way round: it only speaks up when the numbers are close enough to matter.

## Consequences

✅ One extra move is planned below the cap — work with a question behind it. At the cap it is not asked
for, because nothing can be banked there.

⚠️ `second_gain` in the returned dict now means *the move banking buys*, which at `free = 1` is still the
second move. Checked: nothing outside this module reads it.

⭐ Four mutants, each caught by the test that names the behaviour: the cap back at 2, the cost as the best
move, the extra move as always the second, and the fewer-moves guard removed.
