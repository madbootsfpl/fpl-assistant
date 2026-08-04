"""Tests for the team analyser (ADR-031).

The analytics is pure — squad rows + XI ids + xP → indicators. Cover the XI/bench
split, projected-xP-is-XI-only, value, availability issues, weakest links, top pick,
and club concentration.
"""

from src.analytics import analyse_squad


def _p(pid, pos, team, price, status="a", chance=None):
    return {"id": pid, "position": pos, "team": team, "price": price,
            "web_name": f"P{pid}", "status": status, "chance": chance}


# A tiny 4-player "squad": 3 in the XI, 1 on the bench.
SQUAD = [_p(1, "MID", "AAA", 8.0), _p(2, "FWD", "BBB", 10.0),
         _p(3, "DEF", "AAA", 5.0), _p(4, "MID", "CCC", 4.5)]
XP = {1: 30.0, 2: 40.0, 3: 20.0, 4: 5.0}
XI = [1, 2, 3]        # P4 is the bench


def test_projected_xp_is_the_xi_only():
    a = analyse_squad(SQUAD, XI, XP)
    assert a["projected_xp"] == 90.0     # 30 + 40 + 20, NOT the bench's 5
    assert a["bench_xp"] == 5.0


def test_value_is_the_whole_squad():
    a = analyse_squad(SQUAD, XI, XP)
    assert a["value"] == 27.5            # 8 + 10 + 5 + 4.5


def test_xi_and_bench_split():
    a = analyse_squad(SQUAD, XI, XP)
    assert {p["id"] for p in a["xi"]} == {1, 2, 3}
    assert [p["id"] for p in a["bench"]] == [4]


def test_weakest_links_and_top_pick_are_from_the_xi():
    a = analyse_squad(SQUAD, XI, XP)
    assert a["weakest"][0]["id"] == 3           # lowest-xP XI player (20.0)
    assert a["top_pick"]["id"] == 2             # highest-xP XI player (40.0)
    assert 4 not in {w["id"] for w in a["weakest"]}   # the bench isn't a "weak link"


def test_availability_issues_flag_injured_and_doubtful():
    squad = [_p(1, "MID", "AAA", 8.0, status="i"),
             _p(2, "FWD", "BBB", 10.0, status="d", chance=50),
             _p(3, "DEF", "AAA", 5.0)]
    a = analyse_squad(squad, [1, 2, 3], {1: 1, 2: 1, 3: 1})
    ids = {p["id"] for p in a["issues"]}
    assert ids == {1, 2}                        # injured + doubtful; the fit one isn't flagged


def test_club_concentration_flags_clubs_at_the_cap():
    squad = [_p(i, "MID", "AAA", 5.0) for i in range(1, 4)] + [_p(4, "DEF", "BBB", 5.0)]
    a = analyse_squad(squad, [1, 2, 3, 4], {i: 1 for i in range(1, 5)}, max_per_club=3)
    assert a["concentrated_clubs"] == ["AAA"]   # 3 from AAA hits the cap; BBB (1) doesn't


def test_xi_is_ordered_by_position_then_xp():
    a = analyse_squad(SQUAD, XI, XP)
    positions = [p["position"] for p in a["xi"]]
    assert positions == ["DEF", "MID", "FWD"]   # GK/DEF/MID/FWD order


def test_sort_xp_orders_the_xi_by_xp():
    a = analyse_squad(SQUAD, XI, XP, sort="xp")
    assert [p["id"] for p in a["xi"]] == [2, 1, 3]   # 40, 30, 20 — strongest first


def test_per_gameweek_is_carried_into_summaries_when_given():
    gw = {1: {1: 10.0, 2: 20.0}}
    a = analyse_squad(SQUAD, XI, XP, by_gameweek_by_id=gw, gameweeks=[1, 2])
    assert a["gameweeks"] == [1, 2]
    p1 = next(p for p in a["xi"] if p["id"] == 1)
    assert p1["by_gameweek"] == {1: 10.0, 2: 20.0}
    # a player with no breakdown gets an empty dict, not a crash
    assert next(p for p in a["xi"] if p["id"] == 2)["by_gameweek"] == {}
