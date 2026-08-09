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
