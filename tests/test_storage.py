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
    points_per_game: float | None = None,
    status: str | None = None,
    ep_next: float | None = None,
    xg: float | None = None,
    xa: float | None = None,
    xgi: float | None = None,
    xgc: float | None = None,
    goals_scored: int | None = None,
    assists: int | None = None,
    minutes: int | None = None,
    defcon: int | None = None,
    defcon_per90: float | None = None,
    cbi: int | None = None,
    tackles: int | None = None,
    recoveries: int | None = None,
    chance: int | None = None,
    news: str | None = None,
    selected_by: float | None = None,
    penalties_order: int | None = None,
    corners_order: int | None = None,
    freekicks_order: int | None = None,
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
        points_per_game=points_per_game,
        status=status,
        ep_next=ep_next,
        xg=xg,
        xa=xa,
        xgi=xgi,
        xgc=xgc,
        goals_scored=goals_scored,
        assists=assists,
        minutes=minutes,
        defcon=defcon,
        defcon_per90=defcon_per90,
        cbi=cbi,
        tackles=tackles,
        recoveries=recoveries,
        chance=chance,
        news=news,
        selected_by=selected_by,
        penalties_order=penalties_order,
        corners_order=corners_order,
        freekicks_order=freekicks_order,
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


def test_set_piece_orders_round_trip(tmp_path):
    """The corner/FK order fields (Sprint 095, ADR-081) persist and read back."""
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player(penalties_order=1, corners_order=6, freekicks_order=2)])

    row = store.get_players()[0]
    assert row["penalties_order"] == 1
    assert row["corners_order"] == 6
    assert row["freekicks_order"] == 2
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


def test_save_team_elo_updates_only_the_elo_column(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])

    store.save_team_elo({1: 2063.7})

    row = store.conn.execute(
        "SELECT short_name, elo FROM teams WHERE id = 1"
    ).fetchone()
    assert row["short_name"] == "ARS"   # FPL data preserved
    assert row["elo"] == 2063.7
    store.close()


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


def test_save_teams_stores_and_returns_the_code(tmp_path):
    # the FPL asset `code` (for the badge URL, Sprint 055) round-trips through get_teams
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([Team(id=1, name="Arsenal", short_name="ARS", code=3)])
    team = store.get_teams()[0]
    assert team["code"] == 3
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


def test_save_players_stores_xp_inputs(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([
        make_player(id=1, points_per_game=4.4, status="a", ep_next=5.2),
    ])

    row = store.conn.execute(
        "SELECT points_per_game, status, ep_next FROM players WHERE id = 1"
    ).fetchone()
    assert (row[0], row[1], row[2]) == (4.4, "a", 5.2)
    store.close()


def test_save_players_stores_ownership(tmp_path):
    # ADR-044: selected_by (ownership %) round-trips through save + get_players.
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player(id=1, selected_by=3.2), make_player(id=2, selected_by=None)])

    by_id = {r["id"]: r["selected_by"] for r in store.get_players()}
    assert by_id[1] == 3.2 and by_id[2] is None
    store.close()


def test_save_players_stores_crowd_signals(tmp_path):
    # Sprint 060 / ADR-057: the crowd-lens fields round-trip through save + get_players.
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    p = make_player(id=1)
    p.transfers_in_event, p.cost_change_event, p.form, p.ict_index = 123456, 2, 6.5, 57.5
    store.save_players([p])

    row = store.get_players()[0]
    assert (row["transfers_in_event"], row["cost_change_event"]) == (123456, 2)
    assert (row["form"], row["ict_index"]) == (6.5, 57.5)
    store.close()


def test_save_players_stores_scout_news_link(tmp_path):
    # Sprint 064 / ADR-058: the News-lens source link round-trips through save + get_players.
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    p = make_player(id=1)
    p.news, p.scout_news_link = "Knock", "https://example/news"
    store.save_players([p])

    row = store.get_players()[0]
    assert row["news"] == "Knock" and row["scout_news_link"] == "https://example/news"
    store.close()


def test_migration_adds_crowd_columns_to_an_old_players_table(tmp_path):
    db = str(tmp_path / "old.db")
    # A pre-Sprint-060 database: players table without the crowd-signal columns.
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT)")
    conn.execute(
        """CREATE TABLE players (
            id INTEGER PRIMARY KEY, first_name TEXT, second_name TEXT, web_name TEXT,
            team_id INTEGER, position TEXT, price REAL, total_points INTEGER)"""
    )
    conn.commit()
    conn.close()

    store = Storage(db_path=db)     # opening migrates up to the current schema
    cols = {row[1] for row in store.conn.execute("PRAGMA table_info(players)")}
    assert {"transfers_in_event", "cost_change_event", "form", "ict_index", "value_form",
            "scout_news_link"} <= cols
    store.close()


def test_migration_adds_xp_columns_to_an_old_players_table(tmp_path):
    db = str(tmp_path / "old.db")

    # Simulate a pre-Sprint-005 database: a players table without the xP columns.
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT)")
    conn.execute(
        """CREATE TABLE players (
            id INTEGER PRIMARY KEY, first_name TEXT, second_name TEXT, web_name TEXT,
            team_id INTEGER, position TEXT, price REAL, total_points INTEGER)"""
    )
    conn.commit()
    conn.close()

    # Opening Storage migrates the players table up to the current schema.
    store = Storage(db_path=db)
    cols = {row[1] for row in store.conn.execute("PRAGMA table_info(players)")}
    assert {"points_per_game", "status", "ep_next"} <= cols
    store.close()


