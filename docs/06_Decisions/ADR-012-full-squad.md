# Architectural Decision Record: The Full 15-Man Squad

**Decision ID:** ADR-012
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-008)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The optimiser (ADR-008) picks the best **starting XI** — a fixed 1-4-4-2 within a
budget. Real FPL is about the **15 you own**: 2 GK, 5 DEF, 5 MID, 3 FWD, ≤ £100.0m,
≤ 3 per club. This decision settles how to select that full squad.

A planning check confirmed the data supports it (564 players; cheapest legal 15-man
squad is £64.0m — well inside £100m). **No new data or dependency.**

#### Decision Drivers
- **Simplicity** — prefer the simplest model that answers the question (Charter).
- **Reuse** — `select_squad` already takes `formation` and `budget` as parameters, so
  the full squad is a new *caller*, not a new algorithm.
- **Human judgement where it belongs** — the manager, not the solver, should choose the
  cheap bench.
- **Honesty** — record what the numbers do and don't mean.

---

### 💡 Decisions

**1. Simple full-squad model (not two-tier).** `squad --full` maximises the chosen
objective over **all 15** players, subject to:
- exactly **2 GK, 5 DEF, 5 MID, 3 FWD**,
- Σ price ≤ **£100.0m** (the default budget when `--full` is set),
- ≤ **3 players per club**.

All of these are already expressible in `select_squad(formation=…, budget=…)`.

**2. The bench is the manager's, via `--include`.** The model scores all 15 equally,
so on its own `--full` spends nearly the whole £100m on 15 strong players and leaves
**no cheap bench**. That is intended: the manager `--include`s 4 cheap, vetted players
(locking those slots cheap), and the solver optimises the remaining 11. There is **no
auto-bench logic**. The intended workflow:

```
squad --full --include <cheap GK> <cheap DEF> <cheap MID> <cheap FWD>
```

**3. Objective unchanged.** points (default) / value / xp from ADR-011, applied to the
15. include/exclude and `--budget` compose exactly as before.

**4. CLI & display.**
- `squad` → the XI (unchanged; £80m default).
- `squad --full` → the 15 (£100m default), shown grouped by position with totals; the
  objective is stated and forced (`--include`) picks are marked `*`.

**5. Rejected alternative — the two-tier model.** A richer model would add a second set
of variables (own-15 vs start-11) linked by `start[p] ≤ squad[p]` and maximise only the
XI's score, so the solver itself picks a cheap bench. It is more *correct* in theory but
adds real complexity, and the manager reaches the same realistic squad more simply via
`--include`. Rejected on the simplicity driver. (Recorded here so the door is documented,
not reopened by accident.)

---

### ⚠️ Stated limitation — what the total means for a full squad

For the **XI**, the total-points figure is a fair proxy for weekly return — all 11 can
score. For the **15**, the total **counts bench players who will not actually score in a
given gameweek**, so it is a *"squad strength"* proxy, **not** an expected weekly return.

This is inherent to the simple model (it scores all 15 equally). The display for `--full`
will **not** imply the number is a weekly score, and this ADR records the caveat openly
rather than letting the figure mislead.

---

### 🧪 Worked example (pressure-testing the mechanism — run on real data)

Simulating `--full` by calling the existing `select_squad` with the 15-man formation:

| Run | Result |
|---|---|
| `squad --full` (no includes) | £100.0m · **2606 pts** · 15 players — cheapest £5.0m, **zero** players ≤ £4.5m |
| `squad --full --include <4 cheap>` | bench £17.0m (4.0/4.0/4.5/4.5) + best 11 at £83.0m = £100.0m · **2241 pts** |

This confirms both claims **before any command is written**:
1. Alone, `--full` spends up and gives **no cheap bench** (an all-strong 15).
2. `--include` locks the bench cheap and the solver pours the remaining budget into the
   best 11.

It also demonstrates the stated limitation: the total *drops* (2606 → 2241) when the
realistic bench is added, precisely because the 2606 figure was counting bench-quality
players who would never score. The realistic squad is the £83m-on-11 one.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** The optimiser now answers the *real* FPL question (the 15) by reusing the
  generic core — a new caller, not a new algorithm. Bench judgement stays with the human.
* **Negative / Trade-offs:** Without `--include`, `--full` returns an unrealistic
  all-premium 15; the total-for-15 is a squad-strength proxy, not a weekly score (both
  documented). A truly solver-chosen bench would need the rejected two-tier model.
* **Risks & Mitigations:**
  - *"No cheap bench" surprises a user* → help text + README push the `--include` workflow.
  - *The 15-total misleads* → recorded caveat; the display doesn't call it a weekly score.
  - *Infeasible budget* → solver status ≠ Optimal → existing "no legal squad" message.

---

### 🛠 Implementation & Migration
* **Components Affected:** CLI (`squad --full`), display (`render_squad` shows 15), Docs.
  **Not** the optimiser core — `select_squad` already supports it.
* **Action Items:**
  - [x] Record the design + worked example + caveat (US-037)
  - [ ] `squad --full` command + 15-player display + help workflow (US-038)
  - [ ] (Backlog) Flexible formations for the XI; (rejected) two-tier XI/bench model

---

### 🔄 Review & Reconsideration
* **Review Date:** If the "no cheap bench by default" workflow proves clumsy in use.
* **Triggers for Reconsideration:**
  - [ ] Users want the solver to pick the bench automatically → revisit the two-tier model.
  - [ ] A weekly-return number is wanted for the 15 → score only a chosen XI within it.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-037 (this), US-038
- **External Docs:** [ADR-008 (squad selector)](./ADR-008-squad-selector.md) · [ADR-009 (include/exclude)](./ADR-009-squad-include-exclude.md) · [ADR-011 (objective)](./ADR-011-squad-objective.md) · [Sprint 011](../05_Sprints/Sprint11.md)
