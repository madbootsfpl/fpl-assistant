"""Team model."""

from dataclasses import dataclass


@dataclass
class Team:
    id: int
    name: str
    short_name: str

    @classmethod
    def from_api(cls, raw: dict) -> "Team":
        """Build a Team from one entry of bootstrap-static['teams']."""
        return cls(
            id=raw["id"],
            name=raw["name"],
            short_name=raw["short_name"],
        )
