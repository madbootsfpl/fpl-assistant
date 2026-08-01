"""Tests for the model mappers (raw FPL JSON → dataclasses)."""

from src.models import Player, Team


def test_team_from_api_maps_fields():
    team = Team.from_api({"id": 1, "name": "Arsenal", "short_name": "ARS"})

    assert team.id == 1
    assert team.name == "Arsenal"
    assert team.short_name == "ARS"


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
