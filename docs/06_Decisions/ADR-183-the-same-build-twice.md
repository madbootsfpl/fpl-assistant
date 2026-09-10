# Architectural Decision Record: The same build, twice, is the same squad

**Decision ID:** ADR-183
**Date:** 2026-09-10
**Status:** ✅ **Accepted — built** (Sprint 244, 2026-09-10). **1733 → 1738 tests, ruff clean.**
**Superseded By / Replaces:** Third owner report against this control ([ADR-045](./ADR-045-bench-aware-optimisation.md)
built it, [ADR-137](./ADR-137-two-build-modes-named-truthfully.md) corrected its labels). **No `decision_xp`
change**; one term added to the optimiser's objective.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Owner-reported:

> *"Bug: in My Squad, Lab, Build a new team — when toggling between Build mode, there are no changes to the
> team, was expecting weaker/stronger bench."*

Reproduced on the page immediately: both modes rendered an identical fifteen and an identical bench.

⚠️ **This ADR was first written with the wrong diagnosis, and the correction is the substance of it.** The
first draft concluded *"the modes work and are simply inert at a full budget — there is nothing to trade at
£100m."* That was built on measurements which were each **a single sample of a nondeterministic process**, and
it was wrong.

---

### 🔬 The real cause: the optimiser was not deterministic

The objective has **exact ties**, and CBC picks among them arbitrarily — differently **between processes**.
Six identical runs of the *same* build, same inputs:

```
squad 23027   objective 401.400   cost £99.9
squad 27483   objective 401.400   cost £99.7      ← both optimal, both returned
squad 27483   objective 401.400   cost £99.7
squad 23027   objective 401.400   cost £99.9
squad 23027   objective 401.400   cost £99.9
squad 27483   objective 401.400   cost £99.7
```

**Both squads score 401.400 — genuinely tied.** The solver is not wrong; it is answering a question with more
than one right answer, and choosing unpredictably.

**Two consequences, and the reported bug is the smaller one:**

1. **The same build, run twice, returned different squads.** A user who rebuilds gets a different team with
   no explanation and no change of input. That is the more serious defect and nobody had reported it.
2. **One of the tied optima happens to be the squad Strong XI picks.** So roughly half the time, an All-round
   build landed on the Strong-XI answer and the toggle appeared dead. That is what the owner saw.

#### Why the first diagnosis was wrong

Every measurement in the first draft — *"identical at £100m, different at £99.5"*, and a table of six
objective/horizon combinations — was one roll of the dice per cell. Re-run on a deterministic solver, the
modes differ **at every budget tested, including £100m**:

| budget | All-round XI / bench £ | Strong XI XI / bench £ | XI gain |
|---:|---:|---:|---:|
| 100.0 | 305.1 / £22.6m | 306.6 / £21.2m | **+1.5** |
| 95.0 | 301.0 / £20.8m | 305.1 / £17.9m | **+4.1** |
| 90.0 | 294.3 / £20.2m | 297.8 / £19.1m | **+3.5** |
| 85.0 | 280.5 / £21.9m | 293.3 / £16.5m | **+12.8** |
| 80.0 | 266.6 / £19.6m | 278.8 / £17.5m | **+12.2** |

There is no "collision at £100m". **There was a coin flip, and I measured it once per cell and wrote down
the results as if they were facts.**

---

### 🎯 Decision & Justification

**1. Break ties deterministically, toward the cheaper squad.**

```python
_TIE_BREAK = 1e-3
cost_term = _TIE_BREAK * pulp.lpSum(p["price"] * pick[p["id"]] for p in players)
problem += <objective> - cost_term
```

Among squads that score **identically**, prefer the one that costs less: same projected points, more money in
the bank. That is a real preference rather than an arbitrary rule, which is what makes it defensible as a
tie-break rather than a hack.

⚠️ **The magnitude was measured, not guessed.** `1e-6` was tried first and **did not work** — the gap it
creates between two squads £0.2m apart is 2e-7, below CBC's own tolerance, so the solver still could not
separate them. `1e-3` resolves. The safety question is whether it can ever outrank a genuinely better squad,
so that was measured directly:

| | |
|---|---|
| Budgets × modes tested | 5 × 2 = **10** |
| Worst xP given up to the tie-break | **0.000** |

It separates exact ties and nothing else, across every case tried.

**2. Price the mode, now that the comparison means something.** The alternative build is solved too
(**0.08s**) and the page says what the chosen mode bought:

> *"**Strong XI** — 12.8 xP more in your starting XI than **All-round** would give, with £5.4m less on the
> bench."*

