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
FORMATION = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}   # 11 players (a fixed 1-4-4-2 XI)
# A flexible XI: each outfield line is a (min, max) range; the solver picks the shape.
XI_FLEX = {"GK": (1, 1), "DEF": (3, 5), "MID": (2, 5), "FWD": (1, 3)}   # 11, any legal shape
SQUAD_15 = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}    # 15 players (the full FPL squad)
FULL_BUDGET = 100.0                                    # the real FPL squad budget
MAX_PER_CLUB = 3
# Squad archetypes (ADR-043/044), tunable: a low-cost enabler, a premium, and a differential.
LOW_COST_MAX = 4.5              # ≤ this is a "low-cost" / budget enabler (the bench-fodder tier)
PREMIUM_MIN = 9.0              # ≥ this is a "premium" (the elite few)
DIFFERENTIAL_MAX_OWNERSHIP = 5.0   # ≤ this % owned is a "differential" (off-template; ADR-044)
# Bench-aware objective weight (ADR-045): how much a bench player's score counts vs a starter's.
# `--weekly` uses this; `--bench-boost` is just the default max-15 build (all 15 score under the chip),
# so it needs no separate weight — it keeps the best-XI display + an "all 15 score" note.
WEEKLY_BENCH_WEIGHT = 0.1      # a strong XI + a cheap, still-playing bench (rotation cover)

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def _formation_bounds(formation: dict, size):
    """Normalise a formation to {pos: (min, max)} and resolve the total squad `size`.

    A value may be an exact int (→ `(n, n)`) or a `(min, max)` range. `size` is the total
    number of players; if None it's derived from an all-exact formation (their sum), and
    a range formation without an explicit `size` is an error (the total is ambiguous).
    """
    bounds = {
        pos: ((v, v) if isinstance(v, int) else tuple(v))
        for pos, v in formation.items()
    }
    if size is None:
        if all(lo == hi for lo, hi in bounds.values()):
            size = sum(lo for lo, _ in bounds.values())
        else:
            raise ValueError("select_squad: `size` is required for a range formation")
    return bounds, size


def legal_xi_issues(starters) -> list:
    """Reasons `starters` don't form a legal XI — empty if legal (ADR-022).

    Each position's count must sit inside its `XI_FLEX` range (GK 1, DEF 3-5, MID 2-5,
    FWD 1-3). Used to validate a declared 4-man bench: the 11 non-bench players must be a
    legal starting XI. Reuses `XI_FLEX` so the rules live in one place (ADR-014).
    """
    counts = {}
    for p in starters:
        counts[p["position"]] = counts.get(p["position"], 0) + 1
    issues = []
    for position, (lo, hi) in XI_FLEX.items():
        n = counts.get(position, 0)
        if n < lo:
            want = f"{lo}" if lo == hi else f"{lo}-{hi}"
            issues.append(f"{n} {position} (need {want})")
        elif n > hi:
            issues.append(f"{n} {position} (max {hi})")
    return issues


def squad_15_issues(players, max_per_club: int = MAX_PER_CLUB) -> list:
    """Reasons `players` aren't a legal 15-man FPL squad — empty if legal (ADR-055).

    The *hard* structural rules only: exactly 15 players in the `SQUAD_15` split
    (2 GK, 5 DEF, 5 MID, 3 FWD), and no more than `max_per_club` from any one club.
    Budget is deliberately NOT checked here — prices drift, so it's a soft warning the
    caller shows (never a block, ADR-055), computed from the squad's cost at the edge.
    The 15-man counterpart to `legal_xi_issues` (ADR-022); reuses `SQUAD_15`/`MAX_PER_CLUB`
    so the rules live in one place.
    """
    counts: dict = {}
    club_counts: dict = {}
    for p in players:
        counts[p["position"]] = counts.get(p["position"], 0) + 1
        club_counts[p["team"]] = club_counts.get(p["team"], 0) + 1
    issues = []
    if len(players) != 15:
        issues.append(f"{len(players)} players (need 15)")
    for position, need in SQUAD_15.items():
        n = counts.get(position, 0)
        if n != need:
            issues.append(f"{n} {position} (need {need})")
    for club in sorted(c for c, n in club_counts.items() if n > max_per_club):
        issues.append(f"{club_counts[club]} from {club} (max {max_per_club})")
    return issues


# FPL status codes for players who cannot play (all have chance 0). 'a' = available,
# 'd' = doubtful (might play — kept, but flagged). ADR-023.
UNAVAILABLE_STATUS = frozenset({"i", "s", "u", "n"})


def is_unavailable(player) -> bool:
    """True if the player can't play next round (injured / suspended / gone) — ADR-023."""
    return player["status"] in UNAVAILABLE_STATUS


def _selected_by(player):
    """A player's ownership % (ADR-044), or None if the row lacks it (a sqlite Row or a test dict)."""
    try:
        return player["selected_by"]
    except (KeyError, IndexError):
        return None


