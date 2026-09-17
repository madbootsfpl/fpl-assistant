# Architectural Decision Record: Team defence is xGC, not clean sheets

**Decision ID:** ADR-195
**Date:** 2026-09-16
**Status:** ✅ **BUILT 2026-09-17 — the input is swapped; the weight is still 0 and sweeps at GW6.**
**1832 → 1842 tests, ruff clean. 9 mutants, all red.** Originally 📋 Proposed — gate before building. Reopens [ADR-188](./ADR-188-a-defender-plays-for-a-team.md)
with a **different instrument**, not a re-run.
**Superseded By / Replaces:** Would change `cleansheet.py`'s **input** and leave its shape, its guards and its
dormancy intact. Uses [ADR-190](./ADR-190-the-gw4-sitting.md)'s Option 3 for scoring.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The owner, for the third time, on defenders:

> *"Start Thomas over Konsa — not a chance. **Coventry shipped 5 goals last week, haven't got a point yet**,
> whereas Arsenal have just shipped a couple."* … *"Konsa → Affengruber I don't understand. **Fulham have only
> 1 clean sheet and 1 point this season.** Hume for him might be a better move, but not Konsa."*

Measured (`spikes/195-team-defence-xgc/`):

| club | xGC per 90 | rank | the player in question |
|---|---|---|---|
| **Arsenal** | **0.65** | **1 of 20** | Konsa — the app wanted him benched *and* sold |
| Sunderland | 1.39 | 10 | Hume — the owner's preferred sale |
| Fulham | 1.83 | 16 | Affengruber — the buy |
| **Coventry** | **1.94** | **19 of 20** | Thomas — the app wanted him started |

**Arsenal concede a third of what Coventry do, and the model rates their defenders 0.1 xP apart.** The owner's
instinct about *which* player to sell also lands on this ranking: Sunderland 10th vs Arsenal 1st.

#### ⚠️ ADR-188 asked this exact question and got a null. Twice.

It tested a club's **clean-sheet rate**, found the curve *descending*, re-scored it on DEF/GK alone after
ADR-190 (spike 192) and found it descending *more steeply*, and concluded the term double-counts what
points-per-90 already contains.

**Those measurements were sound for the quantity chosen. The quantity was badly chosen.** Over four gameweeks
a clean-sheet rate is a five-valued statistic derived from a coin flip — 0, 1, 2, 3 or 4 of 4 — so its variance
swamps whatever signal it carries. ⭐ **A null from an instrument that cannot resolve the thing is not evidence
of absence**, and it was recorded as though it were.

---

### 📊 What the better instrument shows

`xGC/90` is **continuous**, minutes-normalised, and spreads **3×** between best and worst club:

```
Spearman(club defensive quality, that defender's actual points) = +0.216
n = 379 DEF/GK player-gameweeks (60+ mins) · 1 SE ≈ 0.051   →   4.2 standard errors
```

Where clean-sheet rate showed nothing, xGC/90 shows a clear association. **4.2 SE is not a rounding error.**

⚠️ **What this does not show, stated before anyone over-reads it:**

- **It is a correlation, not a backtest of the term.** A defender at a good club already has a better
  points-per-90, so part of +0.216 is information `decision_xp` **already has**. Whether a delta-vs-league-mean
  *adds* anything is exactly what ADR-188's shape was designed to isolate, and only a §B0 sweep can answer it.
- **The confound is unresolved.** Good clubs have good players. This cannot separate *"a solid defence earns
  clean-sheet points"* from *"Arsenal's defenders are simply better footballers"*.
- **n is four gameweeks.** Same thin sample as every other measurement this month.

---

### 🎯 Proposal

**Change the input, keep everything else.** `cleansheet.py` already computes a delta against the league mean
for DEF/GK only, is gated at `CLEAN_SHEET_WEIGHT = 0`, and carries five mutation-tested guards. Swapping
clean-sheet rate for **xGC/90 delta** is a change to one function's argument, not a new feature.

