# Architectural Decision Record: Declare Phase 1 (CLI Analytics MVP) complete; reframe the Roadmap

**Decision ID:** ADR-026
**Date:** 2026-08-03
**Status:** Accepted
**Superseded By / Replaces:** N/A (a project/roadmap milestone decision; supersedes the *framing*
of the original `Roadmap.md`, not any prior ADR)
**Deciders / Participants:** Tony Sheridan (Owner), ChatGPT (Technical Lead), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Twenty-four sprints built a working CLI FPL analytics & optimisation tool. But the project was
built by *learning* — sprint to sprint — and the code **outran the original `Roadmap.md`**, an
aspirational 5-phase plan written before any building.

Reconciling the two ([Phase1_Reconciliation.md](../04_Roadmap/Phase1_Reconciliation.md)) shows the
mismatch precisely:

- **We finished the analytical + optimisation core** — which the original plan scattered across
  Phases 1, 2 and 5 (xG/xA/xGI/xGC, custom + Elo FDR, value, xP + horizon, DefCon, clean-sheet,
  over/under-performance; an ILP squad optimiser with full-15/flexible-formations/bench; saved
  squads; availability; resilient data). Delivered as a **CLI**.
- **We deliberately did *not* build the original Phase 1 infrastructure spine** — web dashboard
  UI, CI/CD, session auth (`/my-team/`), historical/price data. These were conscious choices
  (CLI over web: ADR-002/003; single-user: ADR-001), not omissions.

So "is Phase 1 complete?" has no clean yes/no against the original text: we over-delivered on
analytics/optimisation and under-delivered on infra. A decision is needed on **how to declare the
milestone and reframe the plan** so the map matches the territory.

#### Decision Drivers
- **Honesty over flattery** — the record must show what was deferred, not imply infra was built.
- **Nothing dropped** — every unbuilt idea stays traceable (carried forward, not deleted).
- **Charter priority order** — Understanding & Documentation first; keep the plan legible.

---

### 💡 Decisions

**1. Declare "Phase 1 — CLI Analytics MVP" complete.** Name the milestone for *what was actually
built*: a working CLI FPL analytics & optimisation tool — 12 commands, 25 ADRs (001–025) + this
one closing the phase, 227 tests, FPL (required, retries hard) + ClubElo (best-effort, degrades).
The label is deliberately **"CLI
Analytics MVP,"** not "original Phase 1, done" — because the original Phase 1 infra spine was
deferred, and the record says so plainly.

**2. Reframe the Roadmap to match reality — carry, don't drop.** Rewrite `Roadmap.md` so Phase 1
reflects the delivered MVP, and **every unbuilt item** (⬜ / ◑ in the reconciliation) is carried
into a reframed **Phase 2+** (or, for nice-to-haves, `Backlog.md`). The original aspirational
plan is preserved *as reconciled* — nothing is deleted; the matrix is the audit trail.

**3. The reconciliation matrix is the evidence.** [Phase1_Reconciliation.md](../04_Roadmap/Phase1_Reconciliation.md)
classifies **every** original Roadmap bullet (Done / Partial / Deferred, with sprint + ADR) **and**
accounts for **every** one of the 24 sprints (no orphans in either direction). The declaration
stands on this, not on a vibe.

**4. Deferred infra is named, not hidden.** Explicitly carried to Phase 2+: web dashboard UI;
CI/CD + pre-commit; session auth (`/my-team/`); historical + price-trend data / backfills; cache
TTLs; source versioning; plus the analytics/optimisation extensions (price predictor, form +
rolling trends, Attack/Defence FDR split, first-class uncertainty-aware xP, chip optimisers,
transfer-path simulation) and the whole of decision-support (Phase 3), AI/RAG (Phase 4), and
evaluation/success-metric loops.

**Not in scope (this is a documentation decision):** building *any* Phase 2 item; re-litigating
prior deferral ADRs (016 soccerdata, 005 FDR split, 012 two-tier); changing tool behaviour.

---

### 🧪 Worked example (pressure-testing — the matrix must balance both ways)

The declaration is only sound if the reconciliation is complete. Verified at the gate:

| Check | Result |
|---|---|
| Every original Roadmap bullet classified (Done/Partial/Deferred) | ✅ — with sprint + ADR each |
| Every one of the 24 sprints mapped to a roadmap area | ✅ — no orphan sprints |
| Items delivered *beyond* the original bullets flagged | ✅ — S16 over/under-perf, S17 DefCon (new BPS), S24 renderer |
| Deferred items carried forward, none deleted | ✅ — all ⬜ / ◑ land in Phase 2+ / Backlog |

Two-way balance (roadmap ↔ sprints) is what makes "declare complete" honest rather than flattering.

---

### ⚖️ Consequences & Trade-offs

* **Positive:** the plan finally matches the built reality; a clear, defensible milestone ("CLI
  Analytics MVP done"); every future idea is traceable in one place; a clean base to *choose* the
  next phase from evidence rather than an outdated wishlist.
* **Negative / Trade-offs:** "Phase 1 complete" needs the qualifier "CLI Analytics MVP" to avoid
  overstating (infra deferred) — a naming nuance carried in the docs. The reframed Phase 2 is now
  large and unordered until prioritised (a Sprint 026 job).
* **Risks & Mitigations:**
  - *Overstating completeness* → precise label + an explicit deferred-infra list (decision 4).
  - *Silently dropping an item* → two-way matrix; carry-forward, never delete.
  - *Scope creep ("just add CI now")* → this ADR is documentation-only; infra is a Phase 2 line-item.

---

### 🛠 Implementation & Migration
* **Components Affected:** **docs only** — `Roadmap.md` (rewrite), `Phase1_Reconciliation.md` (new,
  the matrix), `Backlog.md` (sync), `01_Journal` (milestone entry), `PROJECT_STATUS.md`, ADR index.
  **`src/` and `tests/` are untouched.**
* **Action Items:**
  - [x] Build the two-way reconciliation matrix (US-073)
  - [x] Record this decision + declaration (US-073)
  - [ ] End-to-end completeness review before the rewrite lands (US-074)
  - [ ] Rewrite `Roadmap.md` (Phase 1 ✅ + reframed Phase 2+); sync `Backlog.md`; Journal
        milestone; update `PROJECT_STATUS.md` (US-075)
  - [ ] (Sprint 026) Prioritise the reframed Phase 2 and pick the next direction

---

### 🔄 Review & Reconsideration
* **Review Date:** At Sprint 026 planning (choosing the next phase/direction).
* **Triggers for Reconsideration:**
  - [ ] The owner decides the tool's endpoint is the CLI (then some Phase 2+ items become "won't
        do", not "deferred").
  - [ ] A web UI / decision-support push begins (then Phase 2 gets ordered into sprints).

---

### 🔗 References & Related Artifacts
- **Related Stories:** US-073 (this), US-074, US-075
- **Evidence:** [Phase1_Reconciliation.md](../04_Roadmap/Phase1_Reconciliation.md)
- **External Docs:** [ADR-001 (single-user)](./ADR-001-single-user-vs-multi-user.md) · [ADR-002 (UI)](./ADR-002-ui-approach.md) · [ADR-003 (CLI)](./ADR-003-cli-approach.md) · [Roadmap](../04_Roadmap/Roadmap.md) · [Sprint 025](../05_Sprints/Sprint25.md)
