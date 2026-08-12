"""Tests for Google-auth mode (ADR-106).

**Off by default** — no `[auth]` in the test env, so the app uses the existing gate (the whole suite is the
guardrail). The real Google **OAuth redirect can't be AppTested**, so the *decision logic* is tested with
`auth.current_email` and `st.login` mocked; the live sign-in is owner-smoke-verified on the deploy.
"""

from streamlit.testing.v1 import AppTest

from src.web_streamlit import auth
from src.web_streamlit.cloud_store import clean_handle

_SCRIPT = (
    "import streamlit as st\n"
    "from src.web_streamlit.access import require_access\n"
    "require_access()\n"
    "st.write('APP-RENDERED')\n"
)


def test_auth_is_off_by_default():
    assert auth.is_configured() is False           # no [auth] → Google-auth mode off (the byte-identical guardrail)


def test_user_key_is_a_stable_hash_that_hides_the_email():
    k = auth.user_key("Tony@Example.com ")
    assert k == auth.user_key("tony@example.com") and len(k) == 32   # stable (case/space-insensitive)
    assert "@" not in k and clean_handle(k) == k                     # a valid cloud handle; no raw email
    assert auth.user_key("someone@else.com") != k                    # distinct per user


def _auth_on(monkeypatch, email, *, registered):
    monkeypatch.setattr("src.web_streamlit.auth.is_configured", lambda: True)
    monkeypatch.setattr("src.web_streamlit.auth.current_email", lambda: email)
    monkeypatch.setattr("src.web_streamlit.user_store.is_registered", lambda e: registered)
    monkeypatch.setattr("streamlit.login", lambda *a, **k: None)     # the OAuth redirect can't run in AppTest


def _admitted(at):
    return "_beta_ok" in at.session_state and at.session_state["_beta_ok"]


def test_auth_admits_an_allow_listed_email(monkeypatch):
    _auth_on(monkeypatch, "tester@x.com", registered=True)
    at = AppTest.from_string(_SCRIPT).run()
    assert not at.exception
    assert _admitted(at)                                             # on beta_users → admitted
    assert any("APP-RENDERED" in m.value for m in at.markdown)       # …and the app rendered past the gate


def test_auth_waitlists_a_non_listed_email(monkeypatch):
    _auth_on(monkeypatch, "stranger@x.com", registered=False)
    calls = []
    monkeypatch.setattr("src.web_streamlit.waitlist.add", lambda e, r="full": calls.append((e, r)))
    at = AppTest.from_string(_SCRIPT).run()
    assert not at.exception
    assert ("stranger@x.com", "not_listed") in calls                # captured on the waitlist (ADR-102)
    assert not _admitted(at)                                         # NOT admitted (stopped)
    assert any("waitlist" in w.value.lower() for w in at.warning)
    assert not any("APP-RENDERED" in m.value for m in at.markdown)


def test_auth_shows_the_sign_in_screen_when_not_signed_in(monkeypatch):
    _auth_on(monkeypatch, None, registered=False)
    logins = []
    monkeypatch.setattr("streamlit.login", lambda *a, **k: logins.append(a))
    at = AppTest.from_string(_SCRIPT).run()
    assert not at.exception
    assert logins == [("google",)]                                  # the Sign-in-with-Google button rendered
    assert not any("APP-RENDERED" in m.value for m in at.markdown)  # stopped at the login screen
