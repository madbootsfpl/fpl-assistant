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
    # ⚠️⚠️ **Nullable on purpose, and `0-0` is why** (ADR-346). A fixture that has not kicked off has no
    # score; a goalless draw has a real one. Defaulting either to 0 makes those two indistinguishable on
    # the one screen built to tell them apart. ⭐ `started` is the field that settles it — never the score.
    team_h_score: int | None = None
    team_a_score: int | None = None
    minutes: int | None = None
    started: bool | None = None

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
            # ⭐ `.get()` throughout: these arrive on `/fixtures/` but the same shape is built in tests and
            # from older snapshots, where they simply are not there.
            team_h_score=raw.get("team_h_score"),
            team_a_score=raw.get("team_a_score"),
            minutes=raw.get("minutes"),
            started=None if raw.get("started") is None else bool(raw["started"]),
        )
