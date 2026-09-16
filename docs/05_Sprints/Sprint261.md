# Sprint 261: Three answers to one question

**Dates:** 2026-09-16
**Status:** ✅ Complete — **ADR-202, ML roadmap Phase 0b. No code changed; the deliverable is a number.**
**1823 tests (unchanged), ruff clean.**

---

## The job

Measure the minutes model we already have, so anything learned later has something to beat, and set ADR-192's
cold-start constant. ⭐ *A model with no baseline is not an improvement, it is a replacement.*

Rounds 1–4 of 2026/27, 659 players, 2,547 player-gameweeks, walk-forward throughout. Deterministic — the
headline table was re-run and came back identical.

---

## The baseline

| quantity | value |
|---|---|
| minutes MAE, owned ≥1% | **24.0** (25.9 without the availability leak) |
| start/bench call | **70.1%** |
| points ranking ρ | **0.605** · hit@20 **0.17** · 1 SE **0.040** |

⭐⭐ **The app's minutes model is beaten by "same as last week"** (20.5 MAE, 77.3%) — in every round where a
comparison is possible, at every ownership cut, and above 3% ownership the *constant 90* calls starts better.

⚠️ Its number is **flattered, not penalised**: `chance_factor` reads today's injury news and applies it
retrospectively (195 of 659 players carry a flag). Stripped of it, the model is worse, not better.

**The weak part is the historical fallback.** The first diagnosis compared rounds where the in-season term
fired against rounds where it fell back, and GW4 reversed the pattern — ⚠️ **but that compares two
populations, not two methods**: the fallback group *is* the erratic-minutes group. Re-run as an A/B on the
same players, this season's share is **20.0** and last season's is **32.1**, in all three rounds.
⭐ *A comparison between two groups is a fact about the groups until you run both methods on one of them.*

---

## ⭐⭐ Where it would have gone wrong

Acting on that table means *"replace the model with last week's minutes"*. Scored on the **points ranking**
the app actually produces:

| weight | ρ | MAE | hit@20 |
|---|---|---|---|
| none (`--no-xmins`) | 0.488 | 1.84 | 0.16 |
| xMins v0 (today) | **0.605** | 1.23 | 0.17 |
| oracle (actual minutes) | 0.811 | 0.91 | 0.28 |

The weight is worth **+0.117 ρ — 2.9 SE**, in all four rounds. The largest single effect measured this season.

⭐⭐ **A TERM CAN BE A BAD PREDICTOR OF ITS OWN QUANTITY AND STILL BE A GOOD FEATURE.** MAE on minutes is not
the question the app asks: a constant forecaster has zero variance, so it can win MAE and be unable to rank
two players at all.

---

## ⚠️⚠️ And then the same question gave a third answer

*"Is a better minutes model worth building?"* — three instruments, each executed correctly:

| instrument | verdict |
|---|---|
| swap in a better forecaster | +0.018 ρ (0.4 SE) — **nothing** |
| oracle on actual minutes | +0.206 ρ (5.1 SE) — **huge** |
| oracle net of appearance points | +0.061 ρ (1.5 SE) — **marginal** |

**The first was a false negative.** The substitute is 15% better on *owned* players and a dead heat
board-wide — and the ranking is board-wide. ⭐ *A substitute that is not better on the population being scored
cannot test whether better helps.* ADR-195's lesson: **a null is a statement about the instrument as much as
about the world.**

**The second is inflated.** FPL pays 1 appearance point for 1–59 minutes and 2 from 60, so for every player
who returns nothing else, knowing minutes *determines* the score. ⭐⭐ **AN ORACLE OVER AN INPUT THAT IS ALSO
A COMPONENT OF THE OUTPUT IS PARTLY GRADING ITS OWN ARITHMETIC.**

⭐⭐⭐ **THE SAME QUESTION, MEASURED THREE WAYS, ANSWERED "NOTHING", "HUGE" AND "MARGINAL".**

---

## 🅾️ ADR-192's constant: not set, and that is the finding

Direction confirmed and large — on the 130 players with no past seasons the model runs **+39.1 minutes
optimistic** and calls start/bench at **49.2%, a coin flip**. And sweeping the unknown case from 1.0 to 0.4
declines ρ **monotonically on the whole board and on the cold population itself** (0.710 → 0.686), with the
term **live** (self-ρ 0.984, not ADR-190's unreachable 0.9999).

⭐⭐ **THE ERROR IS REAL AND CORRECTING IT DOES NOT HELP** — the minutes error is largest on players who never
appear, and they already rank at the bottom for other reasons.

The owner's actual complaint *does* reproduce: across 80 top-20 recommendation slots, a player with no history
appears **once**, at 1.0, and **scored 0**; at 0.8 he does not, and the mean top-20 return rises 4.11 → 4.26.
**But n = 1.** ⭐ *One event is not a rate.* Setting a constant on it would breach ADR-199's rule two weeks
after writing it. 📅 Re-measure at the GW8 review.

---

## 💡 The lesson

⭐ **When a measurement will decide whether to build something, measure it more than one way before you
believe the first one.** Every reading here was careful. The first said replace the model; the second said the
model is worth 2.9 SE; the third said a better one is worth at most 1.5 SE of real information. Only the last
of those is a fact you could act on, and it was three instruments deep.

---

## Definition of Done

- ✅ **Tests** — no production code changed, so no new guards; the deliverable is a number. The measurement is
  re-runnable and was **run twice, identical**. Suite unchanged at **1823 passed**, ruff clean.
- ✅ **Manual smoke** — all seven spikes run end to end against the live `data/fpl.db`
- ✅ **Docs** — ADR-202 + index row, Roadmap ML track (0b done, Phase 1 re-gated, availability snapshot added),
  PROJECT_STATUS, this sprint doc

**Next:** the Phase 1 gate — a minutes forecaster that is better *board-wide* — and a `status`/`chance`
snapshot per refresh, so the GW8 baseline has no asterisk.
