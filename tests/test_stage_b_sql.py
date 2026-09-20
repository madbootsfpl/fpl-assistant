"""Stage B's SQL, tested where the logic now lives (docs/SUPABASE_RLS.md B1/B2).

⭐⭐ **These behaviours moved out of Python, so a Python unit test can no longer see them.** `is_registered`
used to fetch every allow-listed address and compare case-insensitively in Python; it now asks a boolean
question and the matching happens in SQL. Faking that in a mock would test the mock — ⭐ *ask "if I deleted the
thing under test, would this still pass?"* — so these run against a real Postgres instead.

Skipped without one; CI's `postgres` job always has one. The SQL is loaded from `sql/stage_b.sql`, the same
file the runbook tells you to paste, so the two cannot drift.
"""

import os
from pathlib import Path

import pytest

DSN = os.environ.get("MADBOOTS_TEST_DSN")
pytestmark = pytest.mark.skipif(
    not DSN, reason="needs a real Postgres — set MADBOOTS_TEST_DSN (CI's postgres job does)")

SQL_FILE = Path(__file__).resolve().parents[1] / "sql" / "stage_b.sql"


@pytest.fixture
def db():
    """A throwaway schema with `beta_users` and Stage B applied, torn down afterwards."""
    import psycopg

    conn = psycopg.connect(DSN, autocommit=True)
    schema = f"stageb_{os.getpid()}"
    conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    conn.execute(f'CREATE SCHEMA "{schema}"')
    conn.execute(f'SET search_path TO "{schema}"')
    for role in ("anon", "authenticated"):
        try:
            conn.execute(f"CREATE ROLE {role} NOLOGIN")
        except Exception:                            # noqa: BLE001 — Supabase-like roles may already exist
            pass
        conn.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO {role}')
    conn.execute("CREATE TABLE beta_users (email text primary key, created_at timestamptz default now())")

    # ⚠️ The file says `public.` throughout; rewrite it to this throwaway schema so the test cannot touch a
    # real one. Everything else — the locking, the matching, the grants — is exactly what the runbook applies.
    sql = SQL_FILE.read_text().replace("public.", f'"{schema}".')
    conn.execute(sql)
    yield conn
    conn.execute(f'DROP SCHEMA "{schema}" CASCADE')
    conn.close()


def _listed(db, email):
    return db.execute("SELECT is_allow_listed(%s)", (email,)).fetchone()[0]


def test_the_gate_matches_regardless_of_case_or_stray_spaces(db):
    """⭐ The allow-list bug of 2026-08-13, now guarded where the fix lives. A hand-typed `beta_users` row with
    capitals or stray spaces must still admit the lower-cased Google address — which is the entire reason the
    old code fetched the whole table."""
    db.execute("INSERT INTO beta_users (email) VALUES ('Colinbermingham@Live.ie'), ('  spaced@x.com  ')")
    assert _listed(db, "colinbermingham@live.ie")     # capitals in the stored row
    assert _listed(db, "COLINBERMINGHAM@LIVE.IE")     # capitals in the query too
    assert _listed(db, "spaced@x.com")                # stored row had stray spaces
    assert _listed(db, "  spaced@x.com ")             # and spaces in the query
    assert not _listed(db, "stranger@example.invalid")


def test_the_gate_returns_a_boolean_and_never_the_list(db):
    """⭐ The security property, not an implementation detail: a correct guess learns only whether that one
    address is listed. There is no call here that returns an address at all."""
    db.execute("INSERT INTO beta_users (email) VALUES ('a@example.invalid'), ('b@example.invalid')")
    assert _listed(db, "a@example.invalid") is True
    assert _listed(db, "nope@example.invalid") is False


def test_registration_admits_up_to_the_cap_and_is_idempotent(db):
    reg = lambda e, c: db.execute("SELECT register_beta_user(%s, %s)", (e, c)).fetchone()[0]  # noqa: E731
    assert reg("A@b.com", 2) == "in"
    assert reg("a@b.com", 2) == "in", "already listed → admitted, no new row"
    assert db.execute("SELECT count(*) FROM beta_users").fetchone()[0] == 1
    assert reg("c@d.com", 2) == "in"
    assert reg("e@f.com", 2) == "full", "at the cap"
    assert db.execute("SELECT count(*) FROM beta_users").fetchone()[0] == 2
    assert reg("not-an-email", 2) == "invalid"


