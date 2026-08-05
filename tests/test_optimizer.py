"""Tests for the squad optimiser (integer programming).

Each test uses a small hand-built player set where the optimum is known, so we can
check the solver picks it and respects each constraint.
"""

import pytest

from src.analytics.optimizer import (
    LOW_COST_MAX,
    PREMIUM_MIN,
    SQUAD_15,
    XI_FLEX,
    archetype_bands,
    available_players,
    best_legal_xi,
    is_unavailable,
    legal_xi_issues,
    objective_scores,
    resolve_players,
    select_squad,
)
from src.ui.squad import formation_str, render_loaded_squad, render_squad


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


def squad_pool(price=4.0):
    """More than enough players per position to fill a 15-man squad (2/5/5/3).

    Distinct teams (so the club cap never bites) and one extra per position, so the
    solver must actually leave someone out rather than take everyone.
    """
    counts = {"GK": 3, "DEF": 6, "MID": 6, "FWD": 4}   # SQUAD_15 + 1 spare each
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


def test_selects_a_full_15_man_squad():
    # The full FPL shape (2/5/5/3) with a spare per position; budget is ample.
    result = select_squad(squad_pool(), budget=100.0, formation=SQUAD_15)

    assert result["status"] == "Optimal"
    assert len(result["selected"]) == 15
    counts = {}
    for s in result["selected"]:
        counts[s["position"]] = counts.get(s["position"], 0) + 1
    assert counts == SQUAD_15


def test_full_squad_respects_budget_and_club_cap():
    # All players £4m → 15 must cost £60m; the ≤3/club cap still holds over the 15.
    result = select_squad(squad_pool(price=4.0), budget=100.0, formation=SQUAD_15)

    assert result["total_cost"] <= 100.0
    from collections import Counter
    by_club = Counter(s["team"] for s in result["selected"])
    assert max(by_club.values()) <= 3


def test_full_squad_forces_a_cheap_bench_in():
    # The manager's workflow (ADR-012): --include locks cheap bench players into the 15.
    pool = squad_pool()
    result = select_squad(pool, budget=100.0, formation=SQUAD_15, include_ids=[1])  # a GK

    picked = {s["id"] for s in result["selected"]}
    assert 1 in picked
    assert next(s for s in result["selected"] if s["id"] == 1)["forced"] is True


def test_bench_players_are_forced_in_tagged_and_sorted_last():
    # ADR-013: --bench forces players into the 15, tags them bench, sorts them to the end.
    pool = squad_pool()
    result = select_squad(pool, budget=100.0, formation=SQUAD_15, bench_ids=[1, 7])  # GK+DEF

    selected = result["selected"]
    assert len(selected) == 15
    benched = [s for s in selected if s["bench"]]
    assert {s["id"] for s in benched} == {1, 7}          # both forced in
    assert all(not s["bench"] for s in selected[:-2])    # bench is last
    assert all(s["bench"] for s in selected[-2:])
    # A benched player is tagged bench, not "forced" (that flag is for --include).
    assert benched[0]["bench"] is True and benched[0]["forced"] is False


def _shape_pool():
    """1 GK + strong DEF (10), medium MID (5), weak FWD (1) — best legal XI is 5-4-1."""
    return (
        [p(1, "GK", 4.0, 3), p(2, "GK", 4.0, 2)]
        + [p(10 + i, "DEF", 4.0, 10) for i in range(6)]
        + [p(20 + i, "MID", 4.0, 5) for i in range(6)]
        + [p(30 + i, "FWD", 4.0, 1) for i in range(3)]
    )


def test_flexible_formation_picks_the_best_legal_shape():
    from collections import Counter
    result = select_squad(_shape_pool(), budget=100.0, formation=XI_FLEX, size=11)

    assert result["status"] == "Optimal"
    assert len(result["selected"]) == 11
    counts = Counter(s["position"] for s in result["selected"])
    assert counts["GK"] == 1
    assert 3 <= counts["DEF"] <= 5 and 2 <= counts["MID"] <= 5 and 1 <= counts["FWD"] <= 3
    # Strong defenders → the solver maxes DEF: a 5-4-1, not the fixed 4-4-2.
    assert (counts["DEF"], counts["MID"], counts["FWD"]) == (5, 4, 1)


