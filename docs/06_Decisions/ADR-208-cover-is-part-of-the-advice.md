# Architectural Decision Record: "Bench him" assumed a bench worth using

**Decision ID:** ADR-208
**Date:** 2026-09-17
**Status:** ✅ **Accepted — built.** 1867 → 1875 tests, ruff clean. 8 mutants, all red.
**Superseded By / Replaces:** Qualifies [ADR-198](./ADR-198-why-73.md)'s confidence levers. Follows
[ADR-206](./ADR-206-a-doubt-is-a-probability.md), which stopped the app selling a flagged star and exposed
this. **No `decision_xp` change, no re-ranking** — the recommendation is unchanged; what it assumes is now
stated.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, after ADR-206 stopped the app trying to sell his doubtful joint-best forward:

> *"We are picking up that João Pedro is a Doubt, we are not suggesting a transfer for him — that's as
> designed, so good. **BUT where we have a gap is that the other 2 fwds are zero to low scoring**, we should be
> getting a backup recommendation in there."*

The week's plan told him, at a cost of 8 confidence points: *"João Pedro is flagged — **bench or replace
him**."*

⭐⭐ **THE ADVICE ASSUMED AN OPTION IT HAD NEVER CHECKED.** FPL auto-substitutes a starter who plays 0 minutes
with the first legal bench player in his position. On RoboTS that is **Walle Egeli at 0.2 xP**. Benching a
doubtful 4.3 to field a 0.2 is not a mitigation — it *is* the loss, and the app was recommending it in the
same breath as charging 8 points of confidence for the problem.

⭐ *An instruction is only as good as the option it assumes you have.*

---

### 🔬 What was measured first, and what it refuted

The owner's framing suggested a deeper fix: rank transfers on **E[max]** rather than **max(E)**. The model
folds the 75% into João Pedro's score and *then* picks the XI; a manager instead lives in one of two worlds —
he plays, or the bench comes on — each with its own best XI. Those are different numbers, and they diverge by
exactly `(1 − chance) × what the auto-sub brings in`.

On a squad constructed to the owner's description, the app priced a cover move at **+0.30** against a true
**+1.35**: understated 4.5×, and above the move it recommended instead.

