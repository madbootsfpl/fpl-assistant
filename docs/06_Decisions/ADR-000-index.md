# ADR Index

An index of all Architectural Decision Records in this project. Add a row for each
new ADR as it is created.

| ADR | Title | Status |
|-----|-------|--------|
| [001](./ADR-001-single-user-vs-multi-user.md) | Single-user vs Multi-user architecture | Accepted |
| [002](./ADR-002-ui-approach.md) | UI approach | Accepted |
| [003](./ADR-003-cli-approach.md) | Command-line interface approach | Accepted |
| [004](./ADR-004-fixtures-and-fdr.md) | Fixtures data model & FDR approach | Accepted |
| [005](./ADR-005-custom-fdr.md) | Custom (overall) fixture difficulty | Accepted |
| [006](./ADR-006-expected-points-v0.md) | Expected Points (xP v0) | Accepted |
| [007](./ADR-007-multi-week-xp.md) | Multi-week xP (fixture horizon) | Accepted |
| [008](./ADR-008-squad-selector.md) | Optimal squad selector (ILP) | Accepted |
| [009](./ADR-009-squad-include-exclude.md) | Squad selector include / exclude | Accepted |
| [010](./ADR-010-clubelo-external-source.md) | ClubElo — first external data source | Accepted |
| [011](./ADR-011-squad-objective.md) | Squad objective toggle (points/value/xp) | Accepted |
| [012](./ADR-012-full-squad.md) | The full 15-man squad (`squad --full`) | Accepted |
| [013](./ADR-013-declared-bench.md) | A declared bench (`squad --bench`) | Accepted |
| [014](./ADR-014-flexible-formations.md) | Flexible formations (`squad --formation`) | Accepted |
| [015](./ADR-015-expected-goals.md) | Expected goals (xG/xA/xGI) from the FPL API | Accepted |
| [016](./ADR-016-soccerdata-evaluation.md) | soccerdata as a data source — **Defer** | Accepted |
| [017](./ADR-017-over-under-performance.md) | Over/under-performance (expected vs actual attacking points) | Accepted |
| [018](./ADR-018-defensive-contribution.md) | Defensive Contribution (DefCon reliability) | Accepted |
| [019](./ADR-019-clean-sheet-solidity.md) | Clean-sheet / defensive-solidity lens (xGC) | Accepted |
| [020](./ADR-020-clubelo-retry.md) | ClubElo retry-with-backoff (transient failures) | Accepted |
| [021](./ADR-021-importance-scaled-retry.md) | Importance-scaled retry (FPL tries hard, ClubElo fails fast) | Accepted |
| [022](./ADR-022-validate-legal-bench.md) | Validate a legal bench (warn, not block) | Accepted |
| [023](./ADR-023-player-availability.md) | Player availability (skip injured; opt-out) | Accepted |
| [024](./ADR-024-saved-squad.md) | Saved / persistent squad (user state, JSON) | Accepted |
| [025](./ADR-025-shared-table-renderer.md) | Shared table renderer (`Col` + `render_rows`) | Accepted |
| [026](./ADR-026-phase1-cli-mvp.md) | Declare Phase 1 (CLI Analytics MVP) complete; reframe the Roadmap | Accepted |
| [027](./ADR-027-historical-past-seasons.md) | Historical past-season data (`history --backfill`) | Accepted |
| [028](./ADR-028-xp-historical-baseline.md) | xP historical baseline (multi-season rate) | Accepted |
| [029](./ADR-029-captain-suggestions.md) | Captain suggestions (recommend + explain; xP, GK-excluded) | Accepted |
| [030](./ADR-030-transfer-suggestions.md) | Transfer suggestions (best single legal upgrades; xP gain, `--bank`) | Accepted |
| [031](./ADR-031-team-analyser.md) | Team Analyser (a saved squad's health check; indicators, not a grade) | Accepted |
| [032](./ADR-032-per-gameweek-xp.md) | Per-gameweek xP breakdown (+ `analyse --sort xp`) | Accepted |
| [033](./ADR-033-llm-grounded-narration-spike.md) | LLM grounded-narration spike (local Ollama; analytics decide, LLM narrates) | Accepted |
| [034](./ADR-034-ask-command-grounded-nl.md) | The `ask` command — grounded NL answers (routing; LLM optional) | Accepted |
| [035](./ADR-035-multi-transfer-plan.md) | Multi-transfer plan (coordinated, greedy; `transfer --count` / `ask` N transfers) | Accepted |