1. `team_xgc90()` beside the existing rate helper — minutes-normalised, `None` for a club with too few minutes
   (unknown stays *no opinion*, never 0 — ADR-172's rule holds).
2. The term keeps its sign convention: **better than the league mean → positive**, DEF/GK only.
3. **Sweep at GW6**, scored on the whole board **and on DEF/GK alone** (ADR-190 Option 3 — which refuted my
   last hypothesis and is worth running precisely because it can).
4. **Prediction recorded first** (§B0): a small positive, ≈0.05–0.20. A large gain still means the term is
   re-ranking by club quality rather than adding defensive information — that warning from ADR-188 stands
   unchanged, because it was never the thing that was wrong.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the largest repeatedly-reported blind spot gets measured with an instrument that can resolve
  it; the number the Team DNA page already shows stops being decorative.
* **Negative:** a fourth attempt at one idea, on a sample that is still thin. If this returns a null too, the
  honest reading is that the effect is inside points-per-90 and the question closes for the season.
* **Risks & Mitigations:**
  - **Risk:** measuring until something passes. **Mitigation:** this is a **different quantity**, not a re-run,
    and the ADR says so before the sweep. If xGC/90 nulls, ⭐ *that is the answer and the question closes* —
    §B0's stopping rule applies, and a fifth instrument would be exactly the mistake this ADR is accusing the
    third of.
  - **Risk:** the confound ships as a finding. **Mitigation:** named above, in advance, so a positive result
    has to argue past it rather than around it.

---

### 🛠 Implementation & Migration
* **Components Affected:** `analytics/cleansheet.py` (input only), `analytics/xp.py` (the rates it passes),
  Docs. **The weight stays 0 until the sweep says otherwise.**
* **Action Items:**
  - [ ] `team_xgc90()` + the delta, reusing ADR-188's shape and guards
  - [ ] Guard: invariance at weight 0 stays byte-identical; unknown club = no opinion, not 0
  - [ ] Sweep at GW6 on both populations; record the result **either way**
  - [ ] If it nulls: **close the question for the season** and adopt ADR-188's Option 3 — the rates as a lens
        on the transfer screen, which is where the owner's knowledge actually enters

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

### 💡 The lesson

> **A null is a statement about the instrument as much as about the world.**

ADR-188's method was right: pre-register, sweep, record the result either way, refuse to ship on a flat curve.
ADR-190's follow-up was right too: score a scoped term on the population it scopes to. Both were executed
carefully, and **both measured a quantity that could not have shown the effect if it existed** — a
binary-derived rate on four observations per club.

The owner had no access to either measurement and was right three times, because he was reading the thing the
statistic was a poor proxy for: *Coventry shipped five last week.*

⭐ **When a careful measurement and a knowledgeable human disagree repeatedly, check what the measurement is
made of before trusting it again.** Three nulls from the same instrument is one null.

---

### 🔗 References & Related Artifacts
- **The question, and the wrong instrument:** [ADR-188](./ADR-188-a-defender-plays-for-a-team.md)
- **The scoped-population method:** [ADR-190](./ADR-190-the-gw4-sitting.md) Option 3 · spike 192
- **The measurement:** `spikes/195-team-defence-xgc/`
- **The related report, same week:** [ADR-194](./ADR-194-a-start-bench-call-gets-a-margin.md) — the other half
  of *"start Thomas over Konsa"*
- **Found by:** the owner, three times, on the same two players


---

## 🔨 Built — 2026-09-17

**The swap is one function.** `_clean_sheet_rates` in `xp.py` now returns
`clean_sheet_prob(team_xgc90(...))` instead of `team_clean_sheet_rate(...)`. `clean_sheet_delta`,
`league_clean_sheet_rate`, the call site and **all five of ADR-188's mutation-tested guards are untouched** —
which was the point: the term's *shape* was never what was wrong, its *input* was.

### ⚠️ The proposal above had a units bug, and it would have shipped quietly

This ADR says *"swapping clean-sheet rate for xGC/90 delta is a change to one function's argument."* It is
not. `clean_sheet_delta` multiplies by `CLEAN_SHEET_POINTS`, and **that only yields points when the delta is
a probability**. A raw goals-per-90 difference would have produced "4 × goals" — a quantity in no unit at all,
with a plausible sign and magnitude to hide behind.

⭐⭐ **A SWAPPED INPUT HAS TO ARRIVE IN THE UNITS THE CONSUMER ALREADY ASSUMES** — and the assumption lived in
a `× 4` three lines away from the change, in a function this ADR explicitly promised not to touch.

Resolved with the standard Poisson form: goals conceded ~ Poisson(xGC), so `P(clean sheet) = e^-xGC`. It also
⭐ **fixes the sign for free**, which matters more than it sounds: for clean-sheet *rate* higher is better, for
xGC **lower** is better, and a raw swap would have **inverted the term** — pricing Coventry's defenders above
Arsenal's — while every existing guard stayed green, because they all test `team − league` and none of them
says which direction "good" points in.

⚠️ Poisson assumes independent chances, which shot quality violates. It is an approximation, and a good one
at the precision a gated term needs.

### 📊 What the live data says about the old instrument

This is the thesis, on the real cache, and it is starker than the ADR argued:

| | clean-sheet rate | xGC/90 |
|---|---|---|
| distinct values across 20 clubs | **5** | **20** |

Spearman between the two rankings is **0.243** — they agree on **6%** of the variance. And the collisions are
not marginal:

- **Arsenal and Hull share a rate of 0.75** — equal-best in the league — on xGC of **0.68** and **1.49**.
- **The `0.00` bucket holds six clubs**, spanning **BOU 1.32 (4th-best defence)** to **CRY 2.04 (the worst)**.

⭐⭐ **A TERM WHOSE INPUT PUTS THE FOURTH-BEST AND THE WORST DEFENCE IN THE LEAGUE IN THE SAME BUCKET CANNOT
CORRELATE WITH ANYTHING CONTINUOUS.** ADR-188's null was never evidence about football.

Resulting deltas at weight 1.0, for scale only: **ARS +1.07** to **CRY −0.44** points per match, a spread of
**1.51** against a per-player weekly sd of 3.51 (ADR-161).

### ⚠️ Two guards that passed while the mechanism was broken

Nine mutants, and **two survived the first sweep — both my fixtures, neither the code**:

1. **The benched-keeper guard was masked by the one-row-per-round guard.** With the benched keeper listed
   *second*, the round had already been claimed by the keeper who played, so his rows were dropped for a
   reason unrelated to being benched. Listed **first**, he claims the round with 0 minutes and the club falls
   below the floor. ⭐ *A fixture that only exercises the lucky ordering will confirm a broken mechanism* —
   third sighting this month, after ADR-189 and ADR-191 §1.
2. **Nothing tested a match in flight.** `not _played(r)` and `minutes <= 0` look redundant and are not: a
   live gameweek has **minutes but no scoreline** (the ADR-125 trap), and counting it would price half a match
   the club is losing as a full observation, moving the recommendation mid-fixture.

### ✅ Action items

- [x] `team_xgc90()` + the delta, reusing ADR-188's shape and guards
- [x] Guard: invariance at weight 0 stays byte-identical; unknown club = no opinion, not 0
- [x] ⚠️ **New guards driving the term at a non-zero weight** — the suite could not see this change at all
      otherwise: `decision_xp` does not even call the rate builder at weight 0, so every ADR-188 guard stayed
      green through a change to the input's units, source **and** sign. ⭐ *A dormant term is not covered, it
      is merely quiet.*
- [ ] **Sweep at GW6** on both populations; record the result either way
- [ ] If it nulls: **close the question for the season** and adopt ADR-188's Option 3

**`TEAM_XGC_MIN_MINUTES = 180`** is a **stated floor, not a measured one** (ADR-199's rule, declared rather
than hidden): two matches, so one freak afternoon cannot define a club. It cannot be measured yet — the
quantity it would be measured against is the thing being gated — and it binds only in the opening fortnight;
by GW6 every club is at ~540 minutes. All 20 clubs clear it today.
