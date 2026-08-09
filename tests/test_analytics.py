"""Tests for the analytics client (ADR-100, US-332).

The client must be **fail-silent** and **off by default**: no thread/write when disabled, a raising store swallowed,
an anonymised payload when on. No live network — `requests.post` is monkeypatched, and the daemon thread is replaced
by a synchronous stand-in so we can inspect the payload.
"""

import types

import pytest

from src.web_streamlit import analytics


class _Resp:
    def raise_for_status(self):
        pass


def _thread_spy(monkeypatch, run=False):
    """Replace analytics' `threading` so `Thread(...).start()` records the call (and runs it inline if `run`)."""
    calls = []

    class _T:
        def __init__(self, target=None, args=(), daemon=None):
            calls.append((target, args))
            self._target, self._args = target, args

        def start(self):
            if run:
                self._target(*self._args)

    monkeypatch.setattr(analytics, "threading", types.SimpleNamespace(Thread=_T))
    return calls


def _enable(monkeypatch, endpoint=("https://p.supabase.co/rest/v1/events", "k")):
    monkeypatch.setattr(analytics, "is_enabled", lambda: True)
    monkeypatch.setattr(analytics, "_events_endpoint", lambda: endpoint)
    monkeypatch.setattr(analytics, "session_id", lambda: "sid123")
    monkeypatch.setattr(analytics, "anon_id", lambda: "anon456")


# --- is_enabled / endpoint ----------------------------------------------------------

def test_is_enabled_requires_the_flag_and_the_store(monkeypatch):
    monkeypatch.setenv("FPL_STORE_URL", "https://p.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    monkeypatch.setenv("FPL_ANALYTICS", "1")
    assert analytics.is_enabled() is True
    monkeypatch.setenv("FPL_ANALYTICS", "off")
    assert analytics.is_enabled() is False               # flag not truthy → off
    monkeypatch.delenv("FPL_ANALYTICS")
    assert analytics.is_enabled() is False               # flag unset → off (default)
    monkeypatch.setenv("FPL_ANALYTICS", "1")
    monkeypatch.delenv("FPL_STORE_URL")
    monkeypatch.delenv("FPL_STORE_KEY")
    assert analytics.is_enabled() is False               # no store → off


def test_events_endpoint_derives_from_the_store_url(monkeypatch):
    monkeypatch.setenv("FPL_STORE_URL", "https://p.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    assert analytics._events_endpoint() == ("https://p.supabase.co/rest/v1/events", "k")   # sibling table
    monkeypatch.delenv("FPL_STORE_URL")
    assert analytics._events_endpoint() == (None, None)


# --- off by default: a hard no-op ---------------------------------------------------

def test_disabled_is_a_no_op_no_thread_no_post(monkeypatch):
    monkeypatch.setattr(analytics, "is_enabled", lambda: False)
    calls = _thread_spy(monkeypatch)
    monkeypatch.setattr("requests.post", lambda *a, **k: pytest.fail("no POST when analytics is off"))
    analytics.track("page_viewed", page="Squads")
    assert calls == []                                   # no thread spawned


# --- enabled: an anonymised, fire-and-forget event ----------------------------------

def test_enabled_posts_an_anonymised_payload(monkeypatch):
    _enable(monkeypatch)
    _thread_spy(monkeypatch, run=True)
    posted = {}
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None:
                        posted.update(url=url, body=json, headers=headers, timeout=timeout) or _Resp())
    analytics.track("page_viewed", page="Squads", view="Health", n=15)

    assert posted["url"].endswith("/rest/v1/events")
    body = posted["body"]
    assert set(body) == {"ts", "session_id", "anon_id", "version", "event", "page", "duration_ms", "ok", "meta"}
    assert body["event"] == "page_viewed" and body["page"] == "Squads" and body["ok"] is True
    assert body["session_id"] == "sid123" and body["anon_id"] == "anon456"
    assert body["version"] == analytics.config.APP_VERSION
    assert body["meta"] == {"view": "Health", "n": 15}                  # small structured context only
    assert "Bearer k" in posted["headers"]["Authorization"] and posted["timeout"] == analytics._TIMEOUT


def test_no_pii_fields_leak_into_the_payload(monkeypatch):
    _enable(monkeypatch)
    _thread_spy(monkeypatch, run=True)
    posted = {}
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: posted.update(body=json) or _Resp())
    analytics.track("squad_saved", page="Squads")
    blob = str(posted["body"]).lower()
    for banned in ("email", "@", "handle", "player_ids", "ip"):
        assert banned not in blob                          # anonymous + minimal (ADR-100)


# --- fail-silent: never raises into the app -----------------------------------------

def test_a_raising_store_is_swallowed(monkeypatch):
    _enable(monkeypatch)
    _thread_spy(monkeypatch, run=True)

    def boom(*a, **k):
        raise ConnectionError("supabase down")
    monkeypatch.setattr("requests.post", boom)
    analytics.track("analysis_run", page="Squads")        # must not raise


def test_track_never_raises_even_if_building_fails(monkeypatch):
    monkeypatch.setattr(analytics, "is_enabled", lambda: True)
    monkeypatch.setattr(analytics, "_events_endpoint", lambda: ("https://x/rest/v1/events", "k"))
    monkeypatch.setattr(analytics, "session_id", lambda: (_ for _ in ()).throw(RuntimeError("no ctx")))
    calls = _thread_spy(monkeypatch)
    analytics.track("page_viewed")                        # session_id raised → swallowed, no thread
    assert calls == []


# --- timed(): a perf event ----------------------------------------------------------

def test_timed_emits_a_perf_event(monkeypatch):
    events = []
    monkeypatch.setattr(analytics, "track", lambda event, **kw: events.append((event, kw)))
    with analytics.timed("data_load", page="Squads"):
        pass
    assert events and events[0][0] == "perf"
    kw = events[0][1]
    assert kw["page"] == "Squads" and kw["op"] == "data_load" and kw["ok"] is True and kw["duration_ms"] >= 0


def test_timed_marks_failure_and_reraises(monkeypatch):
    events = []
    monkeypatch.setattr(analytics, "track", lambda event, **kw: events.append((event, kw)))
    with pytest.raises(ValueError):
        with analytics.timed("analysis"):
            raise ValueError("boom")
    assert events[0][1]["ok"] is False                    # failure recorded, and the error propagated


# --- session id: stable within a session --------------------------------------------

def test_session_id_is_stable_within_a_session():
    from streamlit.testing.v1 import AppTest
    script = (
        "import streamlit as st\n"
        "from src.web_streamlit import analytics\n"
        "st.session_state['a'] = analytics.session_id()\n"
        "st.session_state['b'] = analytics.session_id()\n"
    )
    at = AppTest.from_string(script).run()
    assert at.session_state["a"] == at.session_state["b"] and len(at.session_state["a"]) >= 16
