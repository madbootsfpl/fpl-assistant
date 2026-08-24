"""A double gameweek, end to end (ADR-129).

`element-summary` sends one entry per **fixture**, so in a double gameweek a player has two entries sharing a
`round`. The table used to key on `(element_code, round)`, so the second silently overwrote the first — a
20-point double stored as a 12-point single. Found by auditing the DGW/BGW paths *before* the season's first
double rather than after it; these keep it fixed.
"""

import sqlite3

from src.analytics.gw_form import form_dots, stat_series
from src.models import PlayerGameweek
from src.storage import Storage


def _fixture_entry(rnd, fixture, pts, goals, *, home=True, hs=2, as_=0, minutes=90, price=60):
    return {"round": rnd, "fixture": fixture, "minutes": minutes, "total_points": pts,
            "goals_scored": goals, "was_home": home, "team_h_score": hs, "team_a_score": as_,
            "opponent_team": 5, "bps": pts * 3, "value": price}


def _store(tmp_path):
    return Storage(db_path=str(tmp_path / "t.db"))


# ---- storage keeps both halves ----------------------------------------------------

def test_both_fixtures_of_a_double_survive(tmp_path):
    store = _store(tmp_path)
    store.save_history([PlayerGameweek.from_api(_fixture_entry(19, 100, 8, 1), 999),
                        PlayerGameweek.from_api(_fixture_entry(19, 101, 12, 2, home=False, hs=1, as_=3), 999)])

    rows = store.get_history(999)
    assert len(rows) == 2
    assert sum(r["total_points"] for r in rows) == 20      # not 12
    assert sum(r["goals_scored"] for r in rows) == 3       # not 2
    assert sum(r["minutes"] for r in rows) == 180          # not 90
    store.close()


def test_re_running_the_backfill_is_still_idempotent(tmp_path):
    """Keying on the fixture must not turn a repeat ingest into duplicate rows."""
    store = _store(tmp_path)
    rows = [PlayerGameweek.from_api(_fixture_entry(19, 100, 8, 1), 999),
            PlayerGameweek.from_api(_fixture_entry(19, 101, 12, 2), 999)]
    store.save_history(rows)
    store.save_history(rows)
    assert len(store.get_history(999)) == 2
    store.close()


def test_a_normal_single_fixture_round_is_unchanged(tmp_path):
    store = _store(tmp_path)
    store.save_history([PlayerGameweek.from_api(_fixture_entry(19, 100, 8, 1), 999)])
    rows = store.get_history(999)
    assert len(rows) == 1 and rows[0]["total_points"] == 8
    store.close()


# ---- the migration ----------------------------------------------------------------

def _old_schema_db(path):
    """A database as it was before ADR-129 — keyed on the gameweek."""
    con = sqlite3.connect(str(path))
    con.execute("""CREATE TABLE player_history (
        element_code INTEGER NOT NULL, round INTEGER NOT NULL, minutes INTEGER, total_points INTEGER,
        was_home INTEGER, opponent_team INTEGER, fixture INTEGER, kickoff_time TEXT,
        PRIMARY KEY (element_code, round))""")
    con.executemany("INSERT INTO player_history VALUES (?,?,?,?,?,?,?,?)",
                    [(999, 1, 90, 6, 1, 5, 100, "2026-08-21T19:00:00Z"),
                     (999, 2, 80, 3, 0, 7, 110, "2026-08-28T19:00:00Z")])
    con.commit()
    con.close()


def _pk(store):
    return [r[1] for r in store.conn.execute("PRAGMA table_info(player_history)") if r[5]]


def test_an_old_database_is_rekeyed_without_losing_rows(tmp_path):
    path = tmp_path / "old.db"
    _old_schema_db(path)
    store = Storage(db_path=str(path))
    assert _pk(store) == ["element_code", "fixture"]
    assert store.count_history() == 2                       # both rows carried across
    assert {r["round"] for r in store.get_history(999)} == {1, 2}
    store.close()


def test_the_rekey_is_idempotent(tmp_path):
    path = tmp_path / "old.db"
    _old_schema_db(path)
    Storage(db_path=str(path)).close()
    store = Storage(db_path=str(path))                      # second open must be a no-op
    assert _pk(store) == ["element_code", "fixture"] and store.count_history() == 2
    store.close()


def test_the_rekey_preserves_the_widened_columns(tmp_path):
    """_rekey_history runs after _migrate, so the copy sees every column the old table just gained."""
    path = tmp_path / "old.db"
    _old_schema_db(path)
    store = Storage(db_path=str(path))
    cols = {r[1] for r in store.conn.execute("PRAGMA table_info(player_history)")}
    assert {"bps", "xg", "team_h_score", "value"} <= cols
    store.close()


# ---- what the cards then draw ------------------------------------------------------

def _double_history():
    return {999: [_fixture_entry(19, 100, 8, 1),
                  _fixture_entry(19, 101, 12, 2, home=False, hs=1, as_=3)]}


def test_a_sparkline_shows_one_point_per_gameweek_not_per_fixture():
    """Two rows in one round must combine, not plot twice at the same x."""
    assert stat_series(_double_history(), 999, "total_points") == [(19, 20)]


def test_a_per90_over_a_double_divides_by_the_summed_minutes():
    hist = {999: [_fixture_entry(19, 100, 8, 1, minutes=90),
                  _fixture_entry(19, 101, 12, 2, minutes=45)]}
    assert stat_series(hist, 999, "total_points", per90=True) == [(19, 20 * 90 / 135)]


def test_a_snapshot_stat_is_not_summed_across_a_double():
    """Adding a player's price to itself because he played twice would read as a £6m rise."""
    assert stat_series(_double_history(), 999, "value", agg="last") == [(19, 60)]


def test_form_dots_show_both_results_of_a_double():
    """Two matches, two results — merging them into one dot would hide half the gameweek."""
    assert form_dots(_double_history(), 999) == [(19, "W"), (19, "W")]
