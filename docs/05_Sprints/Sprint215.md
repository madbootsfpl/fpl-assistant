# Sprint 215: The price journey (ADR-160)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-160. 1515 → 1525 tests, ruff clean.

---

### 🔧 What shipped

The app could say where a price was **going** (ADR-092) and that one moved **this gameweek** (the crowd flag).
It could not say where a price had **been**. Now the trend card carries the price journey: what he costs, what
he has done since the season started, and a sparkline once there is one to draw.

**A discrepancy found while checking units decided the shape.** `value` is written when a gameweek is played;
prices move nightly. Watkins reads **£8.0m** in his GW1 row and **£7.9m** everywhere else in the app — so a
sparkline built from `value` alone would have ended on the stale number and visibly disagreed with the price
printed beside it. Today's live price is appended as the final point.

```
distinct rounds with a `value`      : [1]
players whose price moved since GW0 : 10 of 616
players with a 2-point price series : 9
```

Nine players can draw a line. So the **change** carries the feature now and the **line** carries it later —
`cost_change_start` is exact from day one. An unmoved price says "unchanged since the season started" rather
than drawing a dead-flat segment, which is the honest answer for 607 of 616 players.

A double gameweek cannot add a price to itself: `agg="last"`, the rule ADR-129 wrote **for this exact column**
while building something else entirely.

---

### 💡 The lesson

> **Two sources for one fact is usually a smell; here it was the requirement.**

`cost_change_start` and the per-gameweek `value` series measure the same thing at different resolutions and
different freshnesses, and neither alone gives a usable feature — the series is one point long and stale, the
scalar has no shape. Using both, and being explicit about which carries the feature now versus later, is what
made this shippable at GW1 rather than a placeholder waiting for GW6.

> **A chart is a claim about the same numbers the page prints, and it has to survive being read next to them.**

The £8.0m/£7.9m gap sat in the data all along and would never have failed a test. It only shows up when a
reader notices the picture and the label disagree.

### 🧪 Tests

**+10.** The move read straight off FPL and `None` when absent; today's price as the last point (the Watkins
case, by name); an unmoved price yielding one point not a flat pair; the double-gameweek rule; no gameweek
rows still reporting a price. Plus the view: the move named with a line when there is one; both glyph and
colour directions; the unchanged case drawing no line and no arrow; no price → no strip; and the trend panel
byte-identical without it.
