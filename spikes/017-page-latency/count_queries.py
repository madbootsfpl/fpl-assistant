"""Count the database round-trips one page render makes.

⭐⭐ **Counting beats timing here, and the reason matters.** The app reads Supabase in eu-west-1; a local
Postgres answers in ~0.1 ms and Supabase in ~20-40 ms. Timing a page against local Docker would understate
the real cost by two orders of magnitude and produce a confident wrong answer — the same shape as the
`chmod 444` probe that altered what it measured.

A **count** is exact, deterministic, and independent of where the database lives. Multiply it by a separately
measured per-round-trip latency and you have the number ADR-211 asked for.
"""
import sqlite3
import sys
from pathlib import Path
import time
from collections import Counter

sys.path.insert(0, ".")

CALLS = Counter()
ORDER = []
BREAKDOWN = {}


def instrument():
    """Install SQLite's own trace hook on every connection the app opens.

    ⚠️ `sqlite3.Connection` is an immutable type, so its `execute` cannot be monkeypatched. `set_trace_callback`
    is the supported seam and is better anyway: it fires for **every statement actually executed**, including
    ones issued inside the driver, which is precisely what a round-trip count wants.
    """
    from src import db as db_module
    real_connect = db_module.connect

    def connect(target):
        conn = real_connect(target)
        if isinstance(conn, sqlite3.Connection):
            conn.set_trace_callback(_trace)
        CALLS["CONNECT"] += 1
        return conn

    db_module.connect = connect


def _trace(sql: str):
    one = " ".join(str(sql).split())
    if one.upper().startswith(("BEGIN", "COMMIT", "ROLLBACK", "PRAGMA")):
        CALLS["housekeeping"] += 1
        return
    CALLS["query"] += 1
    ORDER.append(one[:100])


def render(page: str):
    from streamlit.testing.v1 import AppTest
    CALLS.clear(); ORDER.clear()
    t = time.perf_counter()
    root = Path.cwd()
    at = AppTest.from_file(str(root / "src/web_streamlit/pages" / page), default_timeout=90).run()
    ms = (time.perf_counter() - t) * 1000
    return at, ms, sum(CALLS.values()), list(ORDER)


if __name__ == "__main__":
    instrument()
    pages = sys.argv[1:] or ["1_My_Squad.py", "2_FDR.py", "3_Signals.py",
                             "4_Team_DNA.py", "5_Players.py", "6_Trending.py"]
    print(f"  {'page':<18} {'queries':>8} {'render ms':>10}   exception")
    for page in pages:
        at, ms, n, order = render(page)
        exc = "yes" if at.exception else "-"
        print(f"  {page:<18} {n:>8} {ms:>10.0f}   {exc}")
        BREAKDOWN[page] = (dict(CALLS), order)


def report_duplicates(page="5_Players.py"):
    """Which statements repeat within a single render? ⭐ A repeat is a round-trip that cost nothing new."""
    _at, _ms, n, order = render(page)
    counts = Counter(order)
    print(f"\n  {page}: {n} queries, {len(counts)} distinct")
    print(f"  {'×':>3}  statement")
    for sql, c in counts.most_common(12):
        print(f"  {c:>3}  {sql[:95]}")
    repeats = sum(c - 1 for c in counts.values())
    print(f"\n  → {repeats} of {n} queries ({repeats/n:.0%}) are repeats of a statement already run this render")
