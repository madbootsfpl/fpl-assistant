# ADR-333 — A layout that has to be told about its content

*The perspective pitch is reverted. Four builds, and it broke on three surfaces nobody had rendered.*

**Date:** 2026-09-29
**Status:** Accepted
**Reverts:** ADR-331 · **Keeps:** ADR-329 (the turf), ADR-330 (turf and paint), ADR-332's landscape rule
**From:** the owner, with two screenshots of the season pitch — *"the players are all over the place …
as much as I like it, I'm leaning to reverting"*

---

## What was wrong

Those screenshots were the **season pitch**, which draws a different card:

| | height at the 70pt design width |
|---|---|
| live card | **80px** — kit · name · points · fixture |
| season card | **111px** — the same, plus event icons and a minutes line |

The perspective pitch places rows at **fixed fractions of the board** — 0.40 / 0.62 / 0.84, or 110px
apart. ⚠️ *A 111px card in a 110px gap overlaps by construction*, and worse once the signals banner
takes its share of the screen. Every row's fixture line sat under the next row's shirt.

## Why it is reverted rather than fixed

It is fixable — derive the rows from the tallest card the board is actually handed. An hour, maybe.
That is not the reason.

⭐⭐⭐ **The flat pitch divides its space with `Expanded`, so any card height works, including ones that
do not exist yet. The perspective pitch positions rows absolutely, so the card must fit the gap and
nothing makes it.** One layout is told the content; the other is not. *A layout that has to be told
about its content will be wrong about content nobody told it about.*

🔴 **And that is not a prediction — it is the record.** Three surfaces broke that I had never rendered:

| | found by | suite at the time |
|---|---|---|
| landscape | the owner, on a shipped build | 508 green |
| the season pitch | the owner, on a shipped build | 512 green |
| the foreground crop in landscape | me, while fixing the first | 508 green |

⚠️⚠️ Every one of my tests pointed at `PitchView`, and `PitchBoard` has two callers. ⭐⭐ *Coverage of the
surface you were thinking about is the coverage that tells you least*, because the surfaces you forget
are exactly the ones nothing covers.

## Decision

`Pitch3D.on = false`. The app draws the flat pitch again.

**What stays, because none of it was the problem:** the turf (ADR-329), the lines at 0.42 and the
centre circle at 0.13, the markings centred on the team rather than the screen (ADR-330), and the
70pt card floor that came out of the owner's constraints.

**What goes:** the tilt, the goal, the hoardings, the keeper in the net.

⚠️ `lib/pitch_3d.dart` is kept and still tested — its tests now switch it on deliberately, because
⭐ *retained code with no tests is not retained, it is abandoned in place.* It should be deleted if a
second attempt is not made; a flag with one setting is a fork nobody is maintaining.

## Consequences

**Good:** the season pitch is legible again, one layout instead of two, and the day's real gains are
untouched — the pitch is grass, centred, and its markings are the owner's own numbers.

**Costs:** ⚠️ four builds and most of a day for a look that did not ship. The owner called it *"a
valiant try"*; the useful part is knowing **why** it did not work, which is written above and is not a
fact about perspective at all.

⭐ **The part worth keeping** is the working method, not the pitch: an HTML mirror of the real
constants ended three rounds of failed mockups, and constraints — *five defenders must fit · the keeper
must never be cut off* — turned out to be solvable where numbers were not. Both survive this revert.
