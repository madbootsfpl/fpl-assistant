# Sprint 007: Optimal Squad Selector

**Dates:** TBC
**Status:** Planned
**Capacity:** ~3 working sessions
**Carried Over:** None (Sprint 006 closed clean)

---

### 🔎 Data verified at planning (per the Sprint 004 lesson)

Checked live `bootstrap-static`: `total_points`, `now_cost` (price), `element_type`
(position) and `team` are **564/564 populated** — everything the selector needs. Still
blocked (preseason): `form` (0/564) and attack/defence strengths (0/20), so richer xP
and the Attack/Defence FDR split remain deferred. This sprint (Tony's Sprint 006 idea)
sidesteps those blockers entirely.

---

### 🧭 Architecturally, what's new — the first *optimisation*

Every feature so far *ranked* or *described* players. The squad selector **chooses a
set under hard constraints** — the first time the app makes a *decision*, not just a
table. That's Roadmap Phase 5 (Optimisation), reached early via Tony's idea.

It also introduces the project's **first external dependency beyond `requests`**:
**PuLP** (an integer-programming solver). It's contained in a new optimiser module —
the layered design keeps the dependency out of everything else.

```
maximise   Σ total_points[p] · pick[p]
subject to Σ price[p] · pick[p] ≤ budget
           1 GK, 4 DEF, 4 MID, 2 FWD          (= 11)
           ≤ 3 players per club
           pick[p] ∈ {0, 1}
→ the solver returns the provably-best XI
```

---

### 🎯 Sprint Goal

**Objective:** Pick the **optimal starting XI** — the 11 players that maximise last
season's `total_points` within a budget, a fixed formation, and the max-3-per-club
rule — and display it. (The 4 bench players stay a manual pick with a £20M budget.)

#### Success Criteria
- [ ] Squad-selector approach agreed (ADR-008) before feature code
- [ ] An integer program (PuLP) selects the XI: budget, formation, ≤3-per-club
- [ ] `squad --budget 80` outputs the XI (players, cost, total points)
- [ ] Infeasible cases (e.g. budget too low) are reported clearly, not crashed
- [ ] Tests cover the optimiser on a small known dataset (optimum + each constraint)
- [ ] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-024 | Agree squad-selector approach (ADR-008): ILP formulation, constraints (budget, 1-4-4-2, ≤3/club), objective (`total_points`), PuLP dependency, output, infeasibility | Critical | Planned | 0.5 session |
| US-025 | Optimiser — `src/analytics/optimizer.py` builds + solves the ILP (add PuLP to requirements) | High | Planned | 1.5 session |
| US-026 | `squad` command + display + Handbook/README | High | Planned | 1 session |

#### Technical Tasks & Maintenance
- [ ] ADR-008 recorded + added to the ADR index - _Planned_
- [ ] Add `pulp` to `requirements.txt` (first dependency beyond `requests`) - _Planned_
- [ ] Update Architecture doc: optimisation component + the new dependency - _Planned_
- [ ] Update `README.md` with the `squad` command - _Planned_
- [ ] New Handbook chapter for optimisation / linear programming - _Planned_

---

### ✅ Definition of Done (this sprint)

Same 3-part DoD that has held for six sprints — a story isn't done until:
1. **Automated tests pass** (and cover the new logic).
2. **Manual smoke test done** — run the real command, eyeball the output, check `--help`.
3. **Documentation updated & checked** — Handbook, Architecture, ADR + index, README,
   sprint board + PROJECT_STATUS, as applicable (Charter Documentation Rules).

A "smoke test" + "docs touched" note goes in the session log for each feature story.

---

### 🚧 Scope Boundaries & Dependencies

| Included (In Scope) | Excluded (Out of Scope) |
|---|---|
| Optimal starting XI (1-4-4-2) via ILP | The 4 bench players (manual, £20M) |
| Budget (default £80M) + ≤3-per-club | Full 15-man squad optimisation |
| Objective: last-season `total_points` | Other formations (deferred) |
| PuLP solver in one module | xP/value as the objective (backlog) |

**External Dependencies:**
- [ ] **PuLP** (new) — integer-programming solver (bundles the CBC solver)
- [ ] Existing players/teams data (no new fetch or schema); Python otherwise stdlib

---

### ⚠️ Risks & Mitigations

| Risk | Impact (High/Med/Low) | Mitigation Strategy |
|---|---|---|
| New dependency (PuLP + CBC solver) | Med | Contain it in the optimiser module; pin in `requirements.txt`; verify install |
| Infeasible constraints (budget too low) | Med | Detect the solver's status; report a clear message, don't crash |
| Solver is a "black box" vs transparent code | Low | Document the ILP formulation in an ADR + a Handbook chapter |
| Formation hard-coded (1-4-4-2) | Low | v0 per Tony's spec; flexible formations are a backlog item |
| Objective is last-season points (preseason) | Low | Honest baseline; switch to xP later (backlog) |

---

### 🗝️ Gating decision (US-024 → ADR-008)

Settle before building:
1. **Algorithm** — integer linear programming via **PuLP** (chosen: delivers a provably
   optimal XI; the Roadmap's named tool).
2. **Constraints** — budget (default £80M), formation 1 GK / 4 DEF / 4 MID / 2 FWD,
   ≤ 3 players per club.
3. **Objective** — maximise last-season `total_points` (switchable to xP later).
4. **Output** — the XI with per-player price/points, plus totals; clear infeasible message.

---

### 📝 Session Progress Log

#### Session 1 - [Date]
* **Completed:**
* **Manual smoke test:**
* **Docs touched:**
* **Issues / Blockers:**
* **Next Steps:**

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:**
* **Carried Forward:**
* **Key Artifacts / Decisions:**

#### Retrospective
* **What Went Well?**
* **What Could Be Improved?**
* **Lessons Learned:**
* **Action Items for Next Sprint:**

---

**Proposed follow-on (Sprint 008):** full 15-man squad optimisation, flexible
formations, or an xP-based objective — plus the deferred data-dependent work once the
season starts.

**Completion Date:** [YYYY-MM-DD]
**Final Notes:**
