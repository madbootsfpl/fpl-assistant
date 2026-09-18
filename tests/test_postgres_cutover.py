"""Streamlit reads Postgres behind a flag, and says so when it cannot (ADR-211, Phase 2b).

`FPL_DATABASE_URL` points every `Storage()` in the CLI and the web app at Postgres. Unset, the app is
byte-for-byte what it was — ⭐ **the variable IS the fallback**, which is simpler and safer than an automatic
runtime failover, because a failover that silently serves last month's snapshot while the pipeline is dead is
the failure this whole phase exists to remove.

The behavioural half (does Postgres actually serve the app?) is covered by running the whole suite against it:

    MADBOOTS_TEST_DSN=postgresql://… pytest

What is tested here is the **cutover decision** — which database gets chosen, what happens when the chosen one
cannot be used, and whether the user is told.
"""

import importlib

import pytest

from src import config as config_module
from src import storage as storage_module


def _reloaded(monkeypatch, url):
    """Re-read config with `FPL_DATABASE_URL` set (or not), as a fresh process would.

    ⚠️ **And restore the real connector.** When the suite runs under `MADBOOTS_TEST_DSN`, conftest patches
    `db.connect` to hand every caller a working Postgres — which is right for the other 1,900 tests and
    exactly wrong for these, which are about what happens when a database *cannot* be reached. ⭐ *A test that
    passes because the harness prevented the condition it tests is not a passing test.*
    """
    from src import db as db_module
    if hasattr(db_module, "_unpatched_connect"):
        monkeypatch.setattr(db_module, "connect", db_module._unpatched_connect)
    monkeypatch.setenv("FPL_DATABASE_URL", url) if url else monkeypatch.delenv(
        "FPL_DATABASE_URL", raising=False)
    importlib.reload(config_module)
    importlib.reload(storage_module)
    return storage_module


@pytest.fixture(autouse=True)
def _restore_modules():
    """Leave the imported modules exactly as they were — these tests reload them."""
    yield
    importlib.reload(config_module)
    importlib.reload(storage_module)


def test_without_the_flag_nothing_changes(monkeypatch):
    """The cutover is opt-in. No variable → the live cache if there is one, else the committed seed."""
    mod = _reloaded(monkeypatch, None)
    assert config_module.DATABASE_URL is None
    assert config_module.DB_PATH in (config_module.LIVE_DB_PATH, config_module.SEED_DB_PATH)
    assert mod.fallback_reason() is None


def test_the_flag_points_every_call_site_at_postgres_without_touching_one(monkeypatch):
    """⭐ The DSN travels in the same variable as the path, so `Storage()` — called in eighteen places in the
    web app alone — follows without a second parameter or a mode flag anywhere."""
    mod = _reloaded(monkeypatch, "postgresql://u:p@example.invalid:5432/db")
    assert config_module.DB_PATH == "postgresql://u:p@example.invalid:5432/db"
    assert mod.db.is_postgres(config_module.DB_PATH)


def test_an_unreachable_database_falls_back_to_the_seed_and_records_why(monkeypatch):
    """⚠️ The app must still render — but the reason must survive, because the sidebar has to show it."""
    mod = _reloaded(monkeypatch, "postgresql://postgres:x@127.0.0.1:1/nothing")
    store = mod.Storage()
    try:
        assert store.count_players() > 0, "the seed still serves the app"
        assert store.is_postgres is False
        assert mod.fallback_reason(), "a silent fallback is the failure this phase removes"
    finally:
        store.close()


def test_a_reader_never_creates_the_schema(monkeypatch):
    """⭐ **The thing that owns a schema should be the only thing that creates it.**

    A reader pointed at the wrong database would otherwise run `CREATE TABLE IF NOT EXISTS`, build eight empty
    tables and render *"no data"* — reporting an empty league instead of a misconfiguration. So a reader asks
    whether the schema is there and declines to invent it; `ensure_schema=True` is how the pipeline says it
    means to.
    """
    import inspect
    src = inspect.getsource(storage_module.Storage.__init__)
    assert "ensure_schema" in src
    assert "_schema_present" in src, "a read-only open must probe, not create"