def available_players(players, keep_ids=()) -> tuple:
    """Split players into (pool, excluded): drop the unavailable, but keep `keep_ids`.

    `keep_ids` are players the manager forced in (include/bench) — they stay in the pool
    even if unavailable (their call), so only the rest of the unavailable are excluded.
    """
    keep = set(keep_ids)
    pool, excluded = [], []
    for p in players:
        if is_unavailable(p) and p["id"] not in keep:
            excluded.append(p)
        else:
            pool.append(p)
    return pool, excluded


def select_squad(
    players,
    budget: float = DEFAULT_BUDGET,
    formation: dict = FORMATION,
    max_per_club: int = MAX_PER_CLUB,
    include_ids=(),
    exclude_ids=(),
    bench_ids=(),
    scores=None,
    size=None,
    band_minimums=None,
    min_differentials=None,
    bench_weight=None,
) -> dict:
    """Pick the starting XI that maximises a per-player score under the constraints.

    `players` are mappings with id, web_name, position, price, total_points, team
    (as returned by Storage.get_players()). `scores` is {player_id: score} to
    maximise; it defaults to `total_points` (so the result is unchanged).
    `include_ids`/`exclude_ids` force players into or out of the XI (pick = 1 / 0).
    `bench_ids` also force players in (like include) but tag them `bench` and sort them
    to the end — the manager's declared bench (ADR-013). Returns a dict with the solver
    `status`, the `selected` players (each flagged `forced` and `bench`), and
    `total_points` / `total_cost`. If no legal squad fits, `status` is not "Optimal" and
    `selected` is empty.

    `bench_weight` (ADR-045) makes a full-15 build **bench-aware**: the solver also designates the
    starting XI (a legal shape) and maximises `Σ score·start + bench_weight·score·bench`, marking
    non-starters `bench`. `0.1` (`--weekly`) builds a strong XI with a cheap-but-playing bench; `1.0`
    (`--bench-boost`) is the max-15. None → the whole-squad objective above (byte-identical).
    """
    include_set = set(include_ids)
    bench_set = set(bench_ids)
    bounds, size = _formation_bounds(formation, size)
    if scores is None:
        scores = {p["id"]: p["total_points"] for p in players}
    # We use PuLP 3.x's current API; it emits DeprecationWarnings pointing at the
    # PuLP 4.0 API (see docs/Backlog.md). Silence those forward-looking notices here.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)

        problem = pulp.LpProblem("squad", pulp.LpMaximize)

        # One binary decision per player: 1 = picked, 0 = not.
        pick = {p["id"]: pulp.LpVariable(f"pick_{p['id']}", cat="Binary") for p in players}

        if bench_weight is None:
            # Objective: maximise the chosen per-player score (the whole squad counts equally).
            problem += pulp.lpSum(scores.get(p["id"], 0.0) * pick[p["id"]] for p in players)
            start = None
        else:
            # Bench-aware (ADR-045): also choose which 11 START (a legal XI), and maximise the
            # XI's score plus `bench_weight` × the bench's — so `--weekly` (w≈0.1) builds a strong
            # XI with a cheap-but-playing bench; `--bench-boost` (w=1) reduces to the max-15 above.
            start = {p["id"]: pulp.LpVariable(f"start_{p['id']}", cat="Binary") for p in players}
            problem += pulp.lpSum(
                scores.get(p["id"], 0.0)
                * (start[p["id"]] + bench_weight * (pick[p["id"]] - start[p["id"]]))
                for p in players
            )
            for p in players:
                problem += start[p["id"]] <= pick[p["id"]]        # can't start who you didn't pick
            problem += pulp.lpSum(start.values()) == 11            # a full XI
            for position, (lo, hi) in XI_FLEX.items():             # …in a legal shape
                xi_pos = pulp.lpSum(start[p["id"]] for p in players if p["position"] == position)
                problem += xi_pos >= lo
                problem += xi_pos <= hi

        # Budget.
        problem += pulp.lpSum(p["price"] * pick[p["id"]] for p in players) <= budget

        # Formation: each position within its (min, max) range, and `size` in total.
        # An exact shape is just a range where min == max.
        for position, (lo, hi) in bounds.items():
            pos_sum = pulp.lpSum(
                pick[p["id"]] for p in players if p["position"] == position
            )
            if lo == hi:
                problem += pos_sum == lo
            else:
                problem += pos_sum >= lo
                problem += pos_sum <= hi
        problem += pulp.lpSum(pick[p["id"]] for p in players) == size

        # At most `max_per_club` players from any one club.
        for club in {p["team"] for p in players}:
            problem += (
                pulp.lpSum(pick[p["id"]] for p in players if p["team"] == club)
                <= max_per_club
            )

        # Archetype bands (ADR-043): at least `count` picked players priced within [lo, hi]
        # (e.g. ≥3 low-cost ≤£4.5m, ≥1 premium ≥£9.0m). The objective (xP) is still maximised.
        for count, lo, hi in (band_minimums or []):
            problem += pulp.lpSum(
                pick[p["id"]] for p in players if lo <= p["price"] <= hi
            ) >= count

        # Differentials (ADR-044): at least `min_differentials` picked players ≤5% owned. The xP
        # objective picks the best qualifiers; players with no ownership data don't count.
        if min_differentials:
            problem += pulp.lpSum(
                pick[p["id"]] for p in players
                if (o := _selected_by(p)) is not None and o <= DIFFERENTIAL_MAX_OWNERSHIP
            ) >= min_differentials

        # Forced picks: lock chosen players in (1) or out (0). Benched players are
        # forced in too — they're part of the squad, just declared as bench.
        for pid in include_set | bench_set:
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
            # Bench-aware (ADR-045) designates the bench (picked but not started); otherwise the
            # declared bench (ADR-013).
            row["bench"] = (start[p["id"]].value() < 0.5) if start is not None \
                else (p["id"] in bench_set)
            selected.append(row)
    # Bench players sort to the end; within each group, by position then points. With no
    # bench declared the `bench` key is constant-False, so the order is unchanged.
    selected.sort(key=lambda p: (p["bench"], _POS_ORDER.get(p["position"], 9), -p["total_points"]))

    return {
        "status": status,
        "selected": selected,
        "total_points": sum(p["total_points"] for p in selected),
        "total_cost": round(sum(p["price"] for p in selected), 1),
    }


