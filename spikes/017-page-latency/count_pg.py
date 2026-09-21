"""The same count, on the Postgres path — because the query MIX differs from SQLite.

⭐ ADR-211 made a reader on Postgres **return early without creating the schema** (it probes instead), so the
eleven `CREATE TABLE IF NOT EXISTS` statements that dominate the SQLite count do not happen here. Counting on
SQLite and assuming Postgres matches would have produced the wrong diagnosis — ⭐ *ask which path the code
actually takes, do not infer it from the one you measured.*

Counts are latency-independent, so a local Postgres answers this correctly even though it could never answer
a question about *timing*.
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, ".")

CALLS = Counter()
ORDER = []
CONNECTIONS = []


def instrument():
    from src import db as db_module

    real_connect = db_module.connect
    real_execute = db_module.PgConnection.execute
    real_executemany = db_module.PgConnection.executemany

    def connect(target):
        CONNECTIONS.append(target)
        return real_connect(target)

    def execute(self, sql, *a, **kw):
        one = " ".join(str(sql).split())
        if not one.upper().startswith(("BEGIN", "COMMIT", "ROLLBACK", "SET ")):
            CALLS["query"] += 1
            ORDER.append(one[:100])
        return real_execute(self, sql, *a, **kw)

    def executemany(self, sql, *a, **kw):
        CALLS["query"] += 1
        ORDER.append("MANY: " + " ".join(str(sql).split())[:94])
        return real_executemany(self, sql, *a, **kw)

    db_module.connect = connect
    db_module.PgConnection.execute = execute
    db_module.PgConnection.executemany = executemany


def render(page):
    import time

    from streamlit.testing.v1 import AppTest
    CALLS.clear(); ORDER.clear(); CONNECTIONS.clear()
    t = time.perf_counter()
    at = AppTest.from_file(str(Path.cwd() / "src/web_streamlit/pages" / page), default_timeout=90).run()
    return at, (time.perf_counter() - t) * 1000, CALLS["query"], len(CONNECTIONS), list(ORDER)
