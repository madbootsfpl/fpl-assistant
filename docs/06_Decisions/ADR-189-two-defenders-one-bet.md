# Architectural Decision Record: Two defenders, one bet

**Decision ID:** ADR-189
**Date:** 2026-09-13
**Status:** ✅ **Accepted — built** (Sprint 250, 2026-09-13). **1753 → 1757 tests, ruff clean.**
🔧 **Corrected same day** — the first implementation did not fire. See §Quantising is not a band.
⚠️ **The warning is DECLINED on evidence; a tie-break ships instead.**
**Superseded By / Replaces:** Takes up the correlated-risk item [ADR-188](./ADR-188-a-defender-plays-for-a-team.md)
scoped out. Extends [ADR-046](./ADR-046-xi-aware-transfers.md)'s ranking with a tie-break, in the shape
[ADR-183](./ADR-183-the-same-build-twice.md) used for the optimiser. **No `decision_xp` change.**
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, unprompted, on a suggestion to sell his Arsenal defender and buy a Sunderland one while already
holding a Sunderland defender:

> *"I have Hume in my squad, a Sunderland player — he would be a better option to transfer to Ballard maybe."*

Two defenders at one club are not two bets. They are **one bet, twice**: the clean sheet arrives for both or
neither.

---

### 🔬 Measured first — and the headline feature does not survive it

This followed [ADR-145](./ADR-145-fixture-concentration.md)'s method exactly, because that ADR killed a very
similar premise (*"player clashes"*) on two measurements.

**Test 1 — is it discriminating?** ADR-145 rejected clashes because **100%** of squads had one, so a warning
would be wallpaper.

```
400 legal squads (£100m, ≤3 per club)
  XIs with 2+ defensive assets from one club : 153 (38%)
  that block's share of XI xP : median 19% · p90 26% · max 39%
```

**38%, not 100%.** It discriminates. First hurdle cleared.

**Test 2 — what does it cost?** This is where it fails.

| club CS rate | E[pts] correlated | E[pts] independent | SD corr | SD indep | ratio |
|---:|---:|---:|---:|---:|---:|
| 25% | 2.0 | 2.0 | 3.46 | 2.45 | **1.41** |
| 50% | 4.0 | 4.0 | 4.00 | 2.83 | **1.41** |
| 75% | 6.0 | 6.0 | 3.46 | 2.45 | **1.41** |

