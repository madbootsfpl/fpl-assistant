# Architectural Decision Record: The minutes baseline, and three answers to one question

**Decision ID:** ADR-202
**Date:** 2026-09-16
**Status:** ✅ **Accepted — measurement complete. ML roadmap Phase 0b. No code changed; the deliverable is a number.**
**1823 tests (unchanged), ruff clean.**
**Superseded By / Replaces:** Sets the benchmark for ML Phase 1. **Declines
[ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md)'s demotion for now** and gives it a re-measure date.
Uses [ADR-101](./ADR-101-calibration-methodology.md)'s harness unchanged and §B0's pre-registered bar.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Phase 0b of the ML roadmap: measure the model we already have, so that anything learned later has a number to
beat. ⭐ **A model with no baseline is not an improvement, it is a replacement.**

It had a second job. ADR-192 found 124 players modelled as **nailed 90-minute starters on no evidence**, set
the direction, and deliberately did not choose the constant. This was where the constant was to be measured.

Data: `data/fpl.db`, 2026/27, rounds 1–4, **659 players / 2,547 player-gameweeks**. Walk-forward throughout —
round N predicted from rounds < N only. Deterministic; the headline table was re-run and is byte-identical.

---

### 📊 Part 1 — how well does the app predict minutes?

Owned by ≥1% of managers (n = 762 player-gameweeks), because ⭐ *a whole-board number is dominated by players
nobody would pick* (ADR-200):

| forecaster | MAE (mins) | bias | start/bench call right |
|---|---|---|---|
| **xMins v0 — the app** | **24.0** | +3.4 | **70.1%** |
| always 90 (= `--no-xmins`) | 31.2 | +31.2 | 65.0% |
| **last GW's minutes** | **20.5** | +12.3 | **77.3%** |
| mean minutes so far | 21.7 | +11.8 | 75.1% |

⭐⭐ **THE APP'S MINUTES MODEL IS BEATEN BY "SAME AS LAST WEEK"** — on error and on the start/bench call,
in **every round where a comparison is possible** (GW2 14.1 vs 16.4, GW3 11.2 vs 16.5, GW4 29.6 vs 31.5).
Not one round; three of three.

And it holds at every ownership cut. Above **3%** even the *constant 90* calls starts better than the model
(76.7% vs 74.0%); above 5% it wins on error too (18.0 vs 21.4).

⚠️ **The model's number here is flattered, not penalised.** `chance_factor` reads **today's** injury status and
applies it retrospectively to round 1 — the one leak in this measurement, and it cannot be closed: FPL serves
availability as a *now* field and we store no history of it. **195 of 659** players carry a non-available
status today. Stripped of it, the model is **25.9 MAE / +19.4 bias / 69.9%**. It loses by more, not less.

**Why it loses** — and the diagnosis needed correcting once. The first cut compared the rounds where the
in-season term fired (MAE 14.2) against the rounds where it fell back to last season (25.8), and GW4 reversed
the pattern. ⚠️ **That comparison is between two populations, not two methods** — the fall-back group is
exactly the group with erratic minutes, so it is harder to predict for anyone. Re-run as an A/B on the *same*
players:

| | GW2 | GW3 | GW4 | all |
|---|---|---|---|---|
| this season's share (what it said) | 14.2 | 13.3 | 33.5 | **20.0** |
| last season's share (the fallback) | 30.2 | 27.9 | 38.7 | **32.1** |
| last GW's minutes | 11.8 | 11.8 | 35.7 | **19.4** |

⭐ *A comparison between two groups is a fact about the groups until you run both methods on one of them.*
The in-season term is **good** (20.0, level with persistence); the **historical fallback is the weak part**
(32.1), and the model reaches for it for 35–52 of ~190 owned players every round, and for all of them at GW1.

---

### 🎯 Part 2 — the question that mattered, and the three different answers it gave

