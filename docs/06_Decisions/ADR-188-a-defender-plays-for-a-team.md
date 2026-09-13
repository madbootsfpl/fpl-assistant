# Architectural Decision Record: A defender plays for a team

**Decision ID:** ADR-188
**Date:** 2026-09-13
**Status:** 📋 **Proposed** — gate before building. **The gate is whether to open a fourth calibration
slot**, not what the term looks like.
**Superseded By / Replaces:** Would add a fourth weight to [ADR-101](./ADR-101-calibration-methodology.md)'s
harness and its §B0 bar. Uses data [ADR-119](./ADR-119-team-dna.md) already computes. **No change to
`decision_xp`'s structure** — one more term, gated at 0 like the other three.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, on an ADR-186 recommendation to sell Konsa (Arsenal) and buy Ballard (Sunderland):

> *"That is a transfer I would not make. I have a cheap Arsenal fullback, currently playing, likelihood of
> clean sheets is probably >50% based on current run… I have Hume in my squad, a Sunderland player — he would
> be a better option to transfer to Ballard maybe. How can we factor that knowledge in?"*

#### The app already has the knowledge. It just does not use it.

From Team DNA, today:

| | Arsenal | Sunderland |
|---|---|---|
| **Clean-Sheet Potential** | **75%** (97th pct) | **25%** (42nd pct) |
| Defensive Strength (team xGA) | 2.7 (95th) | 5.8 (32nd) |
| Grade | **A** | **C** |

He estimated *">50%"* for Arsenal. **It is 75%, on a page the app renders.**

#### What actually drives a defender's xP

```
xP = his own points-per-90  ×  expected minutes  ×  opponent difficulty
```

**There is no term for his own team's defensive solidity.** The only team signal is FDR, which prices *the
opponent*, not the defence behind the player. And the three signals that could carry it are computed and
then zeroed:

```
FORM_WEIGHT = 0.0 · SET_PIECE_WEIGHT = 0.0 · DEFCON_MAGNIFIER_WEIGHT = 0.0
```

So the model recommended selling a defender whose team keeps clean sheets **three times as often**, because
the replacement's *personal* historical scoring rate is higher.

#### Sizing it — the margin is a sixth of the blind spot

The model prefers selling Konsa over Hume by **1.7 xP** across five gameweeks (Konsa 13.1, Hume 14.8).

75% against 25% over five games is ~2.5 extra clean sheets; a defender's clean sheet is 4 points. **Call it
~10 points.** The margin driving the recommendation is roughly **a sixth** of the signal it cannot see.

⚠️ **That 10 is an illustration, not a measurement.** It extrapolates a four-game rate — Arsenal's 75% is
three clean sheets out of four — and this ADR must not be read as claiming a 10-point edge. It is an
order-of-magnitude check that the blind spot is larger than the margin, which is the only claim it needs to
support.

#### And a second thing the model cannot see: correlated risk

Konsa → Ballard leaves **Hume *and* Ballard, both Sunderland**. When Sunderland concede, both fail together.
Konsa + Ballard is diversified across two defences. The owner's alternative is right twice over, and
`suggest_transfers` has no concept of either reason.

---

### 💡 Options Considered

#### Option 1: A team clean-sheet term for DEF/GK, calibrated through §B0 *(Chosen)*
* **Description:** a fourth weight, `CLEAN_SHEET_WEIGHT`, defaulting to **0**, swept by ADR-101's harness
  against the same four criteria as the others. Ships only if it clears the bar.
* **Pros:**
  - ✅ **The data exists and is already displayed.** Team DNA computes clean-sheet potential per club; this
    reuses it rather than inventing a source.
  - ✅ It answers a real, repeatable blind spot — every defender transfer is priced without it.
  - ✅ **Calibrated, not guessed**, which is the only route this project accepts for a weight (ADR-101).
  - ✅ Costs nothing if it fails: the weight stays 0 and the config comment records why.
* **Cons:**
  - ❌ A fourth weight competing for the same thin data. GW4 is one honest attempt; four sweeps on four
    gameweeks is four chances to fool yourself.
  - ❌ Clean-sheet rate is partly **already inside** a defender's points-per-90 — a defender at a good club
    has historically scored more. Double-counting is the real risk, and the harness must be able to see it.

#### Option 2: Ship a hand-set weight now, because the effect is obvious
* **Cons:** ❌ This is precisely what ADR-101 exists to prevent. *"Obvious"* is what every dormant weight
  looked like before it was swept. ❌ And it would be tuned against **one anecdote from one squad**.

#### Option 3: Surface it as a warning rather than pricing it
> *"⚠️ Konsa's club keeps 75% clean sheets; Ballard's keeps 25%."*
* **Pros:** ✅ No model change, no calibration, ships immediately; honest as a lens (ADR-057's rule that
  crowd/team signals are lenses, never xP).
