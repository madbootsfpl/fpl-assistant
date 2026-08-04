Current Phase: Phase 3 — Decision Support (captain · transfer · analyse trio complete; analyser enhanced). Phase 1 MVP done; Phase 2 first slice done
Current Sprint: Sprint 030 - Analyser Enhancements: per-GW xP + sort by xP (✅ Complete, 3/3 stories, retro done)
Current Story: None active — Data Hardening queued for ~GW1 (2026-08-21); owner to steer timing/next direction
Next Milestone: Data Hardening (post-GW1): full 567-player backfill + per-GW history + in-season xP form blending
Current Version: 0.0.1
Last Updated: 2026-08-04
Commands: refresh · history (--backfill) · table · search · filter · fdr (--type) · fixtures · xp (--by-gameweek) · captain (--squad) · transfer (--squad/--bank/--next) · analyse (--squad/--next/--sort) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, recovered 2026-08-04)
Tests: 279 · ADRs: 32 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · per-GW xP breakdown in analyse + xp (ADR-032)
Known issue: none open. (ClubElo recovered 2026-08-04 after a 2026-08-03 outage — refresh pulls Elo again; retry-then-degrade held throughout.)
Deferred (→ later): Data Hardening (post-GW1: full backfill + per-GW history + form blending); multi-move transfer planner; ceiling captaincy; xMins; web UI; AI/RAG (Phase 4)
