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


def test_players_page_has_a_top15_bar_when_data_present():
    # ADR-064: the scatter is gone; a filter-responsive top-15 bar (a vega/altair chart) takes its place
    at = _run(_PAGES / "1_Players.py")
    if at.dataframe:
        assert at.get("arrow_vega_lite_chart") or at.get("vega_lite_chart")


def test_players_page_shows_the_crowd_lens_columns():
    # US-183 / ADR-057: the Players table gains Form · ICT · Trends (crowd flags), display-only
    at = _run(_PAGES / "1_Players.py")
    if not at.dataframe:
        return
    cols = at.dataframe[0].value.columns.tolist()
    assert "Trends" in cols and "Form" in cols and "ICT" in cols


def test_players_page_has_photo_and_badge_columns_when_data_present():
    at = _run(_PAGES / "1_Players.py")
    if at.dataframe:
        df = at.dataframe[0].value
        assert "photos/players" in str(df["photo"].iloc[0])   # the player photo URL
        # the team badge is present iff team.code is in the DB (a refreshed DB); tolerate both
        assert "badge" in df.columns


def test_players_filters_narrow_the_table(monkeypatch):
    # ADR-064 filter: multiselects are [0] Team · [1] Position · [2] Player; slider[0] is max-price
    at = _run(_PAGES / "1_Players.py")
    if not at.multiselect:                                  # no data locally → the info branch
        return
    at.multiselect[1].set_value(["GK"]).run()               # Position → keepers only
    assert not at.exception
    at.slider[0].set_value(5.0).run()                       # …and ≤ £5.0m
    assert not at.exception                                  # narrowing never crashes (table or a note)


def test_players_filter_by_team_narrows_the_table():
    # ADR-064: filter by team (multiselect[0]) restricts the table to that team
    at = _run(_PAGES / "1_Players.py")
    if not at.dataframe:
        return
    at.multiselect[0].set_value(["ARS"]).run()              # Team = ARS
    assert not at.exception
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_player_multiselect_is_team_scoped():
    # US-213: choosing a team scopes the Player multiselect's options to that team's players
    at = _run(_PAGES / "1_Players.py")
    if not at.multiselect:
        return
    all_players = len(at.multiselect[2].options)            # [0] Team · [1] Position · [2] Player
    at.multiselect[0].set_value(["ARS"]).run()              # Team = ARS
    assert not at.exception
    scoped = at.multiselect[2].options
    assert 0 < len(scoped) < all_players                    # a short, team-scoped list
    # every scoped player really is an Arsenal player
    at.multiselect[2].set_value(list(scoped)).run()
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_players_page_sorts_by_team_and_paginates():
    # ADR-063: page through all players (no 50-cap) + sort by team
    at = _run(_PAGES / "1_Players.py")
    if not at.dataframe:
        return
    at.selectbox[0].set_value("team").run()                 # Sort by → team
    assert not at.exception
    teams = at.dataframe[0].value["Team"].tolist()
    assert teams == sorted(teams)                           # first page ordered by team
    # >50 players → a page control (selectbox[1]); moving to the next page doesn't crash
    page_sb = at.selectbox[1]
    assert any(o.startswith("1–") for o in page_sb.options)
    if len(page_sb.options) > 1:
        page_sb.set_value(page_sb.options[1]).run()          # 51–100
        assert not at.exception


def test_fixtures_ticker_grid_and_weeks_selector():
    # US-186: a teams × GW ticker grid; the weeks slider changes the number of GW columns
    at = _run(_PAGES / "2_Fixtures.py")
    assert len(at.dataframe) == 1 or len(at.info) == 1
    if not at.dataframe:
        return
    cols = list(at.dataframe[0].value.columns)
    assert "Team" in cols and sum(c.startswith("GW") for c in cols) == 6   # default 6 weeks
    at.slider[0].set_value(3).run()                                        # → 3 GW columns
    assert not at.exception
    assert sum(c.startswith("GW") for c in at.dataframe[0].value.columns) == 3


