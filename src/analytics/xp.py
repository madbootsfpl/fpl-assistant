"""Expected Points (xP) — the first *cross-domain* metric.

xP joins two threads: a player's scoring rate (`points_per_game`) and their team's
fixture difficulty. The link is `team_id` — a player belongs to a team, a team has
fixtures, each fixture has a difficulty (reusing the FDR `_view` seam).

Formula (ADR-006): per fixture, xP = points_per_game × (1 + (3 − difficulty) × 0.10),
or 0 if the player isn't available. Over a horizon of the next N gameweeks, we sum the
per-fixture xP (ADR-007) — so a double gameweek (two fixtures in one gameweek) adds up.
"""

from src.analytics.fdr import _view

_K = 0.10   # fixture weighting: ±20% at the extremes (ADR-006)


def _multiplier(difficulty) -> float:
    """Turn a 1-5 difficulty into a scoring multiplier (neutral at 3, or if unknown)."""
    if difficulty is None:
        return 1.0
    return 1 + (3 - difficulty) * _K


def _horizon_difficulties(upcoming, source: str, gameweeks: int) -> dict:
    """Map team_id → the difficulties of every fixture the team plays in the next
    `gameweeks` gameweeks.

    The horizon is a gameweek window (not a per-team fixture count), so a double
    gameweek yields two entries for that team and a blank gameweek yields none —
    which is how DGW/BGW are captured (ADR-007).
    """
    events = sorted({f["event"] for f in upcoming if f["event"] is not None})
    horizon = set(events[:gameweeks])

    difficulties_by_team: dict = {}
    for f in upcoming:
        if f["event"] not in horizon:
            continue
        for team_id, team_short in ((f["team_h"], f["home"]), (f["team_a"], f["away"])):
            difficulty, _, _ = _view(f, team_short, source)
            difficulties_by_team.setdefault(team_id, []).append(difficulty)
    return difficulties_by_team


def player_xp(players, upcoming, source: str = "fpl", horizon: int = 1) -> list[dict]:
    """Compute each player's expected points over the next `horizon` gameweeks.

    `players` are rows from Storage.get_players() (team_id, points_per_game, status,
    ep_next, web_name, position, team). `upcoming` is from get_upcoming_fixtures().
    xP is the sum of per-fixture xP over the team's fixtures in the horizon; 0 if the
    player is unavailable or has no points_per_game. Returned sorted by xP, highest first.
    """
    difficulties_by_team = _horizon_difficulties(upcoming, source, horizon)

    results = []
    for p in players:
        ppg = p["points_per_game"]
        available = p["status"] == "a"
        difficulties = difficulties_by_team.get(p["team_id"], [])

        if ppg is None or not available:
            xp = 0.0
        else:
            xp = ppg * sum(_multiplier(d) for d in difficulties)

        results.append({
            "id": p["id"],
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "xp": round(xp, 1),
            "games": len(difficulties),               # fixtures in the horizon (DGW → >horizon)
            "ep_next": p["ep_next"],
            "difficulty": difficulties[0] if difficulties else None,  # next fixture (for N=1 display)
        })

    results.sort(key=lambda r: r["xp"], reverse=True)
    return results
