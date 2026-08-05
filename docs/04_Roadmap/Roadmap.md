# FPL Assistant Roadmap

*Consolidated 2026-08-05 (Sprint 050) into a single forward-looking page. Phase 1 was delivered as a
**CLI** (ADR-002/003), not the original web-first plan; that original 5-phase plan and its bullet-by-bullet
reconciliation live in git history and the per-sprint docs — this page looks **forward**.*

**Where we are:** a mature CLI FPL assistant — an analytics + optimisation core, a decision-support suite,
and a grounded natural-language layer (`ask` + `chat`). **49 ADRs · 421 tests · CI green.** Preseason (0
gameweeks; **GW1 deadline 2026-08-21**), so form/per-GW insight is still ahead.

**Status legend:** ✅ Done · ◑ Partial · ⬜ Not started

---

## ✅ Delivered

### Analytics & optimisation core (the CLI engine)
- **Data:** FPL API client (`bootstrap-static`, `fixtures`, `element-summary`) + SQLite cache (upsert,
  generic migrations). FPL is the source of truth; ClubElo is a best-effort second source that degrades
  gracefully (retry-then-degrade, importance-scaled). Past-season history backfill.
- **Analytics:** custom FDR (overall + ClubElo Elo), Points-per-£m value, **Expected Points (xP)** over a
  multi-week horizon, xG/xA/xGI/xGC, over/under-performance, Defensive Contribution, clean-sheet solidity.
- **One xP metric (ADR-041):** the optimiser and the decision layer share a single `decision_xp` recipe
  (baseline + a sane low-evidence fallback + xMins) — so a squad built on xP has no phantom free transfers.
- **Expected minutes (xMins) v0 (ADR-038):** `chance%` × a recency-weighted historical minutes share
  weights xP **default-on** at every decision edge; shown as expected minutes; `--no-xmins` opts out.
- **Optimisation:** an ILP squad selector (PuLP) — best XI or full 15, flexible formations, declared
  bench, include/exclude, pluggable objective; **archetypes** (`--cheap`/`--premium`/`--differential`,
  ADR-043/044) and **bench-aware** builds (`--weekly`/`--bench-boost`, ADR-045).
- **User state:** saved / reloadable squads (re-priced, with current injuries + departures).

### Decision support
- **`captain`** (ADR-029) — top picks by next-GW xP; opponent, venue, penalty duty.
- **`transfer`** (ADR-030) — best single legal upgrades, **ranked by XI improvement** (XI-gain via
  `best_xi_points`, ADR-046; `--raw` for the old ranking); a coordinated multi-move **plan** (`--count`,
  ADR-035).
- **`analyse`** (ADR-031) — projected XI xP over N GW (per-GW breakdown, ADR-032), weak links, injuries.

### Natural-language layer (grounded)
- **`ask`** — eight intents (captain · transfer · analyse · start/bench · compare · build-a-squad ·
  best-players · **fixtures**), all **analytics-decide, LLM-narrates**, every answer **verified** against
  the data (✓/⚠ trust line, ADR-037). The LLM (local Ollama) is optional — degrades to decision + facts.
- **`chat`** (ADR-047) — a conversational mode where follow-ups build on the last turn (why / next /
  what-about), still analytics-decided each turn.
- **`fixtures`** (ADR-048/049) — a league FDR ranking, a single team's schedule, or a **squad's players by
  their fixture run**; team names resolve or ask, never guess.

### Engineering
- **CI (GitHub Actions):** ruff + pytest on push (Py 3.13/3.14). Layered one-way architecture
  (`api → ingest → storage → analytics → ui → cli`); 49 ADRs; 421 offline tests; shared table renderer.

---

## ▶ Next — a thin web UI (Sprint 051)

A minimal, **read-only, local-only** web layer that **reuses the analytics/`ask` untouched** — the web as
a new *edge* over the same core (**the CLI stays the engine**). Proposed: **FastAPI + Jinja** (server-
rendered, no JS build), testable with `TestClient`. Deliberately small — a GW1-ready shell, not a full
interactive app. *(Discussed Sprint 050; approach to be gated at the sprint's start.)*

---

## Then — Data Hardening (post-GW1)

The substance that comes alive once the season runs (GW1 = 2026-08-21):
- ⬜ Full 567-player history backfill (can ride sooner) + **per-GW `history` ingestion** (empty preseason).
- ⬜ **In-season form** + rolling 3-GW vs 6-GW trends; blend form into xP.
- ◑ Attack/Defence FDR split + recent-form weighting (preseason strengths are 0 — ADR-005).
- ⬜ Price-change predictor (directional flags from net-transfer deltas — flags, not truth).

---

## Later — advanced optimisation & evaluation

- ⬜ **Chip optimisers** — Wildcard / Free Hit (the 15-man build exists), Bench Boost (bench-aware exists),
  Triple Captain.
- ⬜ **Probabilistic xMins (the full ML model)** — per-fixture expected-minutes *probabilities* from
  schedule density, European congestion, rotation profiles. Needs in-season per-GW minutes to train
  (post-GW1) + external European-fixture data + a real ML effort — a later, data-gated phase. The rigorous
  successor to xMins v0.
- ⬜ Multi-week horizon **decay weights**; transfer-path simulation (a −4 now vs rolling).
- ⬜ **Evaluation & feedback loops** — did the suggested captain beat the template? Golden-gameweek
  regression; success metrics (xP calibration, captain hit-rate, net season points). *Critical before
  fully trusting recommendations.*

---

## Infrastructure (carried)

- ⬜ Session/cookie **auth** for user-specific data (`/my-team/{id}/`) — unlocks a manager-ID fetch in
  `analyse`/`transfer`.
- ⬜ **Source versioning** — formalise "version all external sources"; confidence scoring on fallback.
- ⬜ Cache TTLs + a gameweek countdown.

---

## Guiding principles (unchanged)

- **The CLI stays the engine** — new surfaces (web) are edges over the same analytics; generic core, policy
  at the edge.
- **Analytics decide; the LLM only narrates** — grounded, verified, optional.
- **FPL is the source of truth**; external sources degrade gracefully.
- **Learn by building, sprint by sprint** — a gate (ADR) per feature; simple over clever.
