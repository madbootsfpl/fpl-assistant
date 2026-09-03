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
So this reads *the squad they had* and projects the gameweek **still to come** — they can still transfer, and
they can change their captain. That limit is real, it is stated on the surface that renders this, and it does
not make the read useless: most managers make 0-1 transfers a week, and the differential set is stable across
one of them.

⚠️ **Because the projection points forward, a chip played last week must not be projected into next week**
(ADR-177). The eleven is therefore derived from `position` and `is_captain` rather than from FPL's stored
`multiplier`, which records how the *completed* gameweek was scored. Free Hit is the one case counting
differently cannot fix — see `reverts_next_gameweek`.
"""

from src.analytics.league import _BENCH_FROM, _get


def _starters(payload):
    """`[(player_id, multiplier)]` for the eleven they will field **next** gameweek.

    Derived from `position` (1-11 start, 12-15 sit) and `is_captain` (×2) — deliberately **not** from FPL's
    stored `multiplier` (ADR-177).

    ADR-161 read that multiplier at face value, on the grounds that it already encodes Bench Boost and the
    triple captain, and that re-deriving it *"would silently get every chipped gameweek wrong"*. That is true
    of the question it was written about — **what did this squad score last week** — and this module asks a
    different one: **what will it score next week**, when the chip is spent, the bench is a bench again and a
    triple captain is a captain.

    Read forward, it priced a bench-boosted manager on **fifteen** players against a rival's eleven. The
    failure is asymmetric, so it never looked like an error; it looked like a ten-point lead.

    For an unchipped squad this reproduces FPL's multipliers **exactly** — which is why it is applied
    unconditionally rather than behind a chip check. It can only change a week that was chipped.
    """
    picks = _get(payload, "picks", []) or []
    if picks and all(_get(pk, "position") is not None for pk in picks):
        out = []
        for pk in picks:
            pid = _get(pk, "element")
            if pid is not None and _get(pk, "position") < _BENCH_FROM:
                out.append((pid, 2 if _get(pk, "is_captain") else 1))
        return out

    # No usable positions — fall back to the stored multiplier, which is exactly what shipped before ADR-177.
    # A slightly wrong comparison beats no comparison, and this is strictly no worse than the old behaviour.
    out = []
    for pk in picks:
        pid, mult = _get(pk, "element"), _get(pk, "multiplier")
        if pid is not None and mult:
            out.append((pid, mult))
    return out


CHIP_NAMES = {"bboost": "Bench Boost", "3xc": "Triple Captain",
              "freehit": "Free Hit", "wildcard": "Wildcard"}


def chip_name(code) -> str:
    """A chip's display name. An unknown code is returned as-is rather than hidden — if FPL adds one, the
    surface should say something odd rather than say nothing."""
    return CHIP_NAMES.get(code, code or "")


def reverts_next_gameweek(payload) -> bool:
    """True when the squad in this payload **will not exist** next gameweek.

    Free Hit is the one chip a different count cannot repair. Bench Boost and Triple Captain change how the
    *same* fifteen are scored, so dropping the chip projects them correctly; a Free Hit squad is discarded
    wholesale at the deadline and the previous squad comes back. Projecting it forward would price a team
    nobody will own.

    FPL does not publish the reverted squad — but it published it the week before, which is what the caller
    reads instead.
    """
    return (_get(payload, "active_chip") or "") == "freehit"


def captain_of(payload):
    """The captained player's id, or None. Reads `is_captain` rather than the multiplier, so a triple captain
    is still just the captain."""
    for pk in _get(payload, "picks", []) or []:
        if _get(pk, "is_captain"):
            return _get(pk, "element")
    return None


def manager_projection(payload, xp_by_id) -> dict:
    """One manager's projected points for the **next** gameweek: `{"xp", "captain", "starters", "chip"}`.

    `chip` is what they played in the *completed* gameweek, and it is reported rather than applied — it is
    spent, so it changes nothing about next week except that a surface should say it happened (ADR-177).

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
