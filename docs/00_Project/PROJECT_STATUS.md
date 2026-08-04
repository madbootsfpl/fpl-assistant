Current Phase: Phase 4 — AI & Natural-Language Layer (grounded `ask`: five intents, verified). Phase 3 (decision support + xMins v0) complete; Phase 1 MVP done; Phase 2 first slice done
Current Sprint: Sprint 039 - Trust the numbers: sane low-evidence xP + transfer dedup + consistency (✅ Complete, 3/3 stories, retro done)
Current Story: None active — live options: more Phase 4 (further intents / chat / stronger verification), web UI (Phase 2), or Data Hardening (~GW1, also feeds the full Phase-5 xMins + partial-season baseline tuning). Owner to steer
Next Milestone: Owner to steer — more Phase 4, the web UI (Phase 2), or (at GW1, 2026-08-21) Data Hardening + the full probabilistic xMins (Phase 5)
Current Version: 0.0.1
Last Updated: 2026-08-04
Commands: refresh · history (--backfill) · ask · table · search · filter · fdr (--type) · fixtures · xp (--by-gameweek) · captain (--squad/--no-xmins) · transfer (--squad/--bank/--next/--count/--no-xmins) · analyse (--squad/--next/--sort/--no-xmins) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, intermittent) · local Ollama LLM (optional, for `ask`)
Tests: 365 · ADRs: 40 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · Data quality (ADR-040): low-evidence xP shrinks toward a replacement prior (no cameo projects like a star); transfer suggestions are disjoint (no repeated buy); `analyse`/start-bench share `best_legal_xi` · Phase 3: xMins v0 (ADR-038) · Phase 4: grounded `ask` answers five questions — captain · transfer · analyse · start/bench · compare (ADR-039), verified (ADR-037)
Known issue: ClubElo intermittent (timed out 2026-08-04 pm; up earlier same day) — best-effort, degrades; no blocker.
Deferred (→ later): more `ask` intents / a chat mode; Data Hardening (post-GW1: full backfill + per-GW history + form blending); multi-move transfer planner; ceiling captaincy; xMins v0 DONE (Sprint 037, ADR-038); the full probabilistic xMins model (Phase 5, post-GW1); web UI
