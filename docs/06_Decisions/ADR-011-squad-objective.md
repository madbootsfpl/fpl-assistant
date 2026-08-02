# Architectural Decision Record: Squad Objective Toggle

**Decision ID:** ADR-011
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-008)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The squad optimiser (ADR-008) hard-codes one objective: maximise last-season
`total_points`. But the project has built other player metrics — value
(points-per-£m) and Expected Points (xP). This sprint lets the optimiser maximise the
metric the user chooses, connecting the analytics to the decision engine. A planning
check confirmed the inputs are present (no new data).

#### Decision Drivers
- **Reuse** — the tested optimiser and `player_xp`, not new machinery.
- **Keep the core generic** — the optimiser shouldn't know what a score *means*.
- **Honest scope** — only player-level metrics can be a squad objective.

---

### 💡 Decisions

**1. Objectives (player-level).**
- `points` — `total_points` (default).
- `value` — points ÷ price (`points_per_million`); price 0 → score 0.
- `xp` — Expected Points via `player_xp` (v0: next single gameweek, `fpl` difficulty).

**Not an objective:** `elo` — it's *team* strength (used by the FDR), can't be summed
across a squad. It stays in `fdr --type elo`.

**2. Generic optimiser.** `select_squad(..., scores=None)` maximises
`Σ scores[p] · pick[p]`. `scores` defaults to `total_points`, so the existing result
is unchanged. The objective logic lives *outside* the optimiser.

**3. `objective_scores(players, objective, upcoming=None)`** computes the per-player
score for the chosen objective; the `xp` objective reuses `player_xp` (so it needs the
upcoming fixtures).

**4. Display.** The output states the objective (e.g. "objective: value").

---

### 🧪 Worked example (pressure-testing the mechanism)

Two forward slots; the objectives disagree:

| FWD | Points | Price | Value (pts/£m) |
|---|---|---|---|
| A | 10 | £10m | 1.0 |
| B | 8 | £4m | 2.0 |

- `--objective points` → picks **A** (10 > 8).
- `--objective value` → picks **B** (2.0 > 1.0).

Different squads from the same players — the toggle changes the pick. And the
regression case: with `scores=None` the optimiser uses `total_points`, so
`--objective points` reproduces today's XI exactly.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** The value/xP metrics become what the optimiser optimises ("best squad
  for *this* goal"); the optimiser stays a generic "maximise these scores".
* **Negative / Trade-offs:** The `xp` objective couples squad selection to the fixture
  data (needs upcoming fixtures); v0 uses fixed xp settings.
* **Risks & Mitigations:**
  - *Value divide-by-zero* → score 0 (a test covers it).
  - *xp with no fixtures* → xp is 0 (degenerate, but no crash).

---

### 🛠 Implementation & Migration
* **Components Affected:** optimiser (`select_squad` + `objective_scores`), CLI (`squad`), Docs
* **Action Items:**
  - [x] Record the design + worked example (US-034)
  - [ ] Generic optimiser score + `objective_scores` (points/value/xp) (US-035)
  - [ ] `squad --objective …` + display (US-036)
  - [ ] (Backlog) `--type`/`--next` for the xp objective; weighted/multi-objective

---

### 🔄 Review & Reconsideration
* **Review Date:** If more objectives are wanted
* **Triggers for Reconsideration:**
  - [ ] Want the xp objective to be fixture-source/horizon aware
  - [ ] Want a blended objective (points + value)

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-034 (this), US-035/036
- **External Docs:** [ADR-008 (squad selector)](./ADR-008-squad-selector.md) · [ADR-006 (xP)](./ADR-006-expected-points-v0.md) · [Sprint 010](../05_Sprints/Sprint10.md)
