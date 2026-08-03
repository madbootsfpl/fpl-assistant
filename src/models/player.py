"""Player model."""

from dataclasses import dataclass

from src.config import POSITION_MAP


def _to_float(value):
    """FPL sends some numbers as strings (e.g. "4.4").

    Convert to float, or None when the value is absent or blank — so the rest of
    the app never has to deal with the string form.
    """
    if value in (None, "", "None"):
        return None
    return float(value)


@dataclass
class Player:
    id: int
    first_name: str
    second_name: str
    web_name: str
    team_id: int
    position: str
    price: float
    total_points: int
    # xP inputs (Sprint 005, ADR-006). Default None so existing callers keep working.
    points_per_game: float | None = None
    status: str | None = None
    ep_next: float | None = None
    # Expected goals (Sprint 014, ADR-015). xGI = xG + xA; xGC is goals conceded.
    xg: float | None = None
    xa: float | None = None
    xgi: float | None = None
    xgc: float | None = None
    # Actual returns for over/under-performance (Sprint 016, ADR-017). Ints in the API.
    goals_scored: int | None = None
    assists: int | None = None
    minutes: int | None = None
    # Defensive Contribution (Sprint 017, ADR-018). `defcon` = position-correct action
    # count (DEF: CBIT; MID/FWD: CBIT + recoveries); `defcon_per90` is the per-90 rate.
    defcon: int | None = None
    defcon_per90: float | None = None
    cbi: int | None = None          # clearances + blocks + interceptions
    tackles: int | None = None
    recoveries: int | None = None
    # Availability (Sprint 022, ADR-023). `status` above is a/d/i/s/u; `chance` is the
    # % chance of playing next round (None when fully fit); `news` explains an issue.
    chance: int | None = None
    news: str | None = None
    # The stable cross-season id (Sprint 026, ADR-028) — the join key to
    # player_history_past (whose per-season `id` differs from this year's `id`).
    code: int | None = None

    @classmethod
    def from_api(cls, raw: dict) -> "Player":
        """Build a Player from one entry of bootstrap-static['elements'].

        FPL quirks normalised here: element_type → position label; now_cost → £m;
        and points_per_game / ep_next / the expected_* fields arrive as strings, so
        they're parsed to float (absent → None). goals_scored / assists / minutes are
        already ints, so they're taken as-is.
        """
        return cls(
            id=raw["id"],
            first_name=raw["first_name"],
            second_name=raw["second_name"],
            web_name=raw["web_name"],
            team_id=raw["team"],
            position=POSITION_MAP[raw["element_type"]],
            price=raw["now_cost"] / 10,
            total_points=raw["total_points"],
            points_per_game=_to_float(raw.get("points_per_game")),
            status=raw.get("status"),
            ep_next=_to_float(raw.get("ep_next")),
            xg=_to_float(raw.get("expected_goals")),
            xa=_to_float(raw.get("expected_assists")),
            xgi=_to_float(raw.get("expected_goal_involvements")),
            xgc=_to_float(raw.get("expected_goals_conceded")),
            goals_scored=raw.get("goals_scored"),
            assists=raw.get("assists"),
            minutes=raw.get("minutes"),
            defcon=raw.get("defensive_contribution"),
            defcon_per90=_to_float(raw.get("defensive_contribution_per_90")),
            cbi=raw.get("clearances_blocks_interceptions"),
            tackles=raw.get("tackles"),
            recoveries=raw.get("recoveries"),
            chance=raw.get("chance_of_playing_next_round"),
            news=raw.get("news"),
            code=raw.get("code"),
        )
