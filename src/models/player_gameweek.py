"""Per-gameweek history model (ADR-060) — the current season, one row per player per GW.

From `element-summary/{id}/`'s **`history`** array (empty preseason; live from GW1). Unlike
`history_past` (past-season aggregates, keyed by the stable `element_code`), a per-GW row carries only
`element` — the *per-season* id — so the stable `element_code` is passed in from an id→code map. This is a
**current-season working set** keyed `(element_code, round)`: a new season re-backfills and overwrites
round-for-round, so no season name is stored (the payload doesn't carry one).

It feeds the in-season **form** term of `decision_xp` (ADR-060, US-197) — dormant until there's per-GW data.
"""

from dataclasses import dataclass


def _to_float(value):
    """Parse an FPL decimal-as-string to float, or None when absent/blank."""
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value):
    """Parse an FPL integer to int, or None when absent/blank (mirrors PlayerSeason)."""
    if value in (None, "", "None"):
        return None
    return int(value)


@dataclass
class PlayerGameweek:
    element_code: int
    round: int
    minutes: int | None = None
    total_points: int | None = None
    was_home: int | None = None       # 1/0 — FPL sends a bool
    opponent_team: int | None = None
    fixture: int | None = None
    kickoff_time: str | None = None
    # The match result — FPL gives the scoreline, not a W/D/L, so the caller derives it with `was_home`.
    team_h_score: int | None = None
    team_a_score: int | None = None
    # Per-gameweek returns. The season aggregates on `players` are a running total; these are the week itself,
    # which is what a trend line and a form dot need.
    goals_scored: int | None = None
    assists: int | None = None
    clean_sheets: int | None = None
    goals_conceded: int | None = None
    saves: int | None = None
    bonus: int | None = None
    bps: int | None = None
    xg: float | None = None
    xa: float | None = None
    xgi: float | None = None
    xgc: float | None = None
    ict_index: float | None = None
    influence: float | None = None
    creativity: float | None = None
    threat: float | None = None
    defcon: int | None = None
    value: int | None = None          # price that gameweek, in tenths (FPL's own unit)

    @classmethod
    def from_api(cls, raw: dict, element_code: int) -> "PlayerGameweek":
        """Build from one entry of `element-summary['history']`.

        The row has `element` (the season id), not the stable `code`, so `element_code` is passed in.
        """
        return cls(
            element_code=element_code,
            round=_to_int(raw.get("round")),
            minutes=_to_int(raw.get("minutes")),
            total_points=_to_int(raw.get("total_points")),
            was_home=1 if raw.get("was_home") else 0,
            opponent_team=_to_int(raw.get("opponent_team")),
            fixture=_to_int(raw.get("fixture")),
            kickoff_time=raw.get("kickoff_time"),
            team_h_score=_to_int(raw.get("team_h_score")),
            team_a_score=_to_int(raw.get("team_a_score")),
            goals_scored=_to_int(raw.get("goals_scored")),
            assists=_to_int(raw.get("assists")),
            clean_sheets=_to_int(raw.get("clean_sheets")),
            goals_conceded=_to_int(raw.get("goals_conceded")),
            saves=_to_int(raw.get("saves")),
            bonus=_to_int(raw.get("bonus")),
            bps=_to_int(raw.get("bps")),
            xg=_to_float(raw.get("expected_goals")),
            xa=_to_float(raw.get("expected_assists")),
            xgi=_to_float(raw.get("expected_goal_involvements")),
            xgc=_to_float(raw.get("expected_goals_conceded")),
            ict_index=_to_float(raw.get("ict_index")),
            influence=_to_float(raw.get("influence")),
            creativity=_to_float(raw.get("creativity")),
            threat=_to_float(raw.get("threat")),
            defcon=_to_int(raw.get("defensive_contribution")),
            value=_to_int(raw.get("value")),
        )
