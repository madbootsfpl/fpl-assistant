# Phase 1 Reconciliation — Built vs. Original Roadmap

**Date:** 2026-08-03 · **Sprint:** 025 (US-073) · **Decision:** [ADR-026](../06_Decisions/ADR-026-phase1-cli-mvp.md)

This document reconciles what was actually built over 24 sprints against the **original**
`Roadmap.md` (the aspirational 5-phase plan written before building). It is the audit trail behind
declaring **Phase 1 — CLI Analytics MVP** complete and reframing the remaining work into Phase 2+.

**Legend:** ✅ Done · ◑ Partial · ⬜ Deferred (carried to Phase 2+ / Backlog — *not dropped*)

> **The headline.** We built by *learning*, sprint-to-sprint, and the code outran the plan: the
> **analytics + optimisation core** (which the original plan scattered across Phases 1, 2 and 5)
> is done, delivered as a **CLI**. The original **Phase 1 infrastructure spine** — web UI, CI/CD,
> auth, historical data — was *deliberately deferred* (CLI chosen in ADR-002/003; single-user in
> ADR-001). Hence the honest label: not "original Phase 1, done", but **"CLI Analytics MVP"**.

---

## Direction 1 — every original Roadmap item, classified

### Phase 1 — Foundations & Infrastructure

| Item | Status | Where / why |
|---|:--:|---|
| Repo structure, virtual environments | ✅ | Journal Session 1 |
| Pre-commit hooks, GitHub Actions (lint/test) | ⬜ | Deferred → P2 (no CI yet; tests run locally) |
| Env vars: local vs production | ⬜ | Deferred → P2 (single local tool; no prod env) |
| FPL client — `bootstrap-static`, `fixtures` | ✅ | S1, S3 (`src/api/client.py`) |
| FPL client — `element-summary/{id}` | ⬜ | Deferred → P2 (per-player history unused) |
| Session/cookie auth — `/my-team/{id}/` | ⬜ | Deferred → P2 (no user-account fetch) |
| Local cache (SQLite) to avoid 429 | ✅ | S1 (`src/storage.py`) |
| Cache TTLs / auto-expiry | ◑ | Refresh is manual (`refresh` command), no TTL |
| Schema: players, fixtures | ✅ | S1, S3 (+ generic migrations) |
| Schema: historical GW stats, price trends | ⬜ | Deferred → P2 (only current snapshot stored) |
| Historical backfills (past seasons) | ⬜ | Deferred → P2 |
| Schema for multi-manager/league later | ⬜ | Deferred → P2 (single-user by design, ADR-001) |
| Web app boilerplate (FastAPI/React) | ⬜ | **Deferred → P2 — CLI chosen deliberately (ADR-002/003)** |
| Display player tables, raw stats | ✅ | S1+ (console tables; shared renderer S24) |
| Gameweek countdown timer | ⬜ | Deferred → P2 |
| Decide internal-tool vs multi-user | ✅ | Decided **single-user** (ADR-001) |
| Graceful degradation for external sources | ✅ | ADR-010, ADR-020, ADR-021 |
| Source versioning | ⬜ | Deferred → P2 (degradation done; versioning not formalised) |

### Phase 2 — Analytics Engine

| Item | Status | Where / why |
|---|:--:|---|
| Ingest xG / xA / xGI | ✅ | S14, ADR-015 (from **FPL API**, not scrapers) |
| xGC (goals conceded) | ✅ | S14 / S18 (ADR-019) |
| Open datasets / scrapers (soccerdata) | ✅ | S15, evaluated + **deferred** (ADR-016) |
| Updated BPS rules (CBIT, saves) | ◑ | DefCon uses BPS thresholds (ADR-018); GK saves not modelled |
| Confidence scoring + fallback | ◑ | Fallback ✅ (degradation); explicit confidence scores ⬜ |
| Points per £m (season-long value) | ✅ | S10, ADR-011 (`--objective value`) |
| Form per £m (short-term) | ⬜ | Deferred → P2 (needs `form`, preseason zero) |
| Rolling averages (3-GW vs 6-GW) | ⬜ | Deferred → P2 (no historical GW data) |
| Custom FDR — overall | ✅ | S3/S4, ADR-004/005 (+ Elo FDR, ADR-010) |
| Custom FDR — Attack/Defence split | ◑ | Deferred (preseason strengths = 0, ADR-005) |
| Home/away bias | ✅ | Overall home/away strengths (ADR-005) |
| Recent team metrics in FDR | ◑ | Elo is recent-ish (ADR-010); no rolling form |
| Price-change predictor | ⬜ | Deferred → P2 |
| Explicit xP engine (per-player/fixture) | ◑ | xP v0 built (ADR-006/007); **no uncertainty**, not yet "first-class" |
| xP as single source of truth downstream | ◑ | xP is one objective among several, not the sole spine |

### Phase 3 — Decision Support Engine

| Item | Status | Where / why |
|---|:--:|---|
| Expected minutes (xMins) & rotation | ⬜ | Deferred → P3. *Seed:* availability filter (S22, ADR-023) |
| Captain suggestion algorithm | ⬜ | Deferred → P3 (xP/optimiser primitives exist) |
| Transfer recommendation engine | ⬜ | Deferred → P3 |
| Team analyser (upload manager ID) | ⬜ | Deferred → P3. *Seed:* saved squad (S23, ADR-024) |
| Live event layer (re-rank on news) | ⬜ | Deferred → P3 |

