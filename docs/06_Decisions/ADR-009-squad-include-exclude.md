# Architectural Decision Record: Squad Selector — Include / Exclude

**Decision ID:** ADR-009
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-008)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

From a Sprint 007 reflection: let the user force players **in** (favourites) or **out**
(dislikes), and have the optimiser build the best legal XI around them. A planning-time
data check confirmed the inputs are present and surfaced a key nuance: **`web_name` is
not unique** — 14 names are shared by more than one player (e.g. "Wilson" ×3) — so name
resolution must handle ambiguity.

#### Decision Drivers
- **Reuse** — extend the tested ILP optimiser (ADR-008), don't rebuild.
- **Honest input handling** — never silently force the *wrong* player.
- **Clear failures** — ambiguous names, conflicts, and impossible choices reported well.

---

### 💡 Decisions

**1. Fixed decisions in the ILP.** Include → add `pick[p] = 1`; exclude → add
`pick[p] = 0`. Then maximise as before. The solver builds the optimal XI around them.

**2. Name matching — exact `web_name`, case-insensitive.** Chosen over partial/fuzzy
matching, which risks forcing the wrong player.

**3. Disambiguation — `Name:TEAM`.** For a shared name, the user adds the team short
name, e.g. `Wilson:NFO`. A bare ambiguous name errors and **lists the candidates**
(name + team) so the user can retry.

**4. Validation.**
- Name not found → error.
- Bare ambiguous name → error listing candidates.
- Same player included *and* excluded → a pre-check error (clearer than "infeasible").
- Forced set that breaks a rule (too many for a position, over budget) → the solver
  returns **Infeasible**; we report it. *The ILP validates these for free.*

**5. Output.** Mark which players in the XI were forced in.

---

### 🧪 Worked examples (pressure-testing the mechanism)

| Case | Expected | Verifies |
|---|---|---|
| Force in 2 GKs | `pick=1` for both clashes with "= 1 GK" → **Infeasible** | formation guard is automatic |
| Force in a £13M player (£80M budget) | Feasible; the rest of the XI gets cheaper to fit | budget cascades |
| Exclude the top scorer | Best XI *without* them | `pick=0` works |
| `--include Wilson` (3 match) | Error listing Wilson (NFO), (FUL), (LEE) | ambiguity handled |
| Include *and* exclude the same player | "can't do both" pre-check error | conflict caught clearly |

These confirm the fixed-pick mechanism is correct and that most validation falls out
of the solver — only name resolution and the include/exclude conflict need our own code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** Small, contained extension of the optimiser; the solver does most
  validation; the tool goes from "the optimal XI" to "the optimal XI around *my* picks".
* **Negative / Trade-offs:** `Name:TEAM` is a little verbose for shared names; exact
  matching means the user must type the `web_name` correctly (accented names included).
* **Risks & Mitigations:**
  - *Ambiguous / mistyped names* → resolve exactly; list candidates; clear "not found".
  - *Impossible forced set* → solver reports Infeasible; friendly message.

---

### 🛠 Implementation & Migration
* **Components Affected:** optimiser (`select_squad`), a name-resolver, CLI (`squad`), Docs
* **Action Items:**
  - [x] Record the design + worked examples (US-027)
  - [ ] `select_squad(include, exclude)` + `resolve_players(players, names)` (US-028)
  - [ ] `squad --include … --exclude …` + mark forced picks (US-029)
  - [ ] (Backlog) partial/fuzzy matching; forcing by position/club counts

---

### 🔄 Review & Reconsideration
* **Review Date:** If name resolution proves clumsy in use
* **Triggers for Reconsideration:**
  - [ ] Users want fuzzy matching or to force by id
  - [ ] Shared-name disambiguation needs a friendlier form

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-027 (this), US-028/029
- **External Docs:** [ADR-008](./ADR-008-squad-selector.md) · [Architecture §4](../03_Architecture/Architecture.md) · [Sprint 008](../05_Sprints/Sprint8.md) · [Backlog](../Backlog.md)
