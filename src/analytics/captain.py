"""Captain suggestions (ADR-029) — a decision-support layer on xP.

Ranks available *outfield* players by next-gameweek xP and annotates each pick with its
opponent, venue, and penalty duty — a recommendation that explains itself. Two deliberate
choices (both from a live probe): goalkeepers are excluded (captaincy is a ceiling bet and
keepers have none), and penalties are *context, not a score bump* (a taker's returns are
already in their xP — adding a bonus would double-count).
"""

from src.analytics.optimizer import is_unavailable
from src.analytics.xp import player_xp


def _next_opponent(team_id, upcoming):
    """The team's next fixture as (opponent_short, venue) — venue 'H' or 'A'.

    Returns (None, None) if the team has no upcoming fixture (a blank gameweek).
    """
    fixtures = [f for f in upcoming if f["team_h"] == team_id or f["team_a"] == team_id]
    if not fixtures:
        return None, None
    nxt = min(fixtures, key=lambda f: f["event"] if f["event"] is not None else 9999)
    if nxt["team_h"] == team_id:
        return nxt["away"], "H"
    return nxt["home"], "A"


def captain_picks(players, upcoming, baseline_by_code=None, source: str = "fpl", limit: int = 5,
                  minutes_weight=None):
    """Top `limit` captain candidates for the next gameweek (ADR-029).

    Outfield players who aren't injured/suspended/gone (`is_unavailable`), ranked by
    next-GW xP — *doubtful* players are included (flagged), not zeroed. Each pick carries
    its opponent, venue, penalty duty, and a doubtful marker. Returns a list of dicts
    (the xP fields plus opponent/venue/penalty_taker/doubtful/chance), highest xP first.

    `minutes_weight` (xMins v0, ADR-038) optionally scales each xP by expected playing
    time, so a rotation risk doesn't out-rank a nailed-on starter; each pick carries the
    `minutes_weight` used (1.0 when the hook is absent).
    """
    candidates = [p for p in players if p["position"] != "GK" and not is_unavailable(p)]

    ranked = player_xp(
        candidates, upcoming, source=source, horizon=1,
        baseline_by_code=baseline_by_code,
        is_available=lambda p: not is_unavailable(p),   # count doubtful, not only 'a'
        minutes_weight=minutes_weight,
    )
    by_id = {p["id"]: p for p in candidates}

    picks = []
    for r in ranked[:limit]:
        row = by_id.get(r["id"])
        opponent, venue = _next_opponent(row["team_id"], upcoming) if row else (None, None)
        picks.append({
            **r,
            "opponent": opponent,
            "venue": venue,
            "penalty_taker": bool(row and row["penalties_order"] == 1),
            "doubtful": bool(row and row["status"] == "d"),
            "chance": row["chance"] if row else None,
        })
    return picks
