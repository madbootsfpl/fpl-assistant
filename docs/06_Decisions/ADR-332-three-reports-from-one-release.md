# ADR-332 — Three reports from one release

*Build 34 went out. Landscape did not work at all.*

**Date:** 2026-09-29
**Status:** Accepted
**Fixes:** ADR-331 (the perspective pitch) · **Enforces:** ADR-312 (one wordmark)
**From:** the owner, on build 34 — *"keeper is way too high"* · *"MADBOOTS on hoardings is not per our
style guide"* · *"and landscape isn't working at all"*

---

## 1. 🔴 Landscape could not work, at any setting

Not a tuning problem. A landscape phone leaves **281px** of board after the header and mode bar, and
the perspective view has to stack a keeper in the goal plus three rows — **320px** at the 70pt card
that is already the floor. **39px short, with nothing to give**: landscape is wide, so ADR-331's
card-width rule never binds, and height is what runs out.

⭐⭐ *A design that does not fit is not a design that needs tuning.* **Sideways falls back to the flat
pitch**, which ADR-293 and ADR-330 built for exactly that shape. ⭐ It also turns ADR-331's stated cost
into a benefit: the 2D path is no longer dead code kept alive by tests — **it ships, in every landscape
phone**.

### And it shipped, which is the part worth sitting with

I rendered portrait at three formations and two screen sizes and never once rendered landscape, in a
change whose previous ADR was *about* a landscape bug. ⚠️⚠️ **The tests I wrote to prove ADR-331's
constraints were all portrait too**, so a green suite said nothing about half the orientations.
⭐⭐ *Coverage of the case you were thinking about is not coverage.*

Two wrong turns before the shape of it was clear, both recorded because each looked like the fix:

* **Rows in metres.** A short board shows 58m of pitch where a tall one shows 87, so rows fixed at
  44/68/86m put the attack past the near edge.
* **Rows as a fraction of the plane.** The plane deliberately runs past the bottom of the screen, so a
  fraction of *it* is not a fraction of what anyone sees. This broke portrait as well.

⭐⭐⭐ **The third attempt inverts the projection**: say where a row should sit *on the board*, and solve
the pitch backwards. `y = ly·cos·d / (d − ly·sin)` rearranges in one step, so a row still stands on the
grass and still scales with depth, but it lands where the layout needs it at any shape.

⚠️ `crop` was also a flat 110px — 22% of a portrait board and **37%** of a landscape one. *A pixel
budget tuned on one screen is a different design on another.* It is a share now.

## 2. The keeper was up in the advertising

Reported as *"bottom of jersey starts on the cross bar."* His card was centred on the goal mouth — but
a card is ~80pt tall and its **kit is only the top 34pt**, so its middle is nowhere near its shirt.

⭐ *Aligning a thing by its bounding box aligns the box, and nobody is looking at the box.* The shirt is
centred in the mouth now, which puts the name and the price below the goal line where they are legible
against grass.

## 3. 🔴 A seventh hand-built MADBOOTS

I painted the hoardings' lettering with a `TextPainter` in one flat purple, upright, tracking in pixels.
The brand is **MAD in purple, BOOTS in orange, italic, tracking in em** — which is the whole of ADR-312,
written after six hand-built copies disagreed.

⚠️⚠️ **`wordmark.dart` has cited `test_one_wordmark.dart` since ADR-312 and that test did not exist.**
⭐⭐⭐ *A guard a file's own documentation claims is protecting it is worse than no guard*, because
everyone who reads the file believes the rule is enforced — I did.

The hoardings are a **widget layer** over the painted band, so they use `Wordmark` itself. The guard now
exists: nothing outside `brand.dart` and `wordmark.dart` may spell the brand, and the pitch painter may
not construct a `TextPainter`.

⚠️ Its first version failed on **its own comment**, which contains the word `TextPainter` while
explaining why the call went. *A guard that reads prose is a guard that fires on the note explaining it.*

## Verified

512 Dart tests. All three fixes checked against the bug they name by restoring it:

* keeper centred on the mouth again → the jersey test fails;
* 3D in landscape again → the fallback test fails;
* a `TextPainter` back in the painter → the wordmark guard fails.

## Consequences

**Good:** landscape works, the keeper is in his goal, the brand is the brand. The 2D pitch now ships
rather than waiting.

**Costs:** ⚠️ the app draws its pitch two different ways depending on which way the phone is held. That
is defensible — they are different shapes with different room — but it is a thing to hold in mind, and
`Pitch3D.on = false` still returns everything to one.

⚠️ **Open:** the hoardings run off both sides, so the wordmark is clipped at the edges. Still not
decided, still nobody's complaint.
