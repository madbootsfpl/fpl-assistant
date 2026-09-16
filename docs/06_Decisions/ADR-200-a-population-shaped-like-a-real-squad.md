# Architectural Decision Record: A population shaped like a real squad

**Decision ID:** ADR-200
**Date:** 2026-09-16
**Status:** ✅ **Accepted — built; the two thresholds ADR-199 gated are now measured and set.**
**1818 → 1819 tests, ruff clean.**
**Superseded By / Replaces:** Closes two of [ADR-199](./ADR-199-a-threshold-needs-a-provenance.md)'s gates and
unblocks [ADR-191](./ADR-191-spend-the-transfers-you-hold.md) §2. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Three separate measurements were blocked on the same missing thing — `_CLEAR_GAIN`, `_CLEAR_REBUILD`
(ADR-199) and joint transfer planning (ADR-191 §2). All three had been measured over **random legal squads**,
and spike 191 had already found that random squads carry far too much headroom.

**The number that settles it:**

| population | XI xP over 5 GWs |
|---|---|
| random legal squad | **121.3** |
| the owner's TS | 231.1 |
| template (most-owned within budget) | 226.6 |
| the owner's RoboTS | 244.2 |
| the optimiser's own 15 | 291.1 |

⭐ **A random squad is not a bad squad — it is barely a squad.** Everything looks improvable against it.

---

### 🎯 Decision — and the thing that made it harder than expected

**A quality dial, not "a realistic squad".** `population.py` offers `optimal()` (the ceiling),
`template()` (the most-owned 15 the money buys — the only *observed* population here), and `perturbed()`
(k legal swaps from a base). A measurement reports its answer **as a function of quality**, and the threshold
is read off where the app's users actually sit.

#### ⚠️ Quality alone was not enough, and this is the finding

| population | XI xP | best-transfer p75 |
|---|---|---|
| optimum perturbed 9× | **227.0** | **2.88** |
| template | **226.6** | **1.60** |

**The same quality. Nearly double the improvability.** Perturbing the optimum creates **repairable holes** —
a few specific bad players, each individually replaceable. A template squad is **uniformly mediocre**: no
single glaring weakness to fix. Real squads behave like the template, not like a damaged optimum.

⭐ **The population had to be shaped like a real squad, not merely scored like one.** A one-dimensional
"quality" knob would have produced a confident number from the wrong distribution — the same failure as
ADR-188's clean-sheet rate, one level up: not a bad *measurement*, a bad *model of what was being measured*.

So the distribution comes from perturbing the **template**, which keeps real-squad shape and yields a
population instead of the three observed points.

#### The two thresholds

| | was | measured p75 | now |
|---|---|---|---|
| `_CLEAR_GAIN` (best transfer, 1 GW) | 3.0 | 2.30 *(observed 1.60 · 1.77)* | **2.3** |
| `_CLEAR_REBUILD` (rebuild ÷ own projection) | 0.25 | 0.46 *(observed 0.40 · 0.42)* | **0.46** |

⚠️ **`_CLEAR_REBUILD` is the one that mattered.** Real squads gain **0.40–0.48** of their own projection from
a rebuild, so **every real squad cleared 0.25** — the wildcard confidence read **95/High for all of them**.
⭐ *A number that never varies is not a confidence, it is a constant with a gauge drawn round it.*

The original comment called 25% *"deliberately high"* and reasoned it carefully: a quarter of your season
left on the table is not a marginal call. **The reasoning was sound and the premise was untested.** It is a
lot. It is simply not rare.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** two more invented constants become measured; the wildcard gauge starts discriminating;
  and the population is a **reusable module**, so the next calibration does not re-derive it.
* **Negative Impact / Trade-offs:** the wildcard will read lower — a typical squad drops from 95 to ~88. That
  is the correction. And `template()` needs an optimiser solve, so it is not free.
* **Risks & Mitigations:**
  - **Risk:** the template is one squad, and "shaped like a real squad" is still a model. **Mitigation:**
    cross-checked against the owner's two actual squads, which agree to ~10% on both quantities — three
    independent constructions landing together.
  - **Risk:** perturbing the template is itself a construction. **Mitigation:** stated, with both seeds and
    all three k values printed, so the sensitivity is visible rather than hidden behind one number.

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/explain.py` (two constants), `tests/test_explain.py`,
  `tests/test_chips.py`, `spikes/200-realistic-squads/`
* **Action Items:**
  - [x] `population.py` — optimal · template · perturbed · ladder, all returning **legal** 15s
  - [x] Measure both thresholds across the dial, two seeds, cross-checked against real squads
  - [x] Set both; remove them from ADR-199's `UNMEASURED` map
  - [x] Mutation-test — both reversions caught, plus a control that should pass
  - [ ] **Use it for ADR-191 §2** — joint pair planning was gated on this same population
  - [ ] `FLAG_COST` stays gated: not a margin, so the p75 rule does not apply to it

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **"Measure it on realistic data" is not an instruction until you can say what realistic means.**

ADR-199 gated two thresholds with the note *"needs realistic squads"*, which felt like a complete answer and
was not. Building it forced the real question: a squad can match a real one on **quality** and still be wrong
on **shape**, and shape was what the measurement depended on. The 227-vs-226.6 pair is the whole ADR — two
populations indistinguishable on the obvious axis, differing by nearly 2× on the thing being measured.

⭐ The generalisable form: **when you reject a population, say what property made it wrong.** *"Random squads
are unrealistic"* would have led straight to the perturbed optimum, which is unrealistic in a different way
and would have produced a confident wrong number instead of an obviously wrong one.

---

### 🔗 References & Related Artifacts
- **The gate it closes:** [ADR-199](./ADR-199-a-threshold-needs-a-provenance.md)
- **The gate it opens:** [ADR-191](./ADR-191-spend-the-transfers-you-hold.md) §2
- **Where the population problem was first seen:** `spikes/191-two-transfers/`
- **The same shape one level up:** [ADR-195](./ADR-195-team-defence-is-xgc-not-clean-sheets.md) — a sound
  measurement of the wrong quantity
- **The module:** `spikes/200-realistic-squads/population.py`
