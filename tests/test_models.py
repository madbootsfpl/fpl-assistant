"""Tests for the model mappers (raw FPL JSON → dataclasses)."""

from src.models import Fixture, Player, Team


def test_team_from_api_maps_fields():
    team = Team.from_api({"id": 1, "name": "Arsenal", "short_name": "ARS"})

    assert team.id == 1
    assert team.name == "Arsenal"
    assert team.short_name == "ARS"


def test_team_from_api_maps_overall_strength():
    team = Team.from_api({
        "id": 1,
        "name": "Arsenal",
        "short_name": "ARS",
        "strength_overall_home": 4,
        "strength_overall_away": 5,
    })

    assert team.strength_overall_home == 4
    assert team.strength_overall_away == 5


def test_player_from_api_maps_fields_and_normalises_price_and_position():
    raw = {
        "id": 2,
        "first_name": "Test",
        "second_name": "Midfielder",
        "web_name": "Mid",
        "team": 2,
        "element_type": 3,   # → MID
        "now_cost": 75,      # → 7.5
        "total_points": 88,
    }

    player = Player.from_api(raw)

    assert player.id == 2
    assert player.web_name == "Mid"
    assert player.team_id == 2
    assert player.position == "MID"
    assert player.price == 7.5
    assert player.total_points == 88


def test_player_from_api_maps_xp_inputs_and_parses_strings():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 3, "now_cost": 75, "total_points": 88,
        "points_per_game": "4.4", "status": "a", "ep_next": "5.2",
    }

    player = Player.from_api(raw)

    assert player.points_per_game == 4.4   # string → float
    assert player.status == "a"
    assert player.ep_next == 5.2


def test_player_from_api_parses_expected_goals():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 4, "now_cost": 90, "total_points": 200,
        "expected_goals": "25.50", "expected_assists": "2.67",
        "expected_goal_involvements": "28.17", "expected_goals_conceded": "38.60",
    }

    player = Player.from_api(raw)

    assert player.xg == 25.50       # strings → floats
    assert player.xa == 2.67
    assert player.xgi == 28.17
    assert player.xgc == 38.60


def test_player_from_api_expected_goals_absent_are_none():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 3, "now_cost": 50, "total_points": 0,
    }

    player = Player.from_api(raw)

    assert player.xg is None and player.xa is None
    assert player.xgi is None and player.xgc is None


def test_player_from_api_parses_actual_returns_as_ints():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 3, "now_cost": 75, "total_points": 100,
        "goals_scored": 12, "assists": 7, "minutes": 3200,
    }

    player = Player.from_api(raw)

    assert player.goals_scored == 12       # ints, taken as-is (no _to_float)
    assert player.assists == 7
    assert player.minutes == 3200


def test_player_from_api_actual_returns_absent_are_none():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 3, "now_cost": 50, "total_points": 0,
    }

    player = Player.from_api(raw)

    assert player.goals_scored is None and player.assists is None
    assert player.minutes is None


def test_player_from_api_parses_defensive_contribution():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 2, "now_cost": 55, "total_points": 175,
        "defensive_contribution": 419, "defensive_contribution_per_90": "11.47",
        "clearances_blocks_interceptions": 357, "tackles": 62, "recoveries": 155,
    }

    player = Player.from_api(raw)

    assert player.defcon == 419                 # int count, as-is
    assert player.defcon_per90 == 11.47         # per-90 string → float
    assert player.cbi == 357 and player.tackles == 62 and player.recoveries == 155


def test_player_from_api_defensive_contribution_absent_are_none():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 3, "now_cost": 50, "total_points": 0,
    }

    player = Player.from_api(raw)

    assert player.defcon is None and player.defcon_per90 is None
    assert player.cbi is None and player.tackles is None and player.recoveries is None


def test_player_from_api_parses_availability():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Saliba",
        "team": 1, "element_type": 2, "now_cost": 60, "total_points": 137,
        "status": "i", "chance_of_playing_next_round": 0, "news": "Back injury",
    }

    player = Player.from_api(raw)

    assert player.status == "i"
    assert player.chance == 0           # int, as-is
    assert player.news == "Back injury"


