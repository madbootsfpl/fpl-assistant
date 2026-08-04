"""Team analyser (ADR-031) — a saved squad's health check over a horizon.

Pure: given the squad's players, which ids are the starting XI, and each player's xP
over the horizon, it returns *indicators* — projected XI xP, squad value, availability
issues, the weakest XI links, and club concentration — not a made-up grade. The caller
loads the squad, decides the XI (declared bench or `select_squad`), computes xP, and
formats the result.
"""

from src.analytics.optimizer import MAX_PER_CLUB, is_unavailable

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def _summary(player, xp_by_id, by_gameweek_by_id, weight_by_id) -> dict:
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
    }


def _has_issue(player) -> bool:
    """A player worth flagging: injured/suspended/gone, or doubtful."""
    return is_unavailable(player) or player["status"] == "d"


def analyse_squad(
    owned, xi_ids, xp_by_id, *, horizon: int = 5, max_per_club: int = MAX_PER_CLUB,
    sort: str = "position", by_gameweek_by_id=None, gameweeks=(), weight_by_id=None,
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

    def summ(p):
        return _summary(p, xp_by_id, by_gameweek_by_id, weight_by_id)

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
        "issues": [summ(p) for p in owned if _has_issue(p)],
        "weakest": [summ(p) for p in by_xp[:3]],
        "top_pick": summ(by_xp[-1]) if by_xp else None,
        "club_counts": club_counts,
        "concentrated_clubs": sorted(c for c, n in club_counts.items() if n >= max_per_club),
    }
