# ADR-313 — A goal and a bonus point were the same shape

**Date:** 2026-09-27
**Status:** ✅ **Built.** Option C, chosen by the owner from three rendered at true size.
**From:** the owner's list — *"On the player page, could you replace the football and boot icons."*

---

## The decision

**Every event sits on one dark disc borrowed from the card's own ink, and the goal gets a pattern.** The
two numbered pips — bonus and saves — stay the only bright marks in the row.

## ⚠️ The brief was wrong, and finding out was the useful part

The owner sent a screenshot of a player card and a list item reading *"replace the football and boot
icons"*. Rendering the real widget showed **the app draws a plain white ring for a goal**, not a patterned
football — and the screenshot had patterned balls on white discs, a **dark** boot where ours is mint, and a
**grey** bonus circle where ours is amber. Three mismatches.

⭐⭐ **So the screenshot was never our app — it was the reference.** The suggestion image everyone was
waiting for had been attached all along, as a picture of what to copy rather than what to fix. 📌 *Worth
rendering the widget before believing a description of it*, including the owner's and including my own.

## 🔴 The defect, once it was visible

⚠️⚠️⚠️ **A goal and a bonus point were the same shape.** The goal was a plain circle; the bonus and saves
pips are circles with a number in them. At **13pt** the difference between them is a digit nobody reads at
that size.

⭐ `result_pitch.dart` already carried the rule it was breaking, in the boot's own comment: *"an icon that
has to be told apart from the icon beside it is doing less work than the word it replaced."* It was written
about the boot, and the ball was the icon it applied to.

⚠️ Second defect, smaller: the boot was **mint on the pitch's green** — the lowest-contrast pairing
available on the card.

## How it was chosen

Three options, drawn at the app's real geometry — a 76pt card, a 13pt icon — on a full pitch of eleven
cards, because ⭐⭐ *an icon judged alone is judged at the wrong scale: the question is what eleven of them
do to a screen, not what one does to a strip.*

| | | why not |
|---|---|---|
| **A** | white discs, dark glyphs | the reference's own construction, and the most legible — but four white discs across eleven cards are the first thing the eye lands on, ahead of the names |
| **B** | no discs, better glyphs | the smallest change and the calmest, but the least contrast |
| **C** ✅ | **dark discs, light glyphs** | reads as clearly as A, recedes instead of shouting, and leaves the amber pip as the only bright mark — *which suits bonus being the rarest event on the card* |

## The football, at nine points

⭐ A pattern is the whole difference between a football and a circle, and three marks are the fewest that
carry it: a centre panel and three short rim marks. ⚠️ The first attempt drew **spokes running to the
centre** and at this size it read as a **propeller** — *detail added to a small glyph subtracts from it.*

⭐ The glyph is drawn in a 24×24 space and scaled, so the proportions hold wherever it is used.

## Consequences

- ⭐ **Four hard-coded hexes left the file.** Mint, steel blue and amber were retyped in `result_pitch.dart`,
  the surface furthest from `brand.py` — ADR-312's rule, one component along. They are `EVENT_DISC`,
  `EVENT_GLYPH`, `EVENT_MARK`, `CLEAN_SHEET` and `BONUS` now.
- 🐛 **And the first translucent token broke the generator the day it was added.** `#16181DD9` is CSS's
  `#RRGGBBAA`; Dart wants `0xAARRGGBB`. Blindly prepending `FF` produced a **ten-digit literal**, which is
  not a colour — `_colour()` moves the alpha now.
- ⚠️ **Two tests were counting the box instead of the shape.** They matched a `Container` of
  `maxWidth == 10` coloured white — *which is precisely the plain circle that was the bug.* They count
  painters now, which asks the question they mean: **is this a football?**
- ⭐ A guard pins goal and bonus to different shapes, mutation-tested by deleting the football.

**2854 Python · 460 Dart.**