def test_pinned_formation_is_honoured():
    from collections import Counter
    # A pinned 3-5-2 (size derives from the exact shape); overrides the best-shape choice.
    result = select_squad(_shape_pool(), budget=100.0,
                          formation={"GK": 1, "DEF": 3, "MID": 5, "FWD": 2})

    counts = Counter(s["position"] for s in result["selected"])
    assert (counts["DEF"], counts["MID"], counts["FWD"]) == (3, 5, 2)


def test_range_formation_without_size_raises():
    # A range formation has an ambiguous total — `size` is required (fail loud).
    with pytest.raises(ValueError):
        select_squad(formation_11(), budget=80.0, formation=XI_FLEX)


def test_no_bench_leaves_the_order_unchanged():
    # Regression: with no bench declared, every row is bench=False and the order is the
    # same position-then-points sort as before (bench sort key is constant-False).
    pool = squad_pool()
    plain = select_squad(pool, budget=100.0, formation=SQUAD_15)

    assert all(s["bench"] is False for s in plain["selected"])
    positions = [s["position"] for s in plain["selected"]]
    order = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
    assert positions == sorted(positions, key=lambda x: order[x])   # grouped GK→DEF→MID→FWD


def test_objective_scores_points():
    players = [p(1, "MID", 8.0, 100)]
    assert objective_scores(players, "points") == {1: 100}


def test_objective_scores_value_guards_zero_price():
    players = [p(1, "MID", 8.0, 100), p(2, "FWD", 0.0, 50)]
    scores = objective_scores(players, "value")
    assert scores[1] == 12.5   # 100 / 8
    assert scores[2] == 0.0    # price 0 → guarded


def test_objective_scores_xgi_reads_xgi_and_coerces_none():
    players = [{"id": 1, "xgi": 14.7}, {"id": 2, "xgi": None}]
    scores = objective_scores(players, "xgi")
    assert scores == {1: 14.7, 2: 0.0}   # None (unrefreshed/absent) → 0.0


def test_objective_scores_xp_reuses_player_xp():
    players = [{
        "id": 1, "team_id": 1, "points_per_game": 5.0, "status": "a",
        "ep_next": 4.0, "web_name": "P", "position": "MID", "team": "ARS",
    }]
    upcoming = [{
        "event": 1, "team_h": 1, "team_a": 2, "home": "ARS", "away": "BUR",
        "team_h_difficulty": 3, "team_a_difficulty": 3,
        "home_team_strength": None, "away_team_strength": None,
    }]
    scores = objective_scores(players, "xp", upcoming)
    assert scores == {1: 5.0}   # ppg 5.0 × multiplier(diff 3) = 1.0


def test_objective_changes_which_players_are_picked():
    base = [x for x in formation_11() if x["position"] != "FWD"]   # 9 cheap players
    fwd = [p(50, "FWD", 10.0, 20, name="A"),   # value 2.0
           p(51, "FWD", 4.0, 10, name="B"),    # value 2.5
           p(52, "FWD", 4.0, 9, name="C")]     # value 2.25
    players = base + fwd

    points = select_squad(players, budget=80, scores=objective_scores(players, "points"))
    value = select_squad(players, budget=80, scores=objective_scores(players, "value"))

    points_fwd = {s["web_name"] for s in points["selected"] if s["position"] == "FWD"}
    value_fwd = {s["web_name"] for s in value["selected"] if s["position"] == "FWD"}
    assert "A" in points_fwd       # points keeps the high scorer
    assert "A" not in value_fwd    # value drops the expensive one for B + C


def test_default_scores_maximise_points():
    players = formation_11()
    default = select_squad(players, budget=80)
    explicit = select_squad(players, budget=80, scores=objective_scores(players, "points"))
    assert {s["id"] for s in default["selected"]} == {s["id"] for s in explicit["selected"]}


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