def test_the_cap_survives_simultaneous_registrations(db):
    """⚠️⚠️ **Measured, because "one function" is not the same as "atomic".**

    The first version of this SQL moved check-count-insert into a single function and the cap *still* broke:
    `select count(*)` takes no lock, so four concurrent calls against a cap of 5 admitted **6**. The function
    now takes `share row exclusive` on the table first.

    ⭐ The old Python docstring had conceded this — *"a count-then-insert race could let two simultaneous
    sign-ups exceed the cap by one — accepted for a hobby beta"* — so this closes a known, written-down hole.
    """
    import threading

    import psycopg

    schema = db.execute("SELECT current_schema()").fetchone()[0]
    db.execute("INSERT INTO beta_users (email) VALUES ('x1@a.com'), ('x2@a.com'), ('x3@a.com')")

    # Four separate CONNECTIONS, all racing for the last two places under a cap of 5. Separate connections
    # are the point — the lock is what serialises them, and a single connection could not demonstrate it.
    results = []
    lock = threading.Lock()

    def register(i):
        conn = psycopg.connect(DSN, autocommit=True)
        try:
            conn.execute(f'SET search_path TO "{schema}"')
            got = conn.execute("SELECT register_beta_user(%s, %s)",
                               (f"r{i}@example.invalid", 5)).fetchone()[0]
        finally:
            conn.close()
        with lock:
            results.append(got)

    threads = [threading.Thread(target=register, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert db.execute("SELECT count(*) FROM beta_users").fetchone()[0] == 5, \
        f"the cap must hold exactly, got {results}"
    assert results.count("in") == 2 and results.count("full") == 2, results


# ── Stage B3 ──────────────────────────────────────────────────────────────────────────────────────────────

B3_FILE = Path(__file__).resolve().parents[1] / "sql" / "stage_b3.sql"


@pytest.fixture
def db3():
    """A throwaway schema with the squad/prefs/watchlist tables and Stage B3 applied."""
    import psycopg

    conn = psycopg.connect(DSN, autocommit=True)
    schema = f"b3_{os.getpid()}"
    conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    conn.execute(f'CREATE SCHEMA "{schema}"')
    conn.execute(f'SET search_path TO "{schema}"')
    for role in ("anon", "authenticated"):
        try:
            conn.execute(f"CREATE ROLE {role} NOLOGIN")
        except Exception:                            # noqa: BLE001
            pass
        conn.execute(f'GRANT USAGE ON SCHEMA "{schema}" TO {role}')
    conn.execute("CREATE TABLE squads (handle text primary key, data jsonb not null,"
                 " updated_at timestamptz default now())")
    conn.execute("CREATE TABLE user_prefs (user_key text primary key, manager_id text, league_id bigint,"
                 " updated_at timestamptz default now())")
    conn.execute("CREATE TABLE player_watchlist (user_key text primary key,"
                 " player_ids jsonb not null default '[]'::jsonb, updated_at timestamptz default now())")
    conn.execute(B3_FILE.read_text().replace("public.", f'"{schema}".'))
    yield conn
    conn.execute(f'DROP SCHEMA "{schema}" CASCADE')
    conn.close()


def test_saving_one_preference_does_not_forget_the_others(db3):
    """⭐⭐ **The silent data loss this nearly shipped with.** `prefs.remember()` sets **one** value at a
    time — `remember(manager_id=…)` then later `remember(league_id=…)`. A plain upsert writes null into the
    column it was not given, so saving a league would quietly forget the manager id.

    The `coalesce` in `save_prefs` makes a null mean *"leave it"* rather than *"clear it"*. ⚠️ This is not
    visible from Python any more, which is exactly why it is asserted here."""
    db3.execute("SELECT save_prefs(%s, %s, %s)", ("uk1", "2885974", None))
    db3.execute("SELECT save_prefs(%s, %s, %s)", ("uk1", None, 314159))
    row = db3.execute("SELECT get_prefs(%s)", ("uk1",)).fetchone()[0]
    assert row["manager_id"] == "2885974", "saving a league must not forget the manager id"
    assert row["league_id"] == 314159


def test_get_prefs_never_echoes_the_key_back(db3):
    """The caller supplied the key; returning it adds nothing and puts it somewhere it need not be."""
    db3.execute("SELECT save_prefs(%s, %s, %s)", ("uk1", "123", None))
    assert "user_key" not in db3.execute("SELECT get_prefs(%s)", ("uk1",)).fetchone()[0]


def test_get_prefs_names_no_columns_so_a_new_field_cannot_break_the_read(db3):
    """⭐ The property `tests/test_navigation_copy.py` guards, asserted against the running function. A read
    that listed its columns would 400 the moment a field was added ahead of its migration, dropping every
    stored preference — so `get_prefs` returns the whole row via `to_jsonb`."""
    db3.execute("ALTER TABLE user_prefs ADD COLUMN a_new_field text")
    db3.execute("SELECT save_prefs(%s, %s, %s)", ("uk1", "123", None))
    row = db3.execute("SELECT get_prefs(%s)", ("uk1",)).fetchone()[0]
    assert row["manager_id"] == "123", "an unknown column must not break the read"
    assert "a_new_field" in row, "to_jsonb returns whatever the table has, which is the point"


def test_a_delete_that_matched_nothing_reports_false(db3):
    """ADR-148: a delete that silently matched nothing must not read as success."""
    db3.execute("SELECT save_squad(%s, %s)", ("ts", '{"player_ids":[1]}'))
    assert db3.execute("SELECT delete_squad(%s)", ("ts",)).fetchone()[0] is True
    assert db3.execute("SELECT delete_squad(%s)", ("ts",)).fetchone()[0] is False


def test_the_tables_are_closed_to_anon_but_the_functions_are_not(db3):
    """⭐ The whole point: enumeration stops, by-key access continues."""
    schema = db3.execute("SELECT current_schema()").fetchone()[0]
    db3.execute("SELECT save_squad(%s, %s)", ("ts", '{"player_ids":[1]}'))
    db3.execute("SET ROLE anon")
    try:
        for table in ("squads", "user_prefs", "player_watchlist"):
            with pytest.raises(Exception, match="permission denied"):
                db3.execute(f'SELECT count(*) FROM "{schema}".{table}')  # noqa: S608 — name from a fixed tuple
            db3.execute("ROLLBACK")
        assert db3.execute("SELECT get_squad(%s)", ("ts",)).fetchone()[0] == {"player_ids": [1]}
        assert db3.execute("SELECT squad_exists(%s)", ("ts",)).fetchone()[0] is True
    finally:
        db3.execute("RESET ROLE")
