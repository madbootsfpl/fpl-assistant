Current Phase: Sprint 020 COMPLETE — between sprints
Current Sprint: Sprint 020 - Resilience Round 2 (✅ Complete, 2/2 stories, retro done)
Current Story: None active — ready to plan Sprint 021
Next Milestone: Sprint 021 - circuit breaker (if ClubElo persists), combined defensive value, or shared renderer
Current Version: 0.0.1
Last Updated: 2026-08-03
Commands: refresh · table · search · filter · fdr (--type) · fixtures · xp · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective[points|value|xp|xgi]/--include/--exclude)
Sources: FPL (required, retries hard) + ClubElo (best-effort, fails fast)
Tests: 197 · ADRs: 21 · importance-scaled retry (FPL 2/10s, ClubElo 1/5s)
Known issue: ClubElo API read-timing-out since 2026-08-03 (their end; now degrades in ~10s not ~31s; last-known Elo kept). Re-check next session.
Deferred: FBref xG/xA; flexible formations (XI); two-tier bench (rejected, ADR-012); form/attack-defence FPL data (preseason)
