# Architectural Decision Record: Team defence is xGC, not clean sheets

**Decision ID:** ADR-195
**Date:** 2026-09-16
**Status:** 📋 **Proposed** — gate before building. Reopens [ADR-188](./ADR-188-a-defender-plays-for-a-team.md)
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
