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


# --- anon_id: the returning-user cookie (US-333) ------------------------------------

_ANON_SCRIPT = (
    "import streamlit as st\n"
    "from src.web_streamlit import analytics\n"
    "st.session_state['result'] = analytics.anon_id()\n"
)


def _anon_app(monkeypatch, *, existing, available):
    from streamlit.testing.v1 import AppTest

    from src.web_streamlit import remember
    minted = []
    monkeypatch.setattr(remember, "read_cookie", lambda name: existing)
    monkeypatch.setattr(remember, "available", lambda: available)
    monkeypatch.setattr(remember, "write_cookie", lambda name, value, **kw: minted.append((name, value)))
    return AppTest.from_string(_ANON_SCRIPT), minted


def test_anon_id_returns_the_existing_cookie(monkeypatch):
    at, minted = _anon_app(monkeypatch, existing="returning-abc", available=True)
    at.run()
    assert at.session_state["result"] == "returning-abc" and minted == []     # returning → no mint


def test_anon_id_defers_on_the_loading_run_then_mints(monkeypatch):
    at, minted = _anon_app(monkeypatch, existing=None, available=True)
    at.run()                                                                  # run 1: still loading → defer
    assert at.session_state["result"] is None and minted == []                # crucially, no mint yet
    at.run()                                                                  # run 2: settled → mint + write
    assert at.session_state["result"] and minted and minted[0][0] == "fpl_anon"


def test_anon_id_mints_immediately_without_a_component(monkeypatch):
    at, minted = _anon_app(monkeypatch, existing=None, available=False)
    at.run()                                                                  # no component → no waiting
    assert at.session_state["result"] and minted and minted[0][0] == "fpl_anon"


# --- boot(): session_started once + page_viewed (US-334) -----------------------------

def test_boot_emits_session_started_once_then_page_viewed(monkeypatch):
    from streamlit.testing.v1 import AppTest
    events = []
    monkeypatch.setattr(analytics, "is_enabled", lambda: True)
    monkeypatch.setattr(analytics, "anon_id", lambda: None)
    monkeypatch.setattr(analytics, "track", lambda event, **kw: events.append((event, kw.get("page"))))
    script = ("from src.web_streamlit import analytics\n"
              "analytics.boot('Home')\n"       # first render this session
              "analytics.boot('Squads')\n")    # a later page — session_started must NOT repeat
    AppTest.from_string(script).run()
    assert events == [("session_started", "Home"), ("page_viewed", "Home"), ("page_viewed", "Squads")]


def test_boot_is_a_no_op_when_disabled(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(analytics, "is_enabled", lambda: False)
    monkeypatch.setattr(analytics, "track", lambda *a, **k: pytest.fail("no track when analytics is off"))
    AppTest.from_string("from src.web_streamlit import analytics\nanalytics.boot('Home')\n").run()


# --- THE guardrail: analytics can never affect the app (ADR-100) ---------------------

def _home():
    from pathlib import Path
    return str(Path(__file__).resolve().parents[1] / "src" / "web_streamlit" / "Home.py")


def test_analytics_failure_never_breaks_a_page(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.setenv("FPL_STORE_URL", "https://p.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    monkeypatch.setenv("FPL_ANALYTICS", "1")                 # analytics ON
    _thread_spy(monkeypatch, run=True)                       # run the post inline so a raise happens synchronously

    def boom(*a, **k):
        raise ConnectionError("supabase down")
    monkeypatch.setattr("requests.post", boom)
    at = AppTest.from_file(_home(), default_timeout=30).run()
    assert not at.exception                                  # a raising analytics store never reaches the app
    assert any("FPL Assistant" in t.value for t in at.title)  # the page rendered


def test_no_analytics_write_when_disabled(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.delenv("FPL_ANALYTICS", raising=False)       # off by default
    monkeypatch.setattr("requests.post", lambda *a, **k: pytest.fail("no analytics POST when disabled"))
    at = AppTest.from_file(_home(), default_timeout=30).run()
    assert not at.exception
