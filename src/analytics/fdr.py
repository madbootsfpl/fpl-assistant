"""Fixture analysis from a team's perspective (FDR + schedules).

The shared idea is **perspective**: the same fixture is easy for one side and hard
for the other, so each team reads its own difficulty and opponent. `_view` captures
that once; `team_fdr` aggregates it, `team_schedule` lists it.
"""

from collections import defaultdict


def _view(fixture, team, source: str = "fpl"):
    """This fixture seen from `team`'s side: (difficulty, opponent, venue).

    `source` selects which difficulty number:
    - "fpl"    → FPL's published team_h/a_difficulty (ADR-004);
    - "custom" → the opponent's overall strength at the venue the opponent plays
      (ADR-005). If my team is home, the opponent is away, so I face their *away*
      strength; if my team is away, I face the home team's *home* strength.
    """
    is_home = fixture["home"] == team
    opponent = fixture["away"] if is_home else fixture["home"]
    venue = "H" if is_home else "A"
    if source == "custom":
        difficulty = (
            fixture["away_team_strength"] if is_home else fixture["home_team_strength"]
        )
    else:
        difficulty = (
            fixture["team_h_difficulty"] if is_home else fixture["team_a_difficulty"]
        )
    return difficulty, opponent, venue


def team_fdr(fixtures, next_n: int = 5, source: str = "fpl") -> list[dict]:
    """Rank teams by average difficulty over their next `next_n` fixtures.

    `fixtures` is a sequence of upcoming-fixture mappings (from
    Storage.get_upcoming_fixtures()), already ordered by gameweek. `source` picks
    FPL's difficulty or our custom one. Returns a list of dicts sorted easiest-run
    first; a team with no valid difficulty sorts last.
    """
    per_team = defaultdict(list)   # short_name -> list of (difficulty, opponent)
    for f in fixtures:
        for team in (f["home"], f["away"]):
            difficulty, opponent, _ = _view(f, team, source)
            per_team[team].append((difficulty, opponent))

    results = []
    for team, games in per_team.items():
        window = games[:next_n]                       # the team's next N fixtures
        diffs = [d for (d, _) in window if d is not None]
        avg = sum(diffs) / len(diffs) if diffs else None
        results.append({
            "team": team,
            "games": len(window),
            "avg_difficulty": avg,
            "opponents": [opp for (_, opp) in window],
        })

    # Easiest run first; undefined averages sort to the bottom.
    results.sort(key=lambda r: (r["avg_difficulty"] is None, r["avg_difficulty"] or 0.0))
    return results


def team_schedule(fixtures, team) -> list[dict]:
    """One team's upcoming fixtures, each seen from that team's perspective.

    Returns a list of {event, opponent, venue, difficulty}, in the order given
    (the caller passes fixtures already ordered by gameweek).
    """
    schedule = []
    for f in fixtures:
        if team in (f["home"], f["away"]):
            difficulty, opponent, venue = _view(f, team)
            schedule.append({
                "event": f["event"],
                "opponent": opponent,
                "venue": venue,
                "difficulty": difficulty,
            })
    return schedule
