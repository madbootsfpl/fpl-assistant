"""Captain suggestions (ADR-029) — a decision-support layer on xP.

Ranks available *outfield* players by next-gameweek xP and annotates each pick with its
opponent, venue, and penalty duty — a recommendation that explains itself. Two deliberate
choices (both from a live probe): goalkeepers are excluded (captaincy is a ceiling bet and
keepers have none), and penalties are *context, not a score bump* (a taker's returns are
already in their xP — adding a bonus would double-count).
"""

from src import config
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
                  minutes_weight=None, history_by_code=None):
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
        minutes_weight=minutes_weight, history_by_code=history_by_code,
        set_piece_weight=config.SET_PIECE_WEIGHT,       # ADR-096: reflect the set-piece term (dormant → no-op)
        defcon_weight=config.DEFCON_MAGNIFIER_WEIGHT,   # ADR-097: reflect the DefCon magnifier (dormant → no-op)
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


# How clear a captain lead is, calibrated against the **measured** distribution rather than invented (ADR-144).
# Over 300 random legal squads on live data the gap between the top pick and the runner-up came out:
#
#     p25 0.20 · median 0.60 · p75 1.00 · max 2.80
#
# So the captain call is *usually close*: 44% of squads separate their top two by under half a point. These
# thresholds are the quartiles, which is what makes "a clear pick" mean something — it is the top quarter of
# real leads, not a number someone liked the look of.
WHISKER, CLEAR = 0.3, 1.0


def captain_margin(picks) -> dict | None:
    """How far the top captain pick leads the runner-up, and whether that lead means anything.

    Returns ``{gap, runner_up, verdict}`` — or `None` when there is nobody to compare against (a squad with
    one eligible player), because a margin over nothing is not a small margin, it is no margin.

    **The verdict exists because the number alone does not help.** A card that says *"🥇 Salah 5.9 · 🥈 Haaland
    5.6"* leaves a manager to do the subtraction and then guess whether 0.3 is a lot. Against the measured
    spread it is not — it is inside the bottom third of leads, i.e. a coin-flip dressed as a recommendation.
    """
    if not picks or len(picks) < 2:
        return None
    top, runner = picks[0], picks[1]
    if top.get("xp") is None or runner.get("xp") is None:
        return None
    gap = round(top["xp"] - runner["xp"], 1)
    verdict = "whisker" if gap < WHISKER else ("narrow" if gap < CLEAR else "clear")
    return {"gap": gap, "runner_up": runner.get("web_name") or "the runner-up", "verdict": verdict}


def margin_line(margin) -> str:
    """The captain margin as one honest sentence, or `""` when there is no runner-up.

    The closing clause on a whisker is the point of the whole feature. A single gameweek's variance dwarfs
    half a projected point, so a 0.2 lead is not a recommendation — it is the model declining to have an
    opinion, and it should say so rather than let a medal imply certainty.
    """
    if not margin:
        return ""
    gap, who = margin["gap"], margin["runner_up"]
    if margin["verdict"] == "whisker":
        return f"By a whisker — just {gap} ahead of {who}. Too close to call; take the one you fancy."
    if margin["verdict"] == "narrow":
        return f"A narrow lead — {gap} ahead of {who}."
    return f"A clear pick — {gap} ahead of {who}."
