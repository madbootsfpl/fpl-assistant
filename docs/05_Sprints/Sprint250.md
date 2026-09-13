# Sprint 250: Two defenders, one bet (ADR-189)

**Dates:** 2026-09-13
**Status:** ✅ Complete — ADR-189. **1753 → 1756 tests, ruff clean.**
⚠️ The headline feature was **declined on measurement**; a tie-break shipped instead.

> **Owner**, unprompted, on a suggestion to sell his Arsenal defender for a Sunderland one while already
> holding a Sunderland defender: *"I have Hume in my squad, a Sunderland player — he would be a better option
> to transfer to Ballard maybe."*

---

### 🔬 The premise was checked, and half of it failed

Followed ADR-145's method exactly, because that ADR killed a near-identical premise (*"player clashes"*).

**Test 1 — does it discriminate?** Clashes fired for **100%** of squads, which is why a warning would have
been wallpaper. This fires for **38%**. Cleared.

**Test 2 — what does it cost?** This is where it dies.

**Correlation never moves expected points.** It multiplies that component's spread by exactly **√2** —
**1.17 points at worst**, against an XI whose own spread is ~11.6. Ten percent of one component. And ADR-145
already settled that lower variance is not automatically better: chasing wants variance, protecting a lead
does not.

**The owner's instinct bundled two reasons of very different size:**

| reason | worth |
|---|---|
| his defender's club keeps clean sheets 3× as often | **~10 pts** (ADR-188) |
| doubling up on one defence | **~1.2 pts of spread** |

**Eight to one.** He was right twice; only one of them is worth building.

---

### 🎯 What shipped instead

Not a warning — a **tie-break**, because the real defect was elsewhere.

The model preferred one sell over the other by **1.7 xP across five gameweeks**. That is 0.34 a week against
a per-player weekly sd of **3.51**. It was a coin flip presented as a ranking, and the coin landed on the
correlated squad.

```python
TIE_NOISE = 2.0
pairs.sort(key=lambda t: (round(t[0] / TIE_NOISE), -_correlated_after(...), t[0]), reverse=True)
```

⚠️ **Quantised, not subtracted**, and that is the safety argument. Bucketing the gain leaves the primary
ordering intact for any real difference; the preference decides only *inside* a band. Subtracting a penalty
would let it outrank a better move — exactly the failure ADR-183's tie-break was sized to avoid.

Scoped to DEF/GK, because the claim is about **clean sheets**. Two midfielders at one club are not
all-or-nothing together, and widening it would make this an unmeasured "diversify" heuristic.

Verified on 120 live squads: **fires on 7%**, and **never gives up more than the band** (max 1.70 of 2.0).

---

### 💡 The lesson

> **A ranking that separates two options by less than its own noise is not ranking them — it is picking one.**

The defect was never a missing correlation term. It was that the model reported a **1.7 xP** preference as a
recommendation while its own measured noise is **3.51 a week**. Inside that band, *any* stated preference —
cheaper, diversified, fewer clubs — beats a coin flip, and costs nothing.

Third use of this shape: **ADR-183** broke optimiser ties toward the cheaper squad, **ADR-186** surfaced a
better move just out of budget, and now this.

> **Where a model cannot tell two options apart, the right move is not a better model — it is a stated
> preference.**

---

### 🧪 Tests

**+3**, all mutation-checked: a near-tie breaks toward the diversified sell · a difference outside the band
wins on merit · outfield positions are ignored. Mutations killed: the tie-break removed, the band widened to
50, the positions widened, the gate dropped.

The fixture is deliberately built so **raw gain prefers the correlated move** — otherwise the test would pass
without the feature, which is the trap three of the last five sprints fell into.
