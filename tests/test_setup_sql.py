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


# ---- the door later tables walk through (ADR-216) ---------------------------------------

def test_a_table_created_after_setup_arrives_closed(db):
    """⭐⭐ **Hardening the tables that exist does nothing about the ones that do not exist yet.**

    A stock Supabase project grants `all on tables` to `anon` by default, so every table the data pipeline
    creates — players, fixtures, the xP board — came out DELETE-able with the publishable key. Reproduced on
    a real Postgres: eleven pipeline tables, all writable by `anon`.

    ⚠️ The data is public, so this is vandalism rather than disclosure — but `truncate players` with a key
    that ships inside a mobile binary takes the app down for every tester.
    """
    import psycopg

    # Recreate the stock Supabase default this is defending against.
    db.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public "
               "GRANT ALL ON TABLES TO anon, authenticated")
    _apply(db)
    db.execute("CREATE TABLE public.a_later_table (id int primary key, x text)")

    grants = db.execute(
        "select coalesce(string_agg(distinct privilege_type, ','), '') "
        "from information_schema.role_table_grants "
        "where grantee = 'anon' and table_name = 'a_later_table'").fetchone()[0]
    assert grants == "", f"a table created after setup.sql came out with {grants!r} granted to anon"

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _as_anon(db, "select count(*) from public.a_later_table")


