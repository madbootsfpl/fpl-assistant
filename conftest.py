# Root conftest.
#
# Its presence at the repository root tells pytest to add this directory to the
# import path, so tests can do `from src.api.client import FplClient` without any
# extra configuration.

import itertools
import os

import pytest


@pytest.fixture(autouse=True)
def _no_photo_sweep(monkeypatch):
    """Keep the network out of the test suite (Sprint 098, US-255).

    `badges.photo_url_by_id` checks the CDN for missing player photos via `_missing_photo_codes`; rendering
    any page in an AppTest would fire that sweep. Patch it to "nothing missing" so tests stay offline + fast
    (the photo-vs-shirt logic is covered by a unit test that overrides this with a specific missing set).
    """
    from src.web_streamlit import badges
    monkeypatch.setattr(badges, "_missing_photo_codes", lambda codes: frozenset())


# --- Running the suite against Postgres (ADR-211, Phase 2a) --------------------------------------------
# `MADBOOTS_TEST_DSN=postgresql://… pytest` runs every `Storage(...)` against a real Postgres instead of
# SQLite, so "the storage layer works on both backends" is a thing the suite can *prove* rather than a claim
# in an ADR. Unset (the default, and CI) → SQLite exactly as before, byte for byte.
#
# ⭐ **Isolation is per test, via a schema.** A fresh database per test would cost ~100ms × the suite; a shared
# one would let tests see each other's rows. A schema is created before each test and dropped after, and every
# connection that test opens is pinned to it — so a test that opens `Storage` twice (to check something
# survived a close) still sees one database, which is the behaviour it is actually testing.
_pg_schema_counter = itertools.count()


@pytest.fixture(autouse=True)
def _postgres_backend(monkeypatch):
    dsn = os.environ.get("MADBOOTS_TEST_DSN")
    if not dsn:
        yield                               # SQLite — the default path, untouched
        return

    import psycopg

    from src import db as db_module

    schema = f"t{next(_pg_schema_counter)}"
    admin = psycopg.connect(dsn, autocommit=True)
    admin.execute(f'CREATE SCHEMA "{schema}"')

    seeded = {"done": False}

    def connect(target):
        # ⚠️ The target is deliberately ignored: the point is to run the SAME tests, which ask for
        # `:memory:` or a tmp_path file, against Postgres without editing 102 call sites.
        conn = db_module.PgConnection(dsn)
        conn.execute(f'SET search_path TO "{schema}"')
        # ⭐ **A test that asks for the real snapshot must GET the real snapshot.** The ~250 Streamlit
        # AppTests call a bare `Storage()` and render pages against the committed `seed.db` — that snapshot
        # *is* what they test. Handed an empty Postgres they fail for want of data, which proves nothing about
        # either backend. So the snapshot is copied in (6,387 rows, measured at 135 ms) the first time a test
        # asks for it, and not at all for the tests that build their own fixtures.
        if not seeded["done"] and _wants_the_snapshot(target):
            seeded["done"] = True
            _copy_snapshot_into(conn)
        return conn

    # ⭐ Stashed so a test *about connection selection* can opt back into the real connector. Two of them
    # assert what happens when the database is unreachable, and this harness guarantees a reachable one —
    # patching them out would make the tests pass by not running the thing they test.
    monkeypatch.setattr(db_module, "_unpatched_connect", db_module.connect, raising=False)
    monkeypatch.setattr(db_module, "connect", connect)
    yield
    admin.execute(f'DROP SCHEMA "{schema}" CASCADE')
    admin.close()


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "sqlite_only: a test of the SQLite-legacy migration path, which has no Postgres equivalent (ADR-211)",
    )


def pytest_collection_modifyitems(config, items):
    """Skip `sqlite_only` tests when the suite is pointed at Postgres.

    ⚠️ **A skip is not a pass, and this one is load-bearing enough to say why** (ADR-178's third anti-pattern:
    a test that skips is invisible in green). These tests build an *old SQLite file* with raw `sqlite3` and
    assert that opening `Storage` migrates it — `_migrate` and `_rekey_history`. A Postgres database is created
    from the current DDL at first connect, so there is no earlier schema for them to converge from: they are
    **not applicable**, not unimplemented.

    ⚠️ **The gap this could hide, named so it cannot:** Postgres has no migration story at all yet. That is
    fine while its schema is created fresh, and it stops being fine the first time a column is added while it
    holds real data. Tracked in ADR-211's staging, not here.
    """
    if not os.environ.get("MADBOOTS_TEST_DSN"):
        return
    skip = pytest.mark.skip(reason="SQLite-legacy migration path — not applicable to Postgres (ADR-211)")
    for item in items:
        if "sqlite_only" in item.keywords:
            item.add_marker(skip)


