"""The committed snapshot already has every column the code expects (ADR-349).

🔴🔴 **This exists because the same failure shipped twice.** Adding a column means `Storage._migrate` runs
`ALTER TABLE … ADD COLUMN` on any database lacking it — and the committed `data/seed.db` is such a
database. The first test to open it **writes to a file that is in git**.

⚠️⚠️ **And it cannot fail on a developer machine.** A machine that has ever run the app has `data/fpl.db`,
which is gitignored, so the migration lands there invisibly. CI has no such file, so the same code reaches
the snapshot instead. ⭐ *The failure is invisible exactly where the work is done and visible only where
nobody is watching* — which is why it happened a second time four hours after the first.

⭐ So the check moves to where the edit is made: this compares the snapshot's columns against the DDL the
code declares, and fails **before** anything is pushed.
"""

from __future__ import annotations

import pathlib
import sqlite3

import pytest

from src import config, storage

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _declared() -> dict[str, set[str]]:
    """Every table and column the code expects, from the DDL plus the migrations."""
    wanted: dict[str, set[str]] = {}
    for ddl in storage.SCHEMA_DDL:
        name = ddl.split("EXISTS", 1)[1].split("(", 1)[0].strip().strip('"')
        body = ddl.split("(", 1)[1].rsplit(")", 1)[0]
        cols = set()
        for line in body.splitlines():
            line = line.split("--")[0].strip().rstrip(",")
            if not line or line.upper().startswith(("PRIMARY", "FOREIGN", "UNIQUE", "CHECK")):
                continue
            cols.add(line.split()[0].strip('"'))
        wanted[name] = cols
    for table, cols in storage._MIGRATIONS.items():
        wanted.setdefault(table, set()).update(cols)
    return wanted


def _snapshot(table: str) -> set[str]:
    """The snapshot's columns, read **without** opening it through `Storage` — which would migrate it."""
    conn = sqlite3.connect(f"file:{config.SEED_DB_PATH}?mode=ro", uri=True)
    try:
        return {r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
    finally:
        conn.close()


@pytest.mark.parametrize("table", sorted(_declared()))
def test_the_snapshot_carries_every_column_the_code_declares(table: str) -> None:
    """⭐ Fails the moment a column is added without bringing the fixture with it.

    To fix: open the snapshot once so `_migrate` runs, then commit it —

        python -c "from src import config; from src.storage import Storage; Storage(config.SEED_DB_PATH).close()"

    ⚠️ Check the diff is **schema only** before committing: same tables, no row-count change.
    """
    have = _snapshot(table)
    if not have:
        pytest.skip(f"{table} is not in the committed snapshot at all")
    missing = sorted(_declared()[table] - have)
    assert not missing, (
        f"data/seed.db is missing {table}.{missing} — so opening it MIGRATES a file that is in git, "
        f"and CI fails with 'the test suite modified data/seed.db' while every developer machine is fine."
    )
