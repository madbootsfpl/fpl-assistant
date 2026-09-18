"""The storage layer runs on two backends, and the seam between them holds (ADR-211, Phase 2a).

`Storage` holds every table definition and query in this project. Phase 2 needs those statements to run
against Postgres — because scheduling a commit of the SQLite snapshot costs 1.3–32 GB of git a year (ADR-211)
— **without writing any of them twice**. `src/db.py` is the whole of the difference.

⚠️ **These tests do not need a Postgres to be useful.** They check the *assumptions* the translation rests on,
which is the part that can rot silently. The behavioural proof is the whole suite run twice:

    pytest                                                          # SQLite
    MADBOOTS_TEST_DSN=postgresql://… pytest                         # Postgres
"""

import re
import sqlite3
from pathlib import Path

import pytest

from src import db, storage

SQL_CONSTANTS = [name for name in dir(storage)
                 if name.isupper() and isinstance(getattr(storage, name), str)]


def test_no_sql_contains_a_quoted_question_mark():
    """⭐ The assumption `?` → `%s` rests on, made into a test rather than trusted.

    `PgConnection.translate` rewrites every `?` in a statement. That is exact **only** while no `?` appears
    inside a string literal — the day one does, the translation would corrupt the query rather than fail, and
    the symptom would surface far from the cause.
    """
    offenders = []
    for name in SQL_CONSTANTS:
        for literal in re.findall(r"'[^']*'", getattr(storage, name)):
            if "?" in literal:
                offenders.append(f"{name}: {literal}")
    # The whole file, not just the constants — inline SQL is built in several methods.
    source = Path(storage.__file__).read_text()
    for literal in re.findall(r'"[^"\n]*\?[^"\n]*"', source):
        if re.search(r"'[^']*\?[^']*'", literal):
            offenders.append(literal)
    assert not offenders, "a quoted '?' would be rewritten as a placeholder:\n" + "\n".join(offenders)


def test_a_literal_percent_is_escaped_before_placeholders_are_written():
    """⚠️ Found by running it, not by reading it. psycopg parses `%` placeholders in **every** statement —
    including one with no parameters — so the `1%` inside a column comment in `CREATE TABLE
    player_transfer_flow` raised *"incomplete placeholder"* and the schema would not build.

    Order matters: escaping must happen **before** `?` becomes `%s`, or the placeholder we just generated
    gets escaped too and binds nothing."""
    assert db.PgConnection.translate("SELECT '100%' WHERE x = ?") == "SELECT '100%%' WHERE x = %%s".replace(
        "%%s", "%s")
    assert db.PgConnection.translate(storage.CREATE_TRANSFER_FLOW).count("%%") == \
        storage.CREATE_TRANSFER_FLOW.count("%")
    assert "%s" not in db.PgConnection.translate("SELECT 1")     # nothing to bind, nothing invented


def test_the_row_type_matches_sqlite3_Row_where_the_codebase_relies_on_it():
    """⭐ Rows from the two backends must be indistinguishable to everything above `Storage`.

    A plain dict would satisfy `row["name"]` and fail `row[0]`, which `Storage` uses in six places; it would
    also raise `KeyError` where `sqlite3.Row` raises `IndexError`, and the analytics catch **both** in their
    `_get` helpers. ⚠️ *A row object that is nearly the same is how two backends quietly disagree.*
    """
    row = db.Row(["id", "web_name"], [7, "Haaland"])
    assert row["web_name"] == "Haaland"      # named, like sqlite3.Row
    assert row[0] == 7                       # positional, like sqlite3.Row — a dict cannot do this
    assert row.keys() == ["id", "web_name"]  # `headlines.leavers` tests hasattr(row, "keys")
    assert "id" in row and len(row) == 2
    with pytest.raises((KeyError, IndexError)):   # exactly what every `_get` helper catches
        row["nope"]


def test_bools_are_coerced_because_two_INTEGER_columns_receive_them():
    """`was_home` and `finished` are declared INTEGER and arrive as Python bools. SQLite stores that happily;
    Postgres rejects it. ⚠️ The coercion is right *for this schema* — it has no genuine boolean column — and
    this test names the two columns so that adding one is visibly a reason to revisit it."""
    assert db._adapt([True, False, 3, None, "x"]) == [1, 0, 3, None, "x"]
    assert db._adapt({"finished": True}) == {"finished": 1}
    ddl = storage.CREATE_HISTORY + storage.CREATE_FIXTURES
    assert "was_home       INTEGER" in ddl and "finished          INTEGER" in ddl
    assert "BOOLEAN" not in ddl.upper(), "a real boolean column would make _adapt the wrong fix"


def test_a_dsn_is_recognised_and_a_file_path_is_not():
    for dsn in ("postgres://u:p@h/db", "postgresql://u:p@h/db", "POSTGRESQL://u@h/db"):
        assert db.is_postgres(dsn)
    for path in (":memory:", "data/fpl.db", "/tmp/x.db", None, 5):
        assert not db.is_postgres(path)


def test_the_error_tuples_carry_the_sqlite_classes_even_without_psycopg():
    """The CLI and CI run with no psycopg installed, so `import src.storage` must not require it. The tuples
    degrade to their SQLite halves rather than the driver becoming a hard dependency."""
    assert sqlite3.OperationalError in db.MISSING_TABLE
    assert sqlite3.IntegrityError in db.INTEGRITY_ERROR


def test_the_sqlite_only_marker_is_used_only_where_postgres_has_no_equivalent():
    """⚠️ **A skip is not a pass** (ADR-178). This pins *which* tests opt out of the Postgres run, so the list
    cannot quietly grow: the SQLite-legacy column/key migrations, and `reseed` — which copies a **file**, and
    is the manual deploy path ADR-211 exists to replace."""
    marked = set()
    for path in Path(__file__).parent.glob("test_*.py"):
        text = path.read_text()
        for match in re.finditer(r"@pytest\.mark\.sqlite_only\s*\ndef (test_\w+)", text):
            marked.add(match.group(1))
    migrations = {m for m in marked if "migration" in m or "rekey" in m or "old_database" in m}
    reseed = {m for m in marked if "reseed" in m}
    assert marked == migrations | reseed, (
        "only the SQLite-legacy migrations and the file-copy reseed may skip the Postgres run; "
        f"unexpected: {sorted(marked - migrations - reseed)}")
    # 7 column migrations + 3 rekey + 1 history-retention + 2 reseed. Pinned so the list cannot grow
    # quietly; changing it should mean deciding that something new genuinely has no Postgres form.
    assert len(marked) == 13, f"expected 13 opt-outs, found {len(marked)}: {sorted(marked)}"