def _squads_view(view):
    # ADR-069: open the Squads page and switch its segmented control to a manage/build view
    at = _run(_PAGES / "3_Squads.py")
    at.segmented_control[0].set_value(view).run()
    assert not at.exception, f"Squads[{view}] raised: {at.exception}"
    return at


def test_squads_page_analyses_the_demo_squad():
    # Health view: the demo seed populates the picker (ADR-054) → an analysis renders, no crash
    at = _squads_view("Health")
    assert any(s.label == "Squad" for s in at.selectbox)   # the squad picker (a GW selector is also present)
    assert len(at.code) == 1 or len(at.info) >= 1          # the health table (or a "no data" note)


def test_squads_ai_tips_view_renders_a_gameweek_plan():
    # ADR-070 / US-226: the "AI Tips" view (renamed from This week) routes through ask.answer → the
    # grounded plan block renders (no Ollama in the test → the plan + facts, no prose), no crash
    at = _squads_view("AI Tips")
    assert len(at.code) == 1                               # the rendered gameweek plan
    assert "This week" in at.code[0].value                 # the plan block header (the plan is for this GW)


def test_transfer_page_renders_and_reacts_to_the_bank(monkeypatch):
    at = _squads_view("Transfer")
    assert any(s.label == "Squad" for s in at.selectbox)   # the squad picker (a GW selector is also present)
    assert len(at.code) == 1 or len(at.info) >= 1          # the swaps (or a "no upgrades" note)
    next(s for s in at.slider if s.label == "Bank (£m)").set_value(3.0).run()   # move the bank → recompute
    assert not at.exception


def test_sidebar_offers_the_import_team_control():
    # US-191 / ADR-058: the sidebar (on the Squads page) has a manager-ID input + an Import team button
    at = _run(_PAGES / "3_Squads.py")
    assert any(t.label == "FPL manager-ID" for t in at.text_input)
    assert any(b.label == "Import team" for b in at.button)


def test_transfer_page_apply_mutates_the_session_squad():
    # US-173: applying a suggested swap edits the active squad in session_state (no server write)
    at = _squads_view("Transfer")
    at.slider[0].set_value(10.0).run()                     # raise the bank → dearer upgrades → swaps appear
    apply = [b for b in at.button if "Apply this transfer" in b.label]
    if not apply:                                          # still none on this DB → nothing to apply
        return
    before = list(at.session_state["squad"]["player_ids"]) if "squad" in at.session_state else None
    apply[0].click().run()
    assert not at.exception
    squad = at.session_state["squad"]                      # an active squad now exists…
    assert before is None or squad["player_ids"] != before  # …and it changed (or was just adopted)
    assert squad.get("name") and squad.get("cost")         # named + re-costed (no sidebar crash)


def test_captain_page_renders_for_the_demo_squad():
    at = _squads_view("Captain")
    assert len(at.selectbox) >= 1                          # the squad picker (+ a set-captain selector)
    assert len(at.code) == 1 or len(at.info) >= 1          # the captain picks (or a "no data" note)


def test_captain_page_shows_crowd_flags_and_template_risk():
    # US-184: the captain candidates gain a Trends column + a template-risk caption (ADR-057)
    at = _squads_view("Captain")
    if not at.dataframe:
        return
    assert "Trends" in at.dataframe[0].value.columns.tolist()
    assert any("Captaincy risk" in c.value for c in at.caption)


def test_transfer_page_shows_incoming_crowd_flags():
    # US-184: the swap table gains an "In trends" column for the player you'd buy
    at = _squads_view("Transfer")
    at.slider[0].set_value(10.0).run()                     # bank → swaps appear
    if not at.dataframe:
        return
    assert "In trends" in at.dataframe[0].value.columns.tolist()


