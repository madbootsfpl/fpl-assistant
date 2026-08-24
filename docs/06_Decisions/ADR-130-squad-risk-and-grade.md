# Architectural Decision Record: A squad triage view and a squad-level grade

**Decision ID:** ADR-130
**Date:** 2026-08-24
**Status:** ✅ **Accepted — owner-approved, built** (Sprint 182). Prototyped on the live squad; the design
faults called out below were found in that prototype, not reasoned about.
**Superseded By / Replaces:** Extends ADR-038 (xMins), ADR-118 (Player DNA) and ADR-119 (Team DNA) — reusing
all three rather than adding new analytics.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Two features carried on the roadmap from the fplanalyser review, marked ⭐ *data already exists*:

- **Squad Risk Monitor** — one row per owned player, sorted by **how much attention he needs**, not how good
  he is. A driver (Minutes / Fixtures), a "% chance he doesn't reach 60", an attention rating.
- **Squad-grade DNA** — the owned 15 as **one graded picture**: overall grade, Attack / Defence / DefCon /
  Fixtures bars, a verdict headline, a grounded edge line.

They belong together: both aggregate the same 15 players and would share the same plumbing. My Squad ▸ Health
currently shows a player table and a text analysis — it answers *"how good is my squad?"* but not *"what should
I be worried about this week?"*, which is the question a manager actually opens the app with.

---

### ✅ Proposed Decision

**A new pure `analytics/squad_risk.py`**, feeding two cards in My Squad ▸ Health. No new data, no
`decision_xp` change.

#### 1. "% chance he doesn't reach 60" — grounded, never invented

60 minutes is the FPL appearance-points threshold, so it is the honest thing to measure. There is no
probability model in this project and this ADR does not add one; the number comes from what actually happened:

- **Empirically**, once there are enough played gameweeks: the share of his team's gameweeks in which he played
  under 60. This is now possible only because ADR-128/129 store per-gameweek minutes correctly.
- **Otherwise from last season's `starts`** — `starts / 38` as the base rate for reaching 60. Verified sound on
  the live data: a start almost always goes the distance (87-92 minutes per start for regulars), so starting is
  a good proxy for clearing the threshold.
- **Scaled by `chance_factor`** (ADR-038) so an injury flag pulls it down.

Prototyped on a real squad, and it separates people correctly:

```
Raya 3%   Semenyo 3%   Rice 8%   Haaland 11%   Gabriel 21%   Saka 34%   Ødegaard 58%
```

**Unknown must read as unknown.** The prototype scored M.Sangaré and Emersonn at **100%** — not because they
are certain to be substituted but because they are new to the league and have no basis at all. That is *no
data* rendered as *maximum risk*, the same failure this project has now corrected five times. They return
**None** and display as "—", with the card saying it cannot assess them yet.

#### 2. The attention rating and its driver

Two risks per player, the larger naming the **driver**:

- **Minutes** — the figure above.
- **Fixtures** — the difficulty of the run ahead.

**Fixture risk must be relative.** The prototype used `(fdr − 2) / 3`, which returns ~0.40 at the
league-typical 3.2 — so "Fixtures" won as the driver for almost every player while telling you nothing. It will
instead be the team's FDR **percentile across the league** (reusing `analytics.ranking.percentile_rank`,
inverted since lower is easier), so it only becomes the driver when a run is genuinely hard *compared with
everyone else's*.

Availability is not a third risk — a flagged player is already pulled down through `chance_factor`, and the ⛔
warning (US-421) covers the hard cases.

#### 3. Squad-grade DNA

**Reuse the Player DNA engine rather than invent squad percentiles.** Each axis is the **mean percentile of the
owned outfield players** on the matching Player-DNA axis, which needs no new pool and no new maths:

| bar | from |
|---|---|
| Attack | mean of Goal Threat + Creativity |
| Defence | mean Clean-Sheet Potl of the owned clubs (Team DNA) |
| DefCon | mean DefCon percentile |
| Fixtures | mean Fixture Strength of the owned clubs (Team DNA) |

The **grade** reuses `team_dna._grade`'s letter bands so a squad grade and a team grade mean the same thing on
the same scale. The **edge line** is grounded in a count, not a vibe — e.g. *"3 penalty takers — a deliberate
edge"*, *"5 players from two clubs — a rotation risk"*.

---

### 🔀 Alternatives Considered

- **Model minutes probabilistically** (the Phase 5 xMins successor). Rejected here: it needs in-season minutes
  to train and a real ML effort. This ADR deliberately ships the empirical version that the newly-correct
  per-gameweek data makes possible, and leaves the model to its own phase.
- **Rank a squad against other squads.** Rejected: we hold no other squads, and inventing a synthetic
  distribution would be a percentile with nothing behind it.
- **Fold both into the existing Health text analysis.** Rejected: the whole point of a triage view is that it
  is *sorted by what needs attention*, which prose cannot do.
- **A separate top-level tab.** Rejected: both are about the owned 15, which is what Health is for. No new tab
  (consistent with ADR-118/119).

---

### 🧭 Consequences

**Positive** — answers the question a manager opens the app with; reuses three existing engines rather than
adding analytics; the minutes figure is empirical and improves week by week rather than being a fixed guess;
the two features share one module and one data pass.

**Negative / risks (mitigations)** — `starts / 38` under-rates a January signing or a player returning from a
long injury, through no fault of theirs (*mitigation:* it is a base rate, superseded by the empirical figure as
soon as gameweeks accrue; the card says which basis it used); a mean-of-percentiles squad grade is a coarse
measure (*mitigation:* it is honest about being an average, and it is on the same letter scale as Team DNA so
it is at least comparable); an early-season squad of unknowns shows several "—" rows (*mitigation:* correct —
and far better than sorting a manager's attention by a number we made up).

---

### 🧾 Status & follow-ups

- **Accepted and built (Sprint 182).** `analytics/squad_risk.py` (pure) + `web_streamlit/squad_risk_card.py`,
  both wired into My Squad ▸ Health. `team_dna.grade_letter` extracted so a squad grade and a team grade cannot
  drift. 14 new tests. 1210 → **1224**, ruff clean.
- **A third design fault, found in the same way.** The first prototype scored **eight players an identical
  0.79** and named "Fixtures" the driver for every one of them — because it took `max(minutes_risk,
  fixture_risk)`, and those are not the same kind of number. `minutes_risk` is a **probability**;
  `fixture_risk` is a **percentile**. An ordinary-but-above-median run swamped every player-level signal and
  the list sorted by club instead of by who needed attention. They are now **weighted** — `0.7 × minutes +
  0.3 × fixtures` — because the two failures differ in kind: a player who does not play scores nothing at all,
  while a hard fixture only shortens the odds on a return. The triage now reads as one:
  `Palmer 0.70 (Minutes) · Ødegaard 0.64 (Minutes) · … · Haaland 0.19 · Semenyo 0.14`.
- **One substitution from the plan.** The fourth bar is **Output**, not DefCon: Player DNA has an `FPL Output`
  axis and no DefCon one, so Output is the honest reuse and a more informative bar than a fifth defensive
  measure alongside Defence.
- **Not this ADR:** the **Forward GW planner** ("your problem week is GW6") — a bigger build that extends the
  per-GW xP toggle into a multi-gameweek forward view, and the natural next step once this exists.
