# Architectural Decision Record: Validate a Legal Bench

**Decision ID:** ADR-022
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (closes an ADR-014 gap; reuses ADR-014's `XI_FLEX`)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

`squad --full --bench …` (ADR-013) *displays* the starting shape the declared bench implies
(ADR-014), but doesn't *check* it. A shape can be displayable yet illegal — bench all three
forwards and "5-5-0" prints while being an illegal XI (0 forwards). This closes that gap by
validating a complete bench and warning if the resulting XI is illegal.

A probe confirmed the fix is clean and data-supported (no new data).

#### Decision Drivers
- **Correctness** — an illegal bench should be flagged, not shown silently.
- **One source of truth** — reuse the legal-XI ranges already defined for formations.
- **Respect the manager** — inform, don't dictate.

---

### 💡 Decisions

**1. Validate only a *complete* bench.** The check runs when exactly **11 starters** remain
(a full 4-man bench). Fewer benched → no complete XI → the existing "bench 4 for a full XI"
message stands (unchanged); we do not validate an incomplete bench.

**2. The check reuses `XI_FLEX`.** Each starter position count must sit inside the legal-XI
ranges from ADR-014 — **GK 1, DEF 3–5, MID 2–5, FWD 1–3**. Any count outside its range is an
issue. A pure `legal_xi_issues(starters)` returns the reasons (empty = legal). Reusing
`XI_FLEX` means bench-legality and flexible-formations can never disagree.

**3. Warn, not block.** The bench is the manager's advisory choice. On an illegal bench we
**show the squad and print a clear warning** listing the problems — we do **not** error out or
refuse. The manager decides. *(Considered and rejected: hard-blocking. This tool proposes; it
doesn't submit a team to FPL, so refusing would be paternalistic.)*

**4. Message.** Specific and actionable, e.g.
`Note: this bench doesn't leave a legal XI — 0 FWD (need 1-3)`. Multiple problems are listed.

**Not in scope:** auto-fixing the bench; bench *order* (which sub first — stays on the
backlog); validating an incomplete (< 4) bench.

---

### 🧪 Worked example (pressure-testing — run on real data)

Declaring different benches on a real 15-man squad, and applying the proposed check:

| Bench | Starters | `legal_xi_issues` |
|---|---|---|
| 1 GK, 1 DEF, 1 MID, 1 FWD | 4-4-2 | *(none — legal)* |
| 1 GK, 3 FWD | 5-5-0 | `0 FWD (need 1-3)` |
| 1 GK, 3 DEF | 2-5-3 | `2 DEF (need 3-5)` |
| only 2 benched | 13 starters | *(not validated — incomplete)* |

Confirms the check flags each illegal shape with a specific reason, passes a legal one, and
correctly *skips* an incomplete bench — all before any feature code.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** The squad feature is airtight — an illegal declared bench is flagged clearly,
  reusing the single legal-XI definition; no new data or dependency; warn-not-block keeps the
  manager in control.
* **Negative / Trade-offs:** A warning, not a guarantee — the tool still prints an illegal
  squad (by design). Validation is only for a complete bench (an incomplete one is "not a full
  XI yet", handled by the existing message).
* **Risks & Mitigations:**
  - *Firing on an incomplete bench* → gated on `len(starters) == 11` (a test covers it).
  - *Rule duplication* → reuse `XI_FLEX`.
  - *Frustrating hard errors* → warn, not block.

---

### 🛠 Implementation & Migration
* **Components Affected:** analytics (`legal_xi_issues` reusing `XI_FLEX`), display
  (`render_squad` warning), Docs. No data/storage change.
* **Action Items:**
  - [x] Record the design + worked example + warn-not-block (US-062)
  - [ ] `legal_xi_issues` + the `render_squad` warning (US-063)
  - [ ] (Backlog) bench *order*; an auto-suggested legal bench

---

### 🔄 Review & Reconsideration
* **Review Date:** If users want the bench *enforced* rather than warned.
* **Triggers for Reconsideration:**
  - [ ] Demand to block an illegal bench (e.g. a future "export my team" feature).
  - [ ] Want an auto-suggested legal bench.

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-062 (this), US-063
- **External Docs:** [ADR-014 (flexible formations / `XI_FLEX`)](./ADR-014-flexible-formations.md) · [ADR-013 (declared bench)](./ADR-013-declared-bench.md) · [Sprint 021](../05_Sprints/Sprint21.md)
