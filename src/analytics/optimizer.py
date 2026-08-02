"""Squad optimiser — the project's first *optimisation* (ADR-008).

Instead of computing an answer step by step, we *describe* the problem — an objective
and a set of constraints — and let an integer-programming solver (PuLP) find the
provably best starting XI. This is the one module that depends on PuLP.
"""

import warnings

import pulp

DEFAULT_BUDGET = 80.0
FORMATION = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}   # 11 players
MAX_PER_CLUB = 3

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def select_squad(
    players,
    budget: float = DEFAULT_BUDGET,
    formation: dict = FORMATION,
    max_per_club: int = MAX_PER_CLUB,
) -> dict:
    """Pick the starting XI that maximises last-season points under the constraints.

    `players` are mappings with id, web_name, position, price, total_points, team
    (as returned by Storage.get_players()). Returns a dict with the solver `status`,
    the `selected` players, and `total_points` / `total_cost`. If no legal XI fits
    (e.g. the budget is too low), `status` is not "Optimal" and `selected` is empty.
    """
    # We use PuLP 3.x's current API; it emits DeprecationWarnings pointing at the
    # PuLP 4.0 API (see docs/Backlog.md). Silence those forward-looking notices here.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        problem = pulp.LpProblem("squad", pulp.LpMaximize)

        # One binary decision per player: 1 = picked, 0 = not.
        pick = {p["id"]: pulp.LpVariable(f"pick_{p['id']}", cat="Binary") for p in players}

        # Objective: maximise total points.
        problem += pulp.lpSum(p["total_points"] * pick[p["id"]] for p in players)

        # Budget.
        problem += pulp.lpSum(p["price"] * pick[p["id"]] for p in players) <= budget

        # Formation: an exact count per position.
        for position, count in formation.items():
            problem += (
                pulp.lpSum(pick[p["id"]] for p in players if p["position"] == position)
                == count
            )

        # At most `max_per_club` players from any one club.
        for club in {p["team"] for p in players}:
            problem += (
                pulp.lpSum(pick[p["id"]] for p in players if p["team"] == club)
                <= max_per_club
            )

        problem.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[problem.status]
    if status != "Optimal":
        return {"status": status, "selected": [], "total_points": 0, "total_cost": 0.0}

    selected = [dict(p) for p in players if pick[p["id"]].value() > 0.5]
    selected.sort(key=lambda p: (_POS_ORDER.get(p["position"], 9), -p["total_points"]))

    return {
        "status": status,
        "selected": selected,
        "total_points": sum(p["total_points"] for p in selected),
        "total_cost": round(sum(p["price"] for p in selected), 1),
    }
