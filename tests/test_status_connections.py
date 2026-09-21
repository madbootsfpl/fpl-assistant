"""The sidebar freshness caption opens ONE connection (spike 017).

⭐⭐ **It used to open two, and it renders on every page.** `_player_count` opened a `Storage`, counted and
closed; `_data_as_of` opened another, read `data_status` and closed. Against a local SQLite file that costs
nothing. Against Supabase each open is a DNS lookup, a TCP handshake and a TLS handshake before any data
moves — measured at **50-80 ms more than a warm connection** — and Streamlit re-runs the whole script on
every click.

Spike 017 traced **three** connections per page render and **two were this caption**: one line of sidebar
text carrying two thirds of the page's connection overhead.

⚠️ **This counts connections, not milliseconds, and that is deliberate.** A timing test against a local
database would measure a latency the app never experiences and pass whatever the code did — the same trap as
benchmarking Supabase from a laptop. A count is exact, deterministic, and is the thing that actually
multiplies by the network.
"""

import pytest

from src import config
from src import db as db_module
from src.web_streamlit import status


@pytest.fixture
def count_connections(monkeypatch):
    """Count every connection opened, whichever backend is underneath."""
    opened = []
    real = db_module.connect

    def connect(target):
        opened.append(target)
        return real(target)

    monkeypatch.setattr(db_module, "connect", connect)
    return opened


def test_the_freshness_caption_opens_one_connection(count_connections):
    """The property, stated as a number so it cannot drift back."""
    count, as_of = status._freshness()
    assert len(count_connections) == 1, (
        f"the caption opened {len(count_connections)} connections; it renders on every page, and each one "
        f"is a TLS handshake against Supabase")
    assert count and count > 100, "and it must still produce a player count"
    assert as_of and as_of != "unknown", "…and a date"


def test_it_still_reads_the_date_from_the_database_when_there_is_one(monkeypatch, count_connections):
    """⭐ **One connection, but still the RIGHT answer on each backend.** ADR-211 2b: against Postgres the
    date is `data_status.refreshed_at` — the last refresh that actually passed — because a file mtime records
    when something *wrote*, never whether the write was any good. Against SQLite it is the snapshot's mtime,
    which needs no query at all.
    """
    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://fake/db")
    monkeypatch.setattr(status, "fallback_reason", lambda: None)

    class _Store:
        def count_players(self):
            return 667

        def data_status(self):
            return {"refreshed_at": "2026-09-21T08:00:00+00:00"}

        def close(self):
            pass

    monkeypatch.setattr(status, "Storage", lambda *a, **k: _Store())
    count, as_of = status._freshness()
    assert (count, as_of) == (667, "2026-09-21"), "the DB date wins when a database is configured"


def test_a_broken_store_falls_back_to_the_snapshot_date(monkeypatch):
    """⭐ *A caption must never take the page down.* With the database unreadable it reports the local
    snapshot's date, which is the honest answer — that snapshot is what the app is serving."""
    def boom(*a, **k):
        raise RuntimeError("database is on fire")

    monkeypatch.setattr(status, "Storage", boom)
    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://fake/db")
    monkeypatch.setattr(status, "fallback_reason", lambda: None)
    count, as_of = status._freshness()
    assert count is None, "no count is better than a wrong one"
    assert as_of and as_of != "unknown", "the snapshot on disk still has a date"


def test_with_nothing_readable_at_all_it_says_unknown(monkeypatch):
    """⚠️ The worst case, and it must still be a caption rather than a stack trace.

    An earlier version of this test patched only `Storage`, left `DB_PATH` pointing at the real seed, and
    expected `"unknown"` — so it failed on **correct** behaviour. ⭐ *Check what the code actually falls back
    to before asserting what it should say.*
    """
    def boom(*a, **k):
        raise RuntimeError("database is on fire")

    monkeypatch.setattr(status, "Storage", boom)
    monkeypatch.setattr(config, "DATABASE_URL", "postgresql://fake/db")
    monkeypatch.setattr(config, "DB_PATH", "/nonexistent/nothing.db")
    monkeypatch.setattr(status, "fallback_reason", lambda: None)
    assert status._freshness() == (None, "unknown")