⚠️ **Then the population measurement said zero.** Across 64 realistic squads (ADR-200's `population.py`):
mean **+0.00**, max **+0.08**, and **0 of 40** squads where the true best move was a cover move the app
missed.

⭐⭐ **AND THE NULL WAS ABOUT THE POPULATION, NOT THE EFFECT.** Conditioning on the size of the best available
upgrade showed why: **not one** of those squads had a best move under **1.5**, which is the band RoboTS is in
(+1.2). The effect only bites when the bench is weak *and* there is no good upgrade elsewhere — and the
perturbed-template population contains no such squad. Third time this pattern has appeared in two days, after
ADR-195's clean-sheet rate and ADR-202's substitute forecaster. ⭐ *The tell is always the same question: does
the population contain the case?*

**So the big fix stays unbuilt** — not declined, but ungated: it re-prices every transfer for every squad, it
leans on FPL's coarse 25/50/75 whose accuracy ADR-206 already flagged as unmeasured, and ADR-132 warned that
recommending more moves is more ways to be wrong. ⭐ *A mechanism confirmed on one squad and unmeasurable on
the available population is a hypothesis, not a feature.*

---

### 🎯 Decision — say it, don't re-rank it

`auto_sub_cover()` answers one question: **who actually comes on if this player blanks, and what is he
worth?** The flag carries it; the lever states it. Three cases, deliberately worded apart:

| case | what the reader gets |
|---|---|
| flagged starter, cover exists | *"bench or replace him — benching him fields Walle Egeli (0.2 xP)"* |
| flagged starter, **no** cover | *"replace him — you have **no cover** on your bench"* |
| flagged player already benched | *"already on your bench"* |

⭐ **"No cover" is a different problem from "weak cover" and must not be flattened into one** — the first is
solved by a transfer, the second by a judgement call. And the third case removes advice that merely described
the state the reader was already in: ⭐ *advice that describes where you already are is noise wearing the shape
of help.*

**Nothing is re-ranked and no threshold is introduced.** The trigger is the existing flag, so this adds no
constant needing provenance (ADR-199) and cannot fire where the app was previously silent.

---

### ⚠️ What the first smoke run on the owner's real squad caught

It reported *"benching E.Le Fée fields **Foden** (0.0 xP)"* — about a **suspended** player, who would never
come on. FPL's auto-sub skips a substitute who also records 0 minutes.

⭐ **A FALLBACK THAT SHARES THE FAILURE IT IS COVERING FOR IS NOT A FALLBACK.** Cover now excludes
unavailable players, and the true answer for that flag is *"you have no cover on your bench"* — a far more
useful sentence than a wrong name.

⚠️ **Three of eight mutants survived the first sweep, all coverage rather than code**, and one is the lesson
of the day for the third time: **the old unqualified advice could be restored and every test still passed**,
because they all called `_flag_action` directly and the reader never does. Also: a positionless-row guard
whose fixture benched only rows *with* positions, so `None == "FWD"` was false and the guard was never the
reason for the answer; and a starters-only guard whose fixture had no fit substitute available, so "no cover"
held for the wrong reason. ⭐ *A guard is only tested by the case it exists to catch.*

The shared gameweek fixture also carried **no `position` at all** — `best_legal_xi` is stubbed there, so
nothing had ever read it. **Fifth** fixture this month that modelled less than any real row does.

---

### 📊 On the owner's actual squad

```
· Worth 8: João Pedro is flagged — bench or replace him — benching him fields Walle Egeli (0.2 xP)
· Worth 8: E.Le Fée  is flagged — replace him — you have no cover on your bench
· Worth 8: Foden     is flagged — already on your bench
```

---

### 📊 Consequences

**Good:** the most common instruction the app gives about a flagged player now carries the fact that decides
whether to follow it. Free of new constants, new rankings and new churn.

**Costs / limits:**
- ⚠️ **It states, it does not solve.** The reader still has to notice that 0.2 is bad. That is deliberate —
  the alternative needs the E[max] re-ranking that the population could not evaluate.
- The cover figure is on the same basis as the rest of the block (the caller's horizon — **1** in production,
  so it reads as a this-week number). At a wider horizon the same sentence quotes a wider number.
- ⚠️ **A second gap was found and is NOT fixed here** — see below.

---

### 📋 Found while measuring, not built: the tie that was broken the wrong way

On RoboTS, the app recommended **E.Le Fée → Dewsbury-Hall, +1.2 XI xP next GW** — and prints, in the same
block, *"Longer view: −1.5 XI xP"*. Meanwhile **Walle Egeli → Barry (£5.6m)** is **+1.2 next GW and +3.1 over
five**, and turns 0.2 xP of forward cover into **4.5**.

**The two moves tie on the number the app ranks by**, and it has the number that separates them — it computes
the longer view and prints it without letting it choose. ⭐ *A ranking that separates two options by less than
its own noise is not ranking them, it is picking one* (ADR-189), and ⭐ *a number computed for one question
and discarded is invisible in a way a missing number is not* (ADR-191).

**Proposed, not built:** break a near-tie on next-GW gain toward the better horizon figure. It wants its own
measurement and its own gate.

---

### 🔗 Links

- [ADR-206](./ADR-206-a-doubt-is-a-probability.md) — the fix that exposed this
- [ADR-198](./ADR-198-why-73.md) — the levers this qualifies
- [ADR-200](./ADR-200-a-population-shaped-like-a-real-squad.md) — the population that could not see the effect
- [ADR-189](./ADR-189-two-defenders-one-bet.md) · [ADR-191](./ADR-191-spend-the-transfers-you-hold.md) — the tie-break above
- `spikes/208-cover/` — `measure.py` (one squad) · `population.py` (the refutation)
