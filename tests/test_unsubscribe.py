"""Tests for the self-service unsubscribe store (ADR-122, US-428).

No live network — `requests.delete` is monkeypatched. The store reuses the squads `FPL_STORE_URL`/`FPL_STORE_KEY`
(the sibling endpoints are derived). `remove_me()` is **best-effort + fail-silent** — it must never raise.
"""

from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

from src.web_streamlit import access, unsubscribe

# A tiny app that renders the shared "Leave the beta" control as a signed-in tester (ADR-122).
_LEAVE_APP = """
import streamlit as st
from src.web_streamlit import access
st.session_state[access._OK] = True
st.session_state[access._EMAIL] = "tester@example.com"
access.render_leave_beta()
"""


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "anon-key")


class _Deleted:
    """A PostgREST delete that removed a row. ADR-148 reads the returned rows to tell a real delete from one
    that silently matched nothing — so the fake has to answer like the real thing."""

    status_code = 200

    def json(self):
        return [{"ok": 1}]


@pytest.fixture
def capture_deletes(monkeypatch):
    """Record every `requests.delete(url, params=…)` call as `(url, params)`."""
    calls = []

    def fake(url, params=None, headers=None, timeout=None):
        calls.append((url, params))
        return _Deleted()

    monkeypatch.setattr("requests.delete", fake)
    return calls


def test_endpoints_derive_the_sibling_tables(configured):
    base, squads_url, key = unsubscribe._base_and_key()
    assert base == "https://proj.supabase.co/rest/v1"                       # sibling base (beta_users/-waitlist live here)
    assert squads_url == "https://proj.supabase.co/rest/v1/squads"         # the squads endpoint itself
    assert key == "anon-key"


def test_remove_me_by_email_deletes_waitlist_and_beta_users(configured, capture_deletes):
    unsubscribe.remove_me("  Late@Example.com ")                           # no user_key → email tables only
    urls = {u for u, _ in capture_deletes}
    assert urls == {"https://proj.supabase.co/rest/v1/beta_waitlist",
                    "https://proj.supabase.co/rest/v1/beta_users"}
    for _, params in capture_deletes:
        assert params == {"email": "eq.late@example.com"}                  # cleaned (lower-cased + trimmed) + eq. filter


def test_remove_me_with_user_key_also_deletes_squad_and_watchlist(configured, capture_deletes):
    unsubscribe.remove_me("me@x.com", user_key="abc123")
    targets = {(u.rsplit("/", 1)[1], tuple(p.items())) for u, p in capture_deletes}
    assert ("beta_waitlist", (("email", "eq.me@x.com"),)) in targets
    assert ("beta_users", (("email", "eq.me@x.com"),)) in targets
    assert ("squads", (("handle", "eq.abc123"),)) in targets               # per-user squad (handle = user_key hash)
    assert ("player_watchlist", (("user_key", "eq.abc123"),)) in targets
    # ADR-148: cross-device preferences (ADR-147) are a row we create, so the promise has to cover them. A new
    # table is precisely the thing an old promise silently stops covering.
    assert ("user_prefs", (("user_key", "eq.abc123"),)) in targets


def test_user_key_only_when_email_is_missing_or_malformed(configured, capture_deletes):
    """A signed-in tester whose email we can't validate still gets their keyed data removed (no email deletes)."""
    unsubscribe.remove_me("not-an-email", user_key="uk9")
    urls = [u.rsplit("/", 1)[1] for u, _ in capture_deletes]
    assert "beta_users" not in urls and "beta_waitlist" not in urls        # bad email → skip the email tables
    assert set(urls) == {"squads", "player_watchlist", "user_prefs"}       # but the keyed data still goes


def test_remove_me_is_a_noop_without_the_store(monkeypatch):
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    monkeypatch.setattr("requests.delete", lambda *a, **k: pytest.fail("no delete without the store"))
    unsubscribe.remove_me("x@y.com", user_key="uk")                        # off by default → a no-op
    assert unsubscribe.is_configured() is False


def test_remove_me_swallows_a_store_failure(configured, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("supabase down")
    monkeypatch.setattr("requests.delete", boom)
    unsubscribe.remove_me("x@y.com", user_key="uk")                        # best-effort: must NOT raise


# --- UI: the shared "Leave the beta" control (ADR-122) ---

def test_leave_control_renders_when_the_store_is_configured():
    with patch("src.web_streamlit.unsubscribe.is_configured", return_value=True):
        at = AppTest.from_string(_LEAVE_APP, default_timeout=30).run()
    assert not at.exception
    assert any("Leave the beta" in e.label for e in at.get("expander"))    # the disclosure lives under the account line
    assert "Remove me" in [b.label for b in at.button]


def test_clicking_remove_me_opens_the_confirm_dialog():
    with patch("src.web_streamlit.unsubscribe.is_configured", return_value=True):
        at = AppTest.from_string(_LEAVE_APP, default_timeout=30).run()
        [b for b in at.button if b.label == "Remove me"][0].click().run()
    assert access._LEAVING in at.session_state                             # confirm-open flag set (irreversible → confirm)


def test_leave_control_is_hidden_without_the_store():
    with patch("src.web_streamlit.unsubscribe.is_configured", return_value=False):
        at = AppTest.from_string(_LEAVE_APP, default_timeout=30).run()
    assert not at.exception
    assert not at.button and not at.get("expander")                        # nothing to delete → the control is off


# ---- the promise has to be checkable (ADR-148) ---------------------------------------

def test_a_delete_that_matched_nothing_is_reported_not_swallowed(configured, monkeypatch):
    """The failure this exists to catch, and the one that would matter most.

    ADR-142 and ADR-147 both hit it on *writes*: a table with row-level security and no matching policy makes
    PostgREST answer **`200 OK, zero rows`** — Postgres does not raise, it narrows the statement to nothing.
    On a delete that means **telling someone their data is gone while it is still there**, which is the worst
    version of a silent failure in this codebase.

    The UI still swallows it; the status comes back so a caller or a test can check.
    """
    class _NothingMatched:
        status_code = 200

        def json(self):
            return []

    monkeypatch.setattr("requests.delete", lambda *a, **k: _NothingMatched())
    out = unsubscribe.remove_me("me@x.com", user_key="uk")
    assert out["user_prefs"] == "nothing matched (no row, or no DELETE policy)"
    assert all("nothing matched" in v for v in out.values())


def test_every_table_reports_and_a_refusal_is_named(configured, monkeypatch):
    class _Refused:
        status_code = 401

        def json(self):
            return []

    monkeypatch.setattr("requests.delete", lambda *a, **k: _Refused())
    out = unsubscribe.remove_me("me@x.com", user_key="uk")
    assert set(out) == {"beta_waitlist", "beta_users", "squads", "player_watchlist", "user_prefs"}
    assert all(v == "refused (HTTP 401)" for v in out.values())


def test_a_network_failure_still_never_raises(configured, monkeypatch):
    """Fail-silent at the edge is correct — a crash mid-unsubscribe is worse than a retry, and nobody leaving
    should be shown a stack trace. The status is how it stays *diagnosable* without becoming loud."""
    import requests as _rq

    monkeypatch.setattr("requests.delete",
                        lambda *a, **k: (_ for _ in ()).throw(_rq.ConnectionError("down")))
    out = unsubscribe.remove_me("me@x.com", user_key="uk")
    assert all(v.startswith("failed:") for v in out.values())


def test_no_store_returns_an_empty_report_rather_than_a_false_success(configured, monkeypatch):
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    assert unsubscribe.remove_me("x@y.com", user_key="uk") == {}
