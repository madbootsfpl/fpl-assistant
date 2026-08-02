"""Squad optimiser — the project's first *optimisation* (ADR-008).

Instead of computing an answer step by step, we *describe* the problem — an objective
and a set of constraints — and let an integer-programming solver (PuLP) find the
provably best starting XI. This is the one module that depends on PuLP.
"""

import warnings

import pulp

from src.analytics.value import points_per_million
from src.analytics.xp import player_xp

DEFAULT_BUDGET = 80.0
FORMATION = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}   # 11 players (a starting XI)
SQUAD_15 = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}    # 15 players (the full FPL squad)
FULL_BUDGET = 100.0                                    # the real FPL squad budget
MAX_PER_CLUB = 3

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def select_squad(
    players,
    budget: float = DEFAULT_BUDGET,
    formation: dict = FORMATION,
    max_per_club: int = MAX_PER_CLUB,
    include_ids=(),
    exclude_ids=(),
    scores=None,
) -> dict:
    """Pick the starting XI that maximises a per-player score under the constraints.

    `players` are mappings with id, web_name, position, price, total_points, team
    (as returned by Storage.get_players()). `scores` is {player_id: score} to
    maximise; it defaults to `total_points` (so the result is unchanged).
    `include_ids`/`exclude_ids` force players into or out of the XI (pick = 1 / 0).
    Returns a dict with the solver `status`, the `selected` players (each flagged
    `forced`), and `total_points` / `total_cost`. If no legal XI fits, `status` is not
    "Optimal" and `selected` is empty.
    """
    include_set = set(include_ids)
    if scores is None:
        scores = {p["id"]: p["total_points"] for p in players}
    # We use PuLP 3.x's current API; it emits DeprecationWarnings pointing at the
    # PuLP 4.0 API (see docs/Backlog.md). Silence those forward-looking notices here.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        problem = pulp.LpProblem("squad", pulp.LpMaximize)

        # One binary decision per player: 1 = picked, 0 = not.
        pick = {p["id"]: pulp.LpVariable(f"pick_{p['id']}", cat="Binary") for p in players}

        # Objective: maximise the chosen per-player score.
        problem += pulp.lpSum(scores.get(p["id"], 0.0) * pick[p["id"]] for p in players)

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

        # Forced picks: lock chosen players in (1) or out (0).
        for pid in include_set:
            if pid in pick:
                problem += pick[pid] == 1
        for pid in set(exclude_ids):
            if pid in pick:
                problem += pick[pid] == 0

        problem.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[problem.status]
    if status != "Optimal":
        return {"status": status, "selected": [], "total_points": 0, "total_cost": 0.0}

    selected = []
    for p in players:
        if pick[p["id"]].value() > 0.5:
            row = dict(p)
            row["forced"] = p["id"] in include_set
            selected.append(row)
    selected.sort(key=lambda p: (_POS_ORDER.get(p["position"], 9), -p["total_points"]))

    return {
        "status": status,
        "selected": selected,
        "total_points": sum(p["total_points"] for p in selected),
        "total_cost": round(sum(p["price"] for p in selected), 1),
    }


def objective_scores(players, objective: str, upcoming=None) -> dict:
    """Per-player score {id: value} for the chosen squad objective (ADR-011).

    - "value" → points-per-£m (undefined price → 0);
    - "xp"    → Expected Points via player_xp (needs `upcoming` fixtures);
    - anything else → last-season total_points (the default).
    """
    if objective == "value":
        return {
            p["id"]: (points_per_million(p["total_points"], p["price"]) or 0.0)
            for p in players
        }
    if objective == "xp":
        return {r["id"]: r["xp"] for r in player_xp(players, upcoming or [])}
    return {p["id"]: p["total_points"] for p in players}


def resolve_players(players, names) -> tuple[list, list]:
    """Resolve typed names to player ids.

    Each name matches a `web_name` (case-insensitive); a shared name can be
    disambiguated as `web_name:TEAM` (e.g. "Wilson:NFO"). Returns (ids, errors):
    `ids` are the uniquely-resolved player ids; `errors` are human-readable messages
    for names that were not found or were ambiguous (never a silent wrong guess).
    """
    ids: list = []
    errors: list = []
    for name in names:
        wanted, team = name, None
        if ":" in name:
            wanted, team = (part.strip() for part in name.split(":", 1))

        matches = [p for p in players if p["web_name"].lower() == wanted.strip().lower()]
        if team:
            matches = [p for p in matches if str(p["team"]).lower() == team.lower()]

        if not matches:
            errors.append(f"No player matches '{name}'.")
        elif len(matches) > 1:
            candidates = ", ".join(f"{p['web_name']} ({p['team']})" for p in matches)
            errors.append(
                f"'{name}' matches {len(matches)} players: {candidates} "
                "— disambiguate with Name:TEAM."
            )
        else:
            ids.append(matches[0]["id"])
    return ids, errors
