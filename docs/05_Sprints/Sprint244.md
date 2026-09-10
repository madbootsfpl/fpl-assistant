# Sprint 244: The same build, twice, is the same squad (ADR-183)

**Dates:** 2026-09-10
**Status:** ✅ Complete — ADR-183. **1733 → 1738 tests, ruff clean.**

> **Owner:** *"Bug: in My Squad, Lab, Build a new team — when toggling between Build mode, there are no
> changes to the team, was expecting weaker/stronger bench."*

---

### 🔴 The reported bug hid a worse one

The optimiser's objective has **exact ties**, and CBC picked among them arbitrarily — differently between
processes. Six identical runs of the *same* build:

```
squad 23027   objective 401.400   cost £99.9
squad 27483   objective 401.400   cost £99.7   ← both optimal, both returned
squad 27483   objective 401.400   cost £99.7
squad 23027   objective 401.400   cost £99.9
```

**The same build, run twice, returned different squads.** That is the serious defect and nobody had reported
it. The owner's symptom was a side effect: one of the tied optima happens to be the squad Strong XI picks, so
roughly half the time an All-round build landed on it and the toggle looked dead.

**Fix:** among squads that score identically, prefer the **cheaper** one — same projected points, more money
in the bank. A real preference, not an arbitrary rule.

---

### ⭐ The lesson — a measurement of a nondeterministic process is not a measurement

**This ADR was first written with the wrong diagnosis**, and the first draft was confident: *"the modes work
and are simply inert at £100m — at a full budget there is nothing to trade."* It came with a budget table and
a six-cell objective/horizon table.

**Every cell was one roll of a die.** Re-measured on a deterministic solver, the modes differ at **every**
budget including £100m. There was no collision. There was a coin flip, measured once per cell and written
down as fact.

The check that would have caught it cost nothing: **run the same measurement twice before writing it down.**

Worse, the contradiction was available throughout — two of my own reconstructions disagreed — and I explained
it away **three times** (Row-vs-dict, `keep_ids`, solver state leakage) before testing determinism itself.
Each explanation was plausible, and each was a way of not asking the question.

> **When two runs of your own test disagree, that IS the finding. Stop explaining it.**

---

### ⚙️ The constant was measured, not chosen for looking small

`_TIE_BREAK = 1e-6` was the instinct. **It does not work**: the gap it creates between two squads £0.2m apart
is 2e-7, below CBC's own tolerance, so the solver still cannot separate them. `1e-3` resolves.

The safety question — can it outrank a genuinely better squad? — was then measured directly rather than
argued: **5 budgets × 2 modes, worst xP given up 0.000.**

---

### 🔬 Two guards that were wrong first

**The determinism guard could not reach the failure.** Written as five solves **in one process**, it passed
with the fix reverted — the instability was never within a process, it was between them. It now shells out to
four subprocesses.

> **A guard that cannot reach the failure mode is not a guard, however well it reads.**

**And the fixture could not express the thing under test — twice.** First it scored every player in a
position identically, making the whole pool one enormous tie, so the fixture was itself nondeterministic and
the test flaky in both directions. Then its two tied players were both good enough to be picked (no either/or
to resolve), and its price gap was **£2m** where the real one is **£0.2m** — which let `1e-6` pass in the
test while failing in production.

> **A fixture for a tie-break must contain the tie under test, at the scale it occurs, and nothing else.**

The final fixture holds exactly two contests: an exact tie decided only by a £0.2m gap, and a
genuinely-better-but-dearer player who must survive. Together they catch an epsilon that is **too small, too
large, or absent** — none of which the earlier versions caught.

---

### 🧪 Tests

**+5.** Determinism across processes · a tie resolving to the cheaper squad · the tie-break never costing a
point · the page pricing the mode · the two modes returning different squads.

Every one mutation-checked, including four values of `_TIE_BREAK` (0, 1e-6, 1e-3, 0.5, 5.0).
