# ADR-284 — The order is the argument

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner — *"The More tab, remove Signals, and reorder, Mini Leagues, Fixture Ticker change to
Fixture Difficulty Rating, Team DNA, Chip, Squad Lab, Help, Feedback, and Settings"*
**Follows:** ADR-238 (More is a directory, not a menu), ADR-283 (Signals took a tab)

---

## Signals leaves, because it has a tab now

ADR-283 gave Signals a place in the bottom row. Leaving the row in More as well looked like generosity and
was not: ⚠️⚠️ *a directory that still lists what the nav bar carries is teaching two routes to one room and
calling the second one a feature.* The plumbing goes with it — `onOpenSignals` is gone from `MoreView`
entirely rather than left unused.

## The rename says what the reader already calls it

**Fixture ticker → Fixture Difficulty Rating.**

*Ticker* is the name of the widget. **FDR** is the name every FPL manager already has for the thing — ⭐ *a
row named after its implementation asks the reader to learn your vocabulary before they can decide whether
they want it.* The screen title follows the row, because ⚠️ *a list item and the screen it opens disagreeing
about their own name is how a reader concludes they tapped the wrong thing.*

## The order the owner asked for, and what it turns out to encode

```
Mini-leagues                 ← weekly
Fixture Difficulty Rating    ← weekly
Team DNA                     ← a handful of times a season
Chips
Squad Lab
Help & videos                ← about the app, not the game
Tell us something
Settings
```

⭐ **Frequency, then subject.** The two you open every gameweek lead; the three season-scale decisions sit
behind them; the three that are about the app rather than the game go last. ⭐ *The least-used rows are the
ones you can always find, because they are the ones you go looking for by name* — which is the same
argument ADR-230 used to put Chips in More in the first place, applied one level down.

## ⚠️⚠️ And the order is now pinned, which it was not

This is the **third** list reordered on feedback in two days — Trending's pills twice, and now this — and
every time the full suite stayed green either way.

⭐⭐ **An order no test names is an order the next edit reverses by accident, and the only reader who
notices is the owner**, from a screenshot, days later. The More test now asserts the exact sequence and the
absence of Signals; 3/3 mutations killed, including two rows swapping places, the old ticker name
returning, and a Signals row creeping back in.

The tests that already existed needed changing too — they passed `onOpenSignals` and expected
`Fixture ticker`. ⭐ *That they failed to compile is the guard working*: a required callback that vanishes
should break its callers loudly rather than be quietly ignored.
