# Sprint 216: Head to head — ship the decomposition, gate the probability (ADR-161)

**Dates:** 2026-08-27
**Status:** ✅ Complete — ADR-161. 1525 → 1535 tests, ruff clean. ⏳ The win-probability half is **gated**.

---

### 🔧 What shipped

🏆 Leagues answers *"what is my league doing?"*. This answers *"what do I need to do to catch **him**?"* —
a rival picker on the Leagues page, and a decomposed head-to-head beneath it.

The module rests on one structural fact: **the players you both start cancel.** Two managers in a mini-league
share most of their squad, and those players can score 90 points between them without moving the
head-to-head an inch. So the output is the **differential set, priced**, with the shared count and its xP
printed beside it — which is what makes a 3-point gap between two 50-point totals believable.

**Identical elevens with different captains are not identical.** That case decides most real head-to-heads and
a naive set difference gets it exactly wrong: every player is shared, so it finds nothing and calls a dead heat
when the captain *is* the game. Shared players cancel at the **minimum** of the two multipliers, so a captain's
extra copy becomes its own differential. FPL's `multiplier` is taken at face value throughout, because it also
encodes Bench Boost — re-deriving it would have mis-scored every chipped week.

---

### ⏳ What did not ship, and the measurement that stopped it

A probability needs a distribution; `decision_xp` is a rate model and gives a mean. An honest simulator was
*possible* — season history carries goals, assists, clean sheets and minutes over ten seasons — but:

```
GW1 actuals, 60+ minutes (n=188): mean 3.99 · sd 3.51 · median 2 · max 17
  1-differential H2H : gap sd ≈ 5.0     3-differential H2H : gap sd ≈ 8.6
```

Projected gaps out of this module run **2-5 points**. Against that noise a 3-point lead is ~**64%** — and that
flatters it, since the distribution is heavily right-skewed and the normal approximation behind 64% is the
wrong shape. A whole new engine to print *"it's close"* every week, in the one format that invites the most
trust. **Recommended against building it.** The measurement's own limits are in the ADR, and no constant from
it has been baked into anything.

---

### 💡 The lesson

> **When an item names a deliverable and a method in the same breath, split them before estimating.**

"H2H and a win-probability sim" was one roadmap line holding two pieces of work with completely different
evidence requirements — arithmetic over data we already fetch, and a distribution the model does not produce.
Bundled, the hard half drags the easy one, or gets built alongside it on an invented variance purely because
it was in the same sentence.

> **The measurement that kills a feature is worth more than the feature.**

Half an hour against GW1 returns turned "build a win-probability sim" into a number showing it would report a
coin flip every week. That number is in the ADR now, so the question doesn't have to be reopened from scratch.

### 🧪 Tests

**+10.** Captain doubled and bench ignored; the multiplier at face value (bench boost, triple captain); shared
starters cancelling; identical elevens with different captains; a captain's extra copy priced rather than the
whole player; identical squads saying so instead of reporting a dead heat as a result; the note naming the
leader and the biggest differential; an unknown player id not crashing it; empty payloads safe; and the
Leagues page still rendering.