def test_the_sidebar_turns_a_fallback_into_a_WARNING_not_a_caption(monkeypatch):
    """⭐⭐ The whole point of recording the reason. Serving the snapshot is correct; doing it quietly is not —
    a dead pipeline would look exactly like a healthy one. ⚠️ This asserts the *level*: `st.warning`, not
    `st.caption`, because a caption is what the freshness line already uses and it is read as routine."""
    from src.web_streamlit import status as status_module

    calls = {"warning": [], "caption": []}
    monkeypatch.setattr(status_module, "fallback_reason", lambda: "OperationalError: connection refused")

    class _Sidebar:
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(status_module.st, "sidebar", _Sidebar())
    monkeypatch.setattr(status_module.st, "warning", lambda msg, **k: calls["warning"].append(msg))
    monkeypatch.setattr(status_module.st, "caption", lambda msg, **k: calls["caption"].append(msg))
    monkeypatch.setattr(status_module.st, "button", lambda *a, **k: False)
    monkeypatch.setattr(status_module, "_player_count", lambda: 659)
    monkeypatch.setattr(status_module, "is_local", lambda: False)

    status_module.render_data_status()

    assert calls["warning"], "the fallback must be a warning, not a caption"
    assert "snapshot" in calls["warning"][0].lower() and "out of date" in calls["warning"][0].lower()
    assert any("connection refused" in c for c in calls["caption"]), "the reason must be shown, not just the fact"


def test_data_status_records_a_FAILED_attempt_not_only_a_successful_one(tmp_path):
    """⭐ *Recording only successes makes a dead pipeline indistinguishable from a quiet one* — the ambiguity
    ADR-203 built `last_seen_at` to remove, in the place it matters most. `attempted_at` moves every run;
    `refreshed_at` moves only when data was actually published."""
    store = storage_module.Storage(str(tmp_path / "s.db"))
    try:
        assert store.data_status() is None, "nothing written yet is the normal state until 2c"
        store.set_data_status(refreshed_at="2026-09-18T10:00:00Z", attempted_at="2026-09-18T10:00:00Z",
                              event=5, ok=True)
        store.set_data_status(attempted_at="2026-09-18T16:00:00Z", ok=False, note="player count collapsed")
        row = store.data_status()
        assert row["attempted_at"] == "2026-09-18T16:00:00Z", "the failed attempt is recorded"
        assert row["refreshed_at"] == "2026-09-18T10:00:00Z", "but it did NOT move the published-at stamp"
        assert not row["ok"] and row["note"] == "player count collapsed"
    finally:
        store.close()


def test_a_WRITER_that_cannot_reach_postgres_raises_instead_of_writing_to_the_seed(monkeypatch):
    """⭐⭐ **A reader may degrade; a writer must not** — and the asymmetry is not stylistic.

    The fallback target is the committed `data/seed.db`. A `refresh` that quietly degraded would write live
    FPL data **into the repository's snapshot** and print success, so the next `git status` would show a
    modified binary and the pipeline would look healthy while writing to the wrong database entirely.

    ⚠️ Found while wiring `cmd_refresh`, not by a failing test — the reader path was written first and
    inheriting it for writers looked obviously right.
    """
    mod = _reloaded(monkeypatch, "postgresql://postgres:x@127.0.0.1:1/nothing")

    store = mod.Storage()                       # a reader: degrades
    try:
        assert store.count_players() > 0 and mod.fallback_reason()
    finally:
        store.close()

    with pytest.raises(Exception) as caught:    # a writer: refuses
        mod.Storage(ensure_schema=True)
    assert "seed" not in str(caught.value).lower(), "it must fail, not silently retarget"


def test_the_refresh_command_declares_itself_a_writer():
    """The guard above is only worth having if the real writer uses it. ⭐ *Testing a component is not testing
    that anything uses it* — the lesson ADR-207 paid for when eight guards passed on a function with no
    caller at all."""
    import inspect

    from src import cli
    assert "ensure_schema=True" in inspect.getsource(cli.cmd_refresh)
