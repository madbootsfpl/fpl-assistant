# Architectural Decision Record: Fixture concentration — the honest version of "player clashes"

**Decision ID:** ADR-145
**Date:** 2026-08-26
**Status:** ✅ **Accepted — built** (Sprint 199, 2026-08-26). **1398 → 1407 tests, ruff clean.**
The Roadmap's *"player clashes = point cannibalisation"* framing is **rejected on evidence**; the real,
actionable quantity underneath it is built.
**Superseded By / Replaces:** Sits under the forward planner (ADR-131), answering the same *"what's coming?"*
question one level down. No `decision_xp` change.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 The premise did not survive being checked

The Roadmap line: *"**Player clashes** — your own players meeting = point cannibalisation."* The idea is
intuitive: you own an attacker and a defender, they face each other, a goal kills the clean sheet.

**Two measurements on live data killed that framing.**

**1. Clashes are universal, so a list of them is wallpaper.** Across **300 random legal squads** over five
gameweeks:

| filter | clashes per squad | squads affected |
|---|---:|---:|
| any two owned players meeting | **26.3** | **100%** |
| starting XI only, defensive-vs-attacker (the only combination that actually conflicts) | **7.4** | **100%** |

A warning that fires for every manager every week is not information. And the naive version would have been
worse still — 27% of raw clashes are attacker-vs-attacker, where there is no conflict at all: both can score.

**2. A clash costs no expected points — which is the part the premise gets wrong.** `decision_xp` already
prices each player's own fixture (ADR-006/032). A defender facing a strong attack is already discounted; an
attacker facing a strong defence is already discounted. **Summing them does not double-count anything.**

What a clash changes is the **joint** distribution, not either marginal: the two outcomes become
anti-correlated. Your expected score is unchanged; your **variance falls**.

And lower variance is not automatically bad. Chasing a rival wants variance; protecting a lead wants less of
it — the same logic as league effective ownership (ADR-141). *"Cannibalisation"* is the wrong word for
something that is sometimes exactly what you want.

---

### ✅ Decision

**Measure concentration instead: how much of one gameweek's XI projection rides on a single match.** On live
data that distribution is:

| median | p75 | p90 | max |
|---:|---:|---:|---:|
| **29%** | 34% | 40% | 64% |

This is a fact about a squad a manager can act on, and it **subsumes** clashes: a clash is simply a
concentration whose players sit on opposite sides of the same fixture.

**1. Thresholds are the measured quartiles.** `CONCENTRATED = 0.35` (≈ p75), `HEAVY = 0.45` (above p90) — the
same calibrate-against-your-own-spread idiom as ADR-144's captain margin and ADR-138's price peers. The naive
feature fired 100% of the time; this speaks for about a quarter of squad-gameweeks, which is what makes it
worth reading.

**2. Measured on the starting XI, not the 15.** A benched player scores nothing, so counting them would dilute
the share with points that were never at risk.

**3. The clash survives as a _qualifier_, not a warning.** When the concentrated match has players on both
sides, the note adds that their returns partly cancel — *"the week is even less spread than that."* That is
the Roadmap's idea stated as what it actually is.

**4. It names the players.** A bare percentage is not actionable; the share says there is something to look
at, the names say what to do about it — the same rule ADR-131 applies to its hard-fixture counts.

Live output, both saved squads over six gameweeks: **RoboTS produced no note at all**, and TS produced exactly
one —

> 🎯 43% of your GW6 rides on LIV v MCI (4 players: Guéhi, Szoboszlai, Virgil, Haaland). You have players on
> **both** sides, so their returns partly cancel — the week is even less spread than that.

### ⚠️ Risks

- **Concentration is not automatically bad, and the copy must not imply it is.** It is a *shape* — narrow can
  be right when you are chasing. The note describes; it does not instruct.
- **Thresholds are this season's and thin.** One gameweek of projections, same caveat as ADR-144. Named
  constants beside the measurement that produced them, so re-deriving at GW4-6 is quick.
- **Doubles will distort the share** once they exist — a team playing twice contributes to two matches. Worth
  re-checking when the first DGW lands (ADR-129 handles the data side).

### 🧪 Definition of Done

1. **Tests: +9.** The match carrying most of a gameweek; opposed-vs-same-side (the distinction the naive
   framing misses); the note appearing only above p75, with the distribution in the docstring so the numbers
   explain themselves; heavy reading more strongly than concentrated; the note naming players; a zero-xP
   gameweek skipped rather than divided by; empty inputs safe; plus a page test that any note which appears
   names a gameweek, a match and the players.
2. **Manual smoke** — both saved squads, six gameweeks, through the real Health view.
3. **Docs** — this ADR, the Roadmap entry, PROJECT_STATUS, a sprint retro.
