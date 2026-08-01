"""Fixture analysis from a team's perspective (FDR + schedules).

The shared idea is **perspective**: the same fixture is easy for one side and hard
for the other, so each team reads its own difficulty and opponent. `_view` captures
that once; `team_fdr` aggregates it, `team_schedule` lists it.
"""

from collections import defaultdict


def _view(fixture, team):
    """This fixture seen from `team`'s side: (difficulty, opponent, venue)."""
    if fixture["home"] == team:
        return fixture["team_h_difficulty"], fixture["away"], "H"
    return fixture["team_a_difficulty"], fixture["home"], "A"


def team_fdr(fixtures, next_n: int = 5) -> list[dict]:
    """Rank teams by average difficulty over their next `next_n` fixtures.

    `fixtures` is a sequence of upcoming-fixture mappings (from
    Storage.get_upcoming_fixtures()), already ordered by gameweek. Returns a list
    of dicts sorted easiest-run first; a team with no valid difficulty sorts last.
    """
    per_team = defaultdict(list)   # short_name -> list of (difficulty, opponent)
    for f in fixtures:
        for team in (f["home"], f["away"]):
            difficulty, opponent, _ = _view(f, team)
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
