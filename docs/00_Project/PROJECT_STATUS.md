Current Phase: Phase 3 — Decision Support (captain + transfers shipped). Phase 1 MVP complete; Phase 2 first slice done
Current Sprint: Sprint 028 - Transfer Suggestions (✅ Complete, 3/3 stories, retro done). Sequence: 028 transfers ✅ → 029 team analyser → 030 data hardening
Current Story: None active — Sprint 029 (Team Analyser) next in the sequence
Next Milestone: Team Analyser — grade a saved squad's health / fixtures / weak spots over a horizon (compose xP + saved squads + availability)
Current Version: 0.0.1
Last Updated: 2026-08-03
Commands: refresh · history (--backfill) · table · search · filter · fdr (--type) · fixtures · xp · captain (--squad) · transfer (--squad/--bank/--next) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, fails fast)
Tests: 262 · ADRs: 30 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · captain + transfer recommend & explain (ADR-029/030)
Known issue: ClubElo API down since 2026-08-03 (their end — timeouts/502s; last-known Elo kept, degrades as designed). Re-check next session.
Deferred (→ later): multi-move transfer planner (hits vs roll); ceiling/differential captaincy; per-GW history + in-season xP blending (need GW1); web UI; AI/RAG (Phase 4)