def test_the_lockdown_leaves_the_data_tables_readable(db):
    """⭐ **Both halves, or neither is news.** Mobile reads these boards directly (audit §4.1), so a lockdown
    that also stops `anon` reading them has broken the feature it was protecting."""
    lock = (SETUP_SQL.parent / "lock_data_tables.sql").read_text()

    # ⚠️⚠️ **The tables must be created ALREADY OPEN, which is production's situation and was not the first
    # version of this test's.** Creating them after `setup.sql` means they arrive closed by default, so the
    # lockdown's `revoke` does nothing and removing it changes nothing — the mutation passed. The whole point
    # here is a table that has been writable for weeks. ⭐ *A fixture that models less than reality will
    # confirm a broken mechanism.*
    db.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated")
    db.execute("CREATE TABLE public.players (id int primary key, web_name text)")
    db.execute("CREATE TABLE public.xp_board (element_id int primary key)")
    db.execute("INSERT INTO public.players VALUES (1, 'Saka')")
    assert _as_anon(db, "select count(*) from public.players") == 1, "precondition: open before the lockdown"

    _apply(db)
    db.execute(lock)

    assert _as_anon(db, "select count(*) from public.players") == 1, "the board must stay readable"

    import psycopg
    for stmt in ("delete from public.players",
                 "truncate public.xp_board",
                 "insert into public.players values (2, 'X')"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            _as_anon(db, stmt)


def test_events_accepts_analytics_and_gives_nothing_back(db):
    """`events` was explicitly deferred at the 2026-09-19 cutover and stayed open (ADR-216).

    ⭐ **Insert-only is the whole design**: a tester's browser adds a row and can never read one back; the
    Admin view reads with the service-role key, which bypasses RLS entirely.

    ⚠️ ANALYTICS.md used to justify a read policy here, and the reasoning was careful and wrong — it argued
    the key is safe because *"it lives in Streamlit secrets and is never sent to a browser"*, which is true
    of the **key** and irrelevant to the **policy**. ⭐ *A permission is granted to a role, not to the place
    you keep the credential.*
    """
    import psycopg

    lock = (SETUP_SQL.parent / "lock_events.sql").read_text()

    # Created wide open, which is production's situation — not closed-by-default, or this proves nothing.
    db.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO anon, authenticated")
    db.execute("CREATE TABLE public.events (id bigint generated always as identity primary key, "
               "ts timestamptz default now(), event text, page text, meta jsonb)")
    db.execute("INSERT INTO public.events (event, page) VALUES ('before', 'Home')")
    assert _as_anon(db, "select count(*) from public.events") == 1, "precondition: open before the lockdown"

    db.execute(lock)

    # The one thing it must still do.
    _as_anon(db, "insert into public.events (event, page) values ('after', 'Players')")
    assert db.execute("select count(*) from public.events").fetchone()[0] == 2, (
        "⚠️ analytics must still land — a lockdown that silently drops them is worse than an open table, "
        "because the dashboard would simply go quiet")

    # And the three it must not.
    for stmt in ("select count(*) from public.events",
                 "delete from public.events",
                 "update public.events set page = 'x'"):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            _as_anon(db, stmt)

    assert db.execute("select count(*) from public.events").fetchone()[0] == 2, "nothing was destroyed"


def test_the_pipeline_opens_its_own_tables_for_reading(db):
    """⭐⭐ **The bug ADR-216's own fix introduced, one turn later.**

    ADR-216 closed the project's default privileges so a new table arrives with no grants — correct, and it
    left the pipeline's eleven tables unreadable. On a **fresh** project the effect is total: `setup.sql`
    runs, the pipeline creates its tables, and a mobile client can read **none** of them. Production only
    escaped it because its tables predated the change and a one-off migration granted them by hand.

    ⚠️ *A one-off migration cannot cover a table that does not exist yet* — which is the exact fault ADR-216
    was written about, committed by the fix for it. So the grant moved to the thing that creates the tables.
    """
    import psycopg

    from src.storage import DATA_TABLES, Storage

    _apply(db)                                    # setup.sql closes the defaults
    db.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE ALL ON TABLES FROM anon, authenticated")

    # ⚠️ **Opt out of the suite's Postgres harness**, which patches `db.connect` to pin every connection to
    # a throwaway *schema*. Left in place, `Storage(target)` would never reach the database this test built
    # and the tables would be created somewhere else entirely — the same seam `test_postgres_cutover` takes
    # for the same reason. ⭐ *A harness that guarantees a working connection is exactly wrong for a test
    # about which database you land in.*
    from src import db as db_module
    real_connect = getattr(db_module, "_unpatched_connect", db_module.connect)
    patched, db_module.connect = db_module.connect, real_connect

    target = DSN.rsplit("/", 1)[0] + "/" + db.info.dbname
    try:
        store = Storage(target, ensure_schema=True)   # the pipeline's own path
    finally:
        db_module.connect = patched
    try:
        store.conn.execute("INSERT INTO teams (id, name, short_name) VALUES (1, 'Arsenal', 'ARS')")
        store.conn.commit()
    finally:
        store.close()

    for table in DATA_TABLES:
        assert _as_anon(db, f"select count(*) from public.{table}") is not None, (
            f"a client cannot read {table} — the mobile read surface (audit §4.1) is closed")

    # ⭐ Readable, never writable — and the tables a person typed into stay shut regardless.
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _as_anon(db, "delete from public.players")
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        _as_anon(db, "select count(*) from public.squads")


def test_a_grant_that_cannot_apply_does_not_kill_the_pipeline(db, monkeypatch):
    """⚠️⚠️ **The crash the read-grant introduced, on every database that is not Supabase.**

    `anon` and `authenticated` are Supabase's roles. The first version of `_open_for_reading` raised
    `UndefinedObject` where they do not exist and took the **whole pipeline** down — a local Postgres, a CI
    service container, anyone else's deployment.

    ⭐⭐ It passed the suite, because `conftest` creates those roles for the Postgres harness. *The one
    environment that could not reproduce the bug was the one being tested in.*

    ⚠️ Roles are **cluster-wide**, so this cannot drop them — they hold privileges in the other test
    databases and `DROP ROLE` refuses. It drives the identical `"does not exist"` branch by pointing the
    grant at a table that is not there, and the real missing-role case was verified by hand against a plain
    Postgres with no Supabase roles at all.

    ⭐ *A grant is for the benefit of a client that may not exist.* Where there is nothing to open the door
    for, refusing to store the data would be the tail wagging the dog.
    """
    from src import storage as storage_module
    from src.storage import Storage

    monkeypatch.setattr(storage_module, "DATA_TABLES", ("a_table_that_is_not_there",))

    from src import db as db_module
    real_connect = getattr(db_module, "_unpatched_connect", db_module.connect)
    patched, db_module.connect = db_module.connect, real_connect
    target = DSN.rsplit("/", 1)[0] + "/" + db.info.dbname
    try:
        store = Storage(target, ensure_schema=True)   # must not raise
        try:
            store.conn.execute("INSERT INTO teams (id, name, short_name) VALUES (1, 'Arsenal', 'ARS')")
            store.conn.commit()
            assert store.conn.execute("SELECT count(*) FROM teams").fetchone()[0] == 1, (
                "the data must still be stored, and the connection must not be left in an aborted "
                "transaction by the failed grant")
        finally:
            store.close()
    finally:
        db_module.connect = patched


def test_a_grant_failing_for_any_OTHER_reason_still_raises(db, monkeypatch):
    """⚠️ **The other half, and mutation-testing found it missing.**

    Tolerating a missing role is right. Tolerating *everything* is not — a genuine permission failure, a
    typo in a table name, a connection problem would all vanish silently and the boards would quietly stop
    being readable with nothing to say so. ⭐ *A rule that swallows the error it was written for must still
    raise the ones it was not.*
    """
    import psycopg

    from src import storage as storage_module
    from src.storage import Storage

    # Not a missing object — a malformed identifier, which Postgres rejects as a syntax error.
    monkeypatch.setattr(storage_module, "DATA_TABLES", ("1 not a valid name",))

    from src import db as db_module
    real_connect = getattr(db_module, "_unpatched_connect", db_module.connect)
    patched, db_module.connect = db_module.connect, real_connect
    target = DSN.rsplit("/", 1)[0] + "/" + db.info.dbname
    try:
        with pytest.raises(psycopg.Error):
            Storage(target, ensure_schema=True)
    finally:
        db_module.connect = patched
