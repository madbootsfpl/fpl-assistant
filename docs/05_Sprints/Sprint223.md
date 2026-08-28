# Sprint 223: Two regressions from one CSS block (US-450)

**Dates:** 2026-08-28
**Status:** ✅ Complete. 1565 → 1568 tests, ruff clean.

> **Owner, on Cloud:** *"banners are great. player double click is not working and now the player info card is
> behind the players."*

One screenshot, two defects, both introduced by the three CSS lines I added yesterday for the clear-anchor.

---

### 🐛 What went wrong

```css
.fpl-pitch .row{position:relative;z-index:1;}     /* ← both bugs live here */
```

**The card went behind the shirts.** `z-index` on `.row` creates a **stacking context per row**, which traps
`.kit-pop`'s `z-index:40` *inside* its own row. So a card opened on the defenders could no longer rise above
the midfielders — exactly what the screenshot shows. `.kit` was already `position:relative`, so the rows never
needed anything: positioned siblings paint in tree order and the anchor is first in the DOM.

**And closing still did nothing** — for a different reason, which is why fixing the first would not have fixed
this. Paint order is irrelevant to *clicks*: a `.row` is a full-width flex container, so it lies over the
grass and swallowed every tap intended for the anchor beneath it. Rows now pass clicks through
(`pointer-events:none`) and shirts take their own (`pointer-events:auto`).

**Still true, and still not a bug:** tapping the *same shirt* twice cannot work. The component reports the id
of the last element clicked, so the second tap is byte-identical and never reaches Python.

---

### 💡 The lesson

> **A stacking context is invisible until something needs to escape it.**

`z-index:1` looked like it did one thing — put rows above the anchor. It also silently redefined where every
descendant's `z-index` is resolved. The rule worth keeping: **adding `z-index` to a container is a scoping
decision, not a layering one**, and the thing it scopes is usually somewhere else in the file.

> **Two symptoms from one line still need two fixes.**

The card and the tap looked like one bug and were two — paint order and hit-testing are separate systems.
Fixing the stacking would have made the card look right and left the gesture just as dead, which is how a
partial fix gets shipped as a whole one.

### 🧪 Tests

**+3, each verified to fail against the exact CSS that shipped.** No `z-index` in the `.row` rule; rows pass
clicks through while kits take their own; the clear anchor leads the pitch and appears only when tappable.
