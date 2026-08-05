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


def test_squads_page_analyses_the_demo_squad():
    # the demo seed always populates the picker (ADR-054) → an analysis renders, no crash
    at = _run(_PAGES / "3_Squads.py")
    assert len(at.selectbox) == 1                          # the squad picker (demo + session)
    assert len(at.code) == 1 or len(at.info) >= 1          # the health table (or a "no data" note)


def test_transfer_page_renders_and_reacts_to_the_bank(monkeypatch):
    at = _run(_PAGES / "5_Transfer.py")
    assert len(at.selectbox) == 1                          # the squad picker (demo always present)
    # a squad is selected → the ranked swaps (or a "no upgrades" note) render, no crash
    assert len(at.code) == 1 or len(at.info) >= 1
    at.slider[0].set_value(3.0).run()                      # move the bank slider → recompute, no crash
    assert not at.exception


def test_transfer_page_apply_mutates_the_session_squad():
    # US-173: applying a suggested swap edits the active squad in session_state (no server write)
    at = _run(_PAGES / "5_Transfer.py")
    at.slider[0].set_value(10.0).run()                     # raise the bank → dearer upgrades → swaps appear
    if len(at.selectbox) < 2 or not at.button:             # still none on this DB → nothing to apply
        return
    before = list(at.session_state["squad"]["player_ids"]) if "squad" in at.session_state else None
    at.button[0].click().run()                             # "Apply this transfer →"
    assert not at.exception
    squad = at.session_state["squad"]                      # an active squad now exists…
    assert before is None or squad["player_ids"] != before  # …and it changed (or was just adopted)
    assert squad.get("name") and squad.get("cost")         # named + re-costed (no sidebar crash)


def test_captain_page_renders_for_the_demo_squad():
    at = _run(_PAGES / "7_Captain.py")
    assert len(at.selectbox) >= 1                          # the squad picker (+ a set-captain selector)
    assert len(at.code) == 1 or len(at.info) >= 1          # the captain picks (or a "no data" note)


def test_captain_page_sets_and_persists_a_captain():
    # US-175: "Set as captain" writes captain_id onto the (adopted) session squad
    at = _run(_PAGES / "7_Captain.py")
    setbtn = [b for b in at.button if b.label == "Set as captain"]
    if not setbtn:                                         # no data locally → nothing to set
        return
    setbtn[0].click().run()
    assert not at.exception
    cap = at.session_state["squad"].get("captain_id")
    assert cap in at.session_state["squad"]["player_ids"]  # a real, owned captain


def test_consumer_pages_use_a_session_active_squad():
    # build sets session_state["squad"]; the squad pages must offer it in the picker (ADR-054/055)
    squad = {"name": "My squad", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}
    for page in ("3_Squads.py", "5_Transfer.py", "7_Captain.py", "8_My_Squad.py"):
        at = AppTest.from_file(str(_PAGES / page), default_timeout=30)
        at.session_state["squad"] = squad
        at.run()
        assert not at.exception, f"{page} raised: {at.exception}"
        assert any("My squad (yours)" in o for o in at.selectbox[0].options)


def test_build_page_returns_a_squad(monkeypatch):
    at = _run(_PAGES / "6_Build.py")
    # a squad is rendered (or the "no data" note if the DB is empty) — no crash
    assert len(at.code) == 1 or len(at.info) >= 1
    # move an archetype control → rebuild, still no crash
    at.number_input[0].set_value(3).run()                  # 3 low-cost players
    assert not at.exception


def test_build_page_offers_a_download_and_sets_the_active_squad(monkeypatch):
    at = _run(_PAGES / "6_Build.py")
    if not at.code:                                        # no data locally → the "run refresh" note
        return
    assert at.get("download_button"), "an Optimal build must offer a squad.json download"
    at.button[0].click().run()                             # "Use this squad →"
    assert not at.exception
    squad = at.session_state["squad"]                      # …became the session active squad (ADR-054)
    assert squad["name"] == "My squad" and 11 <= len(squad["player_ids"]) <= 15


def test_build_page_renders_non_zero_xp(monkeypatch):
    # regression (US-172): Build must attach xp/minutes_weight so the table + projected total aren't zeros
    at = _run(_PAGES / "6_Build.py")
    if not at.code:
        return
    out = at.code[0].value
    assert "xMins" in out and "xP" in out                  # the xp-objective columns
    total = next((ln for ln in out.splitlines() if ln.startswith("Total:")), "")
    assert "projected" in total and "projected 0.0 xP" not in total   # a real total, not zeros


def test_build_page_names_the_squad(monkeypatch):
    # US-172: the squad-name input flows into the active squad (and the download key)
    at = _run(_PAGES / "6_Build.py")
    if not at.code:
        return
    at.text_input[0].set_value("Tony's XI").run()
    at.button[0].click().run()                             # "Use this squad →"
    assert at.session_state["squad"]["name"] == "Tony's XI"


