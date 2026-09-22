# ADR-253 — The pitch is the screen

**Date:** 2026-09-23
**Status:** Accepted
**From:** the owner's side-by-side of My Team against Fantasy Football Hub, with seven observations
**Builds on:** ADR-235 (one card, three readings), ADR-244 (the apply strip), ADR-243 (the wordmark)

---

## Context

Measured from the two screenshots, same device:

| | MADBOOTS | Hub |
|---|---|---|
| chrome above the pitch | **385px** | 180px |
| green area | **747px** | **1560px** |
| dead space at the bottom | 140px | 0 |

⭐⭐⭐ **They gave the pitch twice the room, and the owner was right that it reads better for it.** Every one
of his seven points was correct.

## Decision

**1. The run is tinted by fixture difficulty.** ⭐ The app already knew the FDR and was drawing the run in
**monochrome** — so reading it meant taking in three numbers and three club abbreviations and holding all
six. ⚠️ *A colour is read before a number is*, and the whole point of the run is to be taken in at a
glance. The Next-GW pill takes the same tint, so a reader learns one colour language rather than two.

⚠️ **Null is neutral, never easy.** An unknown fixture is not a good one, and the white pill is kept for it
— *"we do not know" and "it is a three" are different facts.*

**2. The header is one line.** The web's deadline banner is **96 characters** and wrapped to three here.
The API now sends `when` and `countdown` **as well as** the sentence, and the phone composes
*"GW6 · Sat 10 Oct, 11:00 · in 17 days, 11h"* — 48 characters.

⭐ *A client too narrow for a prose line needs the facts, not a second prose line written for it* — which is
why there is no `compact=True` flag making the API responsible for someone else's layout. The **countdown
stays**: near a deadline it is the only part anyone reads.

**3. The wordmark moved onto the pitch**, in a dark chip in the corner. It had a row of its own — 60px to
say a name the reader already knows. ⚠️ It stays on the other four tabs: *a row worth reclaiming on one
screen is not a row worth reclaiming on all of them.*

**4. One green area, from the mode bar to the bottom.** The bench is a dark panel **sitting on** the
pitch — integrated and still plainly separate — and the apply strip rides below it. ⚠️ *A pitch that stops
two thirds of the way down reads as a web page with a picture on it.*

**5. The apply strip is one line.** The information stays — *what it is worth* and *who comes in* — because
that is the reason to press it, and the competitor's equivalent button says nothing at all. What went was
~100pt of height.

⭐ **Where I would not follow them:** their floating buttons are **occluded by their own tab bar** in the
owner's third screenshot. Floating over the pitch costs you that.

**6. No scroll view.** ⚠️ *A screen whose main subject scrolls has decided its main subject is not
important enough to fit.*

## What building it found

⚠️⚠️ **The rows demanded their intrinsic height and overflowed by 4px**, then by 1px, on a 760pt screen.
A smaller phone — or the stale-data banner appearing — would have clipped a row of shirts. Each row is
`Expanded` now, so the four divide whatever height there is, and each card is a `FittedBox(scaleDown)` so
it shrinks rather than clips. ⭐ *A pitch that must be given enough room is not a pitch that fills the room
it is given.*

⚠️ **The width box had to go inside the `FittedBox`, not outside it.** A `FittedBox` hands its child
unbounded width, and the run's `Expanded` cells cannot lay out against that — *a box that scales its child
must still give it something to be a fraction of.*

⚠️ A test asserted the copy `'Start '` and broke on a wording change that kept the meaning. It pins the
**player's name** now. ⭐ *Pin the thing the test is about, not the wording it happens to sit in.*

## Verification

* **6 widget tests that measure**, because the change is a measurement: the green taking **more than 60%**
  of the screen as a proportion rather than a pixel count, the bench inside the green's bounds, the footer
  inside them, the header showing the parts and **not** the prose line, and the wordmark on the pitch.
* **4/4 mutations killed** — the prose line returning, the wordmark leaving the green, the bench dropping
  out of it, and the pitch pinned back to roughly its old height.
* ⚠️ One mutation was discarded as a **no-op**: `Expanded` → `Flexible(loose)` changes nothing while the
  rows inside are themselves `Expanded`. ⭐ *Reporting it as a survivor would have been a claim about the
  test rather than the truth.*
