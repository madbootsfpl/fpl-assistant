"""Who a player may legally change places with (ADR-246).

⭐⭐⭐ **The rule stays on this side.** FPL's formation limits — one keeper, 3–5 defenders, 2–5 midfielders,
1–3 forwards — live in `XI_FLEX` and are enforced by `legal_xi_issues`. Working them out again in Dart
would be a second implementation of a rule the engine already owns, and ADR-151→156 is this project's
record of one fact being re-taught to six surfaces one at a time.

⚠️⚠️ **The first version built a TWELVE-MAN XI and validated it happily**, because `legal_xi_issues` checks
position ranges and not the size of the list. The visible symptom was a goalkeeper offered a swap with a
forward. ⭐ *A validator answers the question it was asked, and "is this eleven" was never asked.*
"""

import pytest

from src.analytics.optimizer import XI_FLEX
from src.service.answers import _legal_swaps
from src.storage import Storage


@pytest.fixture(scope="module")
def store():
    s = Storage()
    yield s
    s.close()


@pytest.fixture(scope="module")
def squad(store):
    """A legal fifteen, and a legal declared bench (one keeper plus three outfielders)."""
    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked, per_club = [], {}
    for p in store.get_players():
        if need.get(p["position"], 0) and per_club.get(p["team"], 0) < 3 and len(picked) < 15:
            picked.append(dict(p))
            need[p["position"]] -= 1
            per_club[p["team"]] = per_club.get(p["team"], 0) + 1
    keepers = [p for p in picked if p["position"] == "GK"]
    outfield = [p for p in picked if p["position"] != "GK"]
    bench = [keepers[1]["id"]] + [p["id"] for p in outfield[-3:]]
    return picked, bench


def test_a_keeper_may_only_change_places_with_the_other_keeper(squad):
    """⚠️ The one everybody gets wrong first. There is exactly one GK slot in an XI."""
    owned, bench = squad
    swaps = {row["id"]: row["with"] for row in _legal_swaps(owned, bench)}
    keepers = [p["id"] for p in owned if p["position"] == "GK"]
    assert len(keepers) == 2
    for gk in keepers:
        assert swaps[gk] == [k for k in keepers if k != gk], (
            f"keeper {gk} was offered {swaps[gk]}"
        )


def test_every_offered_swap_produces_a_legal_eleven(squad):
    """⭐ The property, checked exhaustively rather than sampled: apply each offered swap and validate."""
    from src.analytics.optimizer import legal_xi_issues

    owned, bench = squad
    by_id = {p["id"]: p for p in owned}
    benched = set(bench)
    starters = [p for p in owned if p["id"] not in benched]

    for row in _legal_swaps(owned, bench):
        player = by_id[row["id"]]
        for other_id in row["with"]:
            other = by_id[other_id]
            leaving, arriving = (other, player) if row["benched"] else (player, other)
            after = [p for p in starters if p["id"] != leaving["id"]] + [arriving]
            assert len(after) == 11, f"{len(after)} players — this is not an XI"
            assert not legal_xi_issues(after), (
                f"{player['web_name']} ↔ {other['web_name']} gives {legal_xi_issues(after)}"
            )


def test_an_illegal_swap_is_never_offered(squad):
    """⚠️⚠️ **The half a "produces a legal eleven" test cannot see.** A function returning *no* options at
    all would pass that one — ⭐ *checking that everything offered is legal says nothing about what was
    left out.* So this checks the converse: every pair NOT offered would genuinely break the formation.
    """
    from src.analytics.optimizer import legal_xi_issues

    owned, bench = squad
    by_id = {p["id"]: p for p in owned}
    benched = set(bench)
    starters = [p for p in owned if p["id"] not in benched]
    swaps = {row["id"]: (row["benched"], set(row["with"])) for row in _legal_swaps(owned, bench)}

    missed = []
    for player in owned:
        on_bench, offered = swaps[player["id"]]
        candidates = starters if on_bench else [by_id[i] for i in bench]
        for other in candidates:
            leaving, arriving = (other, player) if on_bench else (player, other)
            after = [p for p in starters if p["id"] != leaving["id"]] + [arriving]
            legal = len(after) == 11 and not legal_xi_issues(after)
            if legal and other["id"] not in offered:
                missed.append((player["web_name"], other["web_name"]))
    assert not missed, f"legal swaps that were never offered: {missed}"


def test_the_lone_forward_cannot_be_benched_for_a_midfielder(squad):
    """⭐ The rule doing real work: `XI_FLEX` requires at least one forward, so dropping the only one is
    illegal however good the replacement looks.

    ⚠️ **The shared fixture could not reach this**, because its XI happens to carry two forwards — so this
    builds a bench that leaves exactly one. ⭐ *A test that skips when the data is not interesting is a
    test that reports coverage it does not have*, and the interesting case is one bench away.
    """
    owned, _ = squad
    by_id = {p["id"]: p for p in owned}
    keepers = [p for p in owned if p["position"] == "GK"]
    forwards = [p for p in owned if p["position"] == "FWD"]
    mids = [p for p in owned if p["position"] == "MID"]
    # 1 GK + 2 of the 3 forwards + 1 midfielder → an XI with exactly one forward.
    bench = [keepers[1]["id"], forwards[0]["id"], forwards[1]["id"], mids[-1]["id"]]

    starters = [p for p in owned if p["id"] not in set(bench)]
    lone = [p for p in starters if p["position"] == "FWD"]
    assert len(lone) == XI_FLEX["FWD"][0] == 1, (
        f"the fixture is wrong — {len(lone)} forwards in the XI"
    )
    forwards = lone

    swaps = {row["id"]: row["with"] for row in _legal_swaps(owned, bench)}
    for offered in swaps[forwards[0]["id"]]:
        assert by_id[offered]["position"] == "FWD", (
            f"the only forward was offered a swap with a {by_id[offered]['position']}"
        )


def test_no_declared_bench_means_no_swaps(squad):
    """⚠️ Without a declared bench there is no "who is on the pitch" to change — ⭐ *offering a swap
    against an XI the server derived itself would move a player the manager never placed.*"""
    owned, _ = squad
    assert _legal_swaps(owned, []) == []
