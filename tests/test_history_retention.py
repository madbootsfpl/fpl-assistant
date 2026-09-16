"""Per-match history survives a season rollover (ADR-201).

⚠️ **The bug this prevents is silent, total and unrecoverable.** `player_history` was keyed on
`(element_code, fixture)`, and **FPL restarts fixture ids at 1 every August** — so the new season's GW1 would
overwrite the old season's GW1, row for row, with no error and no warning. And it cannot be undone: FPL's
`element-summary` serves per-match detail for the **current season only**; past seasons come back as one
aggregate row per player, so a rollover destroyed a season of per-match data that FPL will not sell back.

That data is the training set for anything learned (the ML roadmap's Phase 0), which is why this landed before
any model did: ⭐ *a model can be built next winter; the gameweek you failed to store cannot.*
"""

import sqlite3

import src.storage as storage_module
from src.analytics.last_season import season_from_kickoff
from src.storage import CREATE_HISTORY, Storage


def _rows(conn):
    """Plain tuples — `Storage` sets `row_factory`, and a `sqlite3.Row` does not compare equal to a tuple."""
    return [tuple(r) for r in
            conn.execute("select element_code, season, fixture, total_points from player_history")]


def test_two_seasons_can_share_a_fixture_id():
    """The whole point. Fixture 1 exists in every season; both rows must survive."""
    conn = sqlite3.connect(":memory:")
    conn.execute(CREATE_HISTORY)
    for season, pts in (("2025/26", 7), ("2026/27", 3)):
        conn.execute("INSERT INTO player_history (element_code, season, round, fixture, total_points) "
                     "VALUES (?, ?, 1, 1, ?)", (100, season, pts))
    got = {(r[1], r[3]) for r in _rows(conn)}
    assert got == {("2025/26", 7), ("2026/27", 3)}, f"one season overwrote the other: {got}"


def test_the_season_comes_from_the_match_not_the_clock():
    """⚠️ A season label read from *now* would relabel historical rows the moment anything re-read them.
    ⭐ *A row's season is a property of the match, not of when the row was written.*

    And August is the boundary, not January — a match in January 2027 belongs to **2026/27**.
    """
    assert season_from_kickoff("2026-08-15T14:00:00Z") == "2026/27"
    assert season_from_kickoff("2027-01-02T15:00:00Z") == "2026/27", "mid-season, still the August it began"
    assert season_from_kickoff("2027-05-24T16:00:00Z") == "2026/27", "the last day is the same season"
    assert season_from_kickoff("2027-08-14T12:00:00Z") == "2027/28", "…and the next August rolls it"
    for junk in (None, "", "nonsense", 12345):
        assert season_from_kickoff(junk) is None, f"{junk!r} must not guess a season"


def test_an_old_database_is_migrated_without_losing_a_row(tmp_path):
    """⚠️ **The backfill has to happen BEFORE `season` joins the key.** Rows written before this migration
    carry `''`, and folding a blank into the primary key would merge every season's GW1 into one row — the
    exact loss the column exists to prevent, performed once, during the fix.
    """
    db = tmp_path / "old.db"
    conn = sqlite3.connect(db)
    conn.execute(CREATE_HISTORY.replace(
        "season         TEXT NOT NULL DEFAULT '',\n", "").replace(
        "PRIMARY KEY (element_code, season, fixture)", "PRIMARY KEY (element_code, fixture)"))
    for code, fx, ko in ((100, 1, "2026-08-15T14:00:00Z"), (100, 2, "2027-01-02T15:00:00Z"),
                         (101, 1, "2026-08-15T14:00:00Z")):
        conn.execute("INSERT INTO player_history (element_code, round, fixture, kickoff_time, total_points) "
                     "VALUES (?, 1, ?, ?, 5)", (code, fx, ko))
    conn.commit()
    conn.close()

    store = Storage(str(db))
    try:
        rows = _rows(store.conn)
        assert len(rows) == 3, f"the migration lost rows: {rows}"
        assert {r[1] for r in rows} == {"2026/27"}, "every row is stamped with the season of its own match"
        pk = {r[1] for r in store.conn.execute("PRAGMA table_info(player_history)") if r[5]}
        assert pk == {"element_code", "season", "fixture"}
    finally:
        store.close()


def test_the_migration_runs_once_not_on_every_open(tmp_path, monkeypatch):
    """⚠️ **The idempotency check compares a SET, and the first version did not.**

    `PRAGMA table_info` lists columns in *table* order and this filters to the primary-key ones — so the
    result is ordered by position, not key ordinal, and `season` (appended to the table) reads last however
    the key was declared. An equality test against the declared order never matched, so the table was dropped
    and rebuilt on **every open**: a permanent migration loop that leaves the data correct and the cost
    invisible. ⭐ *A migration that cannot tell it has already run is not a migration, it is a rebuild.*
    """
    db = tmp_path / "x.db"
    first = Storage(str(db))
    first.conn.execute("INSERT INTO player_history (element_code, season, round, fixture, total_points) "
                       "VALUES (1, '2026/27', 1, 1, 9)")
    first.conn.commit()
    first.close()

    # ⚠️ **Watch the SQL, because the outcome cannot tell you.** A first version asserted the data survived
    # and no scaffolding was left — and **passed with the check reverted**, because a rebuild also preserves
    # every row and drops its own temp table. ⭐ *When the broken and the working versions produce the same
    # end state, assert the work, not the result.*
    #
    # ⚠️ And the *second* version still passed, because it attached the trace to `storage.conn` — by which
    # time `__init__` had already run the migration it was meant to be watching. **The observer has to be in
    # place before the thing it observes**, so the connection is traced at the moment it is opened.
    executed: list[str] = []
    real_connect = sqlite3.connect

    def traced(*args, **kwargs):
        conn = real_connect(*args, **kwargs)
        conn.set_trace_callback(executed.append)
        return conn

    monkeypatch.setattr(storage_module.sqlite3, "connect", traced)
    again = Storage(str(db))
    try:
        assert _rows(again.conn) == [(1, "2026/27", 1, 9)], "a re-open must not disturb the data"
    finally:
        again.close()

    rebuilt = [q for q in executed if "rekeyed" in q.lower()]
    assert not rebuilt, f"the migration re-ran on an already-migrated database: {rebuilt[:2]}"
