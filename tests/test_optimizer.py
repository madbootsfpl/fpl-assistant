"""Tests for the squad optimiser (integer programming).

Each test uses a small hand-built player set where the optimum is known, so we can
check the solver picks it and respects each constraint.
"""

from src.analytics.optimizer import resolve_players, select_squad
from src.ui.squad import render_squad


def p(id, position, price, points, team=None, name=None):
    return {
        "id": id,
        "web_name": name or f"P{id}",
        "position": position,
        "price": price,
        "total_points": points,
        "team": team or f"T{id}",   # distinct team by default (club cap irrelevant)
    }


def formation_11(points_by_pos=None, price=4.0):
    """Exactly one legal XI (1 GK, 4 DEF, 4 MID, 2 FWD), distinct teams."""
    counts = {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}
    players, i = [], 1
    for pos, n in counts.items():
        for _ in range(n):
            players.append(p(i, pos, price, 10))
            i += 1
    return players


def test_selects_a_legal_xi():
    result = select_squad(formation_11(), budget=80)

    assert result["status"] == "Optimal"
    assert len(result["selected"]) == 11
    counts = {}
    for s in result["selected"]:
        counts[s["position"]] = counts.get(s["position"], 0) + 1
    assert counts == {"GK": 1, "DEF": 4, "MID": 4, "FWD": 2}


def test_maximises_points_within_a_position():
    # 5 DEF available for 4 slots; the low-scorer (id 99) should be dropped.
    players = formation_11()
    players = [x for x in players if x["position"] != "DEF"]
    players += [p(20, "DEF", 4.0, 10), p(21, "DEF", 4.0, 10),
                p(22, "DEF", 4.0, 10), p(23, "DEF", 4.0, 10),
                p(99, "DEF", 4.0, 1)]   # clearly worse

    result = select_squad(players, budget=80)
    assert 99 not in {s["id"] for s in result["selected"]}


def test_respects_the_budget_knapsack():
    # 9 forced cheap players (£4 each = £36), then 2 FWD slots with £15 left.
    # FWD A(10pts,£10) B(9,£9) C(8,£6): greedy takes A and stalls; ILP takes B+C = 17.
    base = [x for x in formation_11() if x["position"] != "FWD"]  # 9 players, £36
    fwd = [p(50, "FWD", 10.0, 10, name="A"),
           p(51, "FWD", 9.0, 9, name="B"),
           p(52, "FWD", 6.0, 8, name="C")]

    result = select_squad(base + fwd, budget=36 + 15)
    picked_fwd = {s["web_name"] for s in result["selected"] if s["position"] == "FWD"}
    assert picked_fwd == {"B", "C"}


def test_enforces_max_three_per_club():
    # 4 strong DEF all from club X, plus one DEF from club Y; ≤3/club forces Y in.
    players = [x for x in formation_11() if x["position"] != "DEF"]
    players += [p(30, "DEF", 4.0, 10, team="X"), p(31, "DEF", 4.0, 10, team="X"),
                p(32, "DEF", 4.0, 10, team="X"), p(33, "DEF", 4.0, 10, team="X"),
                p(34, "DEF", 4.0, 9, team="Y")]

    result = select_squad(players, budget=80)
    def_teams = [s["team"] for s in result["selected"] if s["position"] == "DEF"]
    assert def_teams.count("X") <= 3
    assert "Y" in def_teams


def test_reports_infeasible_when_budget_too_low():
    result = select_squad(formation_11(price=4.0), budget=1.0)  # can't afford 11

    assert result["status"] != "Optimal"
    assert result["selected"] == []


def test_include_forces_a_weak_player_in_and_flags_it():
    # A 5th DEF (id 99) scores less, so it wouldn't normally be picked — force it in.
    players = [x for x in formation_11() if x["position"] != "DEF"]
    players += [p(20, "DEF", 4.0, 10), p(21, "DEF", 4.0, 10),
                p(22, "DEF", 4.0, 10), p(23, "DEF", 4.0, 10),
                p(99, "DEF", 4.0, 1)]

    result = select_squad(players, budget=80, include_ids=[99])
    picked = {s["id"]: s for s in result["selected"]}
    assert 99 in picked
    assert picked[99]["forced"] is True


def test_exclude_removes_a_player():
    # Two forwards score 10, a third 1; excluding a 10-scorer forces the 1-scorer in.
    base = [x for x in formation_11() if x["position"] != "FWD"]
    fwd = [p(50, "FWD", 4.0, 10), p(51, "FWD", 4.0, 10), p(52, "FWD", 4.0, 1)]

    result = select_squad(base + fwd, budget=80, exclude_ids=[50])
    ids = {s["id"] for s in result["selected"]}
    assert 50 not in ids
    assert 52 in ids   # the weak forward has to come in


def test_forcing_two_goalkeepers_is_infeasible():
    players = formation_11() + [p(200, "GK", 4.0, 10)]   # a 2nd GK exists
    result = select_squad(players, budget=80, include_ids=[1, 200])  # force both GKs
    assert result["status"] != "Optimal"


def test_resolve_unique_name():
    players = [p(1, "MID", 8.0, 100, name="Haaland")]
    ids, errors = resolve_players(players, ["haaland"])   # case-insensitive
    assert ids == [1]
    assert errors == []


def test_resolve_ambiguous_name_errors_with_candidates():
    players = [p(1, "MID", 8.0, 100, team="NFO", name="Wilson"),
               p(2, "FWD", 6.0, 80, team="FUL", name="Wilson")]
    ids, errors = resolve_players(players, ["Wilson"])
    assert ids == []
    assert len(errors) == 1 and "matches 2 players" in errors[0]


def test_resolve_disambiguates_with_team():
    players = [p(1, "MID", 8.0, 100, team="NFO", name="Wilson"),
               p(2, "FWD", 6.0, 80, team="FUL", name="Wilson")]
    ids, errors = resolve_players(players, ["Wilson:NFO"])
    assert ids == [1]
    assert errors == []


def test_resolve_not_found_errors():
    ids, errors = resolve_players([p(1, "MID", 8.0, 100, name="Haaland")], ["Nobody"])
    assert ids == []
    assert "No player matches" in errors[0]


def test_render_squad_shows_players_and_totals():
    result = {
        "status": "Optimal",
        "selected": [
            {"position": "GK", "web_name": "Raya", "team": "ARS",
             "price": 6.0, "total_points": 162},
        ],
        "total_points": 162,
        "total_cost": 6.0,
    }
    out = render_squad(result, budget=80)

    assert "Raya" in out
    assert "162" in out
    assert "£6.0m" in out
    assert "Total" in out


def test_render_squad_reports_infeasible():
    out = render_squad(
        {"status": "Infeasible", "selected": [], "total_points": 0, "total_cost": 0.0},
        budget=40,
    )
    assert "No legal XI" in out
    assert "Infeasible" in out
