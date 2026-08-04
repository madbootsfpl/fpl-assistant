# Master FPL Assistant Roadmap

*Reframed 2026-08-03 (Sprint 025). **Phase 1 is complete** — declared as the "CLI Analytics MVP".
The original aspirational 5-phase plan is preserved and reconciled item-by-item in
[Phase1_Reconciliation.md](Phase1_Reconciliation.md); the decision is
[ADR-026](../06_Decisions/ADR-026-phase1-cli-mvp.md). Nothing has been dropped — every unbuilt
item below traces to an original bullet.*

**Status legend:** ✅ Done · ◑ Partial · ⬜ Not started (carried forward)

---

## ✅ Phase 1 — CLI Analytics MVP — **COMPLETE (2026-08-03)**

**What shipped:** a working command-line FPL analytics & optimisation assistant — the analytical
and optimisation *core* that the original plan (Phases 1/2/5) is reconciled against, delivered as
a **CLI**. Web UI, CI/CD, auth and historical data were *deliberately* deferred (ADR-001/002/003).

- **Data:** FPL API client (`bootstrap-static`, `fixtures`) + SQLite cache (upsert, generic
  migrations). FPL is the source of truth; ClubElo is a best-effort second source that degrades
  gracefully (retry-then-degrade, importance-scaled).
- **Analytics:** custom FDR (overall + ClubElo Elo), Points-per-£m value, Expected Points (xP) v0
  over a multi-week horizon, xG/xA/xGI/xGC, over/under-performance, Defensive Contribution,
  clean-sheet solidity (xGC/90).
- **Optimisation:** an ILP squad selector (PuLP) — best XI or full 15-man squad, flexible
  formations, declared bench, include/exclude, a pluggable objective (points/value/xp/xgi),
  availability filtering.
- **User state:** saved / reloadable squads (re-priced, with current injuries + departures).
- **Engineering:** 12 commands, 25 ADRs (001–025) + ADR-026 closing the phase, 227 offline tests,
  a shared table renderer.

**Deliberately deferred to Phase 2+ (carried, not dropped)** — full two-way audit in
[Phase1_Reconciliation.md](Phase1_Reconciliation.md).

---

## Phase 2 — Infrastructure, Data Depth & Analytics Hardening  *(next)*

**Goal:** give the proven analytics core the infrastructure and richer data the original Phase 1/2
called for — now that the MVP has shown what's worth investing in.

### Infrastructure (carried forward from the original Phase 1)
- ⬜ **Web dashboard UI** (FastAPI/Flask + React/Next.js; the CLI stays the engine) — the original
  Phase 1 UI, deferred by ADR-002/003.
- ⬜ **CI/CD** — GitHub Actions (lint + the 227 tests) + pre-commit hooks.
- ⬜ **Session/cookie auth** for user-specific data (`/my-team/{id}/`).
- ⬜ **Historical + price-trend schema and backfills** (past-season stats for modelling); cache
  TTLs; a gameweek countdown.
- ⬜ **Source versioning** — formalise the "version all external sources" reliability rule.

### Data & analytics depth (original Phase 2 remainder)
- ⬜ Price-change predictor (directional flags from net transfer deltas — treat as flags, not truth).
- ⬜ Form per £m + rolling 3-GW vs 6-GW trendlines (needs in-season `form` + history).
- ◑ Attack/Defence FDR split + recent-form weighting (deferred while preseason strengths are 0 —
  ADR-005).
- ◑ A **first-class xP engine with uncertainty** — graduate xP v0 into the single source of truth
  for every downstream recommendation.
- ◑ Updated BPS rules beyond DefCon (e.g. GK saves).
- ⬜ Confidence scoring on external-data fallback.

---

## Phase 3 — Decision Support Engine  — ✅ **substantially complete (2026-08-04)**

**Goal:** translate analytics into actionable manager recommendations. The core trio —
recommend-and-explain, all composed on xP + saved squads + availability — is **built and
cross-linked** (`captain` → `transfer` → `analyse`).

- ✅ Captain suggestion (`captain --squad`, ADR-029) — top picks by next-GW xP; opponent, venue,
  penalty duty; GKs excluded (mean ≠ ceiling); doubtful flagged.
- ✅ Transfer recommendation (`transfer --squad`, ADR-030) — best single legal upgrades by xP gain;
  same position, ≤3/club, budget (sale + `--bank`); GKs included; bench flagged.
- ✅ Team analyser (`analyse --squad`, ADR-031) — projected XI xP over N GW (with a per-GW breakdown,
  ADR-032), weak links, injuries, club concentration; indicators, not a grade. *(Uses a saved
  squad — a manager-ID fetch waits on auth.)*
- ◑ Expected minutes (xMins) & rotation — deferred; captaincy/transfers note the "assumes they play"
  caveat and flag bench players until this exists (needs the season started).
- ⬜ Live event layer — re-rank on injuries / lineups / price changes without a full recompute.
- ⬜ Multi-move transfer *planner* (hits vs roll, −4 maths) — the single-move engine is the foundation.

---

## Phase 4 — AI & Natural-Language Layer

**Goal:** an intelligent interface that explains outputs via grounded RAG.

- ⬜ Grounded RAG pipeline — feed structured Phase 2/3 JSON into the LLM; never let it compute
  prices / points / deadlines (the primary anti-hallucination defence).
- ⬜ Chat interface + intent-matching query parser.
- ⬜ Human-readable decision justification.

---

## Phase 5 — Advanced Optimisation & Long-Term Planning

**Goal:** multi-week squad decisions via optimisation. *Core already delivered in the MVP.*

- ✅ Integer-programming solver under budget / positional constraints (ADR-008).
- ✅ Full 15-man squad generation for a horizon (ADR-012).
- ◑ Multi-week horizon — the xP horizon is done (ADR-007); add decaying weights.
- ⬜ Chip optimisers — Wildcard / Free Hit (15-man exists), Bench Boost, Triple Captain.
- ⬜ Transfer-path simulation (a −4 now vs rolling).

---

## Cross-Cutting (all phases)

- ⬜ **Evaluation & feedback loops** — track real outcomes ("did the suggested captain beat the
  template?"); keep golden gameweeks for regression testing. *Critical before trusting
  recommendations — without measurement, models look clever while underperforming.*
- ✅ **Data reliability** — FPL is the source of truth; external sources degrade gracefully
  (ADR-010/020/021). ⬜ Version all external sources.
- ⬜ **Success metrics** — price-flag accuracy, xP calibration, captain hit-rate, net points over a
  season. Define *before* Phase 3 recommendations.

---

## Original plan (for the record)

The original aspirational 5-phase roadmap is fully preserved and reconciled bullet-by-bullet in
[Phase1_Reconciliation.md](Phase1_Reconciliation.md) — every unbuilt item above traces back to an
original line, and nothing has been deleted.
