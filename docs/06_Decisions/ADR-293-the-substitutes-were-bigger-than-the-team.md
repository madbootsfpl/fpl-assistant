# ADR-293 — The substitutes were bigger than the team

**Date:** 2026-09-25
**Status:** Accepted
**From:** the owner, two photographs of the same tablet — *"landscape vs portrait"*
**Follows:** ADR-285 (the pitch scales by proportion), which fixed portrait and did not look sideways

---

## What the photographs showed

Portrait was fine. Landscape was unreadable: the eleven were microscopic and the **bench was full size.**

| | XI kits | bench kits |
|---|---|---|
| tablet portrait | 46pt | 46pt ✅ |
| tablet landscape | **32pt** | **46pt** ❌ |
| phone landscape | **9pt** | 22pt ❌ |

⚠️⚠️ *The substitutes were drawn larger than the team.*

**Why:** the XI rows are `Expanded`, so they divide whatever height is left and each card scales down to
fit its row. The bench is not height-constrained, so it keeps the size ADR-285 computed. ⭐ *A size
derived from the width and a size derived from the height will agree only on the screen you tested.*

And the three banners stacked above the pitch — plan, update, signals — cost that height too, so the
owner's tablet was worse than the 32pt the harness measured.

## The decision: sideways, the bench takes width instead of height

A landscape screen has width going spare — look at the empty green between the players — and no height
at all. So the bench becomes a column on the right, and the eleven get their height back. Measured:

| | before | after |
|---|---|---|
| tablet landscape | 32pt XI / 46pt bench | **45–46pt, matched** |
| phone landscape | 9pt XI / 22pt bench | **17–18pt, matched** |
| portrait, both | — | **unchanged** |

## ⭐⭐ The rule did not need a device class, and I wrote one anyway

The first version was gated to tablets, reasoning that a 390pt-tall phone would end up with a letterbox
pitch. **The measurement said the opposite**: a phone in landscape was the *worst* case of the bug, and
sideways nearly doubles its kits.

⭐ *A rule that needs a device class is a rule that has not found what it depends on yet* — and what this
depends on is the **shape**, which was already in the `BoxConstraints` two lines above. The condition is
now `box.maxWidth > box.maxHeight` and nothing else.

⚠️ This is the second time in two ADRs that a guess about a screen was wrong and a measurement was right.
ADR-285 nearly shipped an upscale that also changed the phone; this nearly shipped a fix that skipped the
device it would have helped most.

## What the tests hold

- **the bench never outgrows the eleven** — across four shapes, largest and smallest kit within 2pt of
  each other. ⭐ *That inequality is the bug, stated as a property rather than as a number.*
- **turning a tablet does not resize the team** — portrait and landscape within 2pt
- **a phone in landscape is helped too**, which is the assumption I got wrong, pinned so it cannot be
  re-guessed
- **no exception on any of the four**, because the first side-bench overflowed by 3.7px — ⚠️ *a layout
  that fits on the device you tested is not a layout that fits*

4/4 mutations killed. ⚠️ One reported `SURVIVED` first and was a lie: `dart format` had collapsed the
target onto one line, so the patch never applied — ⭐ *a mutation that cannot be applied is not a
mutation that survived*, and the harness has to prove it changed something.

## What this does not do

- **The bench is `scaleDown`, not scrollable.** Four cards at the XI's size is nearly a tablet's height,
  so it shrinks slightly rather than clipping. A fifth bench slot would want a rethink, and FPL does not
  have one.
- **It does not reclaim the banners' height.** Three stacked notices above a landscape pitch is its own
  question — ⭐ *and the pitch no longer depends on the answer.*
