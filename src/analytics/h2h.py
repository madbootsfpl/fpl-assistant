"""Head-to-head against one rival — the projected gap, and what it is made of (ADR-161).

🏆 Leagues (ADR-141) answers *"what is my league doing?"* with effective ownership. This answers the narrower,
more actionable question the roadmap kept next to it: **"what do I need to do to catch them?"** — which needs
per-*manager* projections rather than per-player ones.

The whole module rests on one structural fact, and it is why this is worth having at all:

    **the players you both start cancel.**

Two managers in the same mini-league typically share most of their squad. Those shared players can score 90
points or 9 between them and it changes the gap by nothing — the entire head-to-head lives in the handful of
players only one of you starts, plus the captain. So the useful output is not two totals; it is the
**differential set**, priced.

Pure and offline: picks payloads and an xP map in, numbers out. The fetching lives at the edge, as in
`league.py`.

⚠️ **A picks payload is the last completed gameweek's**, because FPL only makes picks public after a deadline.
So this projects *the squad they had*, not the one they will field — they can transfer, and they can change
their captain. That limit is real, it is stated on the surface that renders this, and it does not make the
read useless: most managers make 0-1 transfers a week, and the differential set is stable across one of them.
"""

from src.analytics.league import _BENCH_FROM, _get


def _starters(payload):
    """`[(player_id, multiplier)]` for the players who actually score this gameweek.

    `multiplier` is FPL's own field and is taken at face value rather than re-derived: it already encodes the
    captain (2), the triple captain (3), a benched player (0) and — crucially — **Bench Boost**, which makes
    all fifteen count. Re-deriving it from `is_captain` and the 1-11/12-15 split would silently get every
    chipped gameweek wrong.
    """
    out = []
    for pk in _get(payload, "picks", []) or []:
        pid, mult = _get(pk, "element"), _get(pk, "multiplier")
        if pid is None:
            continue
        if mult is None:                      # a payload without the field: fall back to the position split
            mult = 2 if _get(pk, "is_captain") else (1 if (_get(pk, "position", 99) or 99) < _BENCH_FROM else 0)
        if mult:
            out.append((pid, mult))
    return out


def captain_of(payload):
    """The captained player's id, or None. Reads `is_captain` rather than the multiplier, so a triple captain
    is still just the captain."""
    for pk in _get(payload, "picks", []) or []:
        if _get(pk, "is_captain"):
            return _get(pk, "element")
    return None


def manager_projection(payload, xp_by_id) -> dict:
    """One manager's projected points: `{"xp", "captain", "starters", "chip"}`.

    Reuses the caller's `xp_by_id` — the same `decision_xp` map every other surface decides with (ADR-041).
    There is deliberately no second projection recipe here; a rival's squad is projected exactly the way your
    own is, or the comparison would be measuring the two models against each other rather than the two squads.
    """
    starters = _starters(payload)
    return {
        "xp": round(sum(xp_by_id.get(pid, 0.0) * mult for pid, mult in starters), 1),
        "captain": captain_of(payload),
        "starters": starters,
        "chip": _get(payload, "active_chip") or None,
    }


def _by_id(players):
    return {p["id"]: p for p in players or []}


def _edge_rows(only_mine, xp_by_id, index):
    """Differential players, most valuable first — `[{id, web_name, team, position, xp, multiplier}]`."""
    rows = []
    for pid, mult in only_mine:
        p = index.get(pid)
        rows.append({
            "id": pid,
            "web_name": p["web_name"] if p is not None else f"#{pid}",
            "team": p["team"] if p is not None else "",
            "position": p["position"] if p is not None else "",
            "multiplier": mult,
            "xp": round(xp_by_id.get(pid, 0.0) * mult, 1),
        })
    rows.sort(key=lambda r: -r["xp"])
    return rows


def h2h_gap(mine, theirs, xp_by_id, players=None) -> dict:
    """The projected head-to-head, decomposed (ADR-161).

    `mine` and `theirs` are picks payloads. Returns both projections, the signed `gap` (positive = you are
    ahead), the **shared** starters that cancel, and each side's differentials priced by xP × multiplier.

    `shared_xp` is reported and then deliberately set aside. It is usually the large majority of both totals
    and it is the part you cannot do anything about — printing it is what makes the small `gap` believable
    rather than looking like a rounding error on two big numbers.
    """
    mine_proj, their_proj = manager_projection(mine, xp_by_id), manager_projection(theirs, xp_by_id)
    index = _by_id(players)

    my_mult = dict(mine_proj["starters"])
    their_mult = dict(their_proj["starters"])
    shared_ids = set(my_mult) & set(their_mult)

    # A player you both start at the SAME multiplier cancels exactly. If only one of you captains them, they do
    # not cancel — the extra copy is a differential in its own right, and it is the most common one there is.
    shared_xp = 0.0
    my_only, their_only = [], []
    for pid in shared_ids:
        common = min(my_mult[pid], their_mult[pid])
        shared_xp += xp_by_id.get(pid, 0.0) * common
        if my_mult[pid] > common:
            my_only.append((pid, my_mult[pid] - common))
        elif their_mult[pid] > common:
            their_only.append((pid, their_mult[pid] - common))
    my_only += [(pid, m) for pid, m in my_mult.items() if pid not in shared_ids]
    their_only += [(pid, m) for pid, m in their_mult.items() if pid not in shared_ids]

    return {
        "mine": mine_proj,
        "theirs": their_proj,
        "gap": round(mine_proj["xp"] - their_proj["xp"], 1),
        "shared_count": len(shared_ids),
        "shared_xp": round(shared_xp, 1),
        "my_edge": _edge_rows(my_only, xp_by_id, index),
        "their_edge": _edge_rows(their_only, xp_by_id, index),
        "same_captain": (mine_proj["captain"] is not None
                         and mine_proj["captain"] == their_proj["captain"]),
    }


def catch_up_note(gap: dict, *, my_name: str = "You", their_name: str = "They") -> str:
    """One sentence saying where the head-to-head actually sits, and on whom.

    Named after the question it answers. It leads with the differentials rather than the totals because the
    totals are mostly the same players — a reader told *"52.1 vs 49.8"* learns far less than one told *"three
    players separate you, and their captain is worth 4.2 more than yours."*
    """
    if not gap:
        return ""
    n = len(gap["my_edge"]) + len(gap["their_edge"])
    if n == 0:
        return (f"Identical starting elevens, same captain — this gameweek cannot separate you "
                f"({gap['shared_count']} shared players, {gap['shared_xp']} xP each).")
    lead, margin = (my_name, gap["gap"]) if gap["gap"] >= 0 else (their_name, -gap["gap"])
    who = "differential" if n == 1 else "differentials"
    top = (gap["their_edge"] or gap["my_edge"])[:1]
    detail = f" The biggest single one is {top[0]['web_name']} ({top[0]['xp']} xP)." if top else ""
    return (f"{gap['shared_count']} shared starters cancel out ({gap['shared_xp']} xP each way). "
            f"{n} {who} decide it, and on projection {lead} lead by {margin:.1f}.{detail}")
