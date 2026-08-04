Current Phase: Phase 3 — Decision Support (captain · transfer · analyse trio complete; analyser enhanced). Phase 1 MVP done; Phase 2 first slice done
Current Sprint: Sprint 036 - Fix the `ask analyse` table + assess xMins (✅ Complete, 2/2 stories, retro done)
Current Story: None active — live options: build xMins v0 (now assessed, Phase 3), more Phase 4, web UI (Phase 2), or Data Hardening (~GW1). Owner to steer
Next Milestone: Phase 4 GREEN-LIT by the spike (ADR-033) — build a real `ask` (intent router + grounding contract) when prioritised; local Ollama, analytics-decide/LLM-narrate, pre-humanised facts
Current Version: 0.0.1
Last Updated: 2026-08-04
Commands: refresh · history (--backfill) · ask · table · search · filter · fdr (--type) · fixtures · xp (--by-gameweek) · captain (--squad) · transfer (--squad/--bank/--next) · analyse (--squad/--next/--sort) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, intermittent) · local Ollama LLM (optional, for `ask`)
Tests: 313 · ADRs: 37 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · Phase 4: grounded `ask` (verified — a ✓/⚠ trust line, ADR-037); `ask "analyse"` now shows the full squad table (per-GW + weak links); multi-transfer plans with per-GW columns
Known issue: ClubElo intermittent (timed out 2026-08-04 pm; up earlier same day) — best-effort, degrades; no blocker.
Deferred (→ later): more `ask` intents / a chat mode; Data Hardening (post-GW1: full backfill + per-GW history + form blending); multi-move transfer planner; ceiling captaincy; xMins — assessed (Sprint 036): a lightweight v0 (Phase 3) then a full ML model (Phase 5, post-GW1); web UI
