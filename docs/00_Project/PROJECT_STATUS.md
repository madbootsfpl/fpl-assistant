Current Phase: Phase 3 — Decision Support (captain · transfer · analyse trio COMPLETE). Phase 1 MVP done; Phase 2 first slice done
Current Sprint: Sprint 029 - Team Analyser (✅ Complete, 3/3 stories, retro done). Sequence: 028 transfers ✅ → 029 analyser ✅ → 030 data hardening
Current Story: None active — Sprint 030 (Data Hardening) is the last in the sequence (per-GW/form partly gated on GW1 being played)
Next Milestone: Data hardening — full 567-player history backfill; per-GW history + in-season xP blending once the season starts
Current Version: 0.0.1
Last Updated: 2026-08-04
Commands: refresh · history (--backfill) · table · search · filter · fdr (--type) · fixtures · xp · captain (--squad) · transfer (--squad/--bank/--next) · analyse (--squad/--next) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, fails fast)
Tests: 271 · ADRs: 31 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · captain·transfer·analyse recommend & explain, cross-linked (ADR-029/030/031)
Known issue: ClubElo API down since 2026-08-03 (their end — timeouts/502s; last-known Elo kept, degrades as designed). Re-check next session.
Deferred (→ later): full history backfill + per-GW/in-season blending (Sprint 030; per-GW needs GW1); multi-move transfer planner; ceiling captaincy; xMins; web UI; AI/RAG (Phase 4)