This is the half of the original proposal that survives, and it answers the question the toggle actually
raises — not *"is it different?"* but *"is it worth it?"*

**3. Keep a collision notice as a guard, not as a feature.** If the two modes ever do return the same fifteen,
the page says so rather than rendering silence. On stable data that branch should never fire — which is
precisely why it is worth having: it is the alarm that would have caught **ADR-137's** mode, which was
structurally incapable of differing and went unnoticed until the owner reported it.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:**
  - **The Lab is reproducible.** The same inputs give the same squad, every time, in any process.
  - Ties now resolve to the **cheaper** squad — strictly better for the user at equal xP.
  - The toggle visibly works, and carries a number.
  - A future mode collision announces itself instead of waiting for a report.
* **Negative Impact / Trade-offs:**
  - A second solve per build (0.08s measured).
  - The objective is no longer *purely* xP. Mitigated by measurement — zero xP lost in ten cases — but it is
    a real change to what "optimal" means, and it is stated in the code.
* **Risks & Mitigations:**
  - **Risk:** `1e-3` distorts a near-tie on some future dataset. **Mitigation:** a guard asserts the
    tie-break never lowers the primary objective; if a dataset ever breaks that, it fails in CI.
  - **Risk:** CBC's tolerance changes and `1e-3` stops resolving. **Mitigation:** the determinism guard
    catches it — it asserts equality across repeated solves, not a specific squad.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`analytics/optimizer.py`, `views/squads.py`), Tests, Docs
* **Action Items:**
  - [x] `_TIE_BREAK` in the objective, both branches
  - [x] Solve the other mode; price the chosen one
  - [x] Keep a collision notice as an alarm
  - [x] Guard: **repeated identical solves return an identical squad**
  - [x] Guard: the tie-break never lowers the primary objective
  - [x] Guard: among tied optima the **cheaper** squad wins
  - [x] Guard: the page prices the mode, and says so if they ever collide
  - [x] **Mutation-test every guard**, clean suite re-run between mutants
  - [x] Update PROJECT_STATUS, the Roadmap, and a sprint retro

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

#### 🧭 If this ADR renames/moves/merges/retires a user-facing surface
**Not applicable** — the build-mode radio keeps ADR-137's labels exactly. One caption is added.

---

### 💡 The lesson

> ⭐ **A measurement of a nondeterministic process is not a measurement.**

I ran each configuration once and tabulated the results as facts. The table was internally consistent,
looked authoritative, and was noise — and it produced a confident, wrong diagnosis that would have shipped a
caption explaining a phenomenon that does not exist.

The check that would have caught it, and which cost nothing once applied: **run the same measurement twice
before writing it down.** The contradiction was available at any point — two of my own reconstructions
disagreed, and I explained the difference away three times (Row vs dict, `keep_ids`, state leakage) before
testing determinism itself.

⚠️ **The second lesson is about which bug to report.** *"The toggle does nothing"* was the visible symptom of
*"the optimiser is not reproducible"* — a defect nobody had noticed and which is worse. **The reported symptom
was a way in, not the size of the problem** — the third time this month that has held.

---

### 🔬 Two guards that were wrong first

**1. The determinism guard could not reach the failure.** Written as five solves **in one process**, it
passed with the fix reverted — because the instability was never *within* a process, it was *between* them.
It now shells out to four subprocesses. **A guard that cannot reach the failure mode is not a guard, however
well it reads.**

**2. The fixture could not express the thing under test — twice.**

- **First version:** every player in a position scored identically, so the whole pool was one enormous tie.
  The fixture was itself nondeterministic and the test flaky in *both* directions.
- **Second version:** the two tied players were both good enough to be picked, so there was no either/or to
  resolve; and the price gap was **£2m** where the real one is **£0.2m**, which let `1e-6` pass in the test
  while failing in production.

Both were caught by mutation-testing, not by reading. The final fixture holds **exactly two contests**: an
exact tie decided only by a £0.2m price gap, and a genuinely-better-but-dearer player who must survive. Those
two together catch an epsilon that is too small, too large, or absent — which is the whole safety envelope,
and none of the three was caught before.

> **A fixture for a tie-break must contain the tie under test, at the scale it occurs, and nothing else.**

---

### 🔗 References & Related Artifacts
- **Third report against:** [ADR-045](./ADR-045-bench-aware-optimisation.md) ·
  [ADR-137](./ADR-137-two-build-modes-named-truthfully.md)
- **Found by:** the owner, toggling a control and seeing nothing