def test_save_players_stores_expected_goals(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player(id=1, xg=25.5, xa=2.67, xgi=28.17, xgc=38.6)])

    row = store.get_players(name="Test")[0]
    assert (row["xg"], row["xa"], row["xgi"], row["xgc"]) == (25.5, 2.67, 28.17, 38.6)
    store.close()


def test_migration_adds_expected_goals_columns_to_an_old_players_table(tmp_path):
    db = str(tmp_path / "old.db")

    # A pre-Sprint-014 database: players table without the expected_* columns.
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT)")
    conn.execute(
        """CREATE TABLE players (
            id INTEGER PRIMARY KEY, first_name TEXT, second_name TEXT, web_name TEXT,
            team_id INTEGER, position TEXT, price REAL, total_points INTEGER)"""
    )
    conn.commit()
    conn.close()

    store = Storage(db_path=db)
    cols = {row[1] for row in store.conn.execute("PRAGMA table_info(players)")}
    assert {"xg", "xa", "xgi", "xgc"} <= cols
    store.close()


def test_save_players_stores_actual_returns(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player(id=1, goals_scored=12, assists=7, minutes=3200)])

    row = store.get_players(name="Test")[0]
    assert (row["goals_scored"], row["assists"], row["minutes"]) == (12, 7, 3200)
    store.close()


def test_migration_adds_actual_return_columns_to_an_old_players_table(tmp_path):
    db = str(tmp_path / "old.db")

    # A pre-Sprint-016 database: players table without goals/assists/minutes.
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT)")
    conn.execute(
        """CREATE TABLE players (
            id INTEGER PRIMARY KEY, first_name TEXT, second_name TEXT, web_name TEXT,
            team_id INTEGER, position TEXT, price REAL, total_points INTEGER)"""
    )
    conn.commit()
    conn.close()

    store = Storage(db_path=db)
    cols = {row[1] for row in store.conn.execute("PRAGMA table_info(players)")}
    assert {"goals_scored", "assists", "minutes"} <= cols
    store.close()


def test_save_players_stores_defensive_contribution(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player(
        id=1, defcon=419, defcon_per90=11.47, cbi=357, tackles=62, recoveries=155)])

    row = store.get_players(name="Test")[0]
    assert (row["defcon"], row["defcon_per90"]) == (419, 11.47)
    assert (row["cbi"], row["tackles"], row["recoveries"]) == (357, 62, 155)
    store.close()


def test_migration_adds_defcon_columns_to_an_old_players_table(tmp_path):
    db = str(tmp_path / "old.db")

    # A pre-Sprint-017 database: players table without the DefCon columns.
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT)")
    conn.execute(
        """CREATE TABLE players (
            id INTEGER PRIMARY KEY, first_name TEXT, second_name TEXT, web_name TEXT,
            team_id INTEGER, position TEXT, price REAL, total_points INTEGER)"""
    )
    conn.commit()
    conn.close()

    store = Storage(db_path=db)
    cols = {row[1] for row in store.conn.execute("PRAGMA table_info(players)")}
    assert {"defcon", "defcon_per90", "cbi", "tackles", "recoveries"} <= cols
    store.close()


def test_save_players_stores_availability(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([make_team()])
    store.save_players([make_player(id=1, status="i", chance=0, news="Back injury")])

    row = store.get_players(name="Test")[0]
    assert (row["status"], row["chance"], row["news"]) == ("i", 0, "Back injury")
    store.close()


def test_migration_adds_availability_columns_to_an_old_players_table(tmp_path):
    db = str(tmp_path / "old.db")

    # A pre-Sprint-022 database: players table without chance/news.
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE teams (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT)")
    conn.execute(
        """CREATE TABLE players (
            id INTEGER PRIMARY KEY, first_name TEXT, second_name TEXT, web_name TEXT,
            team_id INTEGER, position TEXT, price REAL, total_points INTEGER)"""
    )
    conn.commit()
    conn.close()

    store = Storage(db_path=db)
    cols = {row[1] for row in store.conn.execute("PRAGMA table_info(players)")}
    assert {"chance", "news"} <= cols
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


def test_get_upcoming_fixtures_includes_team_strengths(tmp_path):
    store = Storage(db_path=str(tmp_path / "test.db"))
    store.save_teams([
        Team(id=1, name="Arsenal", short_name="ARS",
             strength_overall_home=5, strength_overall_away=4),
        Team(id=2, name="Burnley", short_name="BUR",
             strength_overall_home=2, strength_overall_away=2),
    ])
    store.save_fixtures([make_fixture(id=1, team_h=1, team_a=2)])

    row = store.get_upcoming_fixtures()[0]
    assert row["home_team_strength"] == 5   # ARS strength_overall_home
    assert row["away_team_strength"] == 2   # BUR strength_overall_away
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
