# Architectural Decision Record: Optimal Squad Selector (ILP)

**Decision ID:** ADR-008
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

From a Sprint 006 reflection: pick the **optimal starting XI** — the 11 players that
maximise last-season `total_points` within a budget, a fixed formation, and the
max-3-per-club rule. A planning-time data check confirmed the inputs
(`total_points`, `now_cost`, `element_type`, `team`) are all populated. This is the
project's first **optimisation** feature (Roadmap Phase 5) — choosing a *set* under
constraints, not ranking a list.

#### Decision Drivers
- **Actually optimal** — the owner asked for the *best* XI, not a good-enough one.
- **The right tool** — the Roadmap names integer programming (PuLP/scipy).
- **Learning** — integer programming is a valuable, transferable concept.

---

### 💡 Decisions

**1. Algorithm — Integer Linear Programming via PuLP.** A binary "pick" per player,
maximising points under the constraints. The solver returns a **provably optimal** XI.
Chosen over a greedy heuristic, which can't guarantee optimality (see the worked
example). PuLP is the project's first dependency beyond `requests`; it lives in one
optimiser module.

**2. Formulation.**
```
decision:  pick[p] ∈ {0, 1}   for each player p
maximise:  Σ total_points[p] · pick[p]
subject to Σ price[p] · pick[p] ≤ budget         (default £80M)
           Σ pick[p] (GK)  = 1
           Σ pick[p] (DEF) = 4
           Σ pick[p] (MID) = 4
           Σ pick[p] (FWD) = 2                    (→ 11 players)
           Σ pick[p] (club c) ≤ 3   for each club c
```

**3. Constraints & objective.** Budget default £80M; formation 1 GK / 4 DEF / 4 MID /
2 FWD; ≤ 3 players per club; objective = last-season `total_points`; price = current
(`now_cost ÷ 10`).

**4. Scope.** v0 selects from *all* players (availability/`status` filtering is a
backlog refinement). The 4 bench players remain a manual pick (£20M), out of scope.
Other formations, a 15-man squad, and an xP-based objective are backlog items.

---

### 🧪 Worked example (pressure-testing the mechanism)

Two forward slots, £15M between them:

| FWD | Points | Price |
|---|---|---|
| A | 10 | £10M |
| B | 9 | £9M |
| C | 8 | £6M |

- **Greedy by points** takes A (£10M), then needs a 2nd FWD ≤ £5M — none exists —
  and is stuck at 10 pts.
- **ILP** evaluates combinations: **B + C = £15M, 17 pts** — the optimum greedy never sees.

This confirms the objective + budget + position-count constraints behave correctly,
and *why* the budget makes the combination (not each pick) matter — the reason greedy
is insufficient.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** A provably optimal XI; the correct, teachable tool (integer programming);
  no new data or schema (the players table already has points/price/position/team).
* **Negative / Trade-offs:** First dependency beyond `requests` (PuLP + its CBC solver);
  the solver is a "black box" compared with transparent code.
* **Risks & Mitigations:**
  - *Infeasible constraints* (budget too low) → detect the solver status; report clearly.
  - *Black-box concern* → document the formulation (this ADR + a Handbook chapter).

---

### 🛠 Implementation & Migration
* **Components Affected:** new optimiser (analytics), CLI (`squad`), requirements, Docs
* **Action Items:**
  - [x] Record the formulation + worked example (US-024)
  - [ ] `src/analytics/optimizer.py` builds + solves the ILP; add PuLP (US-025)
  - [ ] `squad` command + display (US-026)
  - [ ] (Backlog) availability filter, flexible formations, 15-man squad, xP objective

---

### 🔄 Review & Reconsideration
* **Review Date:** When a 15-man squad or xP objective is wanted
* **Triggers for Reconsideration:**
  - [ ] Need flexible formations or the full 15-man squad
  - [ ] Want to optimise on xP instead of last-season points

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-024 (this), US-025/026
- **External Docs:** [Roadmap Phase 5](../04_Roadmap/Roadmap.md) · [Architecture](../03_Architecture/Architecture.md) · [Sprint 007](../05_Sprints/Sprint7.md) · [Backlog](../Backlog.md)
