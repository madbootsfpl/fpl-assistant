# ADR-368 — A claim about nothing

**Date:** 2026-10-26
**Status:** Accepted
**Found:** `test_the_displaced_player_was_actually_starting`, red on master as the season moved
**Extends:** ADR-273

---

## Context

`/transfers` tells you who a move would **displace** — *"to get this gain, you also have to bench X."* It
was naming players who were **already benched**.

Reproduced under the suite's own conditions: the engine offered a move displacing **Pickford**, who was on
the caller's `bench_ids` list in the same request.

⭐⭐ **It is ADR-273's complaint in a second place.** That ADR exists because the owner said *"Leno to
Tzolakis won't provide a +2.2 xP as I will be playing Pickford"* — a gain that assumed he would start a
keeper he benches. The **gain** learned about his bench. ⚠️ *The sentence underneath it did not.*

## The cause

`_lineup_condition` compares the **best legal XI** before and after:

```python
before = best_legal_xi(owned, rank_xp)
dropped = [p for p in owned if p["id"] in before and p["id"] not in after and p["id"] != out["id"]]
```

`before` is the engine's **optimal** XI, not the manager's actual one. Where they disagree — and a benched
strong keeper is exactly where they disagree — a player can be "dropped from `before`" without ever having
started.

📌 `bench` was computed eleven lines above the call site and **not passed in**. The information was there.

## Decision

Exclude anyone already on the manager's bench from `displaces`. ⭐ *A player who was not starting cannot
stop starting*, and `displaces` exists to say what the reader must **do**.

## Consequences

✅ Two mutants, each caught: restoring the bug, and deleting the feature by never naming anyone — the
second fails `test_a_move_says_whom_it_would_displace`, which has always required the real squad's fixture
to contain a lineup-changing move.

📌 **A hand-built regression test was written and then deleted.** Reproducing "the optimiser displaces
someone" in a synthetic squad is a fixture fighting the optimiser, and the guard that matters already
exists on the real one. ⭐ *A second test that is harder to trust than the first is not a second test.*

⚠️ **It surfaced because the data moved, not because anyone looked.** The bug was reachable the day
ADR-273 shipped; it took a season advancing far enough for the engine's XI and the owner's to disagree in
the committed snapshot. ⭐ *A test that only fails on some data is a test that was passing for the wrong
reason until then* — and this one went red on its own, which is the version of that worth having.
