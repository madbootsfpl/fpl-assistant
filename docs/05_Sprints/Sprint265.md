# Sprint 265: Team defence is xGC, not clean sheets

**Dates:** 2026-09-17
**Status:** ✅ **ADR-195 built — 1832 → 1842 tests, ruff clean, 9 mutants all red. Weight still 0; sweeps at GW6.**

---

## Why this one, now

It was the only open item with a hard date. `GW1_RUNBOOK.md` pre-registers **GW6 as "the real sitting"**, and
ADR-195's own checklist said *"sweep at GW6"* — so if it wasn't built by then, that sitting would sweep the
instrument ADR-195 had already shown couldn't see the effect. The runbook allows **one sweep per checkpoint**:
*"re-running until it passes is the same mistake as choosing the criterion afterwards."* The slot would have
been spent.

GW6 completes **2026-10-12**. GW8 is the 25th.

---

## Built: change the input, keep everything else

`_clean_sheet_rates` now returns `clean_sheet_prob(team_xgc90(...))` instead of `team_clean_sheet_rate(...)`.
`clean_sheet_delta`, `league_clean_sheet_rate`, the call site, and **all five of ADR-188's mutation-tested
guards are untouched** — which was the point. The term's *shape* was never what was wrong.

---

## ⚠️ The ADR had a units bug, and it would have shipped quietly

ADR-195 says *"swapping clean-sheet rate for xGC/90 delta is a change to one function's argument."* It isn't.
`clean_sheet_delta` multiplies by `CLEAN_SHEET_POINTS`, and **that only yields points when the delta is a
probability.** A raw goals-per-90 difference gives "4 × goals" — a quantity in no unit at all, with a
plausible sign and magnitude to hide behind.

⭐⭐ **A swapped input has to arrive in the units the consumer already assumes** — and the assumption lived in
a `× 4` three lines away, inside the function the ADR explicitly promised not to touch.

Fixed with the standard Poisson form, `P(clean sheet) = e^-xGC`. It also ⭐ **fixes the sign for free**, which
matters more than it sounds: higher is better for a *rate*, **lower** is better for xGC. A raw swap would have
**inverted the term** — pricing Coventry's defenders above Arsenal's — with every existing guard still green,
because they all test `team − league` and none of them says which direction "good" points in.

---

## 📊 The thesis on live data, starker than the ADR argued

| | clean-sheet rate | xGC/90 |
|---|---|---|
| distinct values across 20 clubs | **5** | **20** |

Spearman between the two rankings: **0.243** — they agree on 6% of the variance.

- **Arsenal and Hull share a rate of 0.75**, equal-best in the league, on xGC of **0.68** and **1.49**.
- **The `0.00` bucket holds six clubs**, from **BOU 1.32 (4th-best defence)** to **CRY 2.04 (the worst)**.

⭐⭐ **A term whose input puts the fourth-best and the worst defence in the league in the same bucket cannot
correlate with anything continuous.** ADR-188's null was never evidence about football — and the owner, who
said so twice, was right twice.

Deltas at weight 1.0, for scale only: ARS **+1.07** to CRY **−0.44** points per match, a spread of **1.51**
against a per-player weekly sd of 3.51.

---

## ⚠️⚠️ The suite could not see this change at all

`CLEAN_SHEET_WEIGHT` is 0, and `decision_xp` doesn't even call the rate builder at weight 0. So the input's
**units, source and sign** all changed and **every one of ADR-188's five guards stayed green**, along with the
other 1,827 tests.

⭐ **A dormant term is not covered. It is merely quiet.** Ten new guards drive it at a non-zero weight.

---

## The two mutants that survived, both fixtures

1. **The benched-keeper guard was masked by the one-row-per-round guard.** Listed *second*, the benched keeper's
   rows were dropped because the round had already been claimed — a reason with nothing to do with being
   benched. Listed **first**, he claims the round with 0 minutes and the club falls below the floor.
   ⭐ *A fixture that only exercises the lucky ordering will confirm a broken mechanism* — third sighting this
   month, after ADR-189 and ADR-191 §1. ⚠️ **Two guards covering one another is the shape that hides it.**

2. **Nothing tested a match in flight.** `not _played(r)` and `minutes <= 0` look redundant and are not: a live
   gameweek has **minutes but no scoreline** (the ADR-125 trap), and counting it would price half a match the
   club is losing as a full observation — moving the recommendation mid-fixture.

---

## 💡 The lesson

⭐⭐ **An instrument with five values cannot measure a continuous thing, and its null will look exactly like a
real one.** Three months of this question — ADR-188, ADR-190's Option 3, ADR-192 — rested on a statistic that
put six clubs in one bucket. The fix was never a better model or more gameweeks; it was a column that could
tell Bournemouth from Crystal Palace.

---

## Definition of Done

- ✅ **Tests** — 10 new (`tests/test_team_xgc.py`), 1842 passed, ruff clean; 9 mutants, all red after two
  fixture repairs
- ✅ **Manual smoke** — all 20 clubs scored off the live cache, ranked and cross-checked against the old
  instrument; every club clears the 180-minute floor
- ✅ **Docs** — ADR-195 updated with the build, index row, `config.py`, `GW1_RUNBOOK.md` §B0, PROJECT_STATUS,
  this sprint doc

**Next:** the GW6 sitting (on or after **2026-10-12**) sweeps it. Prediction recorded first and unchanged:
small positive ≈0.05–0.20, quite possibly zero, **a large gain is a warning not a win**. If it nulls, the
question closes for the season.
