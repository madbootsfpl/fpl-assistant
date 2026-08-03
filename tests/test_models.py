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
