Current Phase: Phase 3 — Decision Support (captain · transfer · analyse trio complete; analyser enhanced). Phase 1 MVP done; Phase 2 first slice done
Current Sprint: Sprint 037 - Expected minutes (xMins) v0 (✅ Complete, 3/3 stories, retro done)
Current Story: None active — live options: more Phase 4, web UI (Phase 2), or Data Hardening (~GW1, also feeds the full Phase-5 xMins). Owner to steer
Next Milestone: Phase 4 GREEN-LIT by the spike (ADR-033) — build a real `ask` (intent router + grounding contract) when prioritised; local Ollama, analytics-decide/LLM-narrate, pre-humanised facts
Current Version: 0.0.1
Last Updated: 2026-08-04
Commands: refresh · history (--backfill) · ask · table · search · filter · fdr (--type) · fixtures · xp (--by-gameweek) · captain (--squad/--no-xmins) · transfer (--squad/--bank/--next/--count/--no-xmins) · analyse (--squad/--next/--sort/--no-xmins) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, intermittent) · local Ollama LLM (optional, for `ask`)
Tests: 343 · ADRs: 38 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · Phase 3: xMins v0 — recommendations weight xP by expected minutes (chance% × historical minutes share, shown as minutes; `--no-xmins` for raw; ADR-038) · Phase 4: grounded `ask` (verified — a ✓/⚠ trust line, ADR-037); `ask "analyse"` shows the full squad table (per-GW + xMins + weak links)
Known issue: ClubElo intermittent (timed out 2026-08-04 pm; up earlier same day) — best-effort, degrades; no blocker.
Deferred (→ later): more `ask` intents / a chat mode; Data Hardening (post-GW1: full backfill + per-GW history + form blending); multi-move transfer planner; ceiling captaincy; xMins v0 DONE (Sprint 037, ADR-038); the full probabilistic xMins model (Phase 5, post-GW1); web UI
