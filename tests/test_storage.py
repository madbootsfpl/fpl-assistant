"""Tests for the SQLite storage layer.

Every test uses a temporary database (tmp_path), so the real data/fpl.db is
never touched.
"""

import sqlite3

import pytest

from src.models import Player, Team
from src.storage import Storage


def make_team(id: int = 1) -> Team:
    return Team(id=id, name="Arsenal", short_name="ARS")


def make_player(
    id: int = 1,
    total_points: int = 88,
    web_name: str = "Test",
    position: str = "MID",
    price: float = 7.5,
    team_id: int = 1,
) -> Player:
    return Player(
        id=id,
        first_name="Test",
        second_name="Player",
        web_name=web_name,
        team_id=team_id,
        position=position,
        price=price,
        total_points=total_points,
    )


def test_save_and_read_back(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player()])

    players = store.get_players()
    assert len(players) == 1
    assert players[0]["web_name"] == "Test"
    assert players[0]["price"] == 7.5
    store.close()


def test_upsert_is_idempotent_and_refreshes_values(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player(id=1, total_points=88)])

    # Save the same player id again with a new score.
    store.save_players([make_player(id=1, total_points=120)])

    assert store.count_players() == 1                      # no duplicate row
    assert store.get_players()[0]["total_points"] == 120   # value refreshed
    store.close()


def test_foreign_keys_are_enforced(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    # No teams saved, so this player references a team (999) that doesn't exist.
    with pytest.raises(sqlite3.IntegrityError):
        store.save_players([make_player(id=1, team_id=999)])
    store.close()


def test_get_players_filters_by_position(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([
        make_player(id=1, web_name="Middy", position="MID"),
        make_player(id=2, web_name="Deffo", position="DEF"),
    ])

    rows = store.get_players(position="DEF")
    assert [r["web_name"] for r in rows] == ["Deffo"]
    store.close()


def test_get_players_search_by_name_is_case_insensitive(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([
        make_player(id=1, web_name="Haaland"),
        make_player(id=2, web_name="Salah"),
    ])

    rows = store.get_players(name="haa")   # lowercase still matches "Haaland"
    assert [r["web_name"] for r in rows] == ["Haaland"]
    store.close()


def test_get_players_filters_by_max_price(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([
        make_player(id=1, web_name="Cheap", price=5.0),
        make_player(id=2, web_name="Pricey", price=12.0),
    ])

    rows = store.get_players(max_price=8.0)
    assert [r["web_name"] for r in rows] == ["Cheap"]
    store.close()


def test_get_players_filters_by_team(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([
        Team(id=1, name="Arsenal", short_name="ARS"),
        Team(id=2, name="Chelsea", short_name="CHE"),
    ])
    store.save_players([
        make_player(id=1, web_name="Gunner", team_id=1),
        make_player(id=2, web_name="Blue", team_id=2),
    ])

    rows = store.get_players(team="CHE")
    assert [r["web_name"] for r in rows] == ["Blue"]
    store.close()


def test_get_players_filters_combine_with_and(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([
        make_player(id=1, web_name="CheapMid", position="MID", price=5.0),
        make_player(id=2, web_name="PriceyMid", position="MID", price=12.0),
        make_player(id=3, web_name="CheapDef", position="DEF", price=5.0),
    ])

    rows = store.get_players(position="MID", max_price=8.0)
    assert [r["web_name"] for r in rows] == ["CheapMid"]
    store.close()