def test_render_squad_shows_xp_columns_under_the_xp_objective():
    # US-121: under --objective xp the table shows what we optimised — xMins + xP + projected total —
    # not last-season Pts.
    result = {
        "status": "Optimal",
        "selected": [
            {"position": "FWD", "web_name": "Haaland", "team": "MCI", "price": 15.5,
             "total_points": 250, "xp": 34.7, "minutes_weight": 0.82},
        ],
        "total_points": 250,
        "total_cost": 15.5,
    }
    out = render_squad(result, budget=100, objective="xp", full=True)
    assert "xMins" in out and "xP" in out
    assert " 74" in out and "34.7" in out           # 0.82 × 90 → 74 expected minutes; the xP
    assert "projected 34.7 xP" in out               # the total is projected xP, not last-season pts

    points_out = render_squad(result, budget=100, objective="points", full=True)
    assert "Pts" in points_out and "250" in points_out and "xMins" not in points_out


def test_render_squad_marks_forced_players():
    result = {
        "status": "Optimal",
        "selected": [
            {"position": "MID", "web_name": "Garner", "team": "EVE",
             "price": 6.0, "total_points": 159, "forced": True},
        ],
        "total_points": 159,
        "total_cost": 6.0,
    }
    out = render_squad(result, budget=80)

    assert "*" in out
    assert "forced in" in out


def test_render_squad_states_the_objective():
    result = {
        "status": "Optimal",
        "selected": [{"position": "MID", "web_name": "X", "team": "ARS",
                      "price": 6.0, "total_points": 100, "forced": False}],
        "total_points": 100,
        "total_cost": 6.0,
    }
    out = render_squad(result, budget=80, objective="value")
    assert "value" in out


def test_render_squad_reports_infeasible():
    out = render_squad(
        {"status": "Infeasible", "selected": [], "total_points": 0, "total_cost": 0.0},
        budget=40,
    )
    assert "No legal XI" in out
    assert "Infeasible" in out


def test_render_full_squad_says_15_and_adds_the_caveat():
    result = {
        "status": "Optimal",
        "selected": [{"position": "GK", "web_name": "Raya", "team": "ARS",
                      "price": 6.0, "total_points": 162, "forced": False}],
        "total_points": 162,
        "total_cost": 6.0,
    }
    out = render_squad(result, budget=100, full=True)

    assert "15-man squad" in out           # names the mode
    assert "not a weekly" in out           # the ADR-012 caveat is shown
    assert "--bench" in out                # points at the declared-bench workflow


def _full_squad_with_bench(bench_count, starter_count):
    """A result of `starter_count` starters + `bench_count` bench, for render tests."""
    selected = [
        {"position": "MID", "web_name": f"S{i}", "team": "ARS",
         "price": 6.0, "total_points": 100, "forced": False, "bench": False}
        for i in range(starter_count)
    ]
    selected += [
        {"position": "GK", "web_name": f"B{i}", "team": "TOT",
         "price": 4.0, "total_points": 5, "forced": False, "bench": True}
        for i in range(bench_count)
    ]
    total = sum(p["total_points"] for p in selected)
    return {"status": "Optimal", "selected": selected,
            "total_points": total, "total_cost": round(sum(p["price"] for p in selected), 1)}


def test_render_bench_section_marker_and_starters_subtotal():
    out = render_squad(_full_squad_with_bench(bench_count=2, starter_count=13),
                       budget=100, full=True)

    assert "Bench:" in out                 # the bench heading
    assert "**" in out                     # bench marker
    assert "** = benched" in out           # legend
    assert "Starters (13): 1300 pts" in out   # the honest subtotal (13 × 100)


def _bench_row(pos, bench=False):
    return {"position": pos, "web_name": pos, "team": "ARS",
            "price": 5.0, "total_points": 50, "forced": False, "bench": bench}


def _full_squad(starter_positions, bench_positions):
    selected = ([_bench_row(p) for p in starter_positions]
                + [_bench_row(p, True) for p in bench_positions])
    return {"status": "Optimal", "selected": selected,
            "total_points": sum(r["total_points"] for r in selected),
            "total_cost": round(sum(r["price"] for r in selected), 1)}


def test_render_full_legal_bench_calls_starters_the_xi():
    # A legal 4-4-2 XI + a legal 4-man bench (backup GK + 1 DEF/MID/FWD).
    starters = ["GK"] + ["DEF"] * 4 + ["MID"] * 4 + ["FWD"] * 2
    out = render_squad(_full_squad(starters, ["GK", "DEF", "MID", "FWD"]),
                       budget=100, full=True)
    assert "Starters (11)" in out
    assert "is your XI" in out               # legal → no warning


