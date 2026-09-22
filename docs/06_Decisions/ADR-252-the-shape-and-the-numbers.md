# ADR-252 — The shape and the numbers

**Date:** 2026-09-22
**Status:** Accepted
**Completes:** the DNA parity the owner asked for — radar, grade ring, club-vs-club compare
**Builds on:** ADR-118 (the eight axes), ADR-247 / ADR-251 (Team DNA)

---

## Context

Three things left from the owner's DNA screenshots.

⚠️ **And a correction owed first**: I argued against the radar partly on the evidence that his screenshot
of the web page showed *"FPL Output"* clipped to `'PL Output`. He pointed out that was his scroll position,
not the layout. ⭐ *A screenshot is a photograph of a moment, not of a design* — I read an artefact of how
it was captured as a property of the thing.

## Decision

### ⭐⭐ Radar **and** bars, not one or the other

A radar is very good at one thing — *is this a balanced side or a lopsided one?* — and poor at another:
you cannot read `74` off a vertex. The bars are the reverse. The web draws both for that reason, and the
phone does now. ⚠️ *Picking one would answer half the question and look like a decision.*

⚠️ **Null is drawn at the centre, not skipped.** Skipping closes the polygon across the gap and **invents a
shape**; the centre says *"nothing here"*, which is what null means.

### The grade ring

The arc is the score, the letter is the reading. ⭐ *A number alone makes a reader work out whether 83 is
good; a letter alone throws away the distance to the next grade.*

### Compare needs no endpoint

All twenty clubs arrive in the first fetch, so comparison is a **choice**, not a request. ⭐ Two clubs share
one radar, which makes comparison a *shape* rather than a table of differences — the thing a reader takes
in without counting. The picker carries each club's grade ring, because ⚠️ *choosing who to compare against
is itself a judgement, and a bare list of twenty names gives a reader nothing to make it with.*

## ⚠️⚠️ What building it found — the tests could not see three real bugs

The first round of painter tests asserted **"does not throw"**. Three mutations survived them:

* an unranked axis drawn at **mid-table** instead of the centre,
* the empty-axes guard removed,
* the ring's clamp removed, so a score of 140 sweeps 500%.

⭐⭐⭐ **A painter drawing a plausible-but-wrong shape throws nothing** — and a radar's entire job is to be
believed at a glance, *without* checking. The test file's own docstring said exactly this, and then the
tests underneath it could not see it.

**The fix was to make the geometry arithmetic.** `radarPoints`, `radarVertex` and `gradeArcSweep` are pure
functions now, asserted on exactly: first axis straight up, clockwise after, percentile as a fraction of
the radius, null at the centre, the arc clamped at both ends. All three mutations die, plus two more — a
radar rotated 90° and one mirrored.

⭐ Two more things the tests caught, both real:

**The radar overflowed a height-bounded parent** the moment a legend was added. It works in the app only
because it lives in a scroll view, where height is free — ⚠️ *a widget that only works in an unbounded
parent works by luck until someone puts it somewhere else.* `Flexible` now lets it shrink, and the bounded
case is kept as a test on purpose.

**And my own test harness hid an assertion.** *"Renders nothing"* was untestable while the wrapper forced a
320×320 box — a `SizedBox.shrink` inside a fixed square fills it. ⭐ *A harness that constrains the thing
under test measures the harness.*

## Verification

* **12 Dart tests**: five on the geometry as arithmetic, and seven on the widgets — including the legend
  only appearing for two clubs, the empty radar taking **zero height**, and its converse (a radar with axes
  taking room), because *a test that only checks "empty is zero" passes on a widget that always renders
  nothing.*
* **7/7 mutations killed** after the geometry was extracted.
