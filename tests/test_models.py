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