def test_render_full_illegal_bench_is_warned(monkeypatch):
    # Bench all 3 forwards (+ a GK) → starters have 0 FWD → illegal.
    starters = ["GK"] + ["DEF"] * 5 + ["MID"] * 5           # 5-5-0, 11 players
    out = render_squad(_full_squad(starters, ["GK", "FWD", "FWD", "FWD"]),
                       budget=100, full=True)
    assert "doesn't leave a legal XI" in out
    assert "0 FWD (need 1-3)" in out
    assert "is your XI" not in out           # warned, but still printed the squad
    assert "Total:" in out


def _xi(counts):
    """Build a starters list from {position: n} for legal_xi_issues tests."""
    return [{"position": pos} for pos, n in counts.items() for _ in range(n)]


def test_is_unavailable_by_status():
    assert is_unavailable({"status": "i"})       # injured
    assert is_unavailable({"status": "s"})       # suspended
    assert is_unavailable({"status": "u"})       # departed
    assert not is_unavailable({"status": "a"})   # available
    assert not is_unavailable({"status": "d"})   # doubtful — might play


def test_available_players_excludes_unavailable_but_keeps_forced():
    players = [
        {"id": 1, "status": "a"},   # available → pool
        {"id": 2, "status": "i"},   # injured, not forced → excluded
        {"id": 3, "status": "i"},   # injured, forced in → kept
        {"id": 4, "status": "d"},   # doubtful → pool
    ]
    pool, excluded = available_players(players, keep_ids={3})

    assert {p["id"] for p in pool} == {1, 3, 4}
    assert {p["id"] for p in excluded} == {2}


def test_legal_xi_issues_passes_a_legal_xi():
    assert legal_xi_issues(_xi({"GK": 1, "DEF": 4, "MID": 4, "FWD": 2})) == []


def test_legal_xi_issues_flags_too_few_forwards():
    issues = legal_xi_issues(_xi({"GK": 1, "DEF": 5, "MID": 5, "FWD": 0}))
    assert issues == ["0 FWD (need 1-3)"]


def test_legal_xi_issues_flags_too_few_defenders():
    issues = legal_xi_issues(_xi({"GK": 1, "DEF": 2, "MID": 5, "FWD": 3}))
    assert issues == ["2 DEF (need 3-5)"]


def test_legal_xi_issues_flags_extra_goalkeeper():
    issues = legal_xi_issues(_xi({"GK": 2, "DEF": 4, "MID": 3, "FWD": 2}))
    assert "2 GK (max 1)" in issues          # "need 1" for GK, not "need 1-1"


def test_formation_str_counts_outfield_only():
    players = [{"position": "GK"}, {"position": "DEF"}, {"position": "DEF"},
               {"position": "MID"}, {"position": "FWD"}]
    assert formation_str(players) == "2-1-1"


def test_render_xi_states_the_chosen_formation():
    def row(pos):
        return {"position": pos, "web_name": pos, "team": "ARS",
                "price": 5.0, "total_points": 50, "forced": False, "bench": False}
    selected = ([row("GK")] + [row("DEF")] * 5 + [row("MID")] * 4 + [row("FWD")] * 1)  # 5-4-1
    out = render_squad({"status": "Optimal", "selected": selected,
                        "total_points": 550, "total_cost": 55.0}, budget=80)
    assert "Optimal XI (5-4-1)" in out


def test_render_full_four_man_bench_shows_the_implied_shape():
    def row(pos, bench=False):
        return {"position": pos, "web_name": pos, "team": "ARS",
                "price": 5.0, "total_points": 50, "forced": False, "bench": bench}
    # 11 starters as a 4-4-2 + a legal 4-man bench (backup GK + 1 DEF/MID/FWD).
    starters = [row("GK")] + [row("DEF")] * 4 + [row("MID")] * 4 + [row("FWD")] * 2
    bench = [row("GK", True), row("DEF", True), row("MID", True), row("FWD", True)]
    out = render_squad({"status": "Optimal", "selected": starters + bench,
                        "total_points": 750, "total_cost": 100.0}, budget=100, full=True)
    assert "Starters (11) — 4-4-2" in out


