"""Tests for the Admin tester roster + load panel (ADR-120).

The roster answers *"who is actually testing?"* without touching the anonymity invariant (ADR-100): it is a
**separate join** over the owner's own allow-list, not a field on an analytics event. That separation is the
thing most worth pinning — it is why `roster.py` exists as its own module rather than living in `analytics.py`.
"""

from datetime import datetime, timedelta, timezone

from src.web_streamlit import roster
from src.web_streamlit.analytics import load_summary

NOW = datetime(2026, 8, 24, 18, 0, tzinfo=timezone.utc)


def _ago(**kw):
    return (NOW - timedelta(**kw)).isoformat()


# ---- the roster ---------------------------------------------------------------------

def test_a_tester_is_classified_by_when_they_last_persisted():
    assert roster.classify(_ago(days=1), NOW) == "active"
    assert roster.classify(_ago(days=12), NOW) == "dormant"
    assert roster.classify(_ago(days=90), NOW) == "lapsed"


def test_never_signed_in_is_its_own_state_not_the_far_end_of_dormant():
    """A tester who never arrived is a different problem — an unsent invite, a broken link — from one who
    signed in and drifted away."""
    assert roster.classify(None, NOW) == "never"
    assert roster.classify("", NOW) == "never"


def test_an_unparseable_timestamp_reads_as_never_rather_than_crashing():
    assert roster.classify("not-a-date", NOW) == "never"


def test_the_roster_sorts_the_quiet_ones_into_view():
    """The list exists to spot who has gone quiet; a column of blanks at the top would bury that."""
    upd = {"k_a": _ago(days=1), "k_b": _ago(days=12), "k_c": _ago(days=99)}
    rows = roster.build(["a@x.ie", "b@x.ie", "c@x.ie", "d@x.ie"], upd, key_for=lambda e: "k_" + e[0], now=NOW)
    assert [r["status"] for r in rows] == ["active", "dormant", "lapsed", "never"]
    assert rows[-1]["email"] == "d@x.ie" and rows[-1]["days"] is None


def test_the_roster_never_needs_supabase_or_streamlit():
    """`key_for` is injected, so identity derivation stays in auth and this stays a pure function."""
    rows = roster.build(["only@x.ie"], {}, key_for=lambda e: "unused", now=NOW)
    assert rows == [{"email": "only@x.ie", "last_active": None, "status": "never", "days": None}]


def test_totals_count_every_state():
    upd = {"k_a": _ago(days=1), "k_b": _ago(days=1)}
    rows = roster.build(["a@x.ie", "b@x.ie", "c@x.ie"], upd, key_for=lambda e: "k_" + e[0], now=NOW)
    assert roster.totals(rows) == {"active": 2, "dormant": 0, "lapsed": 0, "never": 1, "registered": 3}


def test_an_empty_allow_list_is_safe():
    assert roster.build([], {}, key_for=str) == [] and roster.totals([])["registered"] == 0


# ---- load & concurrency --------------------------------------------------------------

def _ev(sid, mins_ago, op=None, ms=None):
    row = {"session_id": sid, "ts": (NOW - timedelta(minutes=mins_ago)).isoformat()}
    if op:
        row.update(event="perf", duration_ms=ms, meta={"op": op})
    return row


def test_active_now_counts_distinct_sessions_in_the_window():
    rows = [_ev("a", 1), _ev("a", 2), _ev("b", 3), _ev("c", 30)]
    assert load_summary(rows, NOW)["active_now"] == 2      # `a` twice is still one session; `c` is outside


def test_peak_concurrent_finds_the_busiest_window_not_the_current_one():
    """The number to watch is the deadline spike, which by definition isn't happening when you look."""
    rows = [_ev(s, 40) for s in "abcde"] + [_ev("z", 1)]
    out = load_summary(rows, NOW)
    assert out["active_now"] == 1 and out["peak_concurrent"] == 5


def test_p95_takes_the_worst_of_the_timed_operations():
    rows = [_ev("a", 1, "analysis", 900), _ev("b", 1, "data_load", 4000)]
    assert load_summary(rows, NOW)["p95_ms"] >= 4000


def test_health_escalates_on_either_concurrency_or_latency():
    assert load_summary([_ev("a", 1)], NOW)["health"] == "green"
    assert load_summary([_ev(s, 1) for s in "abcdef"], NOW)["health"] == "amber"
    assert load_summary([_ev("a", 1, "analysis", 9000)], NOW)["health"] == "red"


def test_no_events_is_green_and_empty_rather_than_an_error():
    out = load_summary([], NOW)
    assert out == {"active_now": 0, "peak_concurrent": 0, "p95_ms": None, "health": "green", "window_min": 10}


def test_rows_without_timestamps_are_ignored():
    assert load_summary([{"session_id": "a"}, {"ts": "2026-08-24T18:00:00Z"}], NOW)["active_now"] == 0
