"""`sql/setup.sql` — the one file every runbook points at, tested as a whole.

⭐⭐ **Why this file exists at all.** `BETA.md`, `CLOUD_SQUADS.md` and `ANALYTICS.md` each used to carry their
own copy of the setup SQL, written when the tables were open to the anon key. Stages A/B/B3 closed them — and
all three runbooks stayed as they were, still instructing a reader to `create policy ... using (true)` and
`disable row level security`. **Following the documentation would have rebuilt the hole.** Nothing failed;
nothing went red; the docs simply went on describing a system that no longer existed.

So the copies were replaced by one file, and this is the test that keeps it honest. ⭐ *The runbooks now say
"run `sql/setup.sql`" — a pointer cannot drift from what it points at.*

What is pinned here is the **whole claim the file makes**, on a real Postgres built from nothing:
  1. it applies cleanly to a virgin database;
  2. `anon` cannot enumerate any table holding user data;
  3. the paths the app actually needs still work;
  4. it is safe to re-run over a populated database.

Skipped without a Postgres — set `MADBOOTS_TEST_DSN` (CI's `postgres` job has one).
"""

import os
from pathlib import Path

import pytest

DSN = os.environ.get("MADBOOTS_TEST_DSN")
pytestmark = pytest.mark.skipif(
    not DSN, reason="needs a real Postgres — set MADBOOTS_TEST_DSN (CI's postgres job does)")

SETUP_SQL = Path(__file__).resolve().parents[1] / "sql" / "setup.sql"

# ⚠️ Every table holding something a person typed or that identifies them. `anon` must not be able to read any
# of them directly — that is the entire point of the hardening, and the property most likely to be undone by
# a well-meaning edit ("just add a select policy so the upsert works").
CLOSED = ["beta_users", "beta_waitlist", "squads", "user_prefs", "player_watchlist", "events"]


@pytest.fixture
def db():
    """A throwaway *database* — not a schema.

    ⭐ `setup.sql` names `public.` explicitly on every object, exactly as it will when pasted into Supabase's
    SQL Editor. Rewriting it to run inside a test schema would mean testing a rewritten file, so the test
    pays for a real database instead. *Ask "if I deleted the thing under test, would this still pass?"*
    """
    import psycopg

    admin = psycopg.connect(DSN, autocommit=True)
    name = f"mb_setup_{os.getpid()}"
    try:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}"')
        admin.execute(f'CREATE DATABASE "{name}"')
    except psycopg.errors.InsufficientPrivilege:          # pragma: no cover — not CI's postgres image
        pytest.skip("the test DSN's role cannot CREATE DATABASE")

    target = DSN.rsplit("/", 1)[0] + "/" + name
    conn = psycopg.connect(target, autocommit=True)
    for role in ("anon", "authenticated"):                # Supabase provides these; a bare Postgres does not
        try:
            conn.execute(f"CREATE ROLE {role} NOLOGIN")
        except psycopg.errors.DuplicateObject:
            pass
        conn.execute(f"GRANT USAGE ON SCHEMA public TO {role}")
    try:
        yield conn
    finally:
        conn.close()
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def _apply(conn):
    conn.execute(SETUP_SQL.read_text())


def _as_anon(conn, sql, *args):
    """Run one statement as `anon`, returning the value or raising. Role is reset either way."""
    try:
        conn.execute("SET ROLE anon")
        cur = conn.execute(sql, args)
        if cur.description is None:              # an INSERT — nothing to fetch
            return None
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.execute("RESET ROLE")


def test_it_applies_to_a_virgin_database(db):
    _apply(db)
    tables = db.execute(
        "select count(*) from information_schema.tables where table_schema='public'").fetchone()[0]
    functions = db.execute(
        "select count(*) from pg_proc p join pg_namespace n on n.oid=p.pronamespace "
        "where n.nspname='public'").fetchone()[0]
    assert tables == 7, "seven tables hold everything the web app stores"
    assert functions == 12, "the health check in docs/SUPABASE_RLS.md expects 12 — keep them in step"


@pytest.mark.parametrize("table", CLOSED)
def test_anon_cannot_enumerate(db, table):
    """🔴 The property the whole hardening exists for."""
    import psycopg

    _apply(db)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _as_anon(db, f"select count(*) from public.{table}")