def test_render_loaded_squad_reprices_flags_and_departed():
    def row(pos, name, price, pts, status="a", bench=False):
        return {"position": pos, "web_name": name, "team": "ARS", "price": price,
                "total_points": pts, "status": status, "chance": None, "bench": bench}
    loaded = [row("GK", "Raya", 6.0, 120), row("DEF", "Saliba", 6.0, 100, "i")]
    saved = {"saved_at": "2026-08-01", "cost": 100.0}
    out = render_loaded_squad("my-team", saved, loaded, now_cost=12.0, departed=["Henderson"])

    assert "Squad 'my-team'" in out
    assert "was £100.0m → now £12.0m" in out       # re-priced vs saved
    assert "(inj)" in out                          # Saliba flagged injured
    assert "picks now flagged" in out and "Saliba" in out
    assert "Departed" in out and "Henderson" in out


def test_render_flags_doubtful_and_unavailable_picks():
    def row(pos, status="a", chance=None):
        return {"position": pos, "web_name": pos + status, "team": "ARS",
                "price": 5.0, "total_points": 50, "forced": False, "bench": False,
                "status": status, "chance": chance}
    selected = [row("GK"), row("DEF", "d", 75), row("MID", "i")]
    out = render_squad({"status": "Optimal", "selected": selected,
                        "total_points": 150, "total_cost": 15.0}, budget=80)

    assert "(d 75%)" in out       # doubtful pick flagged with chance
    assert "(inj)" in out         # a forced-in / opted-in injured pick flagged


def test_render_full_no_bench_has_no_bench_section():
    result = {
        "status": "Optimal",
        "selected": [{"position": "GK", "web_name": "Raya", "team": "ARS",
                      "price": 6.0, "total_points": 162, "forced": False, "bench": False}],
        "total_points": 162, "total_cost": 6.0,
    }
    out = render_squad(result, budget=100, full=True)
    assert "Bench:" not in out
    assert "Starters (" not in out


def test_render_full_squad_infeasible_message_names_the_squad():
    out = render_squad(
        {"status": "Infeasible", "selected": [], "total_points": 0, "total_cost": 0.0},
        budget=50, full=True,
    )
    assert "No legal 15-man squad" in out


def test_render_xi_has_no_full_squad_caveat():
    # The caveat is only for the 15 — a plain XI must not carry it.
    result = {
        "status": "Optimal",
        "selected": [{"position": "GK", "web_name": "Raya", "team": "ARS",
                      "price": 6.0, "total_points": 162, "forced": False}],
        "total_points": 162,
        "total_cost": 6.0,
    }
    out = render_squad(result, budget=80)
    assert "not a weekly" not in out


def test_best_legal_xi_is_the_shared_primitive():
    # best_legal_xi is what `analyse` (no bench) and start/bench both call, so they can't
    # diverge on the "optimal XI" (ADR-040). It equals select_squad's XI on the same scores.
    from collections import Counter
    pool = _shape_pool()
    scores = {pl["id"]: pl["total_points"] for pl in pool}
    xi = best_legal_xi(pool, scores)
    assert len(xi) == 11
    direct = {pl["id"] for pl in
              select_squad(pool, budget=200.0, formation=XI_FLEX, size=11, scores=scores)["selected"]}
    assert xi == direct
    byid = {pl["id"]: pl for pl in pool}
    counts = Counter(byid[i]["position"] for i in xi)
    assert (counts["DEF"], counts["MID"], counts["FWD"]) == (5, 4, 1)   # strong DEF → 5-4-1


# ---- squad archetypes (ADR-043, US-125) -------------------------------------

def test_archetype_bands_translates_counts():
    assert archetype_bands(cheap=3) == [(3, 0.0, LOW_COST_MAX)]
    assert archetype_bands(premium=1) == [(1, PREMIUM_MIN, 999.9)]
    assert archetype_bands(cheap=2, premium=1) == [(2, 0.0, LOW_COST_MAX), (1, PREMIUM_MIN, 999.9)]
    assert archetype_bands() == []                       # no archetypes → no bands


