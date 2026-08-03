Current Phase: Phase 3 — Decision Support (open; captain suggestions shipped). Phase 1 MVP complete; Phase 2 first slice done
Current Sprint: Sprint 027 - Captain Suggestions (✅ Complete, 3/3 stories, retro done)
Current Story: None active — Sprint 028 to pick the next Phase 3 feature (transfers / team analyser) or data hardening
Next Milestone: Owner to steer — transfer suggestions or a team analyser (compose xP + saved squads), or data hardening (full backfill / per-GW once GW1 plays)
Current Version: 0.0.1
Last Updated: 2026-08-03
Commands: refresh · history (--backfill) · table · search · filter · fdr (--type) · fixtures · xp · captain (--squad/--limit/--type) · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history) — required, retries hard · ClubElo (best-effort, fails fast)
Tests: 249 · ADRs: 29 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · captain picks recommend + explain (ADR-029)
Known issue: ClubElo API down since 2026-08-03 (their end — timeouts/502s; last-known Elo kept, degrades as designed). Re-check next session.
Deferred (→ later): ceiling/differential captaincy (needs variance data); per-GW history + in-season xP blending (need GW1 played); web UI; transfers/team analyser (Phase 3); AI/RAG (Phase 4)
