# Backlog

Captured ideas not yet scheduled into a sprint.

## Enhancements

- **Squad selector: include / exclude players** — let the user force up to ~4 players
  IN (favourites) or OUT (dislikes), and have the optimiser build the best legal XI
  around them. From Tony's Sprint 007 reflection. Clean in ILP: fix `pick[p] = 1` for
  included players and `pick[p] = 0` for excluded ones, then solve as normal. Data-
  supported now (no new data). Strong Sprint 008 candidate.

- **`xp` per-gameweek breakdown** — show xP for each gameweek in the horizon, not just
  the total (e.g. a small `GW1 GW2 GW3 …` mini-row per player). From Tony's Sprint 006
  reflection. Note: FPL only publishes `ep_next` (next GW), so there is no FPL
  multi-week total to show alongside.
- **`xp`/`squad` objective toggle** — let the optimiser/xp use `total_points`, `xp`, or
  `value` as the objective.
- **Flexible formations** for the squad selector (beyond 1-4-4-2) — let the *starting XI*
  take any legal shape (DEF 3–5, MID 2–5, FWD 1–3), with an optional `--formation 3-5-2`
  pin. Deferred from Sprint 011 to keep it focused; a clean stand-alone next sprint.
- ~~**Full 15-man squad** optimisation (2 GK, 5 DEF, 5 MID, 3 FWD, £100M)~~ — **DONE**
  (Sprint 011, `squad --full`, ADR-012). Simple model; the manager picks the bench via
  `--include`. The two-tier "solver picks the bench" model was considered and rejected.

## Tech debt

- **Migrate to the PuLP 4.0 API** — use `prob.add_variable(...)` / `COIN_CMD` instead of
  `LpVariable(...)` / `PULP_CBC_CMD` (currently the 4.0 deprecation notices are
  scope-suppressed in `src/analytics/optimizer.py`).

## Deferred (data-dependent — need season-start data)

- Richer xP: recent `form` + expected minutes.
- Attack/Defence FDR split (needs `strength_attack_*` / `strength_defence_*`).
