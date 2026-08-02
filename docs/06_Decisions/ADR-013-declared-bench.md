# Architectural Decision Record: A Declared Bench (`--bench`)

**Decision ID:** ADR-013
**Date:** 2026-08-02
**Status:** Accepted
**Superseded By / Replaces:** N/A (extends ADR-012)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

The full squad (ADR-012) reuses `--include` for cheap bench fodder — but `--include`
doesn't *say* "this is my bench". All 15 render as one list, and the points total counts
players who won't start. From Tony's Sprint 011 reflection: managers often have 2–3
players they always bench, and want them shown clearly — named, marked, and set apart.

This decision adds a dedicated `--bench` that lets the manager **declare** the bench, for
clearer visibility *and* an honest points total. A planning check confirmed cheap bench
options exist in every position (GK £4.0m, DEF £4.0m, MID/FWD £4.5m). **No new data.**

#### Decision Drivers
- **Visibility** — the bench should be obvious, not inferred.
- **Honesty** — knowing the bench lets us show the *starters'* points, answering the
  ADR-012 caveat.
- **Reuse** — forcing a benched player in is exactly what `--include` already does.

---

### 💡 Decisions

**1. Mechanism.** A benched player is forced into the 15 (`pick == 1`, exactly like
`--include`). `select_squad` gains a `bench_ids` set and tags each result row
`bench=True`. **No new constraint, no objective change** — the optimiser only annotates.

**2. Marker & order.** Bench rows are marked **`**`** and sorted **after** all starters,
under a "Bench" heading. `--include` starters keep **`*`**. A row is one or the other,
never both. A legend line explains each marker that appears.

**3. Implies `--full`.** `--bench` turns on the 15-man squad automatically — a bench is a
15-man concept; a starting XI has none. `full = args.full or bool(args.bench)`.

**4. Cap 4.** A 15-man squad has 15 − 11 = 4 bench slots; naming more than 4 is an error.

**5. Conflicts.** `bench ∩ exclude` and `bench ∩ include` are errors (a player can't be
benched *and* excluded, or declared both a starter-include and a bench). Reuses the
Sprint-008 name resolver and the existing conflict-check pattern.

**6. Starters' subtotal & caveat.** The output shows the squad total (all 15) **and** a
starters' subtotal (non-bench points), **labelled by count**. When exactly 4 are benched
the subtotal is the true starting-XI points (and the ADR-012 caveat is softened);
otherwise the caveat stands and the label makes the count explicit (e.g. "Starters (13)").

**7. Display.** Starters grouped by position (as today) → a "Bench" divider → the bench
rows; then totals, the starters' subtotal, and the marker legend.

**Not in scope:** *choosing* the bench for the user (that is the two-tier model rejected
in ADR-012); bench *order* (who subs on first); persisting a bench across runs.

---

### 🧪 Worked example (pressure-testing the mechanism — run on real data)

Simulating `--bench` by forcing two cheap players in (`select_squad(include_ids=…)`) and
applying the proposed tag / sort / subtotal by hand:

```
declared bench: Dubravka (GK £4.0m), Diop (DEF £4.0m)

GK  Raya        £6.0m 162     ← 13 starters, grouped by position
DEF Gabriel     £8.0m 209
... (11 more) ...
--- Bench ---
GK  Dubravka    £4.0m  96 **  ← forced in, tagged, sorted to the bottom
DEF Diop        £4.0m  31 **

Squad:    £100.0m · 2464 pts (15)
Starters: 2337 pts (13)       ← the honest weekly number
```

This confirms the tag, the `**` marker, the sort, and the split total **before** any
command is written. It also demonstrates decision 6: only **2** were benched, so
"Starters" is **13**, not a true XI — hence the by-count label. Benching a full 4 would
give "Starters (11)" — the real starting-XI points.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** The bench becomes explicit and clearly rendered; the starters' subtotal
  answers the ADR-012 honesty caveat; the optimiser barely changes (annotation, not
  optimisation).
* **Negative / Trade-offs:** `--bench` silently enabling `--full` is a small surprise
  (mitigated: the "15-man squad" header shows the mode). The subtotal is only a true XI
  at a full 4-man bench (mitigated: labelled by count).
* **Risks & Mitigations:**
  - *`**`/`*` confusion* → a legend line, each marker shown only if used.
  - *Sort disturbs the existing `--full` order* → bench sort touches only tagged rows;
    no bench → order unchanged (a regression test pins it).
  - *Naming > 4 / a benched-and-excluded player* → validated up front, clear error, no solve.

---

### 🛠 Implementation & Migration
* **Components Affected:** optimiser (`select_squad` gains `bench_ids` + a `bench` tag),
  CLI (`squad --bench`, validation, implies `--full`), display (`render_squad` bench
  section + subtotal), Docs. The optimiser's *model* is unchanged.
* **Action Items:**
  - [x] Record the design + worked example + by-count caveat (US-040)
  - [ ] `--bench` CLI + validation + `select_squad` tag + `render_squad` section (US-041)
  - [ ] (Backlog) bench *order*; a saved/persistent squad; flexible formations

---

### 🔄 Review & Reconsideration
* **Review Date:** If managers want the tool to *pick* the bench, or to persist one.
* **Triggers for Reconsideration:**
  - [ ] Demand for an auto-chosen bench → revisit the two-tier model (ADR-012).
  - [ ] Want bench substitution order (1st/2nd/3rd sub) → a richer bench model.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-040 (this), US-041
- **External Docs:** [ADR-012 (full squad)](./ADR-012-full-squad.md) · [ADR-009 (include/exclude)](./ADR-009-squad-include-exclude.md) · [ADR-008 (squad selector)](./ADR-008-squad-selector.md) · [Sprint 012](../05_Sprints/Sprint12.md)
