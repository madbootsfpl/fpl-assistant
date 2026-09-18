"""Database connections — one storage layer, two backends (ADR-211).

`Storage` holds every table definition, every upsert and every query in this project, and none of it should
have to be written twice. This module is the **only** place that knows whether those statements are running
against SQLite or Postgres.

**Why there are two.** SQLite is the local cache the CLI has always used and the committed snapshot the web
app reads (ADR-053/056). Postgres is where an autonomous pipeline has to write, because the alternative —
scheduling a commit of the 956 KB snapshot — costs 1.3–32 GB of git history a year depending on cadence
(ADR-211, measured). The destination has to change; the SQL does not.

**The seam is deliberately thin.** `PgConnection` wears `sqlite3.Connection`'s interface — `execute`,
`executemany`, `commit`, `close`, and `with conn:` as a transaction — so `Storage` needs no branching beyond
choosing a connection. Three things actually differ, and each is handled here:

1. **Placeholders.** SQLite takes `?`, psycopg takes `%s`. Every statement is written once in `?` style and
   translated on the way through. ⚠️ That substitution is only safe while no SQL contains a quoted `?`;
   `tests/test_storage_backends.py` asserts exactly that rather than trusting it.
2. **Row access.** `sqlite3.Row` supports **both** named and positional lookup; psycopg's `dict_row` supports
   only named, and `Storage` reads `fetchone()[0]` in six places. ⭐ So rows are wrapped in a `Row` that
   behaves like `sqlite3.Row` — because a row object that is *nearly* the same is how two backends quietly
   diverge, and this codebase has spent three ADRs on that shape of bug (123, 127, 181).
3. **Booleans.** SQLite stores `True` in an `INTEGER` column happily; Postgres refuses. `was_home` and
   `finished` are exactly that, so bools are coerced to ints. ⚠️ Correct **for this schema**, which has no
   genuine boolean column — it would need revisiting if one were ever added.
"""

import sqlite3

_POSTGRES_SCHEMES = ("postgres", "postgresql")


def is_postgres(target) -> bool:
    """True when `target` names a Postgres database rather than a SQLite file path.

    The DSN travels in the same argument as the file path deliberately: `Storage(db_path=…)` already reaches
    every call site, so nothing above this module needs a second parameter or a mode flag.
    """
    return isinstance(target, str) and target.split("://", 1)[0].lower() in _POSTGRES_SCHEMES


class Row:
    """A result row that behaves like `sqlite3.Row` — named *and* positional access, plus `.keys()`.

    ⚠️ **Matching `sqlite3.Row` is the point, not a convenience.** The analytics read rows through `_get(row,
    key)` helpers that catch `(KeyError, IndexError)`, `headlines.leavers` tests `hasattr(row, "keys")`, and
    `Storage` itself indexes `fetchone()[0]`. A plain dict satisfies some of those and not others — and the
    ones it fails are silent.
    """

    __slots__ = ("_cols", "_vals")

    def __init__(self, cols, vals):
        self._cols = cols
        self._vals = tuple(vals)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._vals[key]
        try:
            return self._vals[self._cols.index(key)]
        except ValueError:
            raise KeyError(key) from None      # caught alongside IndexError by every `_get` helper

    def keys(self):
        return list(self._cols)

    def __iter__(self):
        return iter(self._vals)

    def __len__(self):
        return len(self._vals)

    def __contains__(self, key):
        return key in self._cols

    def __eq__(self, other):
        if isinstance(other, Row):
            return self._cols == other._cols and self._vals == other._vals
        return NotImplemented

    def __repr__(self):
        return f"Row({dict(zip(self._cols, self._vals, strict=False))})"


def _row_factory(cursor):
    """psycopg row factory producing `Row`s (called once per result set, not per row)."""
    cols = [d.name for d in cursor.description] if cursor.description else []

    def make(values):
        return Row(cols, values)
    return make


def _adapt(params):
    """Coerce parameters Postgres is stricter about than SQLite.

    Only booleans today: `was_home` and `finished` are declared `INTEGER` and arrive as Python bools, which
    SQLite stores and Postgres rejects. ⚠️ Correct for this schema precisely because it has no real boolean
    column; adding one would make this the wrong place to fix it.
    """
    if params is None:
        return params
    if isinstance(params, dict):
        return {k: int(v) if isinstance(v, bool) else v for k, v in params.items()}
    return [int(p) if isinstance(p, bool) else p for p in params]


