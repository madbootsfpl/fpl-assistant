# ADR-331 — Paint it flat and tilt it

*A perspective pitch, from a reference the owner drew a box round.*

**Date:** 2026-09-29
**Status:** Accepted
**Builds on:** ADR-329 (the turf), ADR-330 (turf and paint are two things), ADR-253, ADR-293
**From:** the owner, with a 3D mockup — *"can you recreate that?"*

---

## Context

I told him a tiled turf could not recede with the lines, and that the 3D pass would be expensive
because `PitchBoard`'s card scaling would have to move with it.

🔴 **Both were wrong, and the reference showed why.** Measured off his image: the cards there are
**90–100px at every depth** — the pitch is in perspective and the players are not. And the way to get a
perspective pitch is not to draw one: ⭐⭐⭐ **paint the pitch flat, exactly as we already do, and tilt the
whole painting.** One `Matrix4` with a perspective entry gives perspective-correct grass, foreshortened
markings and a receding horizon, and nothing is computed in perspective by hand.

## Decision

`lib/pitch_3d.dart`. The plane is painted top-down in **metres** and tilted 39° at a camera distance of
850px. Behind the goal line: 14m of run-off, then the hoardings. The keeper stands **in the goal**, not
on the pitch — which hands the outfield a whole row back.

### The two rules that make it hold

Everything else here is a number the owner chose. These two are not, and they are why it survives a
formation change:

* **The card width is measured, not picked.** The most crowded row sets it, floored at **70pt** — the
  size the flat pitch already ships, and therefore the smallest text known to be readable here.
* **The row's y comes from the pitch; its x comes from the screen.** Spread across the pitch's real
  width the cards ran off both edges and collided in the middle, because the pitch is 1.41× the screen.
  ⭐ *Depth is a pitch measurement; legibility is a screen one.*

### The revert switch

`Pitch3D.on = false` restores build 33's flat pitch. `PitchTurf` and `PitchLines` are untouched and
**still tested** — `pitch_layout_test` and `the_pitch_is_centred_on_the_team_test` now set the flag off
for exactly that reason. ⭐ *A new look that cannot be turned off is a new look you have to be sure
about.* The last build without any of this is tagged **`pitch-2d`**.

## Verified

`the_pitch_holds_every_formation_test.dart` writes the owner's own constraints down as tests, across
**five formations and two screen sizes**: five defenders fit · five midfielders fit · no card overlaps
another · no card crosses into the bench · the card never draws below 70pt.

⚠️⚠️ **Three of my own measurements were wrong, and only the app settled them.**

* **97pt was never viable** — four cards need 388px and a phone row has 382. It overlapped from the
  first render and I quietly dropped to 82 instead of saying the number was impossible.
* **Then I shrank to 66pt**, below anything ever shipped, by applying ADR-253's *tablet up-scaling*
  factor as a shrink. ⭐ *The answer was already in the app: 70pt, five of which have always fitted.*
* **My model of the layout was 66px out**, and I only found it by making the test print where the cards
  actually landed. Every position here is measured or solved, never nudged.

🔴 **And a clamp I added did nothing.** I saw two renders, believed the second was better, and credited
a guard that the mutation test says changes not one pixel — on either screen, in any formation. Removed.
⭐⭐ *An improvement you can see but cannot measure is an improvement you have not made.*

The far and near ends are nothing alike, which is the fact behind all three mistakes: **4m is 11px at
the goal line and 2m is 109px at the bench.** A metre at the near edge is worth twenty at the far one,
so no position here can be judged by eye.

508 Dart tests.

## Consequences

**Good:** the pitch looks like a televised one, and it holds at 3-4-3 through 5-3-2 on a 360px phone.
The grass recedes with the lines, which ADR-329 left open as the thing that could not be done.

**Costs:** ⚠️ two layout paths in `PitchBoard` behind a flag, and the 2D one is now exercised only by
tests. That is the price of the revert switch and it was asked for deliberately — but it is a cost that
grows, and the flag should not live forever.

⚠️ **Open:** the hoardings run off both sides, so `MADBOOTS` is clipped at the edges. It reads as a real
ground and nobody has complained, but it was not decided. The owner also floated a crowd behind the
hoardings, and talked himself out of it in the same sentence.
