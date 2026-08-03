Current Phase: Sprint 024 COMPLETE — build phase feature-complete + tech debt paid down
Current Sprint: Sprint 024 - Shared Table Renderer (✅ Complete, 3/3 stories, retro done)
Current Story: None active — decide the next phase (web view? live data? shared squad renderer?) or pause
Next Milestone: Sprint 025 - open a new phase, or take a remaining small closer (owner to steer)
Current Version: 0.0.1
Last Updated: 2026-08-03
Commands: refresh · table · search · filter · fdr (--type) · fixtures · xp · xg · overperf · defcon · cleansheet · squad (--full/--bench/--formation/--objective/--include[-unavailable]/--exclude/--save/--load)
Sources: FPL (required, retries hard) + ClubElo (best-effort, fails fast)
Tests: 227 · ADRs: 25 · all 5 ranking views share one renderer (ui/_table.py: Col + render_rows), output byte-identical
Known issue: ClubElo API down since 2026-08-03 (their end — now 502s in ~9s; last-known Elo kept). Re-check next session.
Deferred: shared *squad* renderer + availability flags in views (small closers); FBref xG; two-tier bench (rejected, ADR-012); form/attack-defence FPL data (preseason)
