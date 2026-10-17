"""The suite reads the committed seed, on every machine (ADR-355).

🔴 `config.DB_PATH` resolves to `data/fpl.db` when that file exists and `data/seed.db` when it does not —
so the suite read **a gitignored, machine-specific file** locally and the committed snapshot on CI. 81
bare `Storage()` calls, two different databases, and ⚠️⚠️ *it does not fail, it disagrees* — which reads
as a wrong diagnosis rather than a wrong setup.

It bit three times before it was fixed: a local `refresh` turned ten unrelated tests red; a contract
failure was called local-only when it was not; and two tests in `test_web_streamlit.py` **branched** on
which database they got, so half of each had never run on CI at all.

⭐ The pin lives in `conftest.pytest_configure`. This file is the guard on the pin — ⚠️ *and it lives here
rather than in `conftest.py` because pytest does not collect tests from a conftest*, so the first version
of this guard passed when run by name and never ran with the suite.
"""

from src import config
from src.storage import Storage


def test_the_suite_never_reads_the_live_cache():
    """⭐ *A pin nothing checks is a pin someone removes* — and the symptom would not be a red test, it
    would be a different answer on a different machine."""
    assert config.DB_PATH != config.LIVE_DB_PATH, (
        "tests are reading data/fpl.db — a gitignored file whose contents depend on when `refresh` last ran"
    )


def test_a_bare_store_reads_the_config_when_it_is_asked_not_when_it_was_imported(tmp_path, monkeypatch):
    """⚠️⚠️ **The pin has to reach `Storage()` itself, not just the constant.** 🔴 It did not: the default
    argument `db_path=config.DB_PATH` was bound **once, when the `def` ran at import**, so patching the
    config afterwards did nothing at all — a fact one test already recorded as something to work around
    rather than fix (*"the seam has to be the name the service module actually calls"*).

    ⭐⭐ The same trap `conftest` spells out for the language model, one layer down. ⚠️ *A pin that cannot
    reach the constructor is decoration*, and the suite would look pinned while reading whatever it liked.
    """
    import shutil

    elsewhere = tmp_path / "somewhere-else.db"
    shutil.copy(config.SEED_DB_PATH, elsewhere)
    monkeypatch.setattr(config, "DB_PATH", str(elsewhere))

    store = Storage()
    try:
        opened = [row[2] for row in store.conn.execute("PRAGMA database_list")]
    finally:
        store.close()
    assert str(elsewhere) in opened, f"Storage ignored the patched config and opened {opened}"
