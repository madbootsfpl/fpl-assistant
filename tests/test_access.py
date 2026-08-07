"""Tests for the opt-in beta access gate (Sprint 102, ADR-087).

The gate is **off by default** — no `FPL_ACCESS_CODE` configured → the app is open (this is what keeps the
public deploy + the rest of the suite unchanged). When a code is set, a page is blocked until it's entered.
"""

from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.web_streamlit import access

_HOME = str(Path(__file__).resolve().parents[1] / "src" / "web_streamlit" / "Home.py")


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
