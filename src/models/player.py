"""Player model."""

from dataclasses import dataclass

from src.config import POSITION_MAP


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

    @classmethod
    def from_api(cls, raw: dict) -> "Player":
        """Build a Player from one entry of bootstrap-static['elements'].

        Two FPL quirks are normalised here so the rest of the app never sees them:
        - element_type (1-4) becomes a readable position label (GK/DEF/MID/FWD).
        - now_cost is in tenths of a million, so price = now_cost / 10 (e.g. 75 → 7.5).
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
        )
