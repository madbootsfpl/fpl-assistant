# ADR-351 — Two sets are not a list of swaps

**Date:** 2026-10-16
**Status:** Accepted
**Reported by:** the owner, from build 44 — *"you can't transfer outfield players for goalkeepers or vice
versa"*
**Revises:** ADR-244 (the suggested lineup)

---

## Context

This Week's **LINEUP** block said *"3 changes"* and printed:

```
▲ Leno      ▼ Barry        ← a goalkeeper for a midfielder
▲ Guéhi     ▼ Pickford     ← and the reverse
▲ Semenyo   ▼ Virgil
```

FPL does not allow either. A keeper can only replace a keeper.

## ⭐⭐ But the advice was right and only the sentence was wrong

`gameweek_plan` returns `bring_in` and `drop` as **two set differences** — who enters the XI and who
leaves it. The XI itself comes from `best_legal_xi` and **was legal**; the three changes were the right
three.

🔴 The phone zipped the two lists by index:

```dart
for (var i = 0; i < bringIn.length && i < drop.length; i++)
  '▲ ${bringIn[i]} ▼ ${drop[i]}'
```

⚠️⚠️ *The pairing was invented by the renderer* — and `_suggested_lineup` even sorts those sets **by
player id**, so it was not merely arbitrary but meaningless.

⭐ **The CLI and `ask` were always right**, because they never claimed a pairing: *"start Leno, Guéhi,
Semenyo — bench Barry, Pickford, Virgil."* Three surfaces printed the same data and only the newest one
turned it into a lie. ⭐⭐ *A list rendered as pairs is a claim the data never made.*

## Decision

**Pair them once, in the analytics, and return `swaps`** — so the CLI, `ask`, the web app and the phone
cannot disagree about who replaces whom. The same argument as the scores card's `status`.

The rule:

1. **Same position first.** Not because FPL requires it beyond the keeper, but because *"Guéhi for
   Virgil"* reads as a decision and *"Guéhi for Pickford"* reads as a mistake.
2. **Anything else may cross positions** — a legal XI can change shape, and a defender in for a midfielder
   is a real substitution.
3. ⚠️⚠️ **A keeper never falls back.** With no keeper going out there is **no pair to make**, and saying
   so is the whole point.

The client renders `swaps`, and keeps the unpaired lists as the fallback for an older payload — printed
the way the CLI always has, as two groups.

## 🔴 Three things the tests did not catch

**The keeper rule did not decide anything.** A mutation deleting it survived: same-position matching
already pairs GK with GK whenever both are present, so the two were indistinguishable on every realistic
input. ⭐ *A rule that cannot change an outcome is not a rule* — it now refuses to pair rather than falling
back, and a test constructs the case where that differs.

**`sqlite3.Row` has no `.get`.** Ten Streamlit tests failed while every test in the new file passed,
because Streamlit passes rows **straight from the store** rather than through JSON. ⭐ *The one surface
that does not serialise is the one that finds this*, and `kits._get` has carried the convention for it all
along.

**The heading counted a different list from the lines.** It read `bring_in.length` while the lines came
from `swaps`, so a change the server declines to pair — the keeper case above — would be announced as a
change and then not shown. ⭐ *Two numbers drawn from two lists is a discrepancy waiting for the input that
separates them*, and no realistic payload separates them, which is why it survived the first pass. The
heading now counts the lines it is about to print.

📌 The renderer — the actual site of the fault — had no test of its own; the first version of this fix
tested only the analytics. `mobile/test/lineup_swaps_render_test.dart` covers it now, and the mutation
restoring the index-zip fails two of its four tests.

## Consequences

✅ `gameweek-plan`'s contract sample gained `swaps`, which the contract test caught as the shape change it
is.

📌 `_suggested_lineup` (My Team's apply-lineup) keeps its unpaired lists: `apply_plan.dart` lists names and
never pairs them, so adding a field nothing reads would be worse than leaving it.
