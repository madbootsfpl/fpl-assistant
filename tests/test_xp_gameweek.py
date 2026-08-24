"""Tests for the per-gameweek xP breakdown (ADR-032).

The breakdown must decompose the horizon total exactly, and handle a double gameweek
(two fixtures in one GW → summed) and a blank gameweek (no fixture → 0).
"""

from src.analytics import player_xp


def _player(pid=1, ppg=4.0, team_id=1, status="a", minutes=900):
    # `minutes` at the 900-min evidence bar → a no-history player's rate is their ppg (ADR-124's full-evidence end).
    return {"id": pid, "code": None, "web_name": f"P{pid}", "team": "AAA",
            "position": "MID", "team_id": team_id, "points_per_game": ppg,
            "status": status, "ep_next": 1.0, "minutes": minutes}


def _fx(event, home_id, away_id=99, home="AAA", away="OPP", diff=3):
    # diff 3 → multiplier 1.0, so each fixture contributes exactly the rate (4.0)
    return {"event": event, "team_h": home_id, "team_a": away_id, "home": home,
            "away": away, "team_h_difficulty": diff, "team_a_difficulty": diff}


def test_by_gameweek_sums_to_the_total():
    upcoming = [_fx(1, 1), _fx(2, 1), _fx(3, 1)]        # team 1 plays each GW
    r = player_xp([_player(ppg=4.0)], upcoming, horizon=3)[0]
    assert r["gameweeks"] == [1, 2, 3]
    assert r["by_gameweek"] == {1: 4.0, 2: 4.0, 3: 4.0}
    assert round(sum(r["by_gameweek"].values()), 1) == r["xp"] == 12.0


def test_double_gameweek_sums_its_fixtures():
    upcoming = [_fx(1, 1), _fx(2, 1), _fx(2, 1)]        # two fixtures in GW2
    r = player_xp([_player(ppg=4.0)], upcoming, horizon=2)[0]
    assert r["by_gameweek"][1] == 4.0
    assert r["by_gameweek"][2] == 8.0                  # 2 × 4.0
    assert r["xp"] == 12.0 and r["games"] == 3


def test_blank_gameweek_is_zero():
    # GW2 exists (team 2 plays) but team 1 has no fixture that week → 0 for team 1
    upcoming = [_fx(1, 1), _fx(2, 2), _fx(3, 1)]
    r = player_xp([_player(team_id=1, ppg=4.0)], upcoming, horizon=3)[0]
    assert r["gameweeks"] == [1, 2, 3]
    assert r["by_gameweek"] == {1: 4.0, 2: 0.0, 3: 4.0}
    assert r["xp"] == 8.0


def test_unavailable_player_is_zero_every_gameweek():
    upcoming = [_fx(1, 1), _fx(2, 1)]
    r = player_xp([_player(ppg=4.0, status="i")], upcoming, horizon=2)[0]
    assert r["xp"] == 0.0
    assert r["by_gameweek"] == {1: 0.0, 2: 0.0}        # keys still present, all zero
