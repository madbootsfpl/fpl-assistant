"""Player past-season history model (ADR-027).

One row per (player, past season), from `element-summary/{id}/`'s `history_past`.
Keyed by `element_code` — the player's *stable* id across seasons (the per-season
`id` changes yearly). This is a standalone archive: no foreign key to `players`,
because a player's history outlives their presence in the current game (a departed
player still has past seasons — the same lesson as ADR-024's departed squads).

**Data-provenance caveat (ADR-027):** a stat introduced in a later season reads 0 in
earlier ones (e.g. `defensive_contribution` is 0 before 2024/25). A 0 here means "the
stat did not exist", *not* a real zero — so don't trend such fields across seasons.
"""

from dataclasses import dataclass


def _to_float(value):
    """Parse an FPL number (sometimes a string like "28.54") to float, else None."""
    if value in (None, "", "None"):
        return None
    return float(value)


def _to_int(value):
    """Parse an FPL integer to int, or None when absent/blank."""
    if value in (None, "", "None"):
        return None
    return int(value)


def _price(value):
    """FPL costs are in tenths of a million (115 → £11.5m), like `now_cost`."""
    n = _to_float(value)
    return n / 10 if n is not None else None


@dataclass
class PlayerSeason:
    element_code: int
    season_name: str
    total_points: int | None = None
    minutes: int | None = None
    goals_scored: int | None = None
    assists: int | None = None
    clean_sheets: int | None = None
    goals_conceded: int | None = None
    expected_goals: float | None = None
    expected_assists: float | None = None
    expected_goal_involvements: float | None = None
    expected_goals_conceded: float | None = None
    # See the provenance caveat above — unreliable before 2024/25.
    defensive_contribution: int | None = None
    starts: int | None = None
    start_cost: float | None = None   # £m
    end_cost: float | None = None     # £m

    @classmethod
    def from_api(cls, raw: dict) -> "PlayerSeason":
        """Build from one entry of `element-summary['history_past']`.

        Each row carries its own `element_code`, so no id needs threading in. The
        expected_* fields arrive as strings (→ float); costs are tenths-of-£m (→ £m).
        """
        return cls(
            element_code=raw["element_code"],
            season_name=raw["season_name"],
            total_points=_to_int(raw.get("total_points")),
            minutes=_to_int(raw.get("minutes")),
            goals_scored=_to_int(raw.get("goals_scored")),
            assists=_to_int(raw.get("assists")),
            clean_sheets=_to_int(raw.get("clean_sheets")),
            goals_conceded=_to_int(raw.get("goals_conceded")),
            expected_goals=_to_float(raw.get("expected_goals")),
            expected_assists=_to_float(raw.get("expected_assists")),
            expected_goal_involvements=_to_float(raw.get("expected_goal_involvements")),
            expected_goals_conceded=_to_float(raw.get("expected_goals_conceded")),
            defensive_contribution=_to_int(raw.get("defensive_contribution")),
            starts=_to_int(raw.get("starts")),
            start_cost=_price(raw.get("start_cost")),
            end_cost=_price(raw.get("end_cost")),
        )