def test_the_paths_the_app_needs_still_work(db):
    """⭐ **A lock that also stops the app is not a success.** Both halves, or neither is news."""
    _apply(db)
    db.execute("insert into public.beta_users (email) values ('tony@example.com')")

    # writes that must go IN even though nothing comes out
    _as_anon(db, "insert into public.beta_waitlist (email, reason) values ('late@x.com','full')")
    _as_anon(db, "insert into public.events (event, page) values ('page_view','Home')")
    assert db.execute("select count(*) from public.beta_waitlist").fetchone()[0] == 1, (
        "⚠️ 'no error' is not 'a row appeared' — PostgREST answers a policy-narrowed write 200 OK, zero rows")
    assert db.execute("select count(*) from public.events").fetchone()[0] == 1

    # public marketing content stays readable
    assert _as_anon(db, "select count(*) from public.maddie_videos") == 0

    # the gate, matching the way people actually type their address
    assert _as_anon(db, "select public.is_allow_listed('  TONY@Example.com ')") is True
    assert _as_anon(db, "select public.is_allow_listed('nobody@x.com')") is False
    assert _as_anon(db, "select public.touch_last_seen('tony@example.com')") is True

    # squads round-trip
    _as_anon(db, "select public.save_squad('robots', '{\"picks\":[9]}'::jsonb)")
    assert _as_anon(db, "select public.get_squad('robots')") == {"picks": [9]}
    assert _as_anon(db, "select public.squad_exists('robots')") is True
    assert _as_anon(db, "select public.delete_squad('robots')") is True
    assert _as_anon(db, "select public.delete_squad('never-existed')") is False, (
        "ADR-148: a delete that matched nothing must report it, not read as success")

    # preferences and watchlist
    _as_anon(db, "select public.save_prefs('uk1','2885974',123)")
    prefs = _as_anon(db, "select public.get_prefs('uk1')")
    assert prefs["manager_id"] == "2885974" and prefs["league_id"] == 123
    assert "user_key" not in prefs, "never echo the key back — the caller already has it"
    _as_anon(db, "select public.save_watchlist('uk1','[1,2]'::jsonb)")
    assert _as_anon(db, "select public.get_watchlist('uk1')") == [1, 2]


def test_save_prefs_leaves_the_other_preference_alone(db):
    """ADR-147: `remember()` sets one preference at a time, so a null means "leave it", not "clear it"."""
    _apply(db)
    _as_anon(db, "select public.save_prefs('uk1','2885974',123)")
    _as_anon(db, "select public.save_prefs('uk1','999',null)")
    prefs = _as_anon(db, "select public.get_prefs('uk1')")
    assert prefs["manager_id"] == "999"
    assert prefs["league_id"] == 123, "a null must leave the league alone, not clear it"


def test_forget_me_clears_every_table_and_says_which(db):
    """ADR-122/148 — the promise has to be checkable, so it reports per table."""
    _apply(db)
    db.execute("insert into public.beta_users (email) values ('me@x.com')")
    _as_anon(db, "insert into public.beta_waitlist (email, reason) values ('me@x.com','full')")
    _as_anon(db, "select public.save_squad('uk9', '{}'::jsonb)")
    _as_anon(db, "select public.save_prefs('uk9','1',null)")
    _as_anon(db, "select public.save_watchlist('uk9','[]'::jsonb)")

    report = _as_anon(db, "select public.forget_me('me@x.com','uk9')")
    assert report == {"beta_users": 1, "beta_waitlist": 1, "squads": 1,
                      "user_prefs": 1, "player_watchlist": 1}
    assert db.execute("select count(*) from public.squads").fetchone()[0] == 0


def test_re_running_it_is_safe_and_keeps_both_the_data_and_the_lock(db):
    """⭐ The header says "safe to re-run", and a claim in a comment is not a tested claim.

    This is the realistic case: a setup file gets pasted twice, or run again after a schema tweak. If the
    second run dropped data or quietly re-opened a table, the failure would be invisible until someone
    went looking.
    """
    import psycopg

    _apply(db)
    db.execute("insert into public.beta_users (email) values ('tony@example.com')")
    _as_anon(db, "select public.save_squad('robots','{\"picks\":[1]}'::jsonb)")

    _apply(db)                                            # ← again, over a populated database

    assert db.execute("select count(*) from public.beta_users").fetchone()[0] == 1
    assert _as_anon(db, "select public.get_squad('robots')") == {"picks": [1]}
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _as_anon(db, "select count(*) from public.squads")
