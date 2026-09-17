# Sprint 268: "Bench him" assumed a bench worth using

**Dates:** 2026-09-17
**Status:** ✅ **ADR-208 — 1867 → 1875 tests, ruff clean, 8 mutants all red.**

---

## The report

> *"We are picking up that João Pedro is a Doubt, we are not suggesting a transfer for him — that's as
> designed, so good. BUT where we have a gap is that the other 2 fwds are zero to low scoring, we should be
> getting a backup recommendation in there."*

The plan charged **8 confidence points** for *"João Pedro is flagged — bench or replace him."*

⭐⭐ **The advice assumed an option it had never checked.** FPL auto-substitutes a 0-minute starter with the
first legal bench player in his position. On RoboTS that is **Walle Egeli at 0.2 xP**. Benching a doubtful 4.3
to field a 0.2 is not a mitigation — it *is* the loss.

---

## 🔬 The deeper fix was measured, and not built

The model folds the 75% into the player and *then* picks the XI — `max(E)`. A manager lives in one of two
worlds, each with its own best XI — `E(max)`. They diverge by exactly `(1 − chance) × what the auto-sub
brings in`.

On a squad built to the owner's description: app **+0.30**, true **+1.35**. Understated 4.5×.

⚠️ **Then 64 realistic squads said zero** — mean +0.00, max +0.08, **0 of 40** flips.

⭐⭐ **And the null was about the population, not the effect.** Conditioning on the size of the best available
upgrade showed **not one** of those squads had a best move under **1.5** — the band RoboTS is in (+1.2). The
effect needs a weak bench *and* nothing better to do; the perturbed-template population has no such squad.

**Third time in two days**, after ADR-195's clean-sheet rate and ADR-202's substitute forecaster.
⭐ *The tell is always the same question: does the population contain the case?*

So the re-ranking stays **ungated, not declined** — it re-prices every transfer for every squad, leans on
FPL's coarse 25/50/75 whose accuracy ADR-206 flagged as unmeasured, and ADR-132 warned more moves is more ways
to be wrong. ⭐ *A mechanism confirmed on one squad and unmeasurable on the available population is a
hypothesis, not a feature.*

---

## Built: say it, don't re-rank it

| case | the reader gets |
|---|---|
| cover exists | *"bench or replace him — benching him fields Walle Egeli (0.2 xP)"* |
| **no** cover | *"replace him — you have no cover on your bench"* |
| already benched | *"already on your bench"* |

⭐ **"No cover" is a different problem from "weak cover"** — one is solved by a transfer, the other by a
judgement call. And the third case removes advice that described the state the reader was already in.

**No re-ranking, no new threshold.** The trigger is the existing flag, so nothing needs provenance and it
cannot fire where the app was previously silent.

---

## ⚠️ The smoke run on the real squad caught a bug

It said *"benching E.Le Fée fields **Foden** (0.0 xP)"* — about a **suspended** player who would never come
on. ⭐⭐ **A fallback that shares the failure it is covering for is not a fallback.** The true answer for that
flag is *"you have no cover on your bench"*.

**Three of eight mutants survived the first sweep, all coverage rather than code** — and one is the lesson of
the week for the third time: the **old unqualified advice could be restored with every test green**, because
they all called `_flag_action` directly and the reader never does. Plus a positionless-row guard whose fixture
benched only rows *with* positions, and a starters-only guard whose fixture had no fit substitute available.
⭐ *A guard is only tested by the case it exists to catch.*

The shared gameweek fixture also carried **no `position` at all** — fifth fixture this month that modelled
less than any real row does.

---

## 📋 A second gap, found and not fixed

The app recommended **E.Le Fée → Dewsbury-Hall: +1.2 next GW, −1.5 over five.** Meanwhile **Walle Egeli →
Barry (£5.6m): +1.2 next GW, +3.1 over five** — and it turns 0.2 xP of forward cover into **4.5**.

The two **tie on the number the app ranks by**, and the app **computes and prints** the number that separates
them without letting it choose.

⭐ *A ranking that separates two options by less than its own noise is picking one* (ADR-189), and ⭐ *a number
computed for one question and discarded is invisible in a way a missing number is not* (ADR-191).

Proposed, gated: break a near-tie on next-GW gain toward the better horizon figure.

---

## Definition of Done

- ✅ **Tests** — 8 new (`tests/test_flag_cover.py`), one of them through `confidence_levers` because the rest
  do not exercise the wiring; **1875 passed**, ruff clean; 8 mutants, all red after three coverage repairs
- ✅ **Manual smoke** — the owner's real squad (manager 2885974) end to end, at horizons 1 and 5
- ✅ **Docs** — ADR-208 + index row, PROJECT_STATUS, this sprint doc

**Next:** the owner's call on the tie-break and on E[max].