def test_band_minimum_forces_a_premium_into_the_squad():
    # A low-scoring premium FWD isn't picked normally, but a "≥1 premium" band forces it in —
    # the objective is still maximised subject to the constraint (ADR-043).
    pool = squad_pool()                                  # 3GK/6DEF/6MID/4FWD, all £4, score 10
    prem = next(p for p in pool if p["position"] == "FWD")
    prem["price"], prem["total_points"] = 9.5, 1         # a pricey, low-scoring player
    scores = {p["id"]: p["total_points"] for p in pool}

    without = select_squad(pool, budget=100.0, formation=SQUAD_15, scores=scores)
    assert prem["id"] not in {p["id"] for p in without["selected"]}   # worst FWD → left out

    withband = select_squad(pool, budget=100.0, formation=SQUAD_15, scores=scores,
                            band_minimums=[(1, PREMIUM_MIN, 999.9)])
    assert prem["id"] in {p["id"] for p in withband["selected"]}      # the only ≥£9 → forced in


def test_band_minimum_can_be_infeasible():
    # No player is ≥£9m, so "≥1 premium" can't be satisfied → non-Optimal, empty.
    pool = squad_pool()                                  # all £4
    scores = {p["id"]: p["total_points"] for p in pool}
    result = select_squad(pool, budget=100.0, formation=SQUAD_15, scores=scores,
                          band_minimums=[(1, PREMIUM_MIN, 999.9)])
    assert result["status"] != "Optimal" and result["selected"] == []


def test_min_differentials_forces_a_low_owned_player_in():
    # A low-scoring ≤5%-owned FWD isn't picked normally, but "≥1 differential" forces it in;
    # players without ownership data don't count as differentials (ADR-044).
    pool = squad_pool()                                  # no `selected_by` → no differentials
    diff = next(p for p in pool if p["position"] == "FWD")
    diff["selected_by"], diff["total_points"] = 2.0, 1   # a low-owned, low-scoring player
    scores = {p["id"]: p["total_points"] for p in pool}

    without = select_squad(pool, budget=100.0, formation=SQUAD_15, scores=scores)
    assert diff["id"] not in {p["id"] for p in without["selected"]}      # worst FWD → left out

    withdiff = select_squad(pool, budget=100.0, formation=SQUAD_15, scores=scores, min_differentials=1)
    assert diff["id"] in {p["id"] for p in withdiff["selected"]}         # the only ≤5% → forced in


def test_min_differentials_infeasible_without_any_low_owned_players():
    # No player has ownership ≤5% (none have `selected_by`) → "≥1 differential" can't be met.
    pool = squad_pool()
    scores = {p["id"]: p["total_points"] for p in pool}
    result = select_squad(pool, budget=100.0, formation=SQUAD_15, scores=scores, min_differentials=1)
    assert result["status"] != "Optimal" and result["selected"] == []


def test_render_squad_shows_xi_bench_xp_breakout():
    # US-131: a passed xi_ids drives a Starting XI xP + Bench xP breakout (display-only);
    # bench players sort last and are marked.
    def _pl(pid, xp):
        return {"id": pid, "web_name": f"P{pid}", "team": "ARS", "position": "MID",
                "price": 5.0, "total_points": 10, "status": "a", "xp": xp, "minutes_weight": 1.0}
    result = {"status": "Optimal", "selected": [_pl(1, 20.0), _pl(2, 15.0), _pl(3, 5.0)],
              "total_points": 30, "total_cost": 15.0}
    out = render_squad(result, budget=100, objective="xp", full=True, xi_ids={1, 2})
    assert "Starting XI (2)" in out and "projected 35.0 xP" in out     # P1 + P2 in the XI
    assert "Bench (1)" in out and "projected 5.0 xP" in out            # P3 on the bench
    assert out.rindex("P3") > out.rindex("P1")                         # bench sorts last


def test_render_squad_no_xi_breakout_for_non_xp_objectives():
    # The XI/bench xP breakout is xp-only; --objective points shows Pts and no XI xP lines.
    result = {"status": "Optimal", "selected": [
        {"id": 1, "web_name": "P1", "team": "ARS", "position": "MID",
         "price": 5.0, "total_points": 88}],
        "total_points": 88, "total_cost": 5.0}
    out = render_squad(result, budget=100, objective="points", full=True)
    assert "88" in out and "Starting XI" not in out
