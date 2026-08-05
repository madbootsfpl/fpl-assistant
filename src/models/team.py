"""Team model."""

from dataclasses import dataclass


@dataclass
class Team:
    id: int
    name: str
    short_name: str
    # Overall strength on a 1-5 scale (Sprint 004, ADR-005). Default None so
    # existing callers/tests that don't set them keep working.
    strength_overall_home: int | None = None
    strength_overall_away: int | None = None
    # The FPL asset `code` (distinct from `id`) — used to build the badge image URL
    # (Sprint 055). Display-only. Default None so existing callers keep working.
    code: int | None = None

    @classmethod
    def from_api(cls, raw: dict) -> "Team":
        """Build a Team from one entry of bootstrap-static['teams']."""
        return cls(
            id=raw["id"],
            name=raw["name"],
            short_name=raw["short_name"],
            strength_overall_home=raw.get("strength_overall_home"),
            strength_overall_away=raw.get("strength_overall_away"),
            code=raw.get("code"),
        )
