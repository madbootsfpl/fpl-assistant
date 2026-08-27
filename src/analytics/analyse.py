"""Team analyser (ADR-031) — a saved squad's health check over a horizon.

Pure: given the squad's players, which ids are the starting XI, and each player's xP
over the horizon, it returns *indicators* — projected XI xP, squad value, availability
issues, the weakest XI links, and club concentration — not a made-up grade. The caller
loads the squad, decides the XI (declared bench or `select_squad`), computes xP, and
formats the result.
"""

from src.analytics.optimizer import MAX_PER_CLUB, is_unavailable

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def _summary(player, xp_by_id, by_gameweek_by_id, weight_by_id, reported_out=None) -> dict:
    # ADR-155 — a player the press and the crowd both say is leaving (ADR-153/154). Carried on the summary so
    # every consumer of `analyse_squad` inherits it rather than each learning separately: the console table,
    # the web card and anything built later all read the same field.
    leaving = (reported_out or {}).get(player["id"])
    return {
        "id": player["id"],
        "web_name": player["web_name"],
        "team": player["team"],
        "position": player["position"],
        "price": player["price"],
        "xp": round(xp_by_id.get(player["id"], 0), 1),
        "status": player["status"],
        "chance": player["chance"] if "chance" in player.keys() else None,
        "by_gameweek": by_gameweek_by_id.get(player["id"], {}),   # ADR-032; {} when absent
        "minutes_weight": weight_by_id.get(player["id"], 1.0),    # xMins v0 (ADR-038); 1.0 if absent
        "leaving": leaving,                                       # the headline event, or None (ADR-155)
    }


def _has_issue(player, reported_out=None) -> bool:
    """A player worth flagging: injured/suspended/gone, doubtful — **or reported to be leaving**.

    The third case is why this takes an argument now. Health counted *"Availability issues: 1"* on a squad
    holding a player with an agreed move to Al-Hilal, because FPL still reported him `a`. An availability
    count that misses the most consequential unavailability on the page is worse than no count.
    """
    return (is_unavailable(player) or player["status"] == "d"
            or (reported_out or {}).get(player["id"]) is not None)


def analyse_squad(
    owned, xi_ids, xp_by_id, *, horizon: int = 5, max_per_club: int = MAX_PER_CLUB,
    sort: str = "position", by_gameweek_by_id=None, gameweeks=(), weight_by_id=None, reported_out=None,
) -> dict:
    """Summarise a squad's health over the horizon (ADR-031).

    `owned` are the squad's player rows; `xi_ids` the starting-XI ids (the rest are
    bench); `xp_by_id` maps id → xP over the horizon. Returns indicators: `projected_xp`
    (the **XI** only), `bench_xp`, `value`, `xi`/`bench` player summaries, `issues`
    (availability), `weakest` (3 lowest-xP XI links → transfer candidates), `top_pick`
    (highest-xP XI player → captain lead), and `concentrated_clubs` (at the per-club cap).

    `sort` orders the XI: "position" (the formation shape, default) or "xp" (strongest
    first). `by_gameweek_by_id` (id → {gw: xP}) and `gameweeks` add the per-GW breakdown
    (ADR-032) to each summary; omit them for a totals-only analysis.

    `reported_out` maps id → the headline event showing a player is leaving the league (ADR-153/154). It adds
    him to `issues` and marks his summary — **it does not touch his xP**. Health's job is to describe the
    squad you have, and until you transfer him he is in it; what changes is that the description stops
    implying he will play.
    """
    by_gameweek_by_id = by_gameweek_by_id or {}
    weight_by_id = weight_by_id or {}
    xi_ids = set(xi_ids)
    xi = [p for p in owned if p["id"] in xi_ids]
    bench = [p for p in owned if p["id"] not in xi_ids]

    if sort == "xp":
        xi_sorted = sorted(xi, key=lambda p: -xp_by_id.get(p["id"], 0))
    else:
        xi_sorted = sorted(xi, key=lambda p: (_POS_ORDER.get(p["position"], 9),
                                              -xp_by_id.get(p["id"], 0)))
    bench_sorted = sorted(bench, key=lambda p: -xp_by_id.get(p["id"], 0))
    by_xp = sorted(xi, key=lambda p: xp_by_id.get(p["id"], 0))
    # The captain lead is a *recommendation*, so it obeys ADR-154: never name a player reported to be leaving.
    # `weakest` deliberately does not filter — a leaver belongs in the transfer conversation, not out of it.
    captainable = [p for p in by_xp if not (reported_out or {}).get(p["id"])] or by_xp

    def summ(p):
        return _summary(p, xp_by_id, by_gameweek_by_id, weight_by_id, reported_out)

    club_counts: dict = {}
    for p in owned:
        club_counts[p["team"]] = club_counts.get(p["team"], 0) + 1

    return {
        "horizon": horizon,
        "gameweeks": list(gameweeks),
        "projected_xp": round(sum(xp_by_id.get(p["id"], 0) for p in xi), 1),
        "bench_xp": round(sum(xp_by_id.get(p["id"], 0) for p in bench), 1),
        "value": round(sum(p["price"] for p in owned), 1),
        "xi": [summ(p) for p in xi_sorted],
        "bench": [summ(p) for p in bench_sorted],
        "issues": [summ(p) for p in owned if _has_issue(p, reported_out)],
        "weakest": [summ(p) for p in by_xp[:3]],
        "top_pick": summ(captainable[-1]) if captainable else None,
        "club_counts": club_counts,
        "concentrated_clubs": sorted(c for c, n in club_counts.items() if n >= max_per_club),
    }
