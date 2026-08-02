"""Tests for the SQLite storage layer.

Every test uses a temporary database (tmp_path), so the real data/fpl.db is
never touched.
"""

import sqlite3

import pytest

from src.models import Fixture, Player, Team
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


def make_fixture(
    id: int = 1,
    team_h: int = 1,
    team_a: int = 2,
    event: int = 1,
    finished: bool = False,
) -> Fixture:
    return Fixture(
        id=id,
        event=event,
        team_h=team_h,
        team_a=team_a,
        team_h_difficulty=2,
        team_a_difficulty=4,
        finished=finished,
        kickoff_time=None,
    )


def two_teams():
    return [
        Team(id=1, name="Arsenal", short_name="ARS"),
        Team(id=2, name="Aston Villa", short_name="AVL"),
    ]


def test_save_teams_stores_overall_strength(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([
        Team(id=1, name="Arsenal", short_name="ARS",
             strength_overall_home=4, strength_overall_away=5),
    ])

    row = store.conn.execute(
        "SELECT strength_overall_home, strength_overall_away FROM teams WHERE id = 1"
    ).fetchone()
    assert (row[0], row[1]) == (4, 5)
    store.close()


def test_migration_adds_strength_columns_to_an_old_teams_table(tmp_path):
    db = str(tmp_path / "old.db")

    # Simulate a pre-Sprint-004 database: a teams table without the strength columns.
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT)"
    )
    conn.execute("INSERT INTO teams (id, name, short_name) VALUES (1, 'Arsenal', 'ARS')")
    conn.commit()
    conn.close()

    # Opening Storage should migrate the table up to the current schema.
    store = Storage(db_path=db)
    cols = {row[1] for row in store.conn.execute("PRAGMA table_info(teams)")}
    assert "strength_overall_home" in cols
    assert "strength_overall_away" in cols

    # The existing row is preserved; the new column is NULL until the next refresh.
    row = store.conn.execute(
        "SELECT name, strength_overall_home FROM teams WHERE id = 1"
    ).fetchone()
    assert row[0] == "Arsenal"
    assert row[1] is None
    store.close()


def test_foreign_keys_are_enforced(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    # No teams saved, so this player references a team (999) that doesn't exist.
    with pytest.raises(sqlite3.IntegrityError):
        store.save_players([make_player(id=1, team_id=999)])
    store.close()


def test_save_and_count_fixtures(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams(two_teams())
    store.save_fixtures([make_fixture(id=1), make_fixture(id=2, team_h=2, team_a=1)])

    assert store.count_fixtures() == 2
    store.close()


def test_fixture_foreign_key_is_enforced(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])   # only team 1 exists
    # team_a = 999 doesn't exist, so the fixture's FK is violated.
    with pytest.raises(sqlite3.IntegrityError):
        store.save_fixtures([make_fixture(id=1, team_h=1, team_a=999)])
    store.close()


def test_get_upcoming_fixtures_excludes_finished_and_joins_team_names(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams(two_teams())
    store.save_fixtures([
        make_fixture(id=1, event=1, finished=True),    # played — excluded
        make_fixture(id=2, event=2, finished=False),   # upcoming — included
    ])

    upcoming = store.get_upcoming_fixtures()

    assert len(upcoming) == 1
    assert upcoming[0]["home"] == "ARS"   # team_h=1
    assert upcoming[0]["away"] == "AVL"   # team_a=2
    store.close()


def test_get_upcoming_fixtures_filtered_by_team(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([
        Team(id=1, name="Arsenal", short_name="ARS"),
        Team(id=2, name="Aston Villa", short_name="AVL"),
        Team(id=3, name="Chelsea", short_name="CHE"),
    ])
    store.save_fixtures([
        make_fixture(id=1, team_h=1, team_a=2),   # ARS vs AVL
        make_fixture(id=2, team_h=2, team_a=3),   # AVL vs CHE (no ARS)
    ])

    ars = store.get_upcoming_fixtures(team="ARS")
    assert len(ars) == 1
    assert ars[0]["home"] == "ARS"
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