Stopping there would have produced the recommendation *"replace the model with last week's minutes."*
⚠️ **MAE on minutes is not the question the app asks.** A constant forecaster has **zero variance**: it can
win MAE and be useless for a decision, because it cannot rank two players at all. ⭐ *Calibration is not what
a recommendation needs.* So the weight was scored on what the app actually produces — the **points ranking**.

| weight | ρ (mean GW) | MAE | hit@20 |
|---|---|---|---|
| none (`--no-xmins`) | 0.488 | 1.84 | 0.16 |
| **xMins v0 (today)** | **0.605** | 1.23 | 0.17 |
| **ORACLE** — actual minutes played | **0.811** | 0.91 | **0.28** |

⭐⭐ **A TERM CAN BE A BAD PREDICTOR OF ITS OWN QUANTITY AND STILL BE A GOOD FEATURE.** The weight is worth
**+0.117 ρ (2.9 SE)** against not having it, in all four rounds. Acting on the minutes table alone would have
thrown that away — the largest single effect measured this season, against form's +0.005 and clean-sheet's
−0.007 (ADR-190).

#### ⚠️⚠️ And then the same question gave a third answer

Three measurements of *"is a better minutes model worth building?"*, each executed correctly:

| # | instrument | verdict |
|---|---|---|
| 1 | swap in "last GW's minutes" as the weight | **+0.018 ρ (0.4 SE) — no headroom** |
| 2 | oracle: actual minutes, scored on total points | **+0.206 ρ (5.1 SE) — large headroom** |
| 3 | oracle, scored net of appearance points | **+0.061 ρ (1.5 SE) — real but modest** |

**#1 was a false negative.** The substitute is 15% more accurate on owned players but a **dead heat
board-wide** (24.6 vs 24.5) — and the ranking is board-wide. ⭐ *A substitute that is not actually better on
the population being scored cannot test whether better helps.* Exactly [ADR-195](./ADR-195-team-defence-is-xgc-not-clean-sheets.md)'s
lesson: **a null is a statement about the instrument as much as about the world.**

**#2 is inflated.** FPL pays 1 appearance point for 1–59 minutes and 2 from 60, so for every player who
returns nothing else — a large share of the board — knowing his minutes *determines* his score.
⭐⭐ **AN ORACLE OVER AN INPUT THAT IS ALSO A COMPONENT OF THE OUTPUT IS PARTLY GRADING ITS OWN ARITHMETIC.**

**#3 is the information content.** Net of appearance points, having the weight is worth +0.047 (1.2 SE) and
perfect minutes from here **+0.061 (1.5 SE)**.

⭐⭐⭐ **THE SAME QUESTION, MEASURED THREE WAYS, ANSWERED "NOTHING", "HUGE" AND "MARGINAL".** Each run was
careful; each measured a subtly different thing. ⭐ *When a measurement will decide whether to build something,
measure it more than one way before you believe the first one.*

---

### 🎯 Decision

**The baseline, for the GW8 review and for anything learned later to beat:**

| quantity | value |
|---|---|
| minutes MAE, owned ≥1% | **24.0** (25.9 without the availability leak) |
| start/bench call, owned ≥1% | **70.1%** |
| minutes MAE, whole board | **24.5** |
| points ranking ρ (mean GW) | **0.605** |
| hit@20 | **0.17** |
| 1 SE | **0.040** |

**Phase 1 (a learned minutes model) stays on the roadmap, and its ceiling is now known rather than assumed.**
Perfect minutes is worth **+0.206 ρ** on what the app ranks (5.1 SE), of which **+0.061** (1.5 SE) is
information rather than appearance-point arithmetic. Both are **ceilings an oracle reaches and no model can** —
a real forecaster cannot know a player was subbed at 55 or sent off.

⏳ **Gate before Phase 1, and it is cheap:** build a minutes forecaster that is better **board-wide**, not just
on owned players, and re-run measurement #1. That is the test #1 was meant to be. If a genuinely better
forecaster still buys under +1 SE, the ceiling is unreachable in practice and Phase 1 should be declined —
and we will have found that out without training anything.

---

