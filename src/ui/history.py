"""Console rendering for a player's history (Sprint 117, ADR-027/060).

A past-season summary table + a this-season per-GW trend (which fills at GW1). Built on the shared table
renderer (ADR-025). Pure formatting over `analytics.player_history`; display-only.
"""

from ._table import Col, render_rows


def _price(r) -> str:
    """`£start→end` (both £m), or "—" when a cost is missing (US-297)."""
    if r.get("start_cost") is None or r.get("end_cost") is None:
        return "—"
    return f"£{r['start_cost']:.1f}→{r['end_cost']:.1f}"


_SEASON_COLS = [
    Col("Season", 9, "<", lambda r: str(r["season"])),
    Col("Pts", 5, ">", lambda r: str(r["points"])),
    Col("Mins", 6, ">", lambda r: str(r["minutes"])),
    Col("Start", 6, ">", lambda r: str(r["starts"]) if r["starts"] is not None else "—"),
    Col("Pts/90", 7, ">", lambda r: f"{r['pp90']:.1f}"),
    Col("xGI", 6, ">", lambda r: f"{r['xgi']:.1f}" if r["xgi"] is not None else "—"),
    Col("xGC", 6, ">", lambda r: f"{r['xgc']:.1f}" if r["xgc"] is not None else "—"),
    Col("£m", 13, ">", _price),
]

_GW_COLS = [
    Col("GW", 4, ">", lambda r: str(r["round"])),
    Col("Pts", 5, ">", lambda r: str(r["points"])),
    Col("Mins", 6, ">", lambda r: str(r["minutes"])),
]


def render_player_history(hist) -> str:
    """`hist` is an `analytics.player_history` dict. A season table + a per-GW trend (or a 'fills at GW1' note).
    Empty-safe: no player → a nudge; a known player with no backfill → a clear 'run history --backfill' note."""
    player = hist.get("player")
    if not player:
        return "Name a player, e.g. `history Haaland`."
    name = player["web_name"]
    seasons, gws = hist["seasons"], hist["gameweeks"]
    if not seasons and not gws:
        return (f"No history stored for {name} yet — run `history --backfill` to fetch past-season data "
                "(a few minutes; per-GW form fills once the season starts).")

    lines = [f"History — {name} ({player['team']}, {player['position']})", ""]
    if seasons:
        lines += ["Past seasons (most recent last):", ""]
        lines += render_rows(seasons, _SEASON_COLS)
        lines.append("`Pts/90` = points per 90 minutes · `xGI`/`xGC` = expected goal involvements / conceded.")
    if gws:
        lines += ["", f"This season — per gameweek ({len(gws)} played):", ""]
        lines += render_rows(gws, _GW_COLS)
    else:
        lines += ["", "Per-GW form fills once the season starts (GW1) — run `history --backfill` after GW1."]
    return "\n".join(lines)
