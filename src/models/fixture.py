"""Fixture model."""

from dataclasses import dataclass


@dataclass
class Fixture:
    id: int
    event: int | None            # gameweek; None when not yet scheduled
    team_h: int
    team_a: int
    team_h_difficulty: int | None
    team_a_difficulty: int | None
    finished: bool
    kickoff_time: str | None

    @classmethod
    def from_api(cls, raw: dict) -> "Fixture":
        """Build a Fixture from one entry of the /fixtures/ payload.

        `event` (gameweek) and `kickoff_time` can be null for unscheduled
        fixtures, so we read them defensively with .get().
        """
        return cls(
            id=raw["id"],
            event=raw.get("event"),
            team_h=raw["team_h"],
            team_a=raw["team_a"],
            team_h_difficulty=raw.get("team_h_difficulty"),
            team_a_difficulty=raw.get("team_a_difficulty"),
            finished=bool(raw.get("finished", False)),
            kickoff_time=raw.get("kickoff_time"),
        )
