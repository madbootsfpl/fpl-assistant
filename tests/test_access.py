"""Tests for the opt-in beta access gate (Sprint 102, ADR-087).

The gate is **off by default** — no `FPL_ACCESS_CODE` configured → the app is open (this is what keeps the
public deploy + the rest of the suite unchanged). When a code is set, a page is blocked until it's entered.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.web_streamlit import access, remember, user_store

_HOME = str(Path(__file__).resolve().parents[1] / "src" / "web_streamlit" / "Home.py")


def _unlocked(at):
    """True if the real app rendered (not the beta lock screen)."""
    return any("FPL Assistant" in t.value and "beta" not in t.value.lower() for t in at.title)


def test_secret_never_raises_without_a_secrets_file():
    # st.secrets raises when there's no secrets.toml — the helper must swallow that and fall back / None
    assert access.secret("FPL_ACCESS_CODE") is None            # unset in the test env
    assert access.secret("NOPE", "fallback") == "fallback"


def test_secret_reads_the_environment(monkeypatch):
    monkeypatch.setenv("FPL_ACCESS_CODE", "hunter2")
    assert access.secret("FPL_ACCESS_CODE") == "hunter2"


def test_app_is_open_when_no_code_is_configured():
    # the default: no gate → Home renders its real title (not the lock screen)
    at = AppTest.from_file(_HOME, default_timeout=30).run()
    assert not at.exception
    assert at.title and "FPL Assistant" in at.title[0].value and "beta" not in at.title[0].value.lower()


def test_gate_blocks_then_unlocks_with_the_right_code(monkeypatch):
    monkeypatch.setenv("FPL_ACCESS_CODE", "letmein")
    at = AppTest.from_file(_HOME, default_timeout=30).run()
    assert any("beta" in t.value.lower() for t in at.title)     # the lock screen, not the app
    assert at.text_input                                        # a code prompt is shown

    at.text_input[0].set_value("wrong").run()
    assert at.error                                             # a wrong code is rejected

    at.text_input[0].set_value("letmein").run()
    assert any("FPL Assistant" in t.value and "beta" not in t.value.lower() for t in at.title)   # unlocked


# --- "remember me" cookie (ADR-099, US-326) ------------------------------------------

def test_remember_cookie_skips_the_code_gate(monkeypatch):
    """A cookie holding the *current* code lets a refreshed session skip the prompt (no flash)."""
    monkeypatch.setenv("FPL_ACCESS_CODE", "letmein")
    monkeypatch.setattr(remember, "read", lambda: "letmein")
    at = AppTest.from_file(_HOME, default_timeout=30).run()
    assert not at.exception
    assert _unlocked(at)                    # straight in, no lock screen
    assert not at.text_input                # the code prompt never rendered


def test_stale_code_cookie_still_shows_the_gate(monkeypatch):
    """A cookie that doesn't match the current code (e.g. after a rotation) is not trusted."""
    monkeypatch.setenv("FPL_ACCESS_CODE", "letmein")
    monkeypatch.setattr(remember, "read", lambda: "oldcode")
    at = AppTest.from_file(_HOME, default_timeout=30).run()
    assert any("beta" in t.value.lower() for t in at.title)   # the lock screen
    assert at.text_input                                      # re-prompted


def test_a_code_pass_writes_the_remember_cookie(monkeypatch):
    """On a fresh pass the code is written back to the cookie — deferred to the clean post-login run."""
    monkeypatch.setenv("FPL_ACCESS_CODE", "letmein")
    written = []
    monkeypatch.setattr(remember, "read", lambda: None)          # no cookie yet
    monkeypatch.setattr(remember, "write", lambda value, **kw: written.append(value))
    at = AppTest.from_file(_HOME, default_timeout=30).run()
    at.text_input[0].set_value("letmein").run()
    assert _unlocked(at)
    assert written == ["letmein"]           # written once, after the rerun


def test_remember_cookie_skips_the_registration_gate(monkeypatch):
    """A cookie holding a *still-registered* email skips the registration gate and restores the email."""
    monkeypatch.setenv("FPL_USER_CAP", "10")
    monkeypatch.setattr(user_store, "is_configured", lambda: True)
    monkeypatch.setattr(user_store, "is_registered", lambda email: True)
    monkeypatch.setattr(remember, "read", lambda: "tester@example.com")
    at = AppTest.from_file(_HOME, default_timeout=30).run()
    assert not at.exception
    assert _unlocked(at)
    assert at.session_state[access._EMAIL] == "tester@example.com"


def test_stale_registration_cookie_shows_the_gate(monkeypatch):
    """A cookie for a pruned tester (no longer registered) is not trusted — the gate returns."""
    monkeypatch.setenv("FPL_USER_CAP", "10")
    monkeypatch.setattr(user_store, "is_configured", lambda: True)
    monkeypatch.setattr(user_store, "is_registered", lambda email: False)
    monkeypatch.setattr(remember, "read", lambda: "pruned@example.com")
    at = AppTest.from_file(_HOME, default_timeout=30).run()
    assert any("beta" in t.value.lower() for t in at.title)   # the registration lock screen


# --- logout (ADR-099, US-327) --------------------------------------------------------

def test_gate_active_is_false_when_open():
    assert access.gate_active() is False                       # no code / no cap → the public deploy


def test_gate_active_is_true_with_a_shared_code(monkeypatch):
    monkeypatch.setenv("FPL_ACCESS_CODE", "letmein")
    assert access.gate_active() is True


def test_gate_active_is_true_in_registration_mode(monkeypatch):
    monkeypatch.setenv("FPL_USER_CAP", "10")
    monkeypatch.setattr(user_store, "is_configured", lambda: True)
    assert access.gate_active() is True


# A tiny harness: pass the gate, then a button that calls logout() (the real sidebar control is US-328).
_LOGOUT_HARNESS = (
    "import streamlit as st\n"
    "from src.web_streamlit.access import require_access, logout, _OK\n"
    "require_access()\n"
    "st.write('passed' if st.session_state.get(_OK) else 'gated')\n"
    "if st.button('Log out'):\n"
    "    logout()\n"
)


def test_logout_clears_the_session_cookie_and_re_gates(monkeypatch):
    """A valid cookie admits; clicking Log out clears the session, clears the cookie (deferred), and — even
    though the stale cookie still reads valid this session — does not re-admit (the _FORGOTTEN guard)."""
    monkeypatch.setenv("FPL_ACCESS_CODE", "letmein")
    cleared = []
    monkeypatch.setattr(remember, "read", lambda: "letmein")          # a valid cookie is present all along
    monkeypatch.setattr(remember, "clear", lambda: cleared.append(True))
    monkeypatch.setattr(remember, "write", lambda *a, **k: None)

    at = AppTest.from_string(_LOGOUT_HARNESS, default_timeout=30).run()
    assert at.session_state[access._OK] is True                       # the cookie admitted
    assert any(m.value == "passed" for m in at.markdown)

    at.button[0].click().run()                                        # Log out
    assert cleared == [True]                                          # the cookie clear was rendered (deferred)
    assert access._OK not in at.session_state                         # session dropped
    assert at.session_state[access._FORGOTTEN] is True
    assert any("beta" in t.value.lower() for t in at.title)           # re-gated (not re-admitted from the cookie)
