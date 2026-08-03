Current Phase: Phase 2 — Infrastructure, Data Depth & Analytics Hardening (Phase 1 CLI Analytics MVP complete, ADR-026)
Current Sprint: Sprint 026 - Historical Trend Data & Enriched xP (✅ Complete, 4/4 stories, retro done)
Current Story: None active — Sprint 027 to pick the next Phase 2 / Phase 3 direction
Next Milestone: Owner to steer — decision-support (captain picks on the better xP), web UI, or data hardening (full backfill / per-GW once GW1 plays)
Current Version: 0.0.1
Last Updated: 2026-08-03
Commands: refresh · history (--backfill) · table · search · filter · fdr (--type) · fixtures · xp · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL — bootstrap-static + fixtures + element-summary (past-season history, ADR-027) — required, retries hard · ClubElo (best-effort, fails fast)
Tests: 242 · ADRs: 28 · CI: GitHub Actions (ruff + pytest on push, Py 3.13/3.14) · xP uses a multi-season baseline rate (ADR-028)
Known issue: ClubElo API down since 2026-08-03 (their end — timeouts/502s; last-known Elo kept, degrades as designed). Re-check next session.
Deferred (→ later): per-GW history + in-season xP blending (need GW1 played); web UI; session auth; Attack/Def FDR split; decision-support (Phase 3); AI/RAG (Phase 4)
