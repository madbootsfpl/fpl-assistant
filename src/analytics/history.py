"""Player history (Sprint 117, ADR-027/060) — assemble a player's **past-season** summaries + **this-season
per-GW** rows into a display shape. Pure + empty-safe; a **read-view lens** — it never feeds `decision_xp`.
Past seasons are real preseason; the per-GW trend fills once the season starts (GW1).
"""


def _get(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _pp90(points, minutes) -> float:
    """Points per 90 minutes — a minutes-fair rate. 0 when no minutes (avoids a divide-by-zero)."""
    return round(points / (minutes / 90), 1) if minutes else 0.0


def player_history(player, seasons, gameweeks) -> dict:
    """A player's history for display: normalised past-season rows + this-season per-GW rows.

    `player` is the player row (for the header); `seasons` / `gameweeks` are the stored rows (from
    `Storage.get_history_past` / `Storage.get_history`). Empty-safe — a player with no backfill yields empty
    lists. The price columns are deliberately omitted until the stored cost units are verified.
    """
    out_seasons = []
    for r in seasons or []:
        pts, mins = _get(r, "total_points") or 0, _get(r, "minutes") or 0
        start, end = _get(r, "start_cost"), _get(r, "end_cost")          # already £m (ingest converts tenths)
        out_seasons.append({
            "season": _get(r, "season_name") or "?",
            "points": pts,
            "minutes": mins,
            "starts": _get(r, "starts"),
            "pp90": _pp90(pts, mins),
            "xgi": _get(r, "expected_goal_involvements"),
            "xgc": _get(r, "expected_goals_conceded"),
            "start_cost": start,
            "end_cost": end,
            "change": round(end - start, 1) if (start is not None and end is not None) else None,
        })
    out_gw = [{"round": _get(r, "round"), "points": _get(r, "total_points") or 0,
               "minutes": _get(r, "minutes") or 0} for r in (gameweeks or [])]
    return {"player": player, "seasons": out_seasons, "gameweeks": out_gw}


def align_seasons(hist_a, hist_b, *, key: str = "points") -> list[dict]:
    """Outer-join two players' seasons on the season label for a side-by-side comparison (US-312).

    `hist_a`/`hist_b` are `player_history(...)` results. Returns `[{"season", "a", "b"}]` sorted by season
    label — `a`/`b` are each player's value for `key` (e.g. "points"), or `None` for a season only one played.
    Pure/display; nothing here feeds `decision_xp`.
    """
    a_by = {s["season"]: s.get(key) for s in hist_a.get("seasons", [])}
    b_by = {s["season"]: s.get(key) for s in hist_b.get("seasons", [])}
    return [{"season": season, "a": a_by.get(season), "b": b_by.get(season)}
            for season in sorted(a_by.keys() | b_by.keys())]