**Correlation never moves the expected points.** It multiplies the spread of that component by exactly √2 —
worth **1.17 points at its worst**, against an XI whose own spread is ~11.6 (ADR-161's sd 3.51 per starter).
**Ten percent of one component.**

And ADR-145 already settled the framing: **lower variance is not automatically better.** Chasing a rival
wants variance; protecting a lead wants less of it. So even the 1.17 is not unambiguously a cost.

#### The comparison that decides it

The owner's instinct bundled two reasons. They are not the same size:

| reason | worth |
|---|---|
| the outgoing defender's club keeps clean sheets 3× as often | **~10 pts** (ADR-188) |
| doubling up on one defence | **~1.2 pts of spread** |

**The clean-sheet weight dominates by roughly 8 to 1.** He was right on both counts; only one of them is
worth a feature.

---

### 🎯 Decision & Justification

**Decline the warning. Ship the tie-break.**

**1. No warning, no weight.** A surface firing on 38% of squads to report a tenth of one component's spread
is how a product teaches people to ignore its warnings. Recorded here with the numbers so it is not
re-proposed from intuition.

**2. But the ranking was deciding this on noise, and that is a real defect.** Konsa 13.1 against Hume 14.8 is
**1.7 xP over five gameweeks** — 0.34 a week, against a per-player weekly sd of **3.51**. The model picked a
sell on a difference it has no business trusting, and the coin landed on the correlated squad.

So: **when two candidate sells are within noise of each other, prefer the one that leaves less correlated
defensive exposure.**

```python
TIE_NOISE = 2.0
pairs.sort(key=lambda t: (round(t[0] / TIE_NOISE), -_correlated_after(...), t[0]), reverse=True)
```

⚠️ **A band around the leader, not a subtraction and not a bucket.** Only moves within `TIE_NOISE` of the
best are considered, and among those the least correlated wins. Subtracting a penalty would let it outrank a
genuinely better move — the failure ADR-183's tie-break was sized to avoid. Bucketing fails differently, and
did; see below.

**3. Scoped to DEF/GK, because the claim is about clean sheets.** Two midfielders at one club are not
all-or-nothing together — their returns come from goals and assists. Widening it would make this a general
"diversify" heuristic nobody has measured.

#### Verified on live data

```
120 squads — the tie-break changed the top suggestion in 8 (7%)
  xP given up:  median 1.30   max 1.70   (band 2.0)
  any exceeding the band? no
```

It speaks rarely, and never costs more than the noise it was sized against.

---

### 🔧 Quantising is not a band — the first implementation did not fire

Shipped as a sort key: `round(gain / TIE_NOISE)`, then correlation, then gain. The reasoning was that
bucketing keeps the primary ordering intact while letting the preference decide inside a bucket. **It does
not work**, and the owner found it within the hour: the app still recommended selling his Arsenal defender.

His two candidate moves gained **11.4** and **9.7** — **1.7 apart, comfortably inside a band of 2.0**. But:

```
round(11.4 / 2.0) = 6
round( 9.7 / 2.0) = 5      ← different buckets, so the tie-break never engaged
```

> ⭐ **Quantising is not the same as "within noise of each other."** Bucket edges fall where they fall, and
> two near-equal values can land either side of one. A band is a statement about *the distance between two
> numbers*; a bucket is a statement about *where each number sits on a grid*. They are not the same thing,
> and only one of them is what "these are too close to call" means.

Replaced with the direct form: take the best remaining gain, keep every move within `TIE_NOISE` of it, and
pick the least correlated. No edges.

⚠️ **And the test passed the whole time**, which is the part worth keeping. Its fixture gained **14.0** and
**13.6** — which happen to round into the same bucket, so the mechanism appeared to work.

> **A fixture that only exercises the lucky case will confirm a broken mechanism.**

There is now a second guard pinning gains that *straddle a bucket edge*, with an assertion that the fixture
straddles one — so it cannot silently drift back into the easy case.



* **Positive Impact:** a decision previously made by coin-flip now has a reason; no new surface; the declined
  warning is recorded with its evidence so the question is closed rather than recurring.
* **Negative Impact / Trade-offs:** the top suggestion changes for ~7% of squads, giving up a little gain
  inside the noise band — deliberate, and bounded by construction.
* **Risks & Mitigations:**
  - **Risk:** `TIE_NOISE = 2.0` is tuned to a five-gameweek window and would be wrong on a one-week one.
    **Mitigation:** flagged here; the same class of error as ADR-186's, caught then. Re-measure if the
    default horizon changes.
  - **Risk:** someone reads the tie-break as a claim that diversifying is worth points. **Mitigation:** it
    is worth **zero** expected points by construction, and this ADR says so in a table.

---

### 🛠 Implementation & Migration
* **Components Affected:** Code (`analytics/transfer.py`), Tests, Docs
* **Action Items:**
  - [x] `_correlated_after` — defensive assets from the incoming club remaining after the swap
  - [x] `TIE_NOISE`, with ADR-161's sd as the stated reason for the number
  - [x] Quantised sort key, so the primary ordering survives
  - [x] Guard: a near-tie breaks toward the diversified sell
  - [x] Guard: a difference outside the band wins on merit
  - [x] Guard: outfield positions are ignored
  - [x] Mutation-tested — removed · band widened to 50 · positions widened · gate dropped
  - [x] Owner-verified 2026-09-13 — *"its picking another option which is fine"*; see the note below

#### ✅ Always
- [x] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 🔗 It composes with ADR-186, and changes what the cliff reports

Owner-verified after the correction: the *Worth saving for* line now names a **different move at a different
budget**. That is the two features interacting correctly, and it is not obvious, so it is recorded.

```
extra £    tie-break ON                 tie-break OFF
   0.0     Konsa→Affengruber  +9.0      Konsa→Affengruber  +9.0
   0.5     Hume→Ballard      +10.0      Konsa→Ballard     +11.4
```

At £0.5m the tie-break takes the diversified move, which gains **1.0 over the £0 baseline** rather than 2.4 —
**below ADR-186's 2.0 minimum uplift**. So the cliff stops advertising £0.5m and sweeps on to a budget where
waiting actually pays.

**That is the right composition.** If the honest choice at £0.5m is only worth 1.0 more than acting now, then
£0.5m is not worth saving for, and the cliff should say so by not mentioning it. A tie-break that quietly
propped up a threshold it had just undercut would be the bug.

---

### 💡 The lesson

> **A ranking that separates two options by less than its own noise is not ranking them — it is picking one.**

The defect was never that the model lacked a correlation term. It is that it reported a **1.7 xP** preference
as a recommendation when its own measured noise is **3.51 a week**. Any structural preference — cheaper,
diversified, fewer clubs — is strictly better than a coin flip inside that band, and free.

This is the third time that shape has been useful here: ADR-183 broke optimiser ties toward the cheaper
squad, ADR-186 reported a better move just out of budget, and now this. **Where a model cannot tell two
options apart, the right move is not a better model — it is a stated preference.**

---

### 🔗 References & Related Artifacts
- **Method borrowed from:** [ADR-145](./ADR-145-fixture-concentration.md) — check the premise before building
- **Noise baseline:** [ADR-161](./ADR-161-head-to-head.md) — one starter's single-GW sd is 3.51
- **Same tie-break shape:** [ADR-183](./ADR-183-the-same-build-twice.md)
- **The other half of the owner's point:** [ADR-188](./ADR-188-a-defender-plays-for-a-team.md), worth ~8×
  more
