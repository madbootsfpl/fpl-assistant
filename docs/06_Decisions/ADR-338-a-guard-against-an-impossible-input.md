# ADR-338 — A guard against an impossible input

*ADR-337 made the bank go negative. Everything downstream still believed it could not.*

**Date:** 2026-10-01
**Status:** Accepted
**Fixes:** a consequence of ADR-337 · **Touches:** ADR-226 (over budget is a warning, not a block)
**From:** the owner, within an hour of build 38 — *"bank does go negative & red. However when I try to
transfer him or anyone else get this error"*

---

## What happened

The fix worked: planning Haaland in took the bank to **−£8.6m**, red, labelled *Over budget (est.)*.
Then every player tap answered with

```
[{type: greater_than_equal, loc: [body, bank], msg: Input should be greater than or equal to 0,
  input: -8.6, ctx: {ge: 0.0}}]
```

🔴 **Two faults in one screenshot.**

### 1. A guard written when the input was impossible

`_check_money` refused a negative bank, and six Pydantic bodies carried `ge=0`. The reasoning was
sound at the time:

> ⚠️ A negative bank is not a rounding artefact — it silently makes every transfer unaffordable, and the
> answer comes back as "no moves found", which reads as a settled squad rather than a bad request.

True while only a broken client could send one. ⭐⭐⭐ *A guard written against an impossible input becomes
a wall the day the input becomes real* — and ADR-337 made it real the same afternoon.

**Bounded rather than removed.** `MIN_BANK = -50.0`: a plan that spends £9m it does not have is a screen
the app now draws; a typo of −900 still is not. ⭐ *The guard was not wrong, its threshold was zero.*

⚠️ Nothing else needed changing: `replacements` returns over-budget candidates **flagged, never
filtered** (ADR-226), so a negative bank degrades into "everything is dear", which is the truth.

### 2. A raw validation payload where a sentence belonged

`errorDetail` read `decoded['detail']` and stringified it. For a 422 that detail is a **list of
objects**, so the reader got the machinery. ⭐ *An error the reader cannot act on is the same as no
error, except it also says the app is broken.*

It now renders `loc` and `msg` as `bank — Input should be greater than or equal to 0`, one per line.

⚠️ And the generic fallback no longer accepts a `List` at all: an **empty** detail list stringified to
`"[]"`, which is the same fault with less of it.

## Verified

3,034 Python and 531 Dart tests. The reported path is asserted end to end through `TestClient`: bank
−8.6 returns **200**, −900 still returns 422.

⚠️⚠️ **Four tests asserted the old rule**, three of them naming it in the parameter id —
`"bank cannot be negative"`. They now use −900, and say why in a comment. ⭐ *A test that pins a
threshold pins the reasoning behind it, and the reasoning moved.*

⚠️ One of them, `test_a_malformed_body_is_refused_before_the_database_is_opened`, stopped failing with a
422 and started failing with a `ZeroDivisionError` — because a one-player squad now reaches code that
divides by the squad size. That is a real crash on an input no client sends, left alone deliberately:
it is not this bug, and finding it by accident is not a reason to fix it inside an unrelated commit.

## Consequences

**Good:** the feature shipped in build 38 is usable. An overdrawn plan is now a state you can keep
working in — pick the player you are selling, see everything flagged dear, and fix it.

**Costs:** ⚠️ six endpoints now accept a value they will never produce a good answer for. The honest
mitigation is that `replacements` *does* answer sensibly; the others return fewer or no moves, which the
red header already explains.

⭐ **The pattern worth keeping:** this bug shipped an hour after the change that caused it, and the
change was tested. ⚠️ *Tests prove the thing you built works; they do not notice what it made possible
elsewhere.* The one that would have caught it is the one nobody writes — a screen driven past its new
boundary, calling the next endpoint.
