# Sprint 254: Close set-piece as unmeasurable (ADR-096 → ADR-190)

**Dates:** 2026-09-13
**Status:** ✅ Complete — the set-piece xP term is **removed**, not zeroed. **1762 → 1758 tests, ruff clean.**
Verified byte-identical on live data: **657 players, 0 projections changed.**

> Owner, on the gate ADR-190 left open: *"close set-piece as unmeasurable."*

---

## Why removed rather than left at 0

ADR-101's stopping rule: *anything still failing is closed as not supported — not left as a permanent
"revisit later", which is how a dormant weight becomes furniture.*

A weight sitting at `0.0` reads to the next person as **"not calibrated yet"**. This one is *"asked and
answered"*, and the difference matters because the answer is permanent: the term can reach **9 of 657**
players and `history_by_code` holds only completed seasons, so that 9 is fixed for the season. There is no
future gameweek at which this becomes measurable by a whole-board metric.

So the constant is gone and `config.py` carries the reason in its place — because *"why is there no
set-piece weight?"* is exactly the question a future reader asks at that spot.

## What was removed

`config.SET_PIECE_WEIGHT` · the `set_piece_weight` parameter on `player_xp` · the rate branch in `xp.py` ·
the `set_piece_xp` output field (US-314) · its `+X xP set-piece edge` clause in `explain.py` · the
`set_piece` entry in `_CALIBRATE_WEIGHTS` · `src/analytics/setpieces.py` entirely.

Two of those were only found by the test suite failing, which is the argument for deleting rather than
zeroing: **an inert term has inert dependents, and you do not know how many until you pull it.**

## What survives, deliberately

**The duty.** `crowd.SET_PIECES` renders ⚽/🚩/🎯 on the pitch and never depended on the xP term; the Scout
board still reads first-choice duty as a *worth-a-look* signal. The reason string still says
**"Penalty taker"** — it just no longer offers a number afterwards.

> **The app tells you who takes the penalties and declines to tell you what that is worth.**

Which is [ADR-057](../06_Decisions/ADR-057-crowd-signals-lens.md)'s lens rule reached from the other
direction. That ADR says a signal may not enter `decision_xp` **on assertion**; this term tried to enter on
**evidence**, and the evidence could not be gathered. Same destination, opposite route — and it is the same
place ADR-188's clean-sheet term is heading.

## Guards, all mutation-tested

`tests/test_setpieces_closed.py` replaces `tests/test_setpieces.py`:

| mutant | caught |
|---|---|
| the weight comes back, dormant at `0.0` | ✅ (3 tests) |
| the closed question is sweepable again (`set_piece` back in `_CALIBRATE_WEIGHTS`) | ✅ |
| a `set_piece_weight` reference returns anywhere in `src/` | ✅ |

The last is a **sweep for the claim**, not a check of the files I thought of — ADR-184's lesson, where a
retired claim survived 14 days on six surfaces because two guards both checked the same two files.

And the guard that matters most is the one protecting what *stayed*: a "tidy-up" that removed the ⚽ glyphs
along with the weight would be a real regression dressed as consistency.

## Two tests that broke, both correctly

- `test_the_scout_shortlist_never_promises_points` asserted `config.SET_PIECE_WEIGHT == 0.0` — and **errored**
  when the weight was deleted. ⭐ *A test pinned to how a fact is currently stored fails when the fact gets
  more true.* Rewritten to assert the requirement: the weight must not **exist**.
- My own new test asserted `set_piece_glyphs` returned a string; it returns `(glyph, label)` tuples. Caught
  immediately because the lens is real and the test was not.

---

## 💡 The lesson

> **The design decision that made the term correct is the one that made it unmeasurable.**

ADR-096's best idea was refusing to apply the bonus on the trusted historical baseline, because that baseline
already contains an established taker's penalties. Double-counting avoided — genuinely right. But it is
precisely that restriction which shrinks the term's reach to nine cold-start players, and nine players cannot
move a statistic computed over 626.

The correctness and the unmeasurability are **the same fact seen from two sides**, which is why neither the
original ADR nor §B0's pre-registered criteria caught it: both reviewed the term's *logic*, and the problem
was in the relationship between its **scope** and the **instrument**.

Worth carrying forward: when a term is deliberately narrowed to avoid double-counting, ask at that moment how
many rows it still touches — and whether the thing that will judge it can see that many.

---

## Definition of Done

1. **Tests: 1762 → 1758** (six focused closure guards replace ten tests of a term that no longer exists),
   three mutants confirmed red.
2. **Manual smoke** — `decision_xp` over 657 live players before and after: **0 projections changed**.
3. **Docs** — ADR-096 status + closure note, ADR-190 gate ticked, `GW1_RUNBOOK` (§B0 table, step 2, the
   sitting record, the tripwire note), ADR-000 index, PROJECT_STATUS, Roadmap, this retro.