def test_my_squad_page_renders_with_a_legality_banner_and_download():
    at = _run(_PAGES / "8_My_Squad.py")
    # a download (an editable squad view) or the no-data info; a legality banner (success/error) if data
    assert at.get("download_button") or at.info
    if at.get("download_button"):
        assert at.success or at.error                      # the ✓ legal / ⚠ / illegal banner


def test_my_squad_swap_adopts_and_mutates_the_session_squad():
    at = _run(_PAGES / "8_My_Squad.py")
    swap = [b for b in at.button if b.label.startswith("Swap")]
    if not swap:                                           # no data / no candidates → nothing to swap
        return
    swap[0].click().run()
    assert not at.exception
    assert "squad" in at.session_state and at.session_state["squad"].get("cost")   # adopted + re-costed


def test_my_squad_rename_updates_the_active_squad():
    at = _run(_PAGES / "8_My_Squad.py")
    if not at.text_input or not any(b.label == "Rename" for b in at.button):
        return
    at.text_input[0].set_value("Dream Team").run()
    next(b for b in at.button if b.label == "Rename").click().run()
    assert at.session_state["squad"]["name"] == "Dream Team"


def test_my_squad_set_bench_picks_four():
    at = _run(_PAGES / "8_My_Squad.py")
    if not at.multiselect or not any(b.label == "Set bench" for b in at.button):
        return
    at.multiselect[0].set_value(at.multiselect[0].options[:4]).run()
    next(b for b in at.button if b.label == "Set bench").click().run()
    assert not at.exception
    assert len(at.session_state["squad"]["bench_ids"]) == 4


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


def test_photo_url_helper():
    # US-179: the shared player-photo helper (one source for every tab)
    from src.web_streamlit.badges import photo_url, photo_url_by_id
    assert photo_url(12345).endswith("/p12345.png")
    assert photo_url(None) == ""                            # no code → no image
    m = photo_url_by_id([{"id": 1, "code": 999}, {"id": 2, "code": None}])
    assert m[1].endswith("/p999.png") and m[2] == ""        # by player id; missing code → empty


def test_squad_tabs_show_image_tables():
    # US-179: Build/Analyse/Captain/My Squad show a photo+badge image table (augmenting the text summary)
    for page in ("6_Build.py", "3_Squads.py", "7_Captain.py", "8_My_Squad.py"):
        at = _run(_PAGES / page)
        if not at.dataframe:                                # no data locally → the info branch
            continue
        cols = str(at.dataframe[0].value.columns.tolist())
        assert "photo" in cols and "badge" in cols, f"{page} should show photo + badge columns"


def test_transfer_tab_shows_a_swap_image_table():
    # US-179: the Transfer swaps render with both players' photos (out/in image columns)
    at = _run(_PAGES / "5_Transfer.py")
    at.slider[0].set_value(10.0).run()                      # raise the bank → swaps appear
    if not at.dataframe:
        return
    cols = str(at.dataframe[0].value.columns.tolist())
    assert "out" in cols and "in" in cols                   # out→in photo columns


def test_runner_module_points_at_the_app():
    # the `python -m src.web_streamlit` entry — imports cleanly and targets app.py (no server launched)
    from src.web_streamlit import __main__ as runner
    assert runner._APP.name == "Home.py" and runner._APP.exists()


def test_data_freshness_caption_on_every_tab(monkeypatch):
    # US-180/ADR-056: the "Data as of <date>" caption renders in both modes, on every page
    monkeypatch.delenv("FPL_LOCAL", raising=False)
    for page in (_APP, _PAGES / "1_Players.py", _PAGES / "6_Build.py"):
        at = _run(page)
        assert any("Data as of" in c.value for c in at.caption), f"{page} should show a freshness caption"


def test_refresh_button_is_gated_by_local_mode(monkeypatch):
    # cloud (no FPL_LOCAL) → caption only, no refresh button; local (FPL_LOCAL=1, non-seed DB) → the button
    from src import config

    monkeypatch.delenv("FPL_LOCAL", raising=False)
    at = _run(_APP)
    assert "🔄 Refresh data" not in [b.label for b in at.button]      # never on the read-only cloud

    if config.DB_PATH != config.SEED_DB_PATH:                         # a live cache locally
        monkeypatch.setenv("FPL_LOCAL", "1")
        at2 = _run(_APP)
        assert "🔄 Refresh data" in [b.label for b in at2.button]     # local run → the refresh button


def test_is_local_requires_flag_and_a_non_seed_db(monkeypatch):
    from src import config
    from src.web_streamlit.status import is_local

    monkeypatch.setenv("FPL_LOCAL", "1")
    monkeypatch.setattr(config, "DB_PATH", config.SEED_DB_PATH)       # the seed → read-only even locally
    assert not is_local()
    monkeypatch.setattr(config, "DB_PATH", "data/fpl.db")             # a live cache + the flag → local
    assert is_local()
    monkeypatch.delenv("FPL_LOCAL", raising=False)
    assert not is_local()                                            # no flag (cloud) → never local
