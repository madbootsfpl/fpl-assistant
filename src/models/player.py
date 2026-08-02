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

    @classmethod
    def from_api(cls, raw: dict) -> "Player":
        """Build a Player from one entry of bootstrap-static['elements'].

        FPL quirks normalised here: element_type → position label; now_cost → £m;
        and points_per_game / ep_next arrive as strings, so they're parsed to float.
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
        )
