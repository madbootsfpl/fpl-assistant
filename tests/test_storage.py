"""Tests for the SQLite storage layer.

Every test uses a temporary database (tmp_path), so the real data/fpl.db is
never touched.
"""

from src.models import Player, Team
from src.storage import Storage


def make_team(id: int = 1) -> Team:
    return Team(id=id, name="Arsenal", short_name="ARS")


def make_player(id: int = 1, total_points: int = 88) -> Player:
    return Player(
        id=id,
        first_name="Test",
        second_name="Player",
        web_name="Test",
        team_id=1,
        position="MID",
        price=7.5,
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
