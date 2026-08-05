"""Tests for the Streamlit edge (ADR-052) — each page runs headlessly via `AppTest`.

`AppTest.from_file(...)` executes a page script with no live server. Paths are **absolute** (from the
project root) because `AppTest` resolves a relative path against the *test file's* directory. We assert:
renders without exception; the data pages show a table; the Ask page answers a real question. Ollama
needn't run — `ask` degrades to the decision + facts.
"""

import pathlib

from streamlit.testing.v1 import AppTest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_APP = _ROOT / "src" / "web_streamlit" / "Home.py"
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


def test_players_page_has_a_scatter_chart_when_data_present():
    at = _run(_PAGES / "1_Players.py")
    if at.dataframe:                                        # data present → a price-vs-points scatter
        assert len(at.get("vega_lite_chart")) == 1


def test_players_page_has_photo_and_badge_columns_when_data_present():
    at = _run(_PAGES / "1_Players.py")
    if at.dataframe:
        df = at.dataframe[0].value
        assert "photos/players" in str(df["photo"].iloc[0])   # the player photo URL
        # the team badge is present iff team.code is in the DB (a refreshed DB); tolerate both
        assert "badge" in df.columns


def test_players_filters_narrow_the_table(monkeypatch):
    # the interactivity upgrade: position multiselect + max-price slider drive the table live
    at = _run(_PAGES / "1_Players.py")
    if not at.multiselect:                                  # no data locally → the info branch
        return
    at.multiselect[0].set_value(["GK"]).run()               # keepers only
    assert not at.exception
    at.slider[0].set_value(5.0).run()                       # …and ≤ £5.0m
    assert not at.exception                                  # narrowing never crashes (table or a note)


def test_fixtures_page_shows_a_table_and_chart():
    at = _run(_PAGES / "2_Fixtures.py")
    assert len(at.dataframe) == 1 or len(at.info) == 1
    if at.dataframe:                                        # data present → an avg-FDR bar chart
        assert len(at.get("vega_lite_chart")) == 1
        assert "" in at.dataframe[0].value.columns          # a team-badge image column


def test_squads_page_renders():
    at = _run(_PAGES / "3_Squads.py")
    # a selectbox (squads exist) or the "no saved squads" info — both are fine, no crash
    assert len(at.selectbox) == 1 or len(at.info) == 1


def test_transfer_page_renders_and_reacts_to_the_bank(monkeypatch):
    at = _run(_PAGES / "5_Transfer.py")
    if not at.selectbox:                                   # no saved squads locally → the info branch
        assert len(at.info) == 1
        return
    # a squad is selected → the ranked swaps (or a "no upgrades" note) render, no crash
    assert len(at.code) == 1 or len(at.info) >= 1
    at.slider[0].set_value(3.0).run()                      # move the bank slider → recompute, no crash
    assert not at.exception


def test_build_page_returns_a_squad(monkeypatch):
    at = _run(_PAGES / "6_Build.py")
    # a squad is rendered (or the "no data" note if the DB is empty) — no crash
    assert len(at.code) == 1 or len(at.info) >= 1
    # move an archetype control → rebuild, still no crash
    at.number_input[0].set_value(3).run()                  # 3 low-cost players
    assert not at.exception


def test_ask_chat_answers_a_grounded_question():
    at = AppTest.from_file(str(_PAGES / "4_Ask.py"), default_timeout=30).run()
    assert not at.exception
    at.chat_input[0].set_value("who has the best fixtures over the next 5?").run()
    assert not at.exception
    assert any("Avg FDR" in c.value for c in at.code)      # the grounded FDR answer in the chat
    assert len(at.session_state["history"]) == 1           # the turn was kept in history


def test_badge_url_helper():
    from src.web_streamlit.badges import badge_url, badge_url_by_short_name
    assert badge_url(3).endswith("/t3.png")
    assert badge_url(None) == ""                            # no code → no image (no crash)
    m = badge_url_by_short_name([{"short_name": "ARS", "code": 3}, {"short_name": "LIV", "code": None}])
    assert m["ARS"].endswith("/t3.png") and m["LIV"] == ""


def test_runner_module_points_at_the_app():
    # the `python -m src.web_streamlit` entry — imports cleanly and targets app.py (no server launched)
    from src.web_streamlit import __main__ as runner
    assert runner._APP.name == "Home.py" and runner._APP.exists()
