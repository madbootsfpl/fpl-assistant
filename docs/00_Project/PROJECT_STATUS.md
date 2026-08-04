Current Phase: Phase 3 — Decision Support (captain · transfer · analyse trio complete; analyser enhanced). Phase 1 MVP done; Phase 2 first slice done
Current Sprint: Sprint 034 - Deeper Phase 4: per-GW transfer plans + a table in `ask` (✅ Complete, 3/3 stories, retro done)
Current Story: None active — live options: more Phase 4, web UI (Phase 2), or Data Hardening (~GW1). Owner to steer
Next Milestone: Phase 4 GREEN-LIT by the spike (ADR-033) — build a real `ask` (intent router + grounding contract) when prioritised; local Ollama, analytics-decide/LLM-narrate, pre-humanised facts
Current Version: 0.0.1
Last Updated: 2026-08-04
Commands: refresh · history (--backfill) · ask · table · search · filter · fdr (--type) · fixtures · xp (--by-gameweek) · captain (--squad) · transfer (--squad/--bank/--next) · analyse (--squad/--next/--sort) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, intermittent) · local Ollama LLM (optional, for `ask`)
Tests: 304 · ADRs: 36 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · Phase 4: grounded `ask` + multi-transfer plans with per-GW columns; `ask` shows a table + summary (ADR-034/035/036)
Known issue: ClubElo intermittent (timed out 2026-08-04 pm; up earlier same day) — best-effort, degrades; no blocker.
Deferred (→ later): more `ask` intents / a chat mode; Data Hardening (post-GW1: full backfill + per-GW history + form blending); multi-move transfer planner; ceiling captaincy; xMins; web UI
