# Sprint 269: The longer view breaks the tie

**Dates:** 2026-09-17
**Status:** ✅ **ADR-209 — 1875 → 1882 tests, ruff clean. 8 mutants, 7 red + 1 recorded equivalent.**

---

## The gap ADR-208 found and did not fix

The app recommended **E.Le Fée → Dewsbury-Hall, +1.2 XI xP next GW**, and printed beside it *"Longer view:
**−1.5** XI xP."* The alternative, **Walle Egeli → Barry**, was **+1.2 next GW and +3.1 over five** — and
turned the owner's forward cover from 0.2 xP into 4.5.

The two **tie on the number the app ranks by**. It computes the number that separates them, prints it, and
never lets it choose.

---

## 🔬 Measured first, and it reframed the change

Across **96 realistic squads**, the gap between the best and second-best next-gameweek move:

| p10 | p25 | median | p75 | p90 |
|---|---|---|---|---|
| 0.00 | 0.10 | **0.20** | 0.20 | 0.40 |

Against a per-player weekly sd of **3.51**.

⭐⭐ **On a one-gameweek window the transfer ranking was never ranking — it was picking.** Something else was
always going to decide; the only question was what.

### ⚠️ And something already was, unnoticed

`TIE_NOISE = 2.0` was sized for a **five**-gameweek window — its own comment says so — and applied to every
window. My Squad narrows the horizon toward the deadline, and at one gameweek that band catches **100%** of
best-vs-second pairs.

So **ADR-189's correlation rule had silently been deciding every single one-gameweek recommendation** — a rule
that ADR-189 itself established *never moves expected points*.

⭐⭐ **This is the mistake the codebase already warns about, three functions away**: *"a threshold sized
against one window applied to another"* (ADR-186), written about the affordability cliff while the tie-break
beside it did exactly that. ⭐ *A lesson recorded about one number does not check the others.*

---

## Built

1. **`tie_noise(window)` scales by √window**, not linearly — the error in an N-gameweek total grows as √N if
   weekly errors are roughly independent. **Derived, not measured**, and it reduces to exactly 2.0 at five
   gameweeks so no existing caller moves.
2. **Within the band, the longer view is asked before correlation.** ⭐ *A tie-break on expected points
   strictly dominates one on spread, so it must be asked first.*
3. **No wider map → a clean tie**, falling through to the rule that was there before.

---

## 📊 What it trades

| | |
|---|---|
| changes the top move on | **94%** of squads |
| given up next gameweek | mean **−0.30**, worst −0.80 (band 0.89) |
| gained over five | mean **+7.04**, worst **+0.80** |
| trades that lose over five | **0 of 90** |

⭐ **94% is not a wide band, it is an honest one.** With a median separation of 0.20 the ranking genuinely
cannot distinguish the top two — a tie-break that fired rarely would be wrong about how ambiguous the input is.

---

## ⚠️ The interaction stated, not buried

On the live squad it chose **Mitchell → Affengruber** — exactly **ADR-192's case**: `cold_start`, zero past
seasons, two appearances, ppg 8.0 on **n = 1**, projecting 22.4 over five gameweeks.

⭐⭐ **A tie-break inherits the bias of whatever number it breaks the tie on.**

Shipped anyway, and the reason is worth writing down: it does not *introduce* that dependence — `ask` already
ranks on the five-gameweek map, so the inflation already drives primary recommendations. Here it acts only
**within noise**, and the measured effect is **4 → 6 of 96** cold-start top picks.

📌 **It raises ADR-192's priority** — a second, independent reason to fix the input rather than the symptom.

---

## 💡 The lesson

⭐ **A constant carries the window it was sized on, and nothing in the type system says so.** `TIE_NOISE = 2.0`
looked like a number; it was a number *per five gameweeks*, and every caller that handed it a different window
got a silently wrong band. The fix was to make the window an argument — so the question "against what?" has to
be answered at each call site rather than assumed once.

---

## Definition of Done

- ✅ **Tests** — 7 new (`tests/test_tiebreak_horizon.py`), one pinning the wiring because an optional arg
  nothing passes is a silent opt-out (ADR-181); **1882 passed**, ruff clean; 8 mutants, 7 red
- ✅ **Manual smoke** — the owner's real squad before/after, and 96 realistic squads for the trade-off
- ✅ **Docs** — ADR-209 + index row, PROJECT_STATUS, this sprint doc

⚠️ **Not reproduced:** the owner's exact pasted pair. Fresher data made a suspended Foden the obvious top
move by ship time, so the mechanism is demonstrated on the population and on his live second move instead.