def test_player_from_api_availability_absent_are_none():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 3, "now_cost": 50, "total_points": 0,
    }

    player = Player.from_api(raw)

    assert player.chance is None and player.news is None


def test_player_from_api_parses_ownership():
    # selected_by_percent arrives as a string (ADR-044) → parsed to float; absent → None.
    raw = {"id": 1, "first_name": "T", "second_name": "P", "web_name": "Raya",
           "team": 1, "element_type": 1, "now_cost": 60, "total_points": 0,
           "selected_by_percent": "30.8"}
    assert Player.from_api(raw).selected_by == 30.8
    raw.pop("selected_by_percent")
    assert Player.from_api(raw).selected_by is None


def test_player_from_api_parses_crowd_signals():
    # Sprint 060 / ADR-057: transfers/cost_change are ints; form/ict/value_form are strings → float.
    raw = {"id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
           "team": 1, "element_type": 3, "now_cost": 75, "total_points": 0,
           "transfers_in_event": 123456, "transfers_out_event": 7890,
           "cost_change_event": 2, "cost_change_start": -1,
           "form": "6.5", "ict_index": "57.5", "influence": "541.6",
           "creativity": "33.5", "threat": "0.0", "value_form": "1.2"}
    p = Player.from_api(raw)
    assert p.transfers_in_event == 123456 and p.transfers_out_event == 7890
    assert p.cost_change_event == 2 and p.cost_change_start == -1
    assert p.form == 6.5 and p.ict_index == 57.5 and p.value_form == 1.2
    assert (p.influence, p.creativity, p.threat) == (541.6, 33.5, 0.0)


def test_player_from_api_parses_scout_news_link():
    # Sprint 064 / ADR-058: a present link → kept; blank "" or absent → None (empty-safe for the News lens).
    base = {"id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
            "team": 1, "element_type": 3, "now_cost": 75, "total_points": 0}
    assert Player.from_api({**base, "scout_news_link": "https://x/1"}).scout_news_link == "https://x/1"
    assert Player.from_api({**base, "scout_news_link": ""}).scout_news_link is None
    assert Player.from_api(base).scout_news_link is None


def test_player_from_api_crowd_signals_absent_are_none():
    # preseason / a lean payload: the crowd fields are simply absent → None, no crash.
    raw = {"id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
           "team": 1, "element_type": 3, "now_cost": 75, "total_points": 0}
    p = Player.from_api(raw)
    assert p.transfers_in_event is None and p.form is None and p.ict_index is None


def test_player_from_api_missing_xp_inputs_are_none():
    raw = {
        "id": 1, "first_name": "T", "second_name": "P", "web_name": "Test",
        "team": 1, "element_type": 3, "now_cost": 75, "total_points": 88,
    }

    player = Player.from_api(raw)

    assert player.points_per_game is None
    assert player.ep_next is None


def test_fixture_from_api_maps_fields():
    raw = {
        "id": 5,
        "event": 3,
        "team_h": 1,
        "team_a": 2,
        "team_h_difficulty": 2,
        "team_a_difficulty": 4,
        "finished": False,
        "kickoff_time": "2026-09-01T14:00:00Z",
    }

    fx = Fixture.from_api(raw)

    assert fx.id == 5
    assert fx.event == 3
    assert (fx.team_h, fx.team_a) == (1, 2)
    assert fx.team_h_difficulty == 2
    assert fx.finished is False
    assert fx.kickoff_time.startswith("2026-09-01")


def test_fixture_from_api_handles_null_event():
    raw = {
        "id": 6,
        "event": None,
        "team_h": 1,
        "team_a": 2,
        "team_h_difficulty": None,
        "team_a_difficulty": None,
        "finished": False,
        "kickoff_time": None,
    }

    fx = Fixture.from_api(raw)

    assert fx.event is None
    assert fx.kickoff_time is None
