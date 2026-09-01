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

---

## Addendum — the xMins half, attempted (2026-09-01)

The owner asked for the deferred half the same day. **It is still deferred, and the reason changed.**

### ⛔ Blocked on data, not design

`player_history` holds **GW1 only**, while the aggregate `players.minutes` already carries two gameweeks
(Sangaré: 75 in GW1, 165 total). The per-GW backfill has not run since GW2 finished. An in-season minutes
share built today would rest on **one gameweek** and contradict the aggregate every other surface reads.

Worth recording: **ADR-125's trap is already solved.** It warned that FPL writes a per-GW row when a fixture
is merely *scheduled*, so `minutes = 0` can mean "not kicked off yet". `yet_to_play` (ADR-138) already counts
a gameweek only when it has a **scoreline**. The design is ready; the data is not.
**Owner action: `python app.py history --backfill`.**

### 🔧 But the attempt found two real bugs — and they had been cancelling each other

**1. Mine, from that morning.** ADR-172 swapped the shrink target from `ep_next` to the replacement prior and
kept ADR-104's *"do not discount this term by minutes"* rule. That rule is a fact about `ep_next` — expected
points *for the next gameweek*, minutes already priced in. The prior is a **points-per-90 rate**, and a rate
becomes points only when multiplied by expected minutes. The same prior was therefore minutes-scaled in the
`fallback` tier and unscaled in `cold_start`: halving a player's minutes took him to **48%** of his xP on one
path and **76%** on the other.

**2. Pre-existing, and invisible until the first was fixed.** `minutes_share` averages stored seasons, and a
player promoted with his club carries seasons for years spent **outside** the league — Thomas has four, all
zero — which average to a share of **0.0**, read as *"never plays"*. An **empty** history returns `None` and
the module's own rule applies: *never penalise the unknown*. Same ignorance, opposite answers.

> **Two bugs in opposite directions, netting to a plausible number.** The 0.0 share took a player's points
> away; the unweighted prior handed them straight back. Neither was observable while both existed, and no
> test could see a discrepancy that cancels before anyone looks at it. Fixing one made the other appear as a
> regression — Thomas at **0.00 xP** having started both games.

32 players carry an all-empty history; **7 have played this season**, two of them every available minute.

### 💡 The lesson

> **A fix that exposes a regression has not necessarily caused it.** The instinct is to revert; the right
> move is to ask what the removed error was hiding.

And a second, from how the narrower rule was found: the first attempt tested the k-season window, which would
have rescued a genuinely declining player along with Thomas — three empty seasons *after* a full one is real
evidence. `test_only_the_last_k_seasons_count` failed and said so. **The suite knew the correct rule before I
did**, which is the argument for changing a test's subject rather than its expectation.

### 🧪 Tests

**+6** (1661 → 1667), mutation-checked in both directions each time: reverting the fix fails, and
*over*-applying it — scaling `ep_next` too, or widening the empty-history rule to the window — also fails.

---

## Closing state — GW2 backfilled, xMins held (2026-09-01)

**The backfill ran** (`2980ce9`): 626 players, 2071 season rows, **1236 per-GW rows** (was 609), no failures.
GW1 and GW2 both carry scorelines and the per-GW sums match the aggregate exactly. Reseeded and pushed.

**And the xMins work is held anyway — by decision, not by obstacle.** The reason narrowed from two to one:

| | before today | now |
|---|---|---|
| ADR-125's `minutes = 0` trap | recorded as unsolved | ✅ **already solved** by `yet_to_play` (ADR-138) — it arrived for another feature and nobody connected it back |
| per-GW data | GW1 only, a gameweek behind the aggregate | ✅ **closed** — GW1 + GW2, both finished |
| sample size | — | ⏳ **the only thing left.** Two gameweeks cannot separate a player rested once from one being phased out |

Owner's call: **hold for GW4-6**, with ADR-125.

**Why the narrowing is worth writing down.** A deferral that keeps its original reasons accumulates
justification it no longer has — and the next reader inherits a list of obstacles, most of which have quietly
gone. Recording *which* reason survives means the GW4-6 sitting opens on one question (is the sample long
enough to tell rotation from decline?) rather than re-deriving a data problem that was fixed months earlier.
