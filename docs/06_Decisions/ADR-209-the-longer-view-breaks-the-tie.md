# Architectural Decision Record: The longer view breaks the tie, and the band fits its window

**Decision ID:** ADR-209
**Date:** 2026-09-17
**Status:** ✅ **Accepted — built.** 1875 → 1882 tests, ruff clean. 8 mutants, 7 red + 1 recorded equivalent.
**Superseded By / Replaces:** Extends [ADR-189](./ADR-189-two-defenders-one-bet.md)'s tie-break and puts the
longer view ahead of it. Fixes a latent case of [ADR-186](./ADR-186-bank-to-afford.md)'s own warning. Closes
the gap [ADR-208](./ADR-208-cover-is-part-of-the-advice.md) found and did not fix. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

From ADR-208's measurements, on the owner's own squad: the app recommended **E.Le Fée → Dewsbury-Hall, +1.2
XI xP next GW**, and printed beside it *"Longer view: **−1.5** XI xP."* The alternative, **Walle Egeli →
Barry**, was **+1.2 next GW and +3.1 over five** — and turned his forward cover from 0.2 xP into 4.5.

**The two tie on the number the app ranks by.** It computes the number that separates them, prints it, and
never lets it choose.

⭐ *A number computed for one question and discarded is invisible in a way a missing number is not*
(ADR-191), and ⭐ *a ranking that separates two options by less than its own noise is not ranking them, it is
picking one* (ADR-189).

---

### 🔬 Measured first — and it reframed the change

Across **96 realistic squads**, the gap between the **best and second-best** next-gameweek move:

| p10 | p25 | median | p75 | p90 | mean |
|---|---|---|---|---|---|
| 0.00 | 0.10 | **0.20** | 0.20 | 0.40 | 0.21 |

Against a per-player weekly sd of **3.51** (ADR-161).

⭐⭐ **ON A ONE-GAMEWEEK WINDOW THE TRANSFER RANKING WAS NEVER RANKING — IT WAS PICKING.** The top two
candidates are separated by a fifth of a point, which the model cannot resolve. Something else was always
going to decide; the only question was what.

#### ⚠️ And something else already was, unnoticed

`TIE_NOISE = 2.0` was sized for a **five-gameweek** window — its own comment says so, *"2.0 over a
five-gameweek window is 0.4 a week"*. It was applied to **every** window, and My Squad's *"This week"*
narrows the horizon toward the deadline. At one gameweek that band catches **100%** of best-vs-second pairs,
so **ADR-189's correlation rule had silently been deciding every single one-gameweek recommendation** — a rule
that ADR-189 itself established *never moves expected points*.

⭐⭐ **THIS IS THE MISTAKE THE CODEBASE ALREADY WARNS ABOUT, THREE FUNCTIONS AWAY**: *"a threshold sized
against one window applied to another"* — written in `gameweek.py` about the affordability cliff (ADR-186),
while the tie-break beside it did the same thing. ⭐ *A lesson recorded about one number does not check the
others.*

---

### 🎯 Decision

**1. The band is sized for the window it is given.** `tie_noise(window)` scales `TIE_NOISE` by **√window ÷ √5**
— the error in an N-gameweek total grows as √N if weekly errors are roughly independent, so a band that stays
the same *fraction of the noise* scales the same way. ⚠️ That independence is an approximation (a run of hard
fixtures correlates), which is why this is **derived rather than measured** — and it reduces to exactly 2.0 at
five gameweeks, so **no existing caller moves**.

**2. Within the band, the longer view speaks first.** Ordered ahead of the correlation rule deliberately:
ADR-189 established that correlated defence never moves expected points — it widens that component's spread by
√2, ~1.2 points at worst. The longer view moves **expected points**. ⭐ *A tie-break on expected points
strictly dominates one on spread, so it must be asked first.*

**3. No wider map → nothing changes.** `_horizon_gain` returns a constant for every candidate, which is a
clean tie, and the sort falls straight through to the rule that was there before.

---

### 📊 What it trades — measured, 96 squads

| | |
|---|---|
| changes the top move on | **94%** of squads |
| given up next gameweek | mean **−0.30**, worst −0.80 (band is 0.89) |
| gained over five gameweeks | mean **+7.04**, best +14.20, worst **+0.80** |
| trades that lose over five gameweeks | **0 of 90** |

⭐ **94% is not a wide band, it is an honest one.** With a median separation of 0.20 the ranking genuinely
cannot distinguish the top two, so a tie-break that fires rarely would be a tie-break that is wrong about how
ambiguous the input is. **A tie-break firing 94% of the time would be alarming if the gaps were large; here
it is the only reading consistent with them.**

---

### ⚠️ The interaction that has to be stated, not buried

On the owner's live squad the tie-break changed the second move to **Mitchell → Affengruber** — and
Affengruber is **exactly [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md)'s case**: `cold_start`,
**zero past seasons, two appearances**, a points-per-game of 8.0 built on **n = 1**, projecting **22.4 xP over
five gameweeks**.

⭐⭐ **A TIE-BREAK INHERITS THE BIAS OF WHATEVER NUMBER IT BREAKS THE TIE ON.** Leaning on the five-gameweek
map leans on the inflation ADR-192 measured and has not yet corrected.

**Shipped anyway, for a reason worth writing down:** this does not *introduce* that dependence. `ask` already
ranks on the five-gameweek map by default, so the inflation already drives primary recommendations; here it
acts only **within noise**, where by construction the alternative was indistinguishable. Measured across the
population, cold-start players as the top pick go **4 → 6 of 96** — real, small, and bounded.

📌 **It raises ADR-192's priority.** That ADR is Proposed with its direction confirmed and its constant unset
(ADR-202 declined the demotion on ρ). This is a second, independent reason to fix the input rather than the
symptom.

---

### 📊 Consequences

**Good:** the app stops discarding the number that separates two otherwise-identical moves. The band finally
means the same thing on every surface. Both changes are inert at the five-gameweek window.

**Costs / limits:**
- ⚠️ **It leans harder on the horizon map, including ADR-192's inflation.** Stated above; bounded to
  within-noise choices.
- The √N model assumes weekly errors are roughly independent. Derived, not measured — and it *cannot* be
  measured until there are enough gameweeks to estimate the covariance.
- ⚠️ **The owner's exact reported case could not be reproduced** by the time this shipped: fresher data made
  a suspended Foden the obvious top move. The mechanism is demonstrated on the population and on his live
  second move, not on the pair he pasted.
- ⚪ One mutant **recorded as equivalent**: returning 1.0 instead of 0.0 with no wider map. Any constant is a
  clean tie, so nothing changes.

---

### 🔗 Links

- [ADR-208](./ADR-208-cover-is-part-of-the-advice.md) — where this gap was found
- [ADR-189](./ADR-189-two-defenders-one-bet.md) — the tie-break this extends and reorders
- [ADR-186](./ADR-186-bank-to-afford.md) — whose warning this was an unnoticed instance of
- [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) — the inflation this now leans on
- `spikes/209-tiebreak/measure.py`
