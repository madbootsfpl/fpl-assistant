# Architectural Decision Record: Head-to-head — ship the decomposition, gate the probability

**Decision ID:** ADR-161
**Date:** 2026-08-27
**Status:** ✅ **Accepted — built** (Sprint 216, 2026-08-27). **1525 → 1535 tests, ruff clean.**
⏳ **The win-probability half is GATED, not built** — evidence below, owner's call.
**Superseded By / Replaces:** Delivers the H2H half of the roadmap's competitive layer, next to 🏆 Leagues
(ADR-141). **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Leagues answers *"what is my league doing?"*. The roadmap kept a narrower question beside it — *"what do I need
to do to catch him?"* — noting it **needs per-manager projections rather than per-player ones**, and pairing it
with a **win-probability sim**.

The per-manager projection is straightforward: picks are public after each deadline, Leagues already fetches
them, and `decision_xp` prices them. The probability is not, and the two were bundled in one roadmap line as
though they were one piece of work.

---

### ✅ Decision — what shipped

**1. The gap is decomposed, not just totalled.** The module rests on one structural fact: **the players you
both start cancel**. Two managers in a mini-league typically share most of their squad; those players can score
90 points between them and change the head-to-head by nothing. The output is therefore the **differential
set, priced** — plus the shared count and its xP, so a small gap between two large totals is believable
rather than looking like rounding.

**2. Identical elevens with different captains are not identical.** The case that decides most real
head-to-heads, and the one a naive set-difference gets exactly wrong: every player is shared, so it finds no
differentials and calls a dead heat when the captain choice *is* the game. Shared players cancel at the
**minimum** of the two multipliers, so a captain's **extra copy** is priced as its own differential. Two tests
pin it.

**3. FPL's `multiplier` is taken at face value.** It already encodes captain (2), triple captain (3), bench (0)
and — the one that matters — **Bench Boost**, where all fifteen count. Re-deriving it from `is_captain` and the
1-11/12-15 split would have silently mis-scored every chipped gameweek.

**4. Rivals are projected with the same `decision_xp` map you are.** No second recipe (ADR-041). A parallel
projection for rivals would compare two models rather than two squads.

**5. The staleness is stated on the surface.** FPL publishes picks only after a deadline, so this projects
**the squad he had**, not the one he will field. He can transfer and re-captain. Real limit, said plainly.

### ⏳ Gated: the win-probability sim, and the measurement that stopped it

A probability needs a *distribution*; `decision_xp` is a rate model and yields a mean. Building one honestly
means a new event simulator (goals ~ Poisson, clean sheets ~ Bernoulli, minutes) fed by per-player season
rates — which the data *would* support, since season history carries goals, assists, clean sheets and minutes
across up to ten seasons.

**But measured on the live GW1 returns, the answer it would give is "roughly a coin flip", every week:**

```
GW1 actuals, players with 60+ minutes (n=188)
  mean 3.99 · sd 3.51 · median 2 · p90 9 · max 17

  a 1-differential head-to-head : gap sd ≈ 5.0 points
  a 3-differential head-to-head : gap sd ≈ 8.6 points
```

Typical projected gaps out of this module are **2-5 points**. Against a noise sd near 8.6, a 3-point projected
lead is about a **64%** chance — and that is the *optimistic* reading, because the distribution is heavily
right-skewed (mean 3.99, median 2.0, max 17), so the normal approximation that produced 64% is itself the
wrong shape.

So the probability would be a confident-looking number that says *"it's close"* almost every time, at the cost
of a whole new engine — and a percentage invites far more trust than a projected margin does. **Recommendation:
don't build it.** Ship the gap, which is actionable, and let the reader see that three differentials separate
them.

⚠️ **The measurement's own limits, stated so nobody over-reads it:** n is one gameweek, and 3.51 is a
**cross-sectional** spread across players, not one player's week-to-week variance. It is an estimate, not a
calibration — which is precisely why no constant from it has been baked into anything.

### 🧪 Definition of Done

1. **Tests: +10.** Captain doubled and bench ignored; the multiplier taken at face value (bench boost, triple
   captain); shared starters cancelling; **identical elevens with different captains**; a captain's extra copy
   priced rather than the whole player; truly identical squads saying so; the note naming the leader and the
   biggest differential; an unknown player id not crashing it; empty payloads safe. Plus the page still
   rendering.
2. **Manual smoke** — exercised end-to-end on synthetic pairs covering every branch; the live path needs a
   league and a manager id, which is the owner's to run.
3. **Docs** — this ADR, the roadmap item split, PROJECT_STATUS, a sprint retro.

---

### 💡 The lesson

**One roadmap line held two pieces of work with completely different evidence requirements.** "H2H and a
win-probability sim" reads as one feature; the first needs arithmetic over data we already fetch, the second
needs a distribution the model does not produce. Bundled, the hard half would have dragged the easy one — or,
worse, been built along with it on an invented variance because it was in the same sentence.

The generalisable form: **when an item names a deliverable and a method in the same breath, split them before
estimating.** The method is usually the part carrying the risk, and it is usually the part nobody costed.

And the narrower one, which is this project's habit by now: **the measurement that kills a feature is worth
more than the feature.** Half an hour against GW1 returns turned "build a win-probability sim" into a number
saying it would report a coin flip every week — and that number is now in the file, so the question does not
have to be re-opened from scratch.
