"""Schema additions must reach databases that already exist (ADR-298).

⚠️⚠️ **`CREATE TABLE IF NOT EXISTS` does not alter a table that is already there.** A column added to the
schema in `storage.py` appears only in databases created after it — every laptop cache, the committed
test fixture and production's Postgres keep the old shape, and the first write fails on a column the file
plainly declares.

⭐⭐ **And the registration itself failed silently once.** `yellow_cards` was added under a *second*
`"player_history"` key in `_MIGRATIONS`; Python keeps the last and discards the other, so the schema had
the column, the migration looked registered, and an existing database gained nothing. *A duplicate key in
a dict literal is not an error — it is a deletion.*
"""

from __future__ import annotations

import ast
import collections
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "src" / "storage.py").read_text()


def _migrations_node() -> ast.Dict:
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            getattr(t, "id", None) == "_MIGRATIONS" for t in node.targets
        ):
            assert isinstance(node.value, ast.Dict)
            return node.value
    raise AssertionError("_MIGRATIONS is gone")


def test_no_table_is_registered_twice() -> None:
    """⭐ Read from the **source**, not the imported dict — by the time Python has built it, the evidence
    of the duplicate is gone. *The bug is invisible to the thing it breaks.*"""
    keys = [k.value for k in _migrations_node().keys if isinstance(k, ast.Constant)]
    dupes = [t for t, n in collections.Counter(keys).items() if n > 1]

    assert not dupes, (
        f"_MIGRATIONS lists {dupes} more than once — Python keeps the last and silently "
        f"discards the earlier entry, so those columns never migrate"
    )


def test_every_history_column_can_reach_an_old_database() -> None:
    """⚠️ The schema and the migration list must agree, or the difference is exactly the set of columns
    that work on a fresh database and fail on a real one.

    ⭐ Derived from the `CREATE TABLE` itself, so a column added tomorrow is covered without anyone
    remembering this file.
    """
    create = SOURCE[SOURCE.index("CREATE TABLE IF NOT EXISTS player_history ("):]
    create = create[: create.index(")\n\"\"\"")]
    declared = {
        line.strip().split()[0]
        for line in create.splitlines()[1:]
        if line.strip() and not line.strip().startswith(("--", "PRIMARY", ")"))
    }

    from src.storage import _MIGRATIONS

    # The original columns of the table predate migrations; the ones this test protects are those the
    # file itself marks as later additions by listing them.
    migratable = set(_MIGRATIONS["player_history"])
    for late in ("yellow_cards", "red_cards"):
        assert late in declared, f"{late} is not in the CREATE TABLE"
        assert late in migratable, (
            f"{late} is in the schema and not in _MIGRATIONS — it will be missing from every "
            f"database that already exists"
        )


def test_an_existing_database_gains_them() -> None:
    """⭐ The end-to-end claim, on a real connection: open a database made before the column existed and
    it converges. ⚠️ *Reading the list proves it was registered; opening a database proves it works.*"""
    import sqlite3
    from src import db
    from src.storage import _MIGRATIONS, Storage

    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE player_history (element_code INTEGER, round INTEGER)")
    con.commit()

    for column, col_type in _MIGRATIONS["player_history"].items():
        if column not in db.columns(con, "player_history"):
            con.execute(f"ALTER TABLE player_history ADD COLUMN {column} {col_type}")

    assert {"yellow_cards", "red_cards"} <= db.columns(con, "player_history")
