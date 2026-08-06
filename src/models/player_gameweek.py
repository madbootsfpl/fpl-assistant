"""Per-gameweek history model (ADR-060) — the current season, one row per player per GW.

From `element-summary/{id}/`'s **`history`** array (empty preseason; live from GW1). Unlike
`history_past` (past-season aggregates, keyed by the stable `element_code`), a per-GW row carries only
`element` — the *per-season* id — so the stable `element_code` is passed in from an id→code map. This is a
**current-season working set** keyed `(element_code, round)`: a new season re-backfills and overwrites
round-for-round, so no season name is stored (the payload doesn't carry one).

It feeds the in-season **form** term of `decision_xp` (ADR-060, US-197) — dormant until there's per-GW data.
"""

from dataclasses import dataclass


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
        )
