# Sprint 007: Optimal Squad Selector

**Dates:** 2026-08-02
**Status:** ✅ Complete
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
- [x] Squad-selector approach agreed (ADR-008) before feature code
- [x] An integer program (PuLP) selects the XI: budget, formation, ≤3-per-club
- [x] `squad --budget 80` outputs the XI (players, cost, total points)
- [x] Infeasible cases (e.g. budget too low) are reported clearly, not crashed
- [x] Tests cover the optimiser on a small known dataset (optimum + each constraint)
- [x] **Manual smoke test** run before the sprint is closed (Definition of Done)

---

### 📋 Sprint Backlog

| ID | Title / Story | Priority | Status | Estimate |
|---|---|---|---|---|
| US-024 | Agree squad-selector approach (ADR-008): ILP formulation, constraints (budget, 1-4-4-2, ≤3/club), objective (`total_points`), PuLP dependency, output, infeasibility | Critical | ✅ Complete | 0.5 session |
| US-025 | Optimiser — `src/analytics/optimizer.py` builds + solves the ILP (add PuLP to requirements) | High | ✅ Complete | 1.5 session |
| US-026 | `squad` command + display + Handbook/README | High | ✅ Complete | 1 session |

#### Technical Tasks & Maintenance
- [x] ADR-008 recorded + added to the ADR index - _Done (US-024)_
- [x] Add `pulp` to `requirements.txt` (first dependency beyond `requests`) - _Done (US-025)_
- [x] Update Architecture doc: optimisation component + the new dependency - _Done (US-024)_
- [x] Update `README.md` with the `squad` command - _Done (US-026)_
- [x] New Handbook chapter for optimisation / linear programming - _Done (US-025, Ch 22)_

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

#### Session 1 - 2026-08-02 (US-024: ADR-008 — squad selector design)
* **Completed:** Recorded ADR-008: ILP via PuLP; objective = last-season `total_points`; constraints budget £80M default / 1-4-4-2 / ≤3-per-club; price = current; v0 selects from all players (availability deferred). **Pressure-tested the formulation with a worked example** (2 FWD / £15M where greedy stalls at 10 pts but ILP finds B+C = 17) — per the Sprint 006 lesson. Added to ADR index; Architecture §4 gains an optimisation-component note + changelog. US-024 **complete** — no feature code.
* **Manual smoke test:** N/A (docs-only gate story).
* **Docs touched:** ADR-008 (new) + index, Architecture §4/changelog, Sprint7 board, PROJECT_STATUS.
* **Issues / Blockers:** None. (Data verified at planning; formulation verified with a worked example.)
* **Next Steps:** US-025 — the optimiser (`src/analytics/optimizer.py`, add PuLP).

#### Session 2 - 2026-08-02 (US-025: the optimiser)
* **Completed:** Added `src/analytics/optimizer.py` `select_squad()` — builds ADR-008's ILP in PuLP and returns the optimal XI (status, selected, totals). Added `pulp` to requirements (first dependency beyond `requests`; installed 3.3.2). Scope-suppressed PuLP-4.0 deprecation notices (logged a migration backlog item). New Handbook Ch 22 (Optimisation / LP). 5 optimiser tests incl. the knapsack + infeasible cases (81 total). US-025 **complete**.
* **Manual smoke test:** ✅ `select_squad(get_players(), budget=80)` → optimal XI, exactly £80.0m, 2024 pts, valid 1-4-4-2, MCI at the 3-per-club cap.
* **Docs touched:** Handbook Ch 22 + front-page table, Backlog (PuLP 4.0 tech debt), Sprint7 board, PROJECT_STATUS. (Architecture covered in US-024.)
* **Issues / Blockers:** PuLP emitted 4.0-deprecation warnings — scope-suppressed with a backlog item to migrate; not a blocker.
* **Next Steps:** US-026 — the `squad` command + display.

#### Session 3 - 2026-08-02 (US-026: the squad command)
* **Completed:** Added `ui/squad.py` (`render_squad` — the XI grouped by position + totals, or a clear infeasible message) and the `squad --budget N` command (thin handler over `select_squad`). Added `squad` to the `--help` examples, Ch20 command list, README. 4 tests (render optimal/infeasible + parse; 85 total). US-026 **complete** — all Sprint 007 stories done.
* **Manual smoke test:** ✅ `squad --budget 80` → optimal XI (£80.0m, 2024 pts); `squad --budget 40` → infeasible message; `squad` in `--help`.
* **Docs touched:** Handbook Ch20, README, cli `--help`, Sprint7 board, PROJECT_STATUS.
* **Issues / Blockers:** None.
* **Next Steps:** Sprint 007 review & retrospective.

---

### 🏁 Sprint Review & Retrospective

#### Delivered vs. Roll-over
* **Delivered:** All three stories — US-024 (ADR-008), US-025 (the PuLP optimiser), US-026 (the `squad` command). The app now picks the **provably-optimal starting XI** within a budget/formation/club-cap. First optimisation feature and first dependency beyond `requests`. Tests grew 76 → 85.
* **Carried Forward:** None. Backlog gained: PuLP-4.0 migration, availability filter, flexible formations, 15-man squad, xP objective.
* **Key Artifacts / Decisions:** ADR-008 (ILP via PuLP, with a worked example); `src/analytics/optimizer.py`; Handbook Ch 22 (Optimisation); commits `7783ed5`→`6b27391`.

#### Retrospective
* **What Went Well?**
  - **The app crossed from analysis to a decision** — `squad` recommends, it doesn't just rank. From Tony's own retro idea.
  - **The gate story earned its name.** ADR-008's formulation was pressure-tested with a worked example *before* coding — applying the Sprint 006 lesson; no flaw slipped this time.
  - A genuinely new *kind* of code (declarative optimisation) landed cleanly in one module.
  - The dependency (PuLP) stayed sealed; the rest of the codebase was untouched.
  - The 3-part DoD held again (8th sprint).
* **What Could Be Improved?**
  - PuLP's 4.0 deprecation warnings needed handling — scope-suppressed with a backlog item; a future migration is owed.
  - v0 objective is last-season points and the formation is fixed — honest for a first cut, but both are obvious next refinements.
* **Lessons Learned?**
  - Optimisation flips the mindset: describe the *rules*, not the *search*.
  - Pressure-testing an ADR mechanism (worked example) works — the discipline caught nothing to fix *because* it was applied.
  - A "black box" solver is trustworthy when pinned by tests on known-answer cases.
* **Action Items for Next Sprint (008):**
  - [ ] Consider: 15-man squad, flexible formations, or an xP-based objective (backlog).
  - [ ] Revisit data-dependent work (form/expected-minutes xP, Attack/Defence FDR) once the season starts — check data first.
  - [ ] Keep pressure-testing ADR mechanisms + the 3-part DoD.

---

**Proposed follow-on (Sprint 008):** full 15-man squad optimisation, flexible
formations, or an xP-based objective — plus the deferred data-dependent work once the
season starts.

**Completion Date:** 2026-08-02
**Final Notes:** The app crossed from *analysis* to *recommendations* — its first
optimisation, giving a provably-best XI. Tony's own idea, and a landmark step. Sprint
outcome: **Successful** — 3/3 stories, zero roll-over, DoD held.
