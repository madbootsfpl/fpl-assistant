# Architectural Decision Record: Over/Under-performance (expected vs actual attacking points)

**Decision ID:** ADR-017
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (builds on ADR-015; the FPL-native path chosen in ADR-016)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

We store xG/xA (ADR-015) and FPL publishes actual goals/assists. Comparing the two reveals
**over/under-performance**: who's out-scoring their underlying numbers (finishing hot →
regression risk) vs who's unlucky (→ bounce-back). This is the **FPL-native** lens chosen
over soccerdata (ADR-016) — decision-relevant, no new dependency.

A planning probe measured it live: real signal (Semenyo +38, Brooks −25) — and it surfaced a
data-quality issue that shapes the design (below).

#### Decision Drivers
- **Decision-relevant, lightweight** — the path chosen in ADR-016 (FPL data only).
- **Statistically honest** — small samples are noise; the metric must guard against them.
- **Reuse the seams** — model `_to_float`, the generic migration, a thin view.

---

### 💡 Decisions

**1. The formula.** Attacking points, expected vs actual:

```
expected = xG · goal_pts[pos] + xA · 3
actual   = goals · goal_pts[pos] + assists · 3
over/under = actual − expected     (+ = over-performing, − = under-performing)
```

**2. Constants (FPL scoring rules).** `goal_pts` = GK/DEF **6**, MID **5**, FWD **4**; an
assist is **3**. A named constant, so the rules are explicit and adjustable.

**3. Minutes gate.** Rank only players with `minutes ≥ 900` (~10 matches). This is **part of
the metric**, not a filter bolted on: it removes small-sample noise *and* a real preseason
data glitch — Meslier (a GK) showed `goals_scored` 11 with `minutes` 0 and `total_points` 0
(fields reset inconsistently at season rollover), which without the gate read as *actual 66,
expected 0*. `MIN_MINUTES` is a named constant.

**4. Scope: attacking returns only.** goals + assists. Clean sheets, appearance, bonus, and
cards are **out** — so the number is "attacking over/under-performance", not total-points.
GK/DEF naturally sit ≈ 0 on attack (correct — they aren't attackers); a defender's real
value is clean sheets, which this lens does not measure. Stated plainly to avoid over-reading.

**5. View.** A new `overperf` view ranks by the diff and shows **both ends** (top over- and
under-performers), with the minutes threshold noted.

**6. Ingest.** `goals_scored`, `assists`, `minutes` via `Player.from_api` + the generic
storage migration (the ADR-015 pattern).

**Not in scope:** a squad `--objective` on over/under-performance (it's a *diagnostic* lens,
not an optimisation target); predicting next season (regression is a tendency, not a forecast).

---

### 🧪 Worked example (pressure-testing — run on real data)

`overperf` on live data (minutes ≥ 900, 267 players):

```
OVER (regression risk)          UNDER (bounce-back)
  Semenyo   MID  actual 103  exp 64.9  +38     Brooks   MID  actual 14  exp 39.2  −25
  Wilson    MID  actual  77  exp 43.7  +33     Struijk  DEF  actual  3  exp 20.6  −18
  B.Fernandes MID actual 117 exp 90.8  +26     Amad     MID  actual 25  exp 41.5  −16
```

And the guard: **Meslier is absent** — his 0 minutes fall below the gate, so the glitch
(actual 66 / expected 0) never appears. The metric *and* the minutes gate are confirmed
before any feature code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A genuinely useful new lens (regression / bounce-back) from data we already
  fetch — no new dependency, reusing the model/migration/view seams. It *compares* two
  metrics, a first for the app.
* **Negative / Trade-offs:** Attacking-only (no clean sheets/bonus), so it under-serves
  defenders; preseason values are last-season; regression is probabilistic, not certain.
  All stated, not hidden.
* **Risks & Mitigations:**
  - *Small samples / glitches* → minutes gate (a test covers a low-minutes exclusion).
  - *Over-reading the number* → the attacking-only caveat in the output + docs.

---

### 🛠 Implementation & Migration
* **Components Affected:** `Player` model (+3 fields), storage (migration + save +
  get_players), analytics (the over/under function), CLI (`overperf` view), Docs. **No new
  dependency.**
* **Action Items:**
  - [x] Record the design + worked example + the minutes-gate finding (US-050)
  - [ ] Ingest & store goals_scored / assists / minutes + migration (US-051)
  - [ ] The metric + `overperf` view (US-052)
  - [ ] (Backlog) a clean-sheet / defensive over-under (needs CS + xGC modelling)

---

### 🔄 Review & Reconsideration
* **Review Date:** Once the season starts and the numbers become live-form.
* **Triggers for Reconsideration:**
  - [ ] Want a *total-points* over/under (add clean sheets, appearance, bonus).
  - [ ] Want to weight recent form over a season total (needs per-gameweek data).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-050 (this), US-051/052
- **External Docs:** [ADR-015 (expected goals)](./ADR-015-expected-goals.md) · [ADR-016 (soccerdata — defer)](./ADR-016-soccerdata-evaluation.md) · [Sprint 016](../05_Sprints/Sprint16.md)
