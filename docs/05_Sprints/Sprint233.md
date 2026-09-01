# Sprint 233: A shrink needs something to shrink toward (ADR-172)

**Dates:** 2026-09-01
**Status:** ✅ Complete — ADR-172. **1655 → 1661 tests, ruff clean.**

> **Owner, reading the week's answer:** *"Sangaré I think is overrated to score that amount, I'd say 5 and
> that would be in line with other apps."*

---

### 🔧 What shipped

One function changed — `cold_start_rate` in `src/analytics/xp.py`. When `ep_next` carries no information
about a player beyond what `points_per_game` already says, shrink toward the existing replacement prior
instead of toward `ep_next`.

**Before → after, at the top of the board:** Tzolakis 10.0, Sangaré 9.9, Mendy 8.0, *then* Haaland 6.3 —
becomes **Haaland 6.3** first, and **zero** inert cold-start players in the top 20 (was 8, and the top 3 were
all of them).

---

### 🔬 The finding

ADR-124 shrinks a no-history player's `ppg` toward FPL's `ep_next` in proportion to minutes played. Sangaré's
`c` is 0.18, so **82% of his rate should have come from the conservative side**.

But **FPL publishes `ep_next` equal to `points_per_game` — 513 of 626 players.** Verified against the live
`bootstrap-static` API, not inferred from our copy. Blending a number with itself returns it:

```
9.0 × 0.18  +  9.0 × 0.82  =  9.0      at every value of c
```

The protection was **inert**. And this is the exact failure ADR-124 was written to prevent — ADR-104's
`max(ep_next, ppg)` let one big score dominate, and the blend was the fix. The blend is still the right
shape; it assumed its two inputs were independent, and upstream they stopped being so.

---

### 💡 The lesson

> **A formula can stop working without changing, when the data underneath it changes meaning.**

No test caught this because **the code does exactly what it says**. Every unit test passed, both endpoints
ADR-124 pinned still held, and the function was correct in isolation. What broke was an *assumption about the
inputs* that was never written down as an assertion.

The owner caught it by not believing a number. That is worth stating plainly: **the check that worked was a
person looking at output and finding it implausible** — no amount of internal consistency would have surfaced
it, because the arithmetic was never wrong.

Two habits follow. **Pin the assumption, not just the behaviour:** the new tests assert the identical-inputs
case does *not* return the input, and that the rate **slopes** with evidence — a flat line across `c` is the
signature of a cancelled shrink. And **when a projection looks wrong, decompose it before defending it**:
`ppg`, `ep_next`, `c` and the fixture multiplier each had to be printed separately before the cancellation
was visible.

---

### ⚠️ A fixture was depending on the bug

`tests/test_ask.py::_worth_player` builds a MID with `ep_next = ppg` and **no minutes**, then asserts
`xp == ppg` so the value-ranking maths has round numbers. It was getting that equality from the *cancelled
shrink* — and `ppg > 0` with `minutes = 0` **cannot occur in real data**, because FPL derives points-per-game
from games played. The fixture was only plausible while the bug made it so.

Sprint 232 found three tests pinning stale **copy**. This is a different and more dangerous species: a test
pinning a **stale model of the data**, which makes a bug look like the specification.

---

### 🧪 Tests

**+6**, every one mutation-checked. Reverting the fix fails three; dropping the `ppg > 0` guard — the subtle
half, which keeps ADR-104's preseason case intact — fails one; shrinking toward the prior unconditionally
fails two.

**What is pinned is the cancellation, not the symptom.** A test asserting merely *"Sangaré is lower now"*
would pass on any change that lowered him, including a wrong one.

---

### ⏳ Left open, deliberately

**Cold-start xMins is forced to 1.0**, so these players are still modelled as nailed 90-minute starters —
Mendy on 60 minutes a game, Yalcouyé on 38. A second over-estimate stacked on this one; it interacts with
ADR-125's deferred in-season minutes share, and fixing both at once would leave neither measurable.

**Calafiori is the mirror image** — 5.29 baseline, **2.00** xP, because xMins is 0.43 from last season's
injury-hit minutes while `FORM_WEIGHT` is 0 until GW4-6. A second Kinsky, and ADR-125's gate, not this one.