def archetype_bands(cheap=None, premium=None) -> list:
    """Translate low-cost / premium counts into `select_squad` `band_minimums` (ADR-043).

    `cheap` → ≥N players ≤ LOW_COST_MAX; `premium` → ≥M players ≥ PREMIUM_MIN. A None/0 count
    adds no band, so no archetypes → today's unconstrained build.
    """
    bands = []
    if cheap:
        bands.append((cheap, 0.0, LOW_COST_MAX))
    if premium:
        bands.append((premium, PREMIUM_MIN, 999.9))
    return bands


# The legal XI shapes (GK is always 1): DEF 3–5, MID 2–5, FWD 1–3, outfield sums to 10.
_XI_FORMATIONS = [(d, m, f) for d in (3, 4, 5) for m in (2, 3, 4, 5) for f in (1, 2, 3)
                  if d + m + f == 10]


def best_xi_points(players, scores) -> float:
    """The best legal XI's total score from a squad — a fast alternative to `best_legal_xi` (ADR-046).

    Group by position, sort each descending, and try every legal shape (GK 1; DEF 3–5, MID 2–5,
    FWD 1–3, outfield 10), summing the top-N per line. ~O(1) per squad (a handful of formations) and
    equal to `best_legal_xi`'s sum — used to rank transfers by their effect on the *fielded* XI.
    """
    by_pos: dict = {"GK": [], "DEF": [], "MID": [], "FWD": []}
    for p in players:
        by_pos.setdefault(p["position"], []).append(scores.get(p["id"], 0.0))
    for line in by_pos.values():
        line.sort(reverse=True)
    if not by_pos["GK"]:
        return 0.0
    best = 0.0
    for d, m, f in _XI_FORMATIONS:
        if len(by_pos["DEF"]) >= d and len(by_pos["MID"]) >= m and len(by_pos["FWD"]) >= f:
            total = (by_pos["GK"][0] + sum(by_pos["DEF"][:d])
                     + sum(by_pos["MID"][:m]) + sum(by_pos["FWD"][:f]))
            best = max(best, total)
    return best


def best_legal_xi(owned, scores) -> set:
    """The best legal starting XI (ids) from a 15-man squad, ranked on `scores` (id → value).

    The single primitive behind `analyse` (with no declared bench) and start/bench (ADR-040), so
    the two can't diverge on what the "optimal XI" is. Budget-unconstrained (the players are already
    owned); the best flexible formation (`XI_FLEX`).
    """
    result = select_squad(owned, budget=200.0, formation=XI_FLEX, size=11, scores=scores)
    return {p["id"] for p in result["selected"]}


def objective_scores(players, objective: str, upcoming=None) -> dict:
    """Per-player score {id: value} for the chosen squad objective (ADR-011).

    - "value" → points-per-£m (undefined price → 0);
    - "xp"    → Expected Points via player_xp (needs `upcoming` fixtures);
    - "xgi"   → expected goal involvements (None → 0.0); attacking, so GK/DEF ≈ 0;
    - anything else → last-season total_points (the default).
    """
    if objective == "value":
        return {
            p["id"]: (points_per_million(p["total_points"], p["price"]) or 0.0)
            for p in players
        }
    if objective == "xp":
        return {r["id"]: r["xp"] for r in player_xp(players, upcoming or [])}
    if objective == "xgi":
        # Expected goal involvements (ADR-015). None (unrefreshed/absent) → 0.0.
        return {p["id"]: (p["xgi"] or 0.0) for p in players}
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
