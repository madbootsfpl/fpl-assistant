# Milestone — Phase 1 Complete (CLI Analytics MVP)

**Date:** 2026-08-03 · **Sprint:** 025 · **Decision:** [ADR-026](../06_Decisions/ADR-026-phase1-cli-mvp.md)

---

## The milestone

**Phase 1 is complete** — declared as the **CLI Analytics MVP**. Over 24 sprints the project grew
from an empty repo into a working command-line FPL analytics & optimisation assistant, built
sprint-by-sprint with a gate-per-feature and a 3-part Definition of Done.

**What it is:** a CLI tool — 12 commands, 25 ADRs (001–025) + ADR-026 closing the phase, 227
offline tests — that ingests FPL data into a local SQLite cache and turns it into rankings, custom
fixture difficulty, expected points, expected goals, defensive metrics, and an ILP-optimised
squad, with saved/reloadable user squads and graceful degradation when ClubElo is down.

## Why "CLI Analytics MVP" and not "original Phase 1, done"

We built by *learning*, and the code outran the original aspirational roadmap. What we finished is
the **analytical + optimisation core** that the original plan scattered across Phases 1, 2 and 5 —
delivered as a CLI. The original Phase 1 **infrastructure spine** (web UI, CI/CD, session auth,
historical data) was *deliberately deferred* (CLI over web: ADR-002/003; single-user: ADR-001).

So the milestone is named for what was actually built, and the deferred infra is listed openly —
not implied done. The full two-way audit (every roadmap bullet ↔ every sprint) is in
[Phase1_Reconciliation.md](../04_Roadmap/Phase1_Reconciliation.md).

## What's next

The [Roadmap](../04_Roadmap/Roadmap.md) is reframed: **Phase 2 — Infrastructure, Data Depth &
Analytics Hardening** now leads with the carried-forward infra (web UI, CI/CD, auth, historical
data) alongside the analytics remainder. Phases 3 (decision support), 4 (AI/RAG) and 5 (chip
optimisers / transfer-path simulation) follow, with the built bits marked done. Nothing was
dropped. Sprint 026 picks the next direction.

## Notes for future me

- The gate (decide + write the ADR *before* code) and the 3-part DoD held for all 24 sprints —
  they are why the project stayed legible and why this reconciliation was even possible.
- The honest habit paid off at the end too: the completeness review (US-074) caught the README
  overstating the tool (it listed FastAPI and unbuilt features), and the milestone was named
  precisely rather than flatteringly.
- Known external issue at close: ClubElo has been down since 2026-08-03 — the tool degrades to
  last-known Elo, exactly as designed.
