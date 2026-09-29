# ADR-329 — Only a photograph says grass

*A two-stop gradient can say "green". It cannot say "grass".*

**Date:** 2026-09-29
**Status:** Accepted
**Touches:** ADR-223 (the painted pitch), ADR-135 (over-densification), ADR-253 (one green area)
**From:** the owner, with a mockup of his own — *"could we just focus on changing the green grass first,
and only changing the green on the pitch"*

---

## Context

The pitch has been a `LinearGradient` from `#419462` to `#34754E` since ADR-223, with eight mown bands at
3.5% white over it. That was the right call at the time and for the stated reason: **vectors scale to any
phone without an asset**, and the markings must sit relative to the card rows rather than on a fixed
background.

⭐⭐ **That argument was about the markings and it was quietly extended to the surface.** They are not the
same problem. A penalty box is geometry and must be computed. Grass is *texture* — thousands of blades at
no particular position — and ⚠️ *a gradient cannot be made to look like grass by choosing better stops,
because what makes it grass is the noise, not the colour.*

### How the numbers were agreed

The owner could not get the look out of his head and into a brief, and three rounds of my mockups missed —
his words, *"none of these are close at all"*. So the tool changed rather than the process: an HTML mirror
of `pitch_markings.dart`, every constant on a slider, flat by default and verified to place the four card
rows at the same 159 / 301 / 443 / 585 px the app does. He then tuned it and sent the numbers back.

⭐⭐⭐ **This is the part worth keeping.** *A design conversation stalls when one side can only describe and
the other can only build* — and it unstalls the moment the describing side gets something to move.

## Decision

### The grass is an asset; everything else stays painted

`assets/pitch-grass.webp`, a seamless 512 px photograph tiled at **180 logical px** over a `#146B30` base,
with the mockup's own two lighting layers over it and **under** the markings:

* a vignette — an ellipse as wide as the pitch and 85% as tall, centred at 35% — fading to
  `rgba(0,15,5,0.55)` at the edge;
* a top light, `rgba(255,255,255,0.06)` down to `rgba(0,0,0,0.15)`, at **0.65** of the mockup's strength.

⭐ *The photograph alone looks like wallpaper; it is the lighting over it that makes it a place with a
middle and edges.*

### WebP q92, and not lower

| | size |
|---|---|
| source PNG, 1024 px | 1,782 KB |
| PNG, 512 px | 439 KB |
| **WebP q92, 512 px** | **69 KB** |
| WebP q75, 512 px | 18 KB |

🔴 **q75 is measurably broken and looks fine in isolation.** Lossy compression smooths the blades — mean
neighbouring-pixel difference falls from 4.26 to 3.01 — while leaving the wrap-around edges at 5.00. ⚠️ *The
tile's own seam becomes the sharpest edge in the image*, so it tiles as a visible grid. q92 holds the seam
ratio at 1.07 against the source PNG's 1.03, for 16% of the PNG's bytes.

⭐ **Checked, not assumed.** The seam is a property nobody would look for and a reviewer cannot see in one
tile.

### The lines went from 22% white to 42%

⚠️⚠️ **This contradicts the comment that stood above them**, which said the markings are *"deliberately
faint … the eye must land on the xP number first"* and cited ADR-135. That reasoning is unchanged and the
number still has to move: **0.22 was tuned against a flat gradient.** A photograph of grass carries texture
of its own at roughly that contrast, so ⭐ *a line drawn faintly over a flat colour reads as a line; the same
line over noise reads as more noise.*

Also from the owner's tuning: the centre circle from `w * 0.125` to `w * 0.13`, and the mown bands from
eight to six.

### The turf arrives late, and the pitch does not wait for it

The asset is decoded off a `Future` held statically — ⚠️ *a cache keyed on "have I finished yet" races with
itself; one keyed on the request does not* — and until it lands, **the painter draws the old gradient**.
A failed decode lands in the same place. ⭐ *A pitch that waits for its image is a pitch that flashes empty,
and on a cold start that blank is the first thing anyone sees.*

## Verified

487 Dart tests (three new), and the two that matter were **checked against the bug they name**:

* 🔴 **`shouldRepaint` returned a flat `false`**, correct for a painter of pure geometry and fatal for one
  holding an image: the grass would decode, be handed over, and never appear. Reverting it fails the test.
* ⚠️⚠️ **The cold-frame test passed with the background deleted.** It asserted that *something* filled the
  pitch, and the top light is itself a full-size rect — ⭐ *a test that watches the calls cannot tell a
  background from a film laid over one.* It now rasterises and reads the pixel, and fails on that mutation.
* The asset is asserted **declared in `pubspec.yaml`**, not merely present on disk: an undeclared asset is
  missing at runtime, and the failure mode is a silent fallback to the gradient that nobody would report.

**Manual:** the painter rendered to PNG at 390×760 and looked at.

## Consequences

**Good:** the pitch looks like a pitch. 69 KB of APK, one asset, one widget changed; `PitchBoard`,
the cards and the bench are untouched, and `season_view.dart` gets it for free from the same widget.

**Costs:** ⚠️ `PitchMarkings` is now stateful and has an async dependency, where it was a pure painter. That
is a real increase in the number of ways it can be wrong, bought for one visual effect.

⚠️ **Open — and the reason the geometry file now carries a projection it does not use:** the owner's larger
want is a **3D pitch**, and he left *far width* at 1.00 this round on purpose. When it moves, the turf will
need to recede with the lines, which a tiled shader cannot do — and the card scaling in `PitchBoard` has to
move with it, or ⭐ *the players stand on a flat grid above a pitch in perspective*, which reads as broken
rather than as 3D.
