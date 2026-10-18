# ADR-364 — Your players, on the week being played

**Date:** 2026-10-18
**Status:** Accepted
**Found:** the owner, on build 48 — *"i am not seeing my players?"*, against the agreed mockup
**Extends:** ADR-360, ADR-361

---

## Context

The card agreed at the gate has a **YOUR PLAYERS** block: *Isak — goal · 3 bonus — 9*. On the week being
played it was not there.

`yours` is built from `player_history`, and the backfill does not reach a gameweek until **every** fixture
in it is complete (ADR-211 2d). ⭐⭐ *So the block that makes this "not a livescore app" was missing on the
only week anybody was watching* — the same shape as ADR-361, one field along, and left behind by the fix
for it.

## 🔴 I had a reason, and it was wrong

ADR-361 deferred this deliberately:

> *"`yours` still waits for the backfill: the live payload has BPS and bonus but no `total_points`, and a
> points total this app worked out itself would eventually disagree with FPL's."*

True of `/fixtures/`. ⚠️⚠️ **But not of `event/{gw}/live/`**, which carries every player's `total_points`
*and* an `explain` block per fixture — FPL's own per-stat attribution, *"minutes 90 → 2, bonus 3 → 3"*.

📌 **That endpoint has been in this codebase since ADR-299**, added for exactly this reason, with a
docstring that says so: *"The alternative was to derive it, and it would already be wrong."* I reasoned
about a constraint without checking whether the repository had already solved it — the fourth time this
week a fact the project already held did not reach the module that needed it.

## Decision

**Three sources for `yours`, each a weaker claim than the one before:**

1. **stored history** — complete, local, never moves;
2. **FPL's live attribution** — for the week the backfill has not reached;
3. **team membership** — for a fixture not yet played, carrying null counters, never zeroes.

⭐ **The points are FPL's.** Summing `explain`'s per-stat points is reading FPL's arithmetic, not applying
the scoring rules here. ⚠️ *A hand-rolled table starts disagreeing the moment the game changes without
telling us* (ADR-299).

⭐ Per **fixture**, not per week: a double gameweek has two `explain` blocks and `total_points` cannot say
which match earned what. *A player credited to the wrong match is ADR-350 again.*

📌 One call for all 659 players, behind the same sixty-second cache, and **only when a played fixture has
no stored history** — a settled week asks for nothing.

## Consequences

✅ Five mutants, each caught — including *"points credited to every match in the week"*.

🔴 **The caption contradicted the card.** `yours_known` asked only the stored history, so the header said
*"your players not in yet"* over a card that was by then showing them. ⭐ *A caption disagreeing with the
thing underneath it is worse than the gap it was written for.* Either source counts now.
