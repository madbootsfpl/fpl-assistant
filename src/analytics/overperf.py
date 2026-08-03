"""Over/under-performance: expected vs actual attacking points (ADR-017).

Compares what a player's underlying numbers say they *should* have returned (from xG/xA)
with what they *did* (from goals/assists). A positive diff = over-performing (finishing
hot → regression risk); negative = under-performing (unlucky → bounce-back). Attacking
returns only — clean sheets, appearance and bonus points are out of scope.
"""

# FPL points per goal, by position; an assist is always 3.
GOAL_POINTS = {"GK": 6, "DEF": 6, "MID": 5, "FWD": 4}
ASSIST_POINTS = 3
MIN_MINUTES = 900   # ~10 matches — filters small-sample noise + preseason data glitches


def _num(value) -> float:
    return value or 0.0


def over_under(players, min_minutes: int = MIN_MINUTES) -> list[dict]:
    """Rank players by (actual − expected) attacking points, minutes-gated.

    `players` are mappings with position, xg, xa, goals_scored, assists, minutes
    (as returned by Storage.get_players()). Players below `min_minutes` are skipped —
    the sample is too small to read, and it drops preseason glitches (e.g. a reset row
    with goals but zero minutes). Returns rows sorted by `diff` descending.
    """
    rows = []
    for p in players:
        if _num(p["minutes"]) < min_minutes:
            continue
        goal_pts = GOAL_POINTS.get(p["position"], 0)
        expected = _num(p["xg"]) * goal_pts + _num(p["xa"]) * ASSIST_POINTS
        actual = _num(p["goals_scored"]) * goal_pts + _num(p["assists"]) * ASSIST_POINTS
        rows.append({
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "minutes": int(_num(p["minutes"])),
            "expected": round(expected, 1),
            "actual": round(actual, 1),
            "diff": round(actual - expected, 1),
        })
    rows.sort(key=lambda r: r["diff"], reverse=True)
    return rows
