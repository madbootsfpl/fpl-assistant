# Backlog

Captured ideas not yet scheduled into a sprint. *(The larger unbuilt features now live in the
reframed [Roadmap](04_Roadmap/Roadmap.md) Phase 2+; this file holds the small nice-to-haves and
tech-debt.)*

## Enhancements

- **Bench order** — which bench player subs on first (Sprint 012 sequel).
- **Availability flags in the ranking views** — surface injury/suspension flags in
  `table`/`xg`/etc. the way `squad` does (Sprint 022 sequel).
- **Ceiling / "differential" captaincy** — `captain` (Sprint 027, ADR-029) ranks by *mean* xP,
  which favours nailed-on premiums. A ceiling/variance view would surface high-upside punts — but
  it needs variance/form data we don't have yet. Revisit once in-season data accrues.
- **Multi-move transfer *planner*** — `transfer` (Sprint 028, ADR-030) suggests the best *single*
  swaps. A planner would optimise a *sequence* over a horizon: taking a −4 hit vs rolling a free
  transfer, banking transfers, two-moves-this-week maths. A bigger optimisation problem (and it
  wants the real bank + xMins) — a natural late-Phase-3 / Phase-5 feature.

### Done (kept for the trail)

- ~~Include / exclude players~~ — **DONE** (Sprint 008, ADR-009).
- ~~`xp`/`squad` objective toggle~~ — **DONE** (Sprint 010, ADR-011).
- ~~Full 15-man squad~~ — **DONE** (Sprint 011, `squad --full`, ADR-012).
- ~~Declared bench~~ — **DONE** (Sprint 012, `squad --bench`, ADR-013).
- ~~Flexible formations~~ — **DONE** (Sprint 013, `squad --formation` + flexible default,
  ADR-014). Ranges (DEF 3–5, MID 2–5, FWD 1–3); the bench-implied shape shown in `--full`.
- ~~Validate a declared bench yields a legal XI~~ — **DONE** (Sprint 021, `legal_xi_issues`,
  ADR-022). Warns (not blocks) when a full 4-man bench leaves an illegal XI; reuses `XI_FLEX`.
- ~~Saved / persistent squad~~ — **DONE** (Sprint 023, `squad --save`/`--load`, ADR-024).
  User state in `data/squads.json` (gitignored), separate from the FPL cache; reload re-prices +
  flags injuries + notes departures.
- ~~`xp` per-gameweek breakdown~~ — **DONE** (Sprint 030, ADR-032). A `by_gameweek` breakdown on
  `player_xp` (a faithful decomposition of the total); shown in `analyse` and `xp --by-gameweek`,
  plus `analyse --sort xp`. (From Tony's Sprint 006 reflection.)

## Validated, deferred

- **soccerdata / npXG** — evaluated in Sprint 015 ([ADR-016](06_Decisions/ADR-016-soccerdata-evaluation.md)).
  Matching works (~95% FPL↔Understat) and npXG is real, **but** the value is narrow
  (penalties score points in FPL, so penalty-inclusive xG is the relevant signal) and the
  cost is high (14 → 72 packages incl. a selenium/pandas stack, scraping fragility, a
  season-alignment trap). **Deferred.** Revisit only if a decision-driving need appears
  that FPL can't meet — and prefer a *lightweight* direct Understat fetch over the full
  library. Evidence: `spikes/015-soccerdata/`.

## Tech debt

- **Migrate to the PuLP 4.0 API** — use `prob.add_variable(...)` / `COIN_CMD` instead of
  `LpVariable(...)` / `PULP_CBC_CMD` (currently the 4.0 deprecation notices are
  scope-suppressed in `src/analytics/optimizer.py`).
- **Shared *squad* renderer** — `render_squad` / `render_loaded_squad` still duplicate a little
  row logic. The ranking views were unified in Sprint 024 (`ui/_table.py`), but the squad views
  are a different shape (position groups, bench, markers) and were left out — fold them in later.
- ~~Shared table renderer for the ranking views~~ — **DONE** (Sprint 024, `ui/_table.py`
  `Col` + `render_rows`, ADR-025). Five near-duplicate renderers → one; output byte-identical.

## Deferred (data-dependent — need season-start data)

- Richer xP: recent `form` + expected minutes.
- Attack/Defence FDR split (needs `strength_attack_*` / `strength_defence_*`).
- **Per-GW history ingestion** — `element-summary`'s `history` (this-season per-GW) is empty
  preseason (Sprint 026, ADR-027). Ingest it once gameweeks start playing (same endpoint/command);
  it enables within-season form/rolling trends. A `history <player>` season-trend view could follow.
- **Data Hardening (a scheduled sprint, ~GW1)** — the owner's "030" that got reordered: a full
  567-player history backfill (doable any time) + per-GW `history` ingestion + in-season xP **form
  blending**. The form/per-GW parts need the season started (GW1 deadline 2026-08-21), so this is a
  **post-GW1 sprint**; the full backfill can ride along or go sooner.
