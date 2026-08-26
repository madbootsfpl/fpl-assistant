"""Tests for per-user preferences (ADR-147).

The store is faked throughout — no test touches Supabase. What these pin is the behaviour that decides whether
the feature is usable: it degrades to session-only rather than breaking, it writes only when something
changed, and a silent store failure is *reportable* (the ADR-142 lesson, which cost a day).
"""

import requests

from src.web_streamlit import prefs


class _Resp:
    def __init__(self, payload=None, status=200):
        self._payload, self.status_code, self.text = payload, status, ""

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self._payload


def _session(monkeypatch, initial=None):
    """A stand-in for `st.session_state` — a plain dict is enough for what prefs does with it."""
    import streamlit as st
    state = dict(initial or {})
    monkeypatch.setattr(st, "session_state", state, raising=False)
    return state


def _signed_in(monkeypatch, uk="user-abc"):
    monkeypatch.setattr(prefs, "_user_key", lambda: uk)
    monkeypatch.setattr(prefs, "_endpoint", lambda: ("https://x/user_prefs", "k"))


# ---- degrading, which is the common case ---------------------------------------------

def test_signed_out_it_still_remembers_for_the_session(monkeypatch):
    """The page works without an account today and must keep working. Signed out you get session-only —
    exactly the old behaviour — rather than an error or a dead control."""
    state = _session(monkeypatch)
    monkeypatch.setattr(prefs, "_user_key", lambda: None)
    monkeypatch.setattr(prefs, "_endpoint", lambda: (None, None))

    assert prefs.remember(manager_id="123") == "session only (not signed in)"
    assert prefs.recall() == {"manager_id": "123"}
    assert state["_prefs"] == {"manager_id": "123"}


def test_with_no_store_configured_nothing_reaches_the_network(monkeypatch):
    _session(monkeypatch)
    monkeypatch.setattr(prefs, "_user_key", lambda: "u")
    monkeypatch.setattr(prefs, "_endpoint", lambda: (None, None))
    monkeypatch.setattr(requests, "post",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must not call out")))
    assert prefs.remember(manager_id="123") == "store not configured"


def test_a_store_failure_leaves_the_session_value_intact(monkeypatch):
    """A lost sync is acceptable; a lost preference in front of the user is not."""
    _session(monkeypatch)
    _signed_in(monkeypatch)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: (_ for _ in ()).throw(requests.ConnectionError("x")))
    out = prefs.remember(manager_id="123")
    assert "write failed" in out
    assert prefs.recall()["manager_id"] == "123", "the page must still behave for the rest of the session"


# ---- restoring ------------------------------------------------------------------------

def test_it_restores_from_the_cloud_once_per_session(monkeypatch):
    """Once, not per rerun — Streamlit reruns constantly and this is a value that moves twice a season."""
    _session(monkeypatch)
    _signed_in(monkeypatch)
    calls = []

    def fake_get(url, params=None, headers=None, timeout=None):
        calls.append(params)
        return _Resp([{"manager_id": "999", "league_id": 42}])

    monkeypatch.setattr(requests, "get", fake_get)
    assert prefs.recall() == {"manager_id": "999", "league_id": 42}
    prefs.recall()
    prefs.recall()
    assert len(calls) == 1, "a restore per rerun would be a network call on every page view"


def test_a_failed_restore_does_not_wipe_what_the_session_has(monkeypatch):
    """`_load` returns None on failure — deliberately distinct from `{}` ("nothing stored"), so a flaky
    network cannot look like a deliberate clearing of your preferences."""
    _session(monkeypatch)
    _signed_in(monkeypatch)
    monkeypatch.setattr(requests, "get", lambda *a, **kw: (_ for _ in ()).throw(requests.ConnectionError("x")))
    assert prefs.recall() == {}


# ---- writing only when it matters -----------------------------------------------------

def test_an_unchanged_value_is_not_written_again(monkeypatch):
    """Streamlit reruns on every interaction. Re-saving an unchanged preference would be a network call per
    page view for a value that changes about twice a season."""
    _session(monkeypatch, {"_prefs": {"manager_id": "123"}, "_prefs_restored": True})
    _signed_in(monkeypatch)
    monkeypatch.setattr(requests, "post",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("must not write")))
    assert prefs.remember(manager_id="123") == "unchanged"
    assert prefs.remember(manager_id=123) == "unchanged", "compared as text — 123 and '123' are one id"


def test_only_known_fields_are_stored(monkeypatch):
    """A typo'd keyword must not become a column the table doesn't have — that failure surfaces as an opaque
    PostgREST 400 long after the call site."""
    _session(monkeypatch)
    monkeypatch.setattr(prefs, "_user_key", lambda: None)
    assert prefs.remember(nonsense="x") == "nothing to store"
    assert prefs.remember(manager_id=None) == "nothing to store", "None means 'no opinion', not 'clear it'"


# ---- the failure that cost a day last time (ADR-142) ----------------------------------

def test_a_write_that_touches_no_rows_names_row_level_security(monkeypatch):
    """ADR-142's lesson, applied before it can bite. An identical write failed silently for a day because a
    table had SELECT and INSERT policies and no UPDATE policy — and PostgREST reports that as **200 OK with
    zero rows**, not an error. Nothing should show a tester an error over a stored preference, but the
    operator has to be able to find out why nothing sticks."""
    _session(monkeypatch)
    _signed_in(monkeypatch)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _Resp([]))
    out = prefs.remember(manager_id="123")
    assert "row-level security" in out and "no rows" in out


def test_a_refused_write_reports_the_status(monkeypatch):
    _session(monkeypatch)
    _signed_in(monkeypatch)
    monkeypatch.setattr(requests, "post", lambda *a, **kw: _Resp(None, status=401))
    assert "401" in prefs.remember(manager_id="123")
