"""Tests for the fixtures → players planning lens (US-301)."""

from src.analytics.targets import target_by_fixtures


def _team_ranked(*names):
    # Minimal team_fdr-shaped rows, easiest first (the order given).
    return [{"team": n, "avg_difficulty": 2.0 + i, "opponents": [f"{n}-opp"]}
            for i, n in enumerate(names)]


def _player(pid, team, position, *, status="a", selected_by=5.0, price=6.0):
    return {"id": pid, "team": team, "position": position, "web_name": f"p{pid}",
            "price": price, "selected_by": selected_by, "status": status,
            "chance": None}


def test_targets_pick_best_available_from_the_top_run_teams():
    team_ranked = _team_ranked("EASY", "MID")     # only the top team(s) contribute
    players = [
        _player(1, "EASY", "MID"), _player(2, "EASY", "MID"), _player(3, "EASY", "MID"),
        _player(9, "HARD", "MID"),                # a team outside team_ranked → never shown
    ]
    xp = {1: 5.0, 2: 9.0, 3: 1.0, 9: 99.0}
    rows = target_by_fixtures(team_ranked, players, xp, top_teams=1, per_team=2)

    assert [r["id"] for r in rows] == [2, 1]      # top-2 of EASY by xP, HARD excluded
    assert rows[0]["team"] == "EASY" and rows[0]["xp"] == 9.0
    assert rows[0]["opponents"] == ["EASY-opp"]


def test_unavailable_players_are_dropped_but_doubtful_stays_with_its_fit():
    team_ranked = _team_ranked("EASY")
    players = [
        _player(1, "EASY", "FWD", status="i"),                       # injured → dropped
        _player(2, "EASY", "FWD", status="d") | {"chance": 75},      # doubtful → kept, ❓ 75%
        _player(3, "EASY", "FWD", status="a"),                       # fit → kept, ✅
    ]
    rows = target_by_fixtures(team_ranked, players, {2: 8.0, 3: 6.0})

    assert [r["id"] for r in rows] == [2, 3]                          # injured gone
    assert rows[0]["fit"] == "❓ 75%" and rows[1]["fit"] == "✅"


def test_position_filter_scopes_the_targets():
    team_ranked = _team_ranked("EASY")
    players = [_player(1, "EASY", "DEF"), _player(2, "EASY", "MID")]
    xp = {1: 4.0, 2: 7.0}

    assert [r["id"] for r in target_by_fixtures(team_ranked, players, xp, position="DEF")] == [1]
    assert [r["id"] for r in target_by_fixtures(team_ranked, players, xp, position="All")] == [2, 1]
