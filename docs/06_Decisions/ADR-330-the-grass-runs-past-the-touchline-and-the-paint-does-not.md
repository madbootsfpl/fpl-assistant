# ADR-330 — The grass runs past the touchline and the paint does not

*The halfway line fell through the middle of the screen, and the team stood somewhere else.*

**Date:** 2026-09-29
**Status:** Accepted
**Touches:** ADR-253 (one green area), ADR-293 (the bench beside the pitch), ADR-329 (the turf)
**From:** the owner, on a landscape screenshot — *"the pitch is off centre in landscape mode. This is not new."*

---

## Context

`PitchMarkings` wrapped `PitchBoard`, and `PitchBoard` contains the bench. So the markings centred
themselves on the **whole** box while the eleven centred on the box **minus the bench**.

| | markings centre | team centre | out by |
|---|---|---|---|
| landscape 802×527 | x = 401 | x = 348 | **53px** |
| portrait 390×760 | y = 380 | y = 248 | **132px** |

⭐⭐ **One defect, two orientations, and the larger one is the one nobody reported.** Portrait is 2.5× worse
and invisible, because a pitch whose far end runs off the bottom of the screen reads as *a pitch
continuing*. Landscape puts a bench down one side and gives the eye a straight edge to measure against.
⚠️ *A defect visible in one orientation and invisible in the other is still one defect* — and the report
that arrives is not necessarily the worse half.

🔴 **It had been true since ADR-293** put the bench beside the pitch, which is what *"this is not new"*
means, and no test could have caught it: every existing test asked whether the geometry was **correct**
(ADR-223's laws-of-the-game work) or whether the green **filled the screen** (ADR-253). ⭐ *Both were
right. Nothing asked whether they agreed with each other*, because nothing owned the relationship.

## Decision

**Two widgets, because there are two things.**

* `PitchTurf` — the grass. Fills whatever box it is given, so the green still runs behind the bench.
  ADR-253's argument is untouched and still right: *a pitch that stops two thirds of the way down reads
  as a web page with a picture on it.*
* `PitchLines` — the white markings, laid out by `PitchBoard` around **the rows and nothing else**.

⭐⭐⭐ *On a real pitch the grass runs past the touchline and the paint does not.* One widget could not say
that, so it said something false in both orientations. The mown stripes stay with the grass, for the same
reason: **a mower does not stop at the touchline.**

Both callers — the live pitch and `ResultPitch` — reach the board through `PitchBoard`, so the fix lands
once and both get it.

## Verified

Three tests in `the_pitch_is_centred_on_the_team_test.dart`, **all three failing against the old
structure** — restored it and watched them go red. They measure where the centre circle is actually
painted, in screen coordinates, against where the eleven actually stand.

⚠️⚠️ **My first measure was wrong and reported a centred pitch as 17px out.** It averaged all eleven cards,
which weights the answer by how many stand in each row — 1 · 4 · 4 · 2 — and pulls it toward the middle.
⭐ *A measurement that looks like the thing you are measuring is the easiest kind to get wrong*; the rows
are each `Expanded`, so the centre of the playing area is the mean of the four **row** centres.

⚠️ **The landscape case was not landscape.** `flutter_test`'s window is 800×600 and a `SizedBox` wider than
it is silently clamped, so the 802px case ran at 800. ⭐ *A test that names a shape it was not given is
testing the default surface under another name.* Pinned with `setSurfaceSize`.

490 Dart tests.

## Consequences

**Good:** the pitch is centred on the team in both orientations, on the live pitch and the season pitch,
and the green still runs full-bleed. The markings now also sit in a box that does not include the bench,
so they scale to the playing area rather than to the screen.

**Costs:** ⚠️ two widgets where there was one, and `PitchBoard` now owns a piece of the pitch's appearance
rather than only its layout. That is the relationship nobody owned, so it had to go somewhere — but it is
a new thing to keep in mind when either moves.

⭐ **This closes the 2D pitch.** The turf (ADR-329) and the centring are both in; the 3D pass is a separate
question and is not owed anything by this one.
