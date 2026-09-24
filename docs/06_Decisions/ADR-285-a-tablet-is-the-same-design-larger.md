# ADR-285 — A tablet is the same design, larger

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner (ADR-278's screenshots) — *"landscape reads well; portrait stretches the pitch and
leaves dead green space"*
**Follows:** ADR-253 (the pitch fills the screen)

---

## What "dead green space" turned out to mean

ADR-253 made the pitch fill the screen, and on a tablet it does — **91% of a 1280pt portrait screen.**
So the green was not the problem. The measurement was:

```
phone   390×760    pitch 651 (86%)   shirt 22.3×31
tablet  800×1280   pitch 1171 (91%)  shirt 22.3×31   ← the same shirt
```

⭐⭐ **The green stretched and the players did not.** Four rows divided 1171pt between them and each drew
a 70×86 card designed for a 390pt phone, so the shirts floated in bands of empty grass.

The card said why, in a comment that was right when it was written:

> *"Never up, only down: on a tall screen the card stays the size it was designed at."*

Correct for phones. The whole of the bug on tablets.

## The rule: proportion, not "fill the slot"

My first fix let each card grow into its slot. That helped and was still wrong — ⚠️ *the complaint was
about the gaps between the rows, and I read it as a complaint about the size of the shirts.* At 1.6× the
tablet still had 660pt of gap against 512pt of content.

A phone draws a 70pt card on a 390pt screen: **18% of the width**. A tablet drawing that same 18% gets
~143pt, and fills the rows vertically for exactly the reason it fills them horizontally.

⭐ **A tablet is not a phone with more room for whitespace; it is the same design, larger.** Driven off
`shortestSide`, so a tablet looks the same turned either way, and bounded by the row's own slot so a
crowded row can never overlap whatever the proportion asks for.

## ⚠️ Three mistakes, each caught by something that already existed

**Per row, not once.** I measured each row separately, which gave the lone goalkeeper a 112pt card above
82pt defenders — a row of one has the whole width to itself. ⭐⭐ *The code had already said why that is
wrong*: `_Card.width` is a constant precisely so **"a five-DEF row and a one-FWD row must draw the same
card, or the eye reads the wider one as more important."** Making a width responsive is not a reason to
stop it being uniform.

**The phone changed too.** The rule grew phone cards from 70 to 82, because a four-across row has slack at
70pt. ADR-253's layout was tuned by the owner against screenshots — ⚠️ *changing it as a side effect of a
tablet fix is how a report about one screen becomes a surprise on another.* Gated at the standard 600pt
tablet threshold, and the phone is now byte-for-byte what it was.

**`MediaQuery.width` is not the width you were given.** In the app the pitch is full-bleed so the two
agree; ADR-253's own tests hand the pitch a 390pt box inside an 800pt window, and **overflowed by 49px**
the moment I used the screen. ⭐ *A measurement taken from the screen rather than from the space a widget
was actually given is right until something is laid out beside it* — and a split-screen tablet is exactly
that something. A `LayoutBuilder` now supplies it.

## ⚠️⚠️ And a test that measured the container instead of the thing in it

A mutation removing the up-scaling entirely **survived**: the card's box was still 143pt wide while the
shirt inside stayed phone-sized, and the test measured the box.

Worse, the obvious fix did not work either. `tester.getSize` reports a widget's **layout** size, and a
`FittedBox` scales by a *transform* — so the kit measured 22.3×31 on a tablet and a phone alike. Only
`getRect`, which goes through `localToGlobal`, sees what is on the screen:

```
phone   22.3 × 31.0
tablet  45.6 × 63.6      ← 2.05×, and all fifteen agree
```

⭐ *If the change is something the eye can see, the test has to look where the eye looks.*

8/8 mutations killed, including the phone guard, the threshold, the proportion, the slot bound, the
ceiling, the bench wiring, the growth itself, and the return of `MediaQuery.width`.

## What this does not do

- **The bench matches the eleven**, as it always has on a phone — *a fix that stops at the edge of the
  thing that was reported is a fix that creates the next report.*
- **Nothing else on the screen scales.** The header, the mode bar and the nav are chrome, and chrome that
  grows with the screen is a waste of the screen. If they look small on a tablet, that is a separate
  report and a separate decision.