* **Cons:** ❌ It puts the judgement back on the reader for a fact the model could price. ❌ But it is the
  **right fallback if the weight fails §B0**, and should be adopted then rather than leaving the blind spot
  unmarked.

---

### 🎯 Decision & Justification

**Propose the weight; calibrate it; adopt Option 3 if it fails.**

**1. `CLEAN_SHEET_WEIGHT = 0.0`**, applied to DEF/GK only, from the club's clean-sheet rate. A fourth entry in
`_CALIBRATE_WEIGHTS`, swept by the existing harness.

**2. It faces §B0's four criteria unchanged** — ρ must improve by ≥1 SE, MAE must not worsen by >1%, hit@20
must not fall, and the gain must hold across ≥2 adjacent sweep values.

**3. Its prediction is recorded now, before the sweep** — the discipline §B0 exists to enforce:

| weight | expectation | if it comes back very differently |
|---|---|---|
| `CLEAN_SHEET_WEIGHT` | **small positive, ≈ 0.05–0.15**, and quite possibly **zero** — much of a club's clean-sheet tendency is already inside a defender's own points-per-90, since he was scoring those clean-sheet points last season too. | **A large gain is a warning, not a win.** It most likely means the term is re-ranking defenders by *club quality* — which FDR and the baseline rate already carry — rather than adding defensive information. Check it is not simply reproducing the FDR ordering before believing it. |

**4. The sitting is GW6, not now.** GW4 has one honest attempt in it and three weights already queued.
Adding a fourth to the same thin sample is how a noise result gets shipped. **This weight joins the GW6
sitting**, where all four are swept together against a season's worth of returns.

⚠️ **Correlated defensive risk is explicitly out of scope.** Two defenders from one club failing together is
a real effect and a different feature — a portfolio constraint, not a per-player weight. Named here so it is
not quietly folded in, and so it does not get lost.

---

### ⚖️ Consequences & Trade-offs

* **Positive Impact:** the largest structural blind spot in defender pricing gets measured; a signal the app
  already computes and displays stops being decorative; and either outcome is informative.
* **Negative Impact / Trade-offs:** a fourth weight on a bar designed for three; and a real chance the answer
  is *"no"*, which costs a sitting.
* **Risks & Mitigations:**
  - **Risk:** double-counting with points-per-90. **Mitigation:** the prediction above says so in advance, so
    a large positive is treated as suspicious rather than exciting.
  - **Risk:** four gameweeks of clean-sheet data is a tiny sample (Arsenal's 75% is 3 of 4). **Mitigation:**
    GW6 sitting, GW10 last look, then closed — ADR-101's stopping rule applies unchanged.
  - **Risk:** it fails and the blind spot stays unmarked. **Mitigation:** Option 3 is then adopted, not
    forgotten — written into the action items.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`config.py`, `analytics/xp.py`, `analytics/backtest.py`), Docs
* **Action Items — at the GW6 sitting, not before:**
  - [ ] `CLEAN_SHEET_WEIGHT = 0.0` in `config.py`, with the dormancy comment the other three carry
  - [ ] The term in `decision_xp`, DEF/GK only, from the club clean-sheet rate
  - [ ] A fourth entry in `_CALIBRATE_WEIGHTS`, swept by the existing harness
  - [ ] Guard: at weight 0 every projection is **byte-identical** — the invariance test the other three have
  - [ ] Sweep at GW6 against §B0's four criteria; record the result **either way** in this ADR
  - [ ] **If it fails:** adopt Option 3 — a lens on the transfer surface naming both clubs' clean-sheet rates
  - [ ] Update the GW1_RUNBOOK §B0 table with the fourth weight and its prediction

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A number the app displays and does not use is a claim it is making to the reader and not to itself.**

Team DNA has shown *Clean-Sheet Potential: 75%, 97th percentile* for weeks. A manager reading that page would
reasonably assume the recommendation engine knew it. It did not — the two surfaces share a database and not a
model.

The owner found it the only way it could be found: by knowing something the app also knew, and noticing the
advice did not reflect it. **The gap between what a system measures and what it acts on is invisible from
inside the system**, which is why the A/B is worth more than any test in this repo.

---

### 🔗 References & Related Artifacts
- **Calibration discipline:** [ADR-101](./ADR-101-calibration-methodology.md) + `docs/GW1_RUNBOOK.md` §B0
- **The data it would use:** [ADR-119](./ADR-119-team-dna.md) (Team DNA) · ADR-019 (`cleansheet.py`)
- **Why it is a lens until calibrated:** ADR-057 — team/crowd signals are never `decision_xp` on assertion
- **Found by:** the owner's two-team A/B, on an ADR-186 recommendation