def _wants_the_snapshot(target) -> bool:
    """True when a test asked for the app's real database rather than a fixture of its own."""
    from src import config
    return target in (config.DB_PATH, config.SEED_DB_PATH)


def _copy_snapshot_into(conn) -> None:
    """Create the schema and copy every row of the committed SQLite snapshot into it.

    The DDL runs here rather than leaving it to `Storage._init_schema`, because the rows have to land in
    tables that already exist — `_init_schema`'s `CREATE TABLE IF NOT EXISTS` then finds its work done.
    Skips silently when no snapshot is on disk, so a fresh clone still runs the rest of the suite.
    """
    import sqlite3

    from src import config
    from src import storage as storage_module

    if not os.path.exists(config.SEED_DB_PATH):
        return
    for ddl in (storage_module.CREATE_TEAMS, storage_module.CREATE_PLAYERS, storage_module.CREATE_FIXTURES,
                storage_module.CREATE_HISTORY_PAST, storage_module.CREATE_HISTORY,
                storage_module.CREATE_HEADLINE_EVENTS, storage_module.CREATE_AVAILABILITY,
                storage_module.CREATE_TRANSFER_FLOW):
        conn.execute(ddl)

    src = sqlite3.connect(config.SEED_DB_PATH)
    src.row_factory = sqlite3.Row
    try:
        names = [r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        for table in names:
            rows = src.execute(f"SELECT * FROM {table}").fetchall()  # noqa: S608 — names come from the schema
            if not rows:
                continue
            cols = rows[0].keys()
            placeholders = ", ".join("?" * len(cols))
            conn.executemany(
                f'INSERT INTO {table} ({", ".join(cols)}) VALUES ({placeholders})',  # noqa: S608
                [tuple(r[c] for c in cols) for r in rows])
    finally:
        src.close()


# --- The committed snapshot is a fixture, and a fixture nothing may write to -------------------------
# ⭐⭐ **Two tests spent weeks quietly modifying `data/seed.db`.** Opening `Storage()` on the fallback path
# runs `CREATE TABLE IF NOT EXISTS` for every table, and the snapshot predates `player_transfer_flow` and
# `data_status` — so each run left two new (empty) tables in a **version-controlled binary**. No data was
# wrong and nothing went red. The only symptom was a `git status` that was always dirty, which is easy to
# read as "that file is just like that" — ⭐ *a signal that is always on carries no information.*
#
# ⚠️ It was found by `chmod 444` and seeing who complained, which is a fine way to find it once and no way to
# keep it found. This is the version that runs every time.
_SEED = "data/seed.db"
_seed_digest_at_start = None


def _digest(path):
    import hashlib
    from pathlib import Path
    p = Path(path)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def pytest_sessionstart(session):
    global _seed_digest_at_start
    _seed_digest_at_start = _digest(_SEED)


def pytest_sessionfinish(session, exitstatus):
    """Fail the run if the suite modified the committed snapshot.

    ⚠️ Deliberately a **session-level failure**, not a per-test one: the write happens inside `Storage()`,
    far from whichever test triggered it, so attributing it to a single test would be wrong more often than
    right. The message says how to find the culprit instead.
    """
    if _seed_digest_at_start is None or exitstatus != 0:
        return                                  # nothing to compare, or the run already failed for a reason
    if _digest(_SEED) != _seed_digest_at_start:
        session.exitstatus = 1
        print(
            f"\n\n🔴 The test suite modified {_SEED}, which is committed to git.\n"
            f"   A test opened the real snapshot instead of a copy — most likely via the Postgres fallback\n"
            f"   path, which resolves to `config.SEED_DB_PATH`.\n"
            f"   To find it:  chmod 444 {_SEED} && pytest -q   (the writer fails loudly)\n"
            f"   To fix it:   redirect the seed to a tmp_path copy — see `_redirect_the_seed` in\n"
            f"                tests/test_postgres_cutover.py.\n"
            f"   Then:        git checkout {_SEED}\n"
        )
