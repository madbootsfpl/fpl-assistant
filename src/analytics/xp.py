"""Expected Points (xP) — the first *cross-domain* metric.

xP joins two threads: a player's scoring rate (`points_per_game`) and their team's
next fixture difficulty. The link is `team_id` — a player belongs to a team, a team
has a next fixture, that fixture has a difficulty (reusing the FDR `_view` seam).

Formula (ADR-006): xP = points_per_game × (1 + (3 − difficulty) × 0.10), or 0 if the
player isn't available. Difficulty is neutral at 3, swinging xP by ±20% at the extremes.
"""

from src.analytics.fdr import _view

_K = 0.10   # fixture weighting: ±20% at the extremes (ADR-006)


def _multiplier(difficulty) -> float:
    """Turn a 1-5 difficulty into a scoring multiplier (neutral at 3, or if unknown)."""
    if difficulty is None:
        return 1.0
    return 1 + (3 - difficulty) * _K


def _next_fixture_difficulty(upcoming, source: str) -> dict:
    """Map team_id → the difficulty of that team's NEXT upcoming fixture.

    `upcoming` is ordered by gameweek, so the first fixture seen for a team is its
    next one; later fixtures for that team are ignored.
    """
    difficulty_by_team = {}
    for f in upcoming:
        for team_id, team_short in ((f["team_h"], f["home"]), (f["team_a"], f["away"])):
            if team_id not in difficulty_by_team:
                difficulty, _, _ = _view(f, team_short, source)
                difficulty_by_team[team_id] = difficulty
    return difficulty_by_team


def player_xp(players, upcoming, source: str = "fpl") -> list[dict]:
    """Compute each player's expected points for their team's next fixture.

    `players` are rows from Storage.get_players() (team_id, points_per_game, status,
    ep_next, web_name, position, team). `upcoming` is from get_upcoming_fixtures().
    Returns a list of dicts sorted by xP, highest first.
    """
    difficulty_by_team = _next_fixture_difficulty(upcoming, source)

    results = []
    for p in players:
        ppg = p["points_per_game"]
        available = p["status"] == "a"
        difficulty = difficulty_by_team.get(p["team_id"])

        if ppg is None or not available:
            xp = 0.0
        else:
            xp = ppg * _multiplier(difficulty)

        results.append({
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "xp": round(xp, 1),
            "ep_next": p["ep_next"],
            "difficulty": difficulty,
        })

    results.sort(key=lambda r: r["xp"], reverse=True)
    return results