### Phase 4 — AI & Natural-Language Layer

| Item | Status | Where / why |
|---|:--:|---|
| Grounded RAG pipeline | ⬜ | Deferred → P4 |
| Chat interface / query parser | ⬜ | Deferred → P4 |
| Strategy / decision justification | ⬜ | Deferred → P4 |

### Phase 5 — Advanced Optimisation

| Item | Status | Where / why |
|---|:--:|---|
| Integer-programming solver (budget/position) | ✅ | S7, ADR-008 (PuLP) |
| Full 15-man squad generation | ✅ | S11, ADR-012 (wildcard-style horizon) |
| Chip optimisers (WC/FH/BB/TC) | ⬜ | Deferred → P5 (15-man exists; chip logic not) |
| Multi-week horizon (3–6 GW) | ◑ | xP horizon ✅ (ADR-007); **decaying weights** ⬜ |
| Transfer-path simulation (−4 vs roll) | ⬜ | Deferred → P5 |

### Cross-Cutting

| Item | Status | Where / why |
|---|:--:|---|
| Evaluation & feedback loops, golden GWs | ⬜ | Deferred → P2+ (227 unit tests exist; no outcome-tracking) |
| FPL = source of truth | ✅ | ADR-010 (FPL required, ClubElo best-effort) |
| External sources degrade gracefully | ✅ | ADR-020, ADR-021 |
| Version external data sources | ⬜ | Deferred → P2 |
| Success metrics defined early | ⬜ | Deferred → P2 (define before decision-support) |

---

## Direction 2 — every sprint, accounted for (no orphans)

| Sprint | Delivered | Maps to |
|:--:|---|---|
| 001 | Foundation slice: FPL client + SQLite + console table | P1 ingestion / cache / UI-as-CLI |
| 002 | CLI + Analytics layers (ADR-003) | P1 architecture (CLI ⟶ substitutes web UI) |
| 003 | Fixtures entity + FDR (ADR-004) | P1 schema + P2 FDR |
| 004 | Team strengths + overall FDR (ADR-005) | P2 custom FDR |
| 005 | Expected Points v0 (ADR-006) | P2 xP engine |
| 006 | Multi-week xP horizon (ADR-007) | P5 multi-week / P2 xP |
| 007 | ILP squad selector (ADR-008) | **P5 solver** |
| 008 | Include/exclude + name resolver (ADR-009) | P5 optimiser |
| 009 | ClubElo external source + Elo FDR (ADR-010) | P2 FDR + cross-cutting degradation |
| 010 | Pluggable objective points/value/xp (ADR-011) | P5 / P2 |
| 011 | Full 15-man squad (ADR-012) | P5 chip (wildcard-style 15) |
| 012 | Declared bench (ADR-013) | P5 optimiser |
| 013 | Flexible formations (ADR-014) | P5 optimiser |
| 014 | Expected goals xG/xA/xGI/xGC (ADR-015) | **P2 metric ingestion** |
| 015 | soccerdata spike — deferred (ADR-016) | P2 ingestion (evaluation) |
| 016 | Over/under-performance (ADR-017) | P2 analytics *(beyond original bullets)* |
| 017 | Defensive Contribution / DefCon (ADR-018) | P2 (anticipated new BPS rules) |
| 018 | Clean-sheet xGC lens (ADR-019) | P2 defensive analytics |
| 019 | ClubElo retry (ADR-020) | Cross-cutting reliability |
| 020 | Importance-scaled retry (ADR-021) | Cross-cutting reliability |
| 021 | Validate legal bench (ADR-022) | P5 optimiser |
| 022 | Player availability (ADR-023) | **P3 seed** (xMins-adjacent) / P2 |
| 023 | Saved squad — user state (ADR-024) | **P3 seed** (team-analyser precursor) |
| 024 | Shared table renderer (ADR-025) | P1 UI / tech-debt |

**All 24 sprints map; no orphans in either direction.**

---

## Summary — what "Phase 1 — CLI Analytics MVP" means

**Delivered:** a working CLI FPL analytics & optimisation tool — 12 commands, 25 ADRs (001–025,
the build) + ADR-026 closing the phase, 227 tests, FPL (required, retries hard) + ClubElo
(best-effort, degrades). It covers the **analytical and optimisation heart** of the original
Phases 1/2/5.

**Explicitly deferred to Phase 2+ (nothing dropped):** web dashboard UI, CI/CD + pre-commit,
session auth (`/my-team/`), historical/price-trend data + backfills, cache TTLs / countdown timer,
source versioning; price predictor, form + rolling trends, Attack/Defence FDR split, a first-class
uncertainty-aware xP engine; **all** of decision-support (xMins, captain, transfers, team
analyser, live events), AI/RAG, chip optimisers + transfer-path simulation, and evaluation/success
metrics.

The reframed Roadmap carries every ⬜ / ◑ item above into Phase 2+; nice-to-haves live in
[`Backlog.md`](../Backlog.md).