def test_captain_page_sets_and_persists_a_captain():
    # US-175: "Set as captain" writes captain_id onto the (adopted) session squad
    at = _squads_view("Captain")
    setbtn = [b for b in at.button if b.label == "Set as captain"]
    if not setbtn:                                         # no data locally → nothing to set
        return
    setbtn[0].click().run()
    assert not at.exception
    cap = at.session_state["squad"].get("captain_id")
    assert cap in at.session_state["squad"]["player_ids"]  # a real, owned captain


def test_consumer_views_use_a_session_active_squad():
    # build sets session_state["squad"]; the Squads manage views must offer it in the picker (ADR-054/055)
    squad = {"name": "My squad", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}
    for view in ("Health", "Transfer", "Captain", "My Squad"):
        at = AppTest.from_file(str(_PAGES / "3_Squads.py"), default_timeout=30)
        at.session_state["squad"] = squad
        at.run()
        at.segmented_control[0].set_value(view).run()
        assert not at.exception, f"Squads[{view}] raised: {at.exception}"
        picker = next(s for s in at.selectbox if s.label == "Squad")   # by label (a GW selector was added)
        assert any("My squad (yours)" in o for o in picker.options)


def test_help_page_renders_the_guide_without_data():
    # ADR-068: the Help tab is static — it renders even with no DB, and carries the key steps + an example
    at = _run(_PAGES / "7_Help.py")
    blob = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.code)
    assert "Squads" in blob and "My Squad" in blob             # the core steps (new nav)
    assert "Ask" in blob and "worth the money" in blob         # the Ask step + a copy-paste example
    assert "AI Tips" in blob                                   # US-226: the gameweek tab (renamed) is in the guide
    assert "this week for my-team" in blob                     # US-224: the gameweek Ask example
    assert "quality rating" in blob                            # US-224: the stat-board rating is explained
    assert not at.get("dataframe")                             # static content — no data widgets


def test_sidebar_consolidated_to_seven_tabs():
    # ADR-069: 12 → 7 tabs; Player Stats merged into Players, the 5 squad tools into Squads
    present = sorted(p.name for p in _PAGES.glob("*.py"))
    assert present == sorted(["1_Players.py", "2_Fixtures.py", "3_Squads.py", "4_Ask.py",
                              "5_News.py", "6_Trending.py", "7_Help.py"])
    for gone in ("2_Player_Stats.py", "4_Build_Squad.py", "5_My_Squad.py",
                 "6_Squad_Health.py", "7_Transfer.py", "8_Captain.py"):
        assert not (_PAGES / gone).exists()


def test_player_stats_board_renders_via_the_segmented_control():
    # ADR-069: Player Stats merged into Players — a stat board renders when its segmented-control view is picked
    at = _run(_PAGES / "1_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Over / under-perf").run()
    assert not at.exception
    assert len(at.dataframe) >= 1 or len(at.info) >= 1     # the board rendered


def test_player_stats_filter_narrows_a_board():
    # ADR-064/069: the shared filter narrows a stat board on the merged Players page
    at = _run(_PAGES / "1_Players.py")
    if not at.dataframe:
        return
    at.segmented_control[0].set_value("Defensive Contribution").run()
    at.multiselect[0].set_value(["ARS"]).run()             # Team = ARS (the first filter multiselect)
    assert not at.exception
    for df in at.dataframe:                                 # the board is now ARS-only
        assert set(df.value["Team"].tolist()) <= {"ARS"}


