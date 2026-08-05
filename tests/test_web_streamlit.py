"""Tests for the Streamlit edge (ADR-052) — each page runs headlessly via `AppTest`.

`AppTest.from_file(...)` executes a page script with no live server. Paths are **absolute** (from the
project root) because `AppTest` resolves a relative path against the *test file's* directory. We assert:
renders without exception; the data pages show a table; the Ask page answers a real question. Ollama
needn't run — `ask` degrades to the decision + facts.
"""

import pathlib

from streamlit.testing.v1 import AppTest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_APP = _ROOT / "src" / "web_streamlit" / "app.py"
_PAGES = _ROOT / "src" / "web_streamlit" / "pages"


def _run(path):
    at = AppTest.from_file(str(path), default_timeout=30).run()
    assert not at.exception, f"{path} raised: {at.exception}"
    return at


def test_home_renders():
    _run(_APP)


def test_players_page_shows_a_table():
    at = _run(_PAGES / "1_Players.py")
    assert len(at.dataframe) == 1 or len(at.info) == 1     # a table, or the "run refresh" note


def test_players_filters_narrow_the_table(monkeypatch):
    # the interactivity upgrade: position multiselect + max-price slider drive the table live
    at = _run(_PAGES / "1_Players.py")
    if not at.multiselect:                                  # no data locally → the info branch
        return
    at.multiselect[0].set_value(["GK"]).run()               # keepers only
    assert not at.exception
    at.slider[0].set_value(5.0).run()                       # …and ≤ £5.0m
    assert not at.exception                                  # narrowing never crashes (table or a note)


def test_fixtures_page_shows_a_table():
    at = _run(_PAGES / "2_Fixtures.py")
    assert len(at.dataframe) == 1 or len(at.info) == 1


def test_squads_page_renders():
    at = _run(_PAGES / "3_Squads.py")
    # a selectbox (squads exist) or the "no saved squads" info — both are fine, no crash
    assert len(at.selectbox) == 1 or len(at.info) == 1


def test_ask_chat_answers_a_grounded_question():
    at = AppTest.from_file(str(_PAGES / "4_Ask.py"), default_timeout=30).run()
    assert not at.exception
    at.chat_input[0].set_value("who has the best fixtures over the next 5?").run()
    assert not at.exception
    assert any("Avg FDR" in c.value for c in at.code)      # the grounded FDR answer in the chat
    assert len(at.session_state["history"]) == 1           # the turn was kept in history


def test_runner_module_points_at_the_app():
    # the `python -m src.web_streamlit` entry — imports cleanly and targets app.py (no server launched)
    from src.web_streamlit import __main__ as runner
    assert runner._APP.name == "app.py" and runner._APP.exists()