### 🅾️ ADR-192's constant: NOT SET, and that is the finding

The direction is confirmed and the error is large. On the **130** players with no past seasons (453
player-gameweeks) the live model runs **+39.1 minutes optimistic** and calls start/bench at **49.2% — a coin
flip.** ADR-192 was right about the mechanism.

**And correcting it makes the ranking worse.** Sweeping the unknown case from 1.0 down to 0.4:

| value | ρ whole board | ρ on the cold population | MAE cold |
|---|---|---|---|
| **1.00 (today)** | **0.605** | **0.710** | 0.85 |
| 0.80 | 0.604 | 0.703 | 0.84 |
| 0.60 | 0.601 | 0.697 | 0.83 |
| 0.40 | 0.598 | 0.686 | 0.85 |

Monotonically declining on the whole board **and on the sub-population the term is scoped to** — so this is
not ADR-190's blind spot. ⚠️ **And the term is live**, not unreachable: ρ(ranking at 1.0, ranking at 0.4) is
**0.984** on the cold population, nowhere near the 0.9999 that marks an unmeasurable term.

⭐⭐ **THE ERROR IS REAL AND CORRECTING IT DOES NOT HELP** — because the minutes error is largest on players
who never appear, and those players are already ranked at the bottom for other reasons. ⭐ *An input can be
measurably wrong in a place where the output does not care.*

**The one thing that does move**, reported as diagnosis and **not as a third criterion** — whole-board hit@20
is flat at 0.17 across the entire sweep, so the §B0 verdict was already in (⭐ *reaching for a new metric after
two have declined is how you choose the answer*, ADR-190). Across 4 gameweeks × top-20 = **80 recommendation
slots**, a player with no history appears **once**, at value 1.0, and **he scored 0**. At 0.8 and below he does
not appear, and the mean return of a top-20 slot rises 4.11 → 4.26.

That is ADR-192's complaint, reproduced exactly — **and it is n = 1.** ⭐ *One event is not a rate*
(ADR-183). Setting a constant on it would breach [ADR-199](./ADR-199-a-threshold-needs-a-provenance.md)'s own
rule two weeks after writing it.

📅 **Re-measure at the GW8 review (on or after 2026-10-26)**, where 8 gameweeks give ~160 slots. ADR-192 stays
**Proposed**, with the direction confirmed, the size measured, and the number still unchosen.

---

### 📊 Consequences

**Good:** the benchmark exists, with its population and its leak stated. Phase 1 has a measured ceiling and a
cheap gate in front of it. ADR-192 has a size, a date and a reason it did not ship.

**Costs / limits:**
- ⚠️ **Four gameweeks, one season.** GW4 is anomalous for every forecaster (MAE 29.6–48.9 against 11.2–25.5 in
  GW3), and one round in four moves the aggregate a long way. This is a first reading, not a settled number.
- ⚠️ **The availability leak cannot be closed retrospectively** — availability is a *now* field. Storing a
  snapshot of `status`/`chance` each refresh would fix it for future baselines and is worth doing before the
  GW8 review; it is not done here.
- `selected_by` is today's ownership used to define a historical population. Acceptable for a population cut,
  wrong for anything that reads the number itself.

---

### 🔗 Links

- [ADR-101](./ADR-101-calibration-methodology.md) — the walk-forward harness, used unchanged
- [ADR-038](./ADR-038-expected-minutes-v0.md) · [ADR-173](./ADR-173-minutes-you-have-actually-played.md) — the model measured here
- [ADR-192](./ADR-192-no-opinion-is-not-full-confidence.md) — the constant this was to set, and did not
- [ADR-195](./ADR-195-team-defence-is-xgc-not-clean-sheets.md) — the same lesson about instruments, from the other direction
- `spikes/202-minutes-baseline/` — `baseline.py` · `xmins_on_points.py` · `better_minutes_on_points.py` · `oracle_bound.py` · `oracle_net_of_appearance.py` · `cold_start_sweep.py` · `cold_start_top.py`