def test_pool_shows_an_availability_fit_column():
    # ADR-074: the Pool has a Fit column (🚑/🚫/⛔/❓, blank = available) + a legend caption
    at = _run(_PAGES / "1_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert "Fit" in df.columns
    flags = set(df["Fit"].astype(str))
    assert flags & {"🚑", "🚫", "⛔", "❓"}                 # at least one flagged player on the first page
    assert any("injured" in c.value for c in at.caption)   # the availability legend


def test_pool_number_columns_stay_numeric_formatting_is_display_only():
    # ADR-072: money/value columns are formatted via NumberColumn (display) — the frame still holds the
    # raw numbers (not pre-rounded strings), so they stay sortable and truthful.
    import pandas as pd

    at = _run(_PAGES / "1_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert {"£m", "Val/£m"} <= set(df.columns)
    assert pd.api.types.is_numeric_dtype(df["£m"])       # not stringified
    assert pd.api.types.is_numeric_dtype(df["Val/£m"])


def test_clean_sheets_board_shows_a_quality_rating_and_legend():
    # ADR-071: xGC/90 board gains a relative Rating column (🟢…🔴) + a "vs the players shown" legend
    at = _run(_PAGES / "1_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Clean sheets").run()
    assert not at.exception
    assert any("relative to the players shown" in c.value for c in at.caption)   # the legend
    if at.dataframe:
        df = at.dataframe[0].value
        assert "Rating" in df.columns
        assert df["Rating"].astype(str).str.contains("🟢|🟡|🟠|🔴", regex=True).any()


def test_stat_boards_show_the_availability_fit_column():
    # ADR-074 / US-229: every stat board gains the Fit column (raw rows on xG; a lookup on the trimmed ones)
    for view in ("Over / under-perf", "Defensive Contribution", "Clean sheets", "xG / xA / xGI"):
        at = _run(_PAGES / "1_Players.py")
        if not at.segmented_control:
            return
        at.segmented_control[0].set_value(view).run()
        assert not at.exception, f"{view} raised: {at.exception}"
        if not at.dataframe:
            continue
        df = at.dataframe[0].value
        assert "Fit" in df.columns, f"{view} missing the Fit column"
        assert set(df["Fit"].astype(str)) & {"🚑", "🚫", "⛔", "❓"}, f"{view} has no flags on page 1"


def test_xg_board_rates_only_meaningful_players():
    # ADR-071/073: the xG board rates xGI, but only for outfield players with minutes — the column is
    # named "xGI rating" and sits before xGC; goalkeepers (xGI ≈ noise) are left unrated (—).
    at = _run(_PAGES / "1_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("xG / xA / xGI").run()
    assert not at.exception
    if not at.dataframe:
        return
    cols = list(at.dataframe[0].value.columns)
    assert "xGI rating" in cols and "Rating" not in cols            # renamed
    assert cols.index("xGI rating") < cols.index("xGC")             # sits before xGC (away from it)

    pos = [m for m in at.multiselect if m.label == "Position"]      # filter to GK → all unrated
    if pos:
        pos[0].set_value(["GK"]).run()
        ratings = set(at.dataframe[0].value["xGI rating"].astype(str))
        assert ratings <= {"—"}, f"goalkeepers should not be rated on xGI, got {ratings}"


_TAB_EMOJI = {"1_Players.py": "👟", "2_Fixtures.py": "📅", "3_Squads.py": "🧩", "4_Ask.py": "💬",
              "5_News.py": "📰", "6_Trending.py": "📈", "7_Help.py": "🧭"}


def test_every_tab_has_an_emoji_led_header():
    # US-222: each tab's title leads with a distinct emoji (like Home's ⚽ FPL Assistant), no crash
    for fname, emoji in _TAB_EMOJI.items():
        at = _run(_PAGES / fname)
        assert not at.exception, f"{fname} raised: {at.exception}"
        assert at.title and emoji in at.title[0].value, f"{fname} title missing {emoji}"


def test_squads_gameweeks_selector_drives_the_horizon():
    # US-237 (ADR-077): a "Gameweeks ahead" dropdown (default 5) flows into Health — set it to 2 and
    # the analysis projects over 2 GW (a GW2 column, no GW5)
    at = _run(_PAGES / "3_Squads.py")
    gw = [s for s in at.selectbox if s.label == "Gameweeks ahead"]
    assert gw and gw[0].value == 5                          # present, default 5 (today's behaviour)
    gw[0].set_value(2).run()
    at.segmented_control[0].set_value("Health").run()
    assert not at.exception
    if at.code:
        blob = " ".join(c.value for c in at.code)
        assert "2 GW" in blob and "GW2" in blob and "GW5" not in blob   # horizon narrowed to 2


def test_captain_view_notes_it_is_next_gameweek():
    # US-237: captaincy is a one-week decision — a caption says the GW selector doesn't apply
    at = _squads_view("Captain")
    assert any("next gameweek" in c.value.lower() for c in at.caption)


def test_my_squad_shows_a_quick_stats_summary():
    # US-239: My Squad shows a summary metrics row (Projected XI over the horizon · Captain · Bench ·
    # Unavailable · Doubtful), and the Projected-XI label tracks the Gameweeks-ahead selector
    at = _squads_view("My Squad")
    labels = [m.label for m in at.metric]
    assert any("Projected XI" in lbl for lbl in labels)
    assert {"Bench", "Unavailable", "Doubtful"} <= set(labels) and any("Captain" in lbl for lbl in labels)

    gw = [s for s in at.selectbox if s.label == "Gameweeks ahead"][0]
    gw.set_value(2).run()
    assert any(m.label == "Projected XI (2 GW)" for m in at.metric)


def test_my_squad_flags_unavailable_players_by_name():
    # US-240: My Squad names the flagged players (with their flag), else "all 15 available"
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()
    injured = next((p for p in rows if p["status"] == "i"), None)
    if injured is None:
        return
    others = [p for p in rows if p["status"] == "a"][:14]
    squad = {"name": "Test XI", "player_ids": [injured["id"]] + [p["id"] for p in others],
             "bench_ids": [], "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "3_Squads.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception
    caps = " ".join(c.value for c in at.caption)
    assert "Flagged" in caps and injured["web_name"] in caps and "🚑" in caps


def test_my_squad_points_to_build():
    # ADR-069: the My Squad view stays the tweaker + points to the Build view for a full rebuild
    at = _squads_view("My Squad")
    assert any("Build" in c.value for c in at.caption)


def test_build_page_returns_a_squad(monkeypatch):
    at = _run(_PAGES / "3_Squads.py")
    # a squad is rendered (or the "no data" note if the DB is empty) — no crash
    assert len(at.code) == 1 or len(at.info) >= 1
    # move an archetype control → rebuild, still no crash
    at.number_input[0].set_value(3).run()                  # 3 low-cost players
    assert not at.exception


def test_build_formation_preview_shows_the_xi_score():
    # US-230 (ADR-075): the "Preview the best XI in a shape" expander shows a Projected XI xP total
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:                                        # no data locally → the "run refresh" note
        return
    mets = [(m.label, str(m.value)) for m in at.metric]
    xi = [(lbl, val) for lbl, val in mets if "Projected XI" in lbl]
    assert xi, f"expected a Projected XI metric, got {mets}"
    assert "xP" in xi[0][1] and any(ch.isdigit() for ch in xi[0][1])   # a numeric xP total


def test_build_compare_all_formations_is_gated():
    # US-231 (ADR-075): the "Compare all formations" table is absent by default and appears only on tick,
    # ranking all 7 shapes by XI xP (desc) with a Δ-vs-best column.
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:                                        # no data locally → the "run refresh" note
        return
    assert not any("Formation" in df.value.columns for df in at.dataframe)   # off by default → no table

    cb = [c for c in at.checkbox if c.label == "Compare all formations"]
    assert cb, "the Compare all formations checkbox should exist"
    cb[0].set_value(True).run()
    assert not at.exception
    comp = [df.value for df in at.dataframe if "Formation" in df.value.columns]
    assert comp, "ticking Compare should render the all-formations table"
    df = comp[0]
    assert {"Formation", "XI xP", "Δ vs best"} <= set(df.columns)
    assert len(df) == 7                                                       # every legal shape
    xps = df["XI xP"].dropna().tolist()
    assert xps == sorted(xps, reverse=True)                                   # ranked best-first


def test_build_page_offers_a_download_and_sets_the_active_squad(monkeypatch):
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:                                        # no data locally → the "run refresh" note
        return
    assert at.get("download_button"), "an Optimal build must offer a squad.json download"
    at.button[0].click().run()                             # "Use this squad →"
    assert not at.exception
    squad = at.session_state["squad"]                      # …became the session active squad (ADR-054)
    assert squad["name"] == "My squad" and 11 <= len(squad["player_ids"]) <= 15


def test_build_page_renders_non_zero_xp(monkeypatch):
    # regression (US-172): Build must attach xp/minutes_weight so the table + projected total aren't zeros
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:
        return
    out = at.code[0].value
    assert "xMins" in out and "xP" in out                  # the xp-objective columns
    total = next((ln for ln in out.splitlines() if ln.startswith("Total:")), "")
    assert "projected" in total and "projected 0.0 xP" not in total   # a real total, not zeros


def test_build_page_names_the_squad(monkeypatch):
    # US-172: the squad-name input flows into the active squad (and the download key)
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:
        return
    at.text_input[0].set_value("Tony's XI").run()
    at.button[0].click().run()                             # "Use this squad →"
    assert at.session_state["squad"]["name"] == "Tony's XI"


def test_build_page_objective_switch_rebuilds(monkeypatch):
    # ADR-062: switching the objective (xp→xgi) rebuilds on the same engine, no crash, still a squad
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:
        return
    next(s for s in at.selectbox if s.label == "Objective").set_value("xgi").run()
    assert not at.exception and at.code


def test_build_page_weekly_and_include_unavailable(monkeypatch):
    # ADR-062: the new build-mode radio + include-unavailable checkbox drive the same select_squad
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:
        return
    at.radio[0].set_value("Weekly (playing bench)").run()
    at.checkbox[-1].set_value(True).run()                  # include injured/suspended
    assert not at.exception and at.code                    # still a valid 15 renders


def test_build_page_formation_preview_is_display_only(monkeypatch):
    # ADR-062: the formation preview is XI-only and never adds a second (save) download
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:
        return
    next(s for s in at.selectbox if s.label == "Formation").set_value("4-3-3").run()
    assert not at.exception
    assert len(at.get("download_button")) == 1             # only the full-15 build is downloadable


def test_build_page_exclude_removes_the_player_from_the_save(monkeypatch):
    # ADR-062: the "Must exclude" control wires through to the saved 15 (the tester's key ask)
    at = _run(_PAGES / "3_Squads.py")
    if not at.code:
        return
    opts = at.multiselect[1].options                       # [0] include, [1] exclude, [2] bench
    if not opts:
        return
    label = opts[0]
    at.multiselect[1].set_value([label]).run()
    if not at.code or not at.button:                       # still Optimal + "Use this squad →" present
        return
    at.button[0].click().run()
    excluded_name = label.split(" · ")[0]                  # "web_name · team · £Xm"
    assert excluded_name not in at.session_state["squad"]["player_names"]


def test_my_squad_page_renders_with_a_legality_banner_and_download():
    at = _squads_view("My Squad")
    # a download (an editable squad view) or the no-data info; a legality banner (success/error) if data
    assert at.get("download_button") or at.info
    if at.get("download_button"):
        assert at.success or at.error                      # the ✓ legal / ⚠ / illegal banner


def test_my_squad_pitch_view_lays_out_the_squad():
    # US-187: the squad renders as a formation card-grid — a card (markdown name) per player, not a table
    at = _squads_view("My Squad")
    if not at.get("download_button"):                      # no data locally → the info branch
        return
    assert len(at.dataframe) == 0                          # the pitch replaced the dataframe
    assert len(at.markdown) >= 11                          # ≥ an XI of player-name cards


def test_my_squad_swap_adopts_and_mutates_the_session_squad():
    at = _squads_view("My Squad")
    swap = [b for b in at.button if b.label.startswith("Swap")]
    if not swap:                                           # no data / no candidates → nothing to swap
        return
    swap[0].click().run()
    assert not at.exception
    assert "squad" in at.session_state and at.session_state["squad"].get("cost")   # adopted + re-costed


def test_my_squad_rename_updates_the_active_squad():
    at = _squads_view("My Squad")
    name_inputs = [t for t in at.text_input if t.label == "Squad name"]   # not the sidebar manager-ID
    if not name_inputs or not any(b.label == "Rename" for b in at.button):
        return
    name_inputs[0].set_value("Dream Team").run()
    next(b for b in at.button if b.label == "Rename").click().run()
    assert at.session_state["squad"]["name"] == "Dream Team"


def test_my_squad_set_bench_picks_four():
    at = _squads_view("My Squad")
    if not at.multiselect or not any(b.label == "Set bench" for b in at.button):
        return
    at.multiselect[0].set_value(at.multiselect[0].options[:4]).run()
    next(b for b in at.button if b.label == "Set bench").click().run()
    assert not at.exception
    assert len(at.session_state["squad"]["bench_ids"]) == 4


def test_trending_page_shows_a_leaderboard():
    # US-194: a community leaderboard (owned board renders now; momentum boards note "live at GW1")
    at = _run(_PAGES / "6_Trending.py")
    assert at.dataframe or at.info                          # a board, or the no-data note
    if at.dataframe:
        cols = list(at.dataframe[0].value.columns)
        assert "Player" in cols and "Trends" in cols        # a crowd leaderboard with flags
    # Community Signals (ADR-059): a button-gated "Talked about" board — present, no fetch on load
    assert any(b.label.startswith("Show what") for b in at.button)


def test_talked_about_board_paginates(monkeypatch):
    # US-233 (ADR-076): a big buzz list (a 100-post sample mentions many players) pages at 30
    import streamlit as st

    from src.api import reddit
    from src.storage import Storage

    store = Storage()
    names = [p["web_name"] for p in store.get_players() if len(p["web_name"] or "") >= 4][:35]
    store.close()
    if len(names) < 31:
        return                                                # need >30 mentioned to trigger a page control
    rss = ('<feed xmlns="http://www.w3.org/2005/Atom">'
           + "".join(f'<entry><link href="https://r.test/{i}"/><title>{n} watch</title></entry>'
                     for i, n in enumerate(names))
           + "</feed>")
    st.cache_data.clear()                                     # don't inherit another test's cached fetch
    monkeypatch.setattr(reddit.RedditRssClient, "get_subreddit_rss", lambda self, *a, **k: rss)

    at = _run(_PAGES / "6_Trending.py")
    btn = [b for b in at.button if b.label.startswith("Show what")]
    assert btn, "the Talked about button should exist"
    btn[0].click().run()
    assert not at.exception
    assert any(sb.label == "Page" for sb in at.selectbox), "the buzz board should paginate (>30 mentioned)"
    assert any("Showing 1–30 of" in c.value for c in at.caption)


def test_trending_filter_narrows_the_owned_board():
    # ADR-064 reuse: the shared Team/Position/Player filter narrows Trending (the owned board is populated)
    at = _run(_PAGES / "6_Trending.py")
    if not at.dataframe:
        return
    at.multiselect[0].set_value(["ARS"]).run()             # Team = ARS (the first filter multiselect)
    assert not at.exception
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_trending_owned_board_paginates():
    # ADR-063: the always-populated owned board pages past 30 (no 30-cap)
    from src.web_streamlit.paginate import page_labels
    at = _run(_PAGES / "6_Trending.py")
    if not at.dataframe:
        return
    first = page_labels(31, 30)[0]                          # "1–30" (avoids hard-coding the en-dash)
    assert any(first in sb.options for sb in at.selectbox)  # a 30-row page control is present


def test_news_page_lists_flagged_players_or_all_clear():
    # US-190 / ADR-058: the News lens shows flagged players (News + Source cols) or an all-clear message
    at = _run(_PAGES / "5_News.py")
    if at.dataframe:
        cols = list(at.dataframe[0].value.columns)
        assert "News" in cols and "Source" in cols
    else:
        assert at.success or at.info                       # "no current news" (or the run-refresh note)


def test_ask_page_example_prompts_are_clickable():
    # US-227/US-234: the Ask page lists example questions as buttons; clicking one runs it
    at = AppTest.from_file(str(_PAGES / "4_Ask.py"), default_timeout=30).run()
    assert not at.exception
    labels = [b.label for b in at.button if b.key and b.key.startswith("example_")]
    assert any("best differential midfielders" in lbl for lbl in labels)
    assert any("this week for my-team" in lbl for lbl in labels)

    btn = next(b for b in at.button if b.key == "example_0")
    btn.click().run()                                       # clicking runs the grounded pipeline
    assert not at.exception and len(at.session_state["history"]) == 1


def test_ask_chat_answers_a_grounded_question():
    at = AppTest.from_file(str(_PAGES / "4_Ask.py"), default_timeout=30).run()
    assert not at.exception
    at.chat_input[0].set_value("who has the best fixtures over the next 5?").run()
    assert not at.exception
    assert any("Avg FDR" in c.value for c in at.code)      # the grounded FDR answer in the chat
    assert len(at.session_state["history"]) == 1           # the turn was kept in history


def test_ask_build_offers_use_this_squad(monkeypatch):
    # ADR-062: a "build me a squad" answer offers "Use this squad →" → adopts the session squad
    at = AppTest.from_file(str(_PAGES / "4_Ask.py"), default_timeout=30).run()
    assert not at.exception
    at.chat_input[0].set_value("build me a squad for £100m").run()
    assert not at.exception
    btn = [b for b in at.button if "Use this squad" in b.label]
    if not btn:                                            # no data locally → no build → skip
        return
    btn[0].click().run()
    squad = at.session_state["squad"]
    assert squad["name"] == "My squad" and 11 <= len(squad["player_ids"]) <= 15


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


def test_squad_views_show_image_tables():
    # US-179 / ADR-069: the Build/Health/Captain views show a photo+badge image table
    for view in ("Build", "Health", "Captain"):
        at = _squads_view(view)
        if not at.dataframe:                                # no data locally → the info branch
            continue
        cols = str(at.dataframe[0].value.columns.tolist())
        assert "photo" in cols and "badge" in cols, f"Squads[{view}] should show photo + badge columns"


def test_transfer_view_shows_a_swap_image_table():
    # US-179: the Transfer view's swaps render with both players' photos (out/in image columns)
    at = _squads_view("Transfer")
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
    # US-180/ADR-056: the "… data as of <date>" caption renders in both modes, on every page.
    # US-219: it now leads with the player count so a stale snapshot is obvious.
    monkeypatch.delenv("FPL_LOCAL", raising=False)
    for page in (_APP, _PAGES / "1_Players.py", _PAGES / "3_Squads.py"):
        at = _run(page)
        assert any("data as of" in c.value for c in at.caption), f"{page} should show a freshness caption"
        assert any("players · data as of" in c.value for c in at.caption), \
            f"{page} freshness caption should show the player count (US-219)"


def test_cloud_shows_a_snapshot_note_local_does_not(monkeypatch):
    # US-219: the read-only cloud (no FPL_LOCAL) notes it's a snapshot; a local run doesn't.
    from src import config

    monkeypatch.delenv("FPL_LOCAL", raising=False)
    at = _run(_APP)
    assert any("snapshot" in c.value for c in at.caption)             # cloud → the snapshot note

    if config.DB_PATH != config.SEED_DB_PATH:                         # a live cache locally
        monkeypatch.setenv("FPL_LOCAL", "1")
        at2 = _run(_APP)
        assert not any("snapshot" in c.value for c in at2.caption)    # local → no snapshot note


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
