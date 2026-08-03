Current Phase: Sprint 019 COMPLETE — between sprints
Current Sprint: Sprint 019 - ClubElo Resilience (✅ Complete, 2/2 stories, retro done)
Current Story: None active — ready to plan Sprint 020
Next Milestone: Sprint 020 - FPL-client retry, a combined defensive value, or another backlog pick
Current Version: 0.0.1
Last Updated: 2026-08-03
Commands: refresh · table · search · filter · fdr (--type) · fixtures · xp · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective[points|value|xp|xgi]/--include/--exclude)
Sources: FPL (required) + ClubElo (best-effort, retry-with-backoff)
Tests: 194 · ADRs: 20 · ClubElo resilient to transient 502s
Known issue: ClubElo API read-timing-out since 2026-08-03 (their end; retry+degrade working, last-known Elo kept). Re-check next session.
Deferred: FBref xG/xA; flexible formations (XI); two-tier bench (rejected, ADR-012); form/attack-defence FPL data (preseason)