class PgConnection:
    """A psycopg connection wearing `sqlite3.Connection`'s interface (ADR-211).

    **Transaction semantics are copied, not approximated.** `sqlite3`'s `with conn:` commits on success and
    rolls back on an exception, while a bare `execute` outside such a block stands alone. Autocommit would
    break the first half — `save_availability` writes hundreds of rows inside one `with`, and a failure
    half-way should leave none of them. So this tracks block depth: statements inside a `with` commit together
    at the end, statements outside it commit immediately.
    """

    def __init__(self, dsn: str):
        import psycopg  # imported here so the CLI runs without it installed

        self._conn = psycopg.connect(dsn, row_factory=_row_factory)
        self._depth = 0

    @staticmethod
    def translate(sql: str) -> str:
        """`?` placeholders → `%s`, escaping any literal `%` first.

        ⚠️ **Both halves are load-bearing, and the second was found by running it.** psycopg parses `%`
        placeholders in every statement — *including one with no parameters at all* — so the `1%` inside a
        column comment in `CREATE TABLE player_transfer_flow` raised *"incomplete placeholder"* and the schema
        would not build. Escaping runs **first**, so the `%s` this method generates is never double-escaped.

        The `?` → `%s` half is exact only while no SQL contains a quoted `?`; `tests/test_storage_backends.py`
        asserts that rather than trusting it.
        """
        out = []
        for line in sql.split("\n"):
            # ⚠️ **A `?` inside a SQL comment is prose, not a placeholder.** `CREATE TABLE data_status` carried
            # the comment *"did the last attempt pass validation?"*, and rewriting that `?` produced a query
            # psycopg counted a parameter for — *"1 placeholders but 0 parameters were passed"* — so the
            # schema would not build. ⭐⭐ The guard test for this swept for a `?` inside a **quoted literal**,
            # which was the failure I imagined; the real one was a comment, and I wrote it myself twenty
            # minutes later. *A guard against a claim must sweep for the claim, not for the version of it you
            # thought of* (ADR-184, again).
            code, sep, comment = line.partition("--")
            out.append(code.replace("%", "%%").replace("?", "%s") + sep + comment.replace("%", "%%"))
        return "\n".join(out)

    def execute(self, sql, params=()):
        # ⚠️ **A failed statement must be rolled back, and this has no SQLite equivalent.** Postgres marks the
        # whole transaction aborted after any error, so every later statement fails with *"current transaction
        # is aborted"* until someone rolls back. `Storage` deliberately catches a missing table and carries on
        # (ADR-151); without this, that recovery would poison the connection instead.
        try:
            cur = self._conn.execute(self.translate(sql), _adapt(params))
        except Exception:
            if self._depth == 0:
                self._conn.rollback()
            raise
        if self._depth == 0:
            self._conn.commit()
        return cur

    def executemany(self, sql, seq_of_params):
        rows = [_adapt(p) for p in seq_of_params]
        with self._conn.cursor() as cur:
            cur.executemany(self.translate(sql), rows)
        if self._depth == 0:
            self._conn.commit()

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()

    def __enter__(self):
        self._depth += 1
        return self

    def __exit__(self, exc_type, exc, tb):
        self._depth -= 1
        if self._depth == 0:
            self._conn.rollback() if exc_type else self._conn.commit()
        return False


def _optional_pg_errors(*names):
    """Postgres error classes by name, or `()` when psycopg is not installed.

    The CLI and CI run without psycopg, so the exception tuples below must degrade to their SQLite halves
    rather than making the driver a hard dependency of `import src.storage`.
    """
    try:
        from psycopg import errors
    except ImportError:
        return ()
    return tuple(getattr(errors, n) for n in names if hasattr(errors, n))


# ⚠️ **"The table is not there" is spelled differently by each driver, and `Storage` catches it on purpose**
# (a snapshot older than a table must degrade, never raise — ADR-151). Catching only the SQLite spelling
# meant that on Postgres the same situation became a crash.
MISSING_TABLE = (sqlite3.OperationalError,) + _optional_pg_errors("UndefinedTable", "UndefinedColumn")

# Likewise for a foreign-key violation: both backends enforce the constraint, and only the class name differs.
INTEGRITY_ERROR = (sqlite3.IntegrityError,) + _optional_pg_errors("IntegrityError")


def connect(target: str):
    """Open `target` — a Postgres DSN or a SQLite path — as a connection `Storage` can use unchanged."""
    if is_postgres(target):
        return PgConnection(target)
    conn = sqlite3.connect(target)
    # Foreign keys are OFF by default in SQLite, per connection, so a player/fixture cannot reference a team
    # that does not exist. Postgres enforces them without asking.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn
