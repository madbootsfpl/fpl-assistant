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
