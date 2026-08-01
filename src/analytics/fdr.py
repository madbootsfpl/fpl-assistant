"""Fixture Difficulty Rating (FDR) — the first *aggregating* metric.

Where points-per-£m transforms a single row, FDR summarises a *group*: each team's
average difficulty over its next few fixtures. The key idea is **perspective** — the
same fixture is easy for one side and hard for the other, so each team reads its own
difficulty (home → team_h_difficulty, away → team_a_difficulty).
"""

from collections import defaultdict


def team_fdr(fixtures, next_n: int = 5) -> list[dict]:
    """Rank teams by average difficulty over their next `next_n` fixtures.

    `fixtures` is a sequence of upcoming-fixture mappings (from
    Storage.get_upcoming_fixtures()), already ordered by gameweek. Returns a list
    of dicts sorted easiest-run first; a team with no valid difficulty sorts last.
    """
    # Attribute each fixture to *both* teams, each from its own perspective.
    per_team = defaultdict(list)   # short_name -> list of (difficulty, opponent)
    for f in fixtures:
        per_team[f["home"]].append((f["team_h_difficulty"], f["away"]))
        per_team[f["away"]].append((f["team_a_difficulty"], f["home"]))

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
