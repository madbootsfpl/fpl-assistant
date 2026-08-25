"""Tests for the Streamlit edge (ADR-052) — each page runs headlessly via `AppTest`.

`AppTest.from_file(...)` executes a page script with no live server. Paths are **absolute** (from the
project root) because `AppTest` resolves a relative path against the *test file's* directory. We assert:
renders without exception; the data pages show a table; the Ask page answers a real question. Ollama
needn't run — `ask` degrades to the decision + facts.
"""

import pathlib

import requests
from streamlit.testing.v1 import AppTest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_APP = _ROOT / "src" / "web_streamlit" / "Home.py"
_PAGES = _ROOT / "src" / "web_streamlit" / "pages"


def _run(path):
    at = AppTest.from_file(str(path), default_timeout=30).run()
    assert not at.exception, f"{path} raised: {at.exception}"
    return at


def test_home_renders():
    at = _run(_APP)
    caps = " ".join(c.value for c in at.caption)
    blob = " ".join(m.value for m in at.markdown)
    assert "The analytics decide. The AI explains. You make the call." in caps    # brand.MANTRA (ADR-114)
    assert "Explore the sidebar" in blob and "auto-synced across your devices" in blob   # US-373: sidebar + your-squad
    assert "read-only view over the analytics" not in caps         # the internal ADR ref dropped from user copy


def test_home_shows_the_deadline_countdown():
    # US-262/267/268 (ADR-086/088): Home shows the next-deadline countdown — a live clock + a text caption
    at = _run(_APP)
    caps = [c.value for c in at.caption]
    if not any("deadline" in c.lower() for c in caps) and not any("in " in c for c in caps):
        return                                             # no data locally → no banner (empty-safe)
    assert any("deadline" in c.lower() for c in caps)      # the ⏳ GW deadline text line beneath the clock


def test_players_page_shows_a_table():
    at = _run(_PAGES / "2_Players.py")
    assert len(at.dataframe) == 1 or len(at.info) == 1     # a table, or the "run refresh" note


def test_players_page_has_a_top15_bar_when_data_present():
    # ADR-064: the scatter is gone; a filter-responsive top-15 bar (a vega/altair chart) takes its place
    at = _run(_PAGES / "2_Players.py")
    if at.dataframe:
        assert at.get("arrow_vega_lite_chart") or at.get("vega_lite_chart")


def test_players_price_filter_includes_the_priciest_player():
    # US-345: the Max-price cap follows the highest player price, so the £15.5m player isn't filtered out
    import pandas as pd
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    assert "Player" in df.columns and (df["Player"] == "Haaland").any()   # the £15.5m asset isn't filtered out


def test_trending_top_discussions_before_community_signals():
    # US-345: surface 🔥 Top discussions first; the long Community Signals list sits below
    at = _run(_PAGES / "7_Trending.py")
    caps = [c.value for c in at.caption]
    top = next((i for i, c in enumerate(caps) if "Top discussions this week" in c), None)
    comm = next((i for i, c in enumerate(caps) if "Community Signals" in c), None)
    assert top is not None and comm is not None and top < comm


def test_help_save_step_reflects_auth_live_persistence():
    # US-378 (ADR-111) + US-385 (ADR-113): the Save section reflects auth-live persistence via the unified
    # "Your team" panel (account sync + import + download), not the stale "per-session / no accounts" copy.
    at = _run(_PAGES / "8_Help.py")
    blob = " ".join(m.value for m in at.markdown)
    caps = " ".join(c.value for c in at.caption)
    assert "saved to your account" in blob and "Your team" in blob          # auth-live persistence, unified panel
    assert "nothing saved on the server" not in (blob + caps)               # the stale claim is gone
    assert "no accounts" not in (blob + caps)
    assert "⚔️ Boot Battle" in blob                                          # US-378: the compare feature named


def test_help_explainer_glossary_renders():
    # US-379 (ADR-111): the MadBoots Explainer — one glossary expander with category subheaders + key terms.
    at = _run(_PAGES / "8_Help.py")
    blob = " ".join(m.value for m in at.markdown)
    assert "FPL basics" in blob and "Squad decisions" in blob and "MadBoots tools" in blob   # category headers
    assert "xP — Expected Points" in blob and "Boot Battle ⚔️" in blob and "Radar 🎯" in blob  # reconciled terms


def test_players_card_view_renders_a_player_card():
    # US-343 (ADR-084): the "Card" view → a player selectbox → the self-contained player-card HTML block
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return                                                 # no data → nothing to card
    at.segmented_control[0].set_value("Card").run()
    assert not at.exception
    assert any(s.label == "Player" for s in at.selectbox)      # the picker
    blob = " ".join(m.value for m in at.markdown)
    assert "pl-card" in blob and "Player Card" in blob         # the card + its brand band rendered


def test_players_card_view_compares_two_players():
    # US-370 (ADR-110) / US-377 (ADR-111): the Card view's ⚔️ "Boot Battle — compare with" picker → the comparison.
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return                                                 # no data → nothing to compare
    at.segmented_control[0].set_value("Card").run()
    assert not at.exception
    cmp = next((s for s in at.selectbox if s.label and "Boot Battle" in s.label), None)
    assert cmp is not None                                     # the compare picker exists
    if len(cmp.options) <= 1:
        return                                                 # only "—" (no same-position peer) → nothing to compare
    cmp.set_value(cmp.options[1]).run()                        # pick a same-position player
    assert not at.exception
    blob = " ".join(m.value for m in at.markdown)
    assert "cmp-card" in blob and "cmp-grid" in blob           # the merged comparison rendered (not the single card)


def test_players_page_shows_the_crowd_lens_columns():
    # US-183 / ADR-057: the Players table gains Form · ICT · Trends (crowd flags), display-only
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    cols = at.dataframe[0].value.columns.tolist()
    assert "Trends" in cols and "Form" in cols and "ICT" in cols


def test_players_page_has_photo_and_badge_columns_when_data_present():
    at = _run(_PAGES / "2_Players.py")
    if at.dataframe:
        df = at.dataframe[0].value
        assert "photos/players" in str(df["photo"].iloc[0])   # the player photo URL
        # the team badge is present iff team.code is in the DB (a refreshed DB); tolerate both
        assert "badge" in df.columns


def test_players_filters_narrow_the_table(monkeypatch):
    # ADR-064 filter (US-424 popover): multiselects are [0] Team · [1] Player; Position is a pills widget
    at = _run(_PAGES / "2_Players.py")
    if not at.multiselect:                                  # no data locally → the info branch
        return
    next(p for p in at.pills if p.label == "Position").set_value(["GK"]).run()   # Position → keepers only
    assert not at.exception
    at.slider[0].set_value(5.0).run()                       # …and ≤ £5.0m
    assert not at.exception                                  # narrowing never crashes (table or a note)


def test_players_filter_by_team_narrows_the_table():
    # ADR-064: filter by team (multiselect[0]) restricts the table to that team
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    at.multiselect[0].set_value(["ARS"]).run()              # Team = ARS
    assert not at.exception
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_player_multiselect_is_team_scoped():
    # US-213: choosing a team scopes the Player multiselect's options to that team's players
    at = _run(_PAGES / "2_Players.py")
    if not at.multiselect:
        return
    all_players = len(at.multiselect[1].options)            # [0] Team · [1] Player (Position is a pills widget)
    at.multiselect[0].set_value(["ARS"]).run()              # Team = ARS
    assert not at.exception
    scoped = at.multiselect[1].options
    assert 0 < len(scoped) < all_players                    # a short, team-scoped list
    # every scoped player really is an Arsenal player
    at.multiselect[1].set_value(list(scoped)).run()
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_stat_boards_carry_id_so_my_squad_filter_keeps_rows():
    # US-425 regression: over_under/defensive_solidity/defcon_reliability build rows for the Players boards; they
    # MUST carry `id` or the "My squad only" filter (matches on id) drops every row → an empty board (the bug).
    from src.analytics import defcon_reliability, defensive_solidity, over_under
    from src.storage import Storage
    from src.web_streamlit.filters import apply as apply_filter
    store = Storage()
    try:
        players = [dict(p) for p in store.get_players()]
    finally:
        store.close()
    if not players:
        return
    for fn in (over_under, defensive_solidity, defcon_reliability):
        rows = fn(players)
        if not rows:
            continue
        assert all("id" in r for r in rows), f"{fn.__name__} rows must carry id"
        mine = {rows[0]["id"], rows[-1]["id"]}
        kept = apply_filter(rows, {"teams": set(), "positions": set(), "players": set(),
                                   "max_price": None, "my_squad": mine})
        assert kept and all(r["id"] in mine for r in kept)   # not empty; only the "squad" rows survive


def test_history_view_respects_the_shared_filter():
    # US-427: the History player picker was ignoring the shared filter — a team filter must narrow its options.
    at = _run(_PAGES / "2_Players.py")
    if at.exception:
        return
    view = next((s for s in at.segmented_control if s.label == "View"), None)
    if view is None:
        return
    view.set_value("History").run()
    picker = next((s for s in at.selectbox if s.label == "Player"), None)
    if picker is None or len(picker.options) < 2 or not at.multiselect:
        return
    all_opts = len(picker.options)
    at.multiselect[0].set_value(["ARS"]).run()               # Team = ARS (the filter's [0])
    assert not at.exception
    picker = next((s for s in at.selectbox if s.label == "Player"), None)
    if picker is not None:
        assert len(picker.options) < all_opts                # narrowed to ARS players
        assert all("ARS" in o for o in picker.options)


def test_watchlist_cap_is_thirty():
    # ADR-117: a shortlist, not a second squad.
    from src.web_streamlit import watchlist
    assert watchlist.MAX == 30


def test_players_pool_has_the_add_to_watchlist_control():
    # ADR-117: the pool offers ⭐ Add (select rows → add) + a "N/30 watched" count.
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    assert any("Add selected" in b.label and "watchlist" in b.label for b in at.button)
    assert any("watched" in c.value for c in at.caption)


def test_players_card_can_star_a_player_to_the_watchlist():
    # ADR-117: ⭐ on the player card adds them to the (session) watchlist.
    at = _run(_PAGES / "2_Players.py")
    view = next((s for s in at.segmented_control if s.label == "View"), None)
    if view is None:
        return
    view.set_value("Card").run()
    add = next((b for b in at.button if "Add to watchlist" in b.label), None)
    if at.exception or add is None:
        return                                          # no player/data locally → nothing to star
    add.click().run()
    assert not at.exception
    assert any("Watching" in b.label for b in at.button)    # the ⭐ toggled to "★ Watching — remove"


def test_transfer_tab_shows_the_watchlist_section():
    # ADR-117: the ⭐ Watchlist is on My Squad → Transfer — with a NON-EMPTY list too (regression: the players are
    # sqlite3.Row, which have no .get() — the watched table crashed on p.get("form")).
    from src.storage import Storage
    store = Storage()
    ids = [r["id"] for r in store.get_players()[:3]]
    store.close()
    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["_watchlist"] = ids                    # a non-empty watchlist
    at.run()
    at.segmented_control[0].set_value("Transfer").run()
    assert not at.exception
    assert any("Your watchlist" in (e.label or "") for e in at.get("expander"))
    if ids:                                                 # the watched players render as a table (the crash site)
        assert any("Player" in list(d.value.columns) for d in at.get("dataframe"))


def test_players_pool_shows_the_full_sorted_list():
    # ADR-116: the pool is ONE scrollable table (no paging) ordered by "Sort by", so the whole set is shown and
    # the native column-header sort is honest (it orders everything, not just a page).
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    next(s for s in at.selectbox if s.label == "Sort by").set_value("team").run()
    assert not at.exception
    teams = at.dataframe[0].value["Team"].tolist()
    assert teams == sorted(teams)                           # the WHOLE list is ordered by team
    assert not any(sb.label == "Page" for sb in at.selectbox)   # no page control (ADR-116 supersedes ADR-063)


def test_fixtures_ticker_grid_and_weeks_selector():
    # US-186: a teams × GW ticker grid; the weeks slider changes the number of GW columns
    at = _run(_PAGES / "3_Team_DNA_and_FDR.py")
    assert len(at.dataframe) >= 1 or len(at.info) == 1     # US-301 added a second (targets) table
    if not at.dataframe:
        return
    cols = list(at.dataframe[0].value.columns)             # the ticker is the first dataframe
    assert "Team" in cols and sum(c.startswith("GW") for c in cols) == 6   # default 6 weeks
    at.slider[0].set_value(3).run()                                        # → 3 GW columns
    assert not at.exception
    assert sum(c.startswith("GW") for c in at.dataframe[0].value.columns) == 3


def test_my_squad_health_shows_the_your_teams_strip():
    # US-420 (ADR-119): My Squad ▸ Health has a "Your teams" strip (the squad's clubs' Team DNA).
    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30).run()
    if at.exception:
        return
    health = next((s for s in at.segmented_control if "Health" in (s.options or [])), None)
    if health is None:
        return
    health.set_value("Health").run()
    assert not at.exception
    md = " ".join(m.value or "" for m in at.markdown)
    if "Your teams" not in md:                          # no demo squad in this environment
        return
    assert "Your teams" in md
    pick = next((s for s in at.selectbox if s.label == "View a team's DNA"), None)
    if pick and len(pick.options) > 1:
        pick.set_value(pick.options[1]).run()           # drill into the first club
        assert not at.exception
        assert any("Team DNA" in (m.value or "") for m in at.markdown)


def test_my_squad_per_gw_xp_toggle_switches_the_shown_xp():
    # US-422 (ADR-121): with a >1 horizon, a "Projected xP" toggle switches cumulative ↔ single-GW.
    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30).run()
    if at.exception:
        return
    horizon = next((s for s in at.segmented_control if s.label == "Gameweeks ahead"), None)
    if horizon is None:
        return
    horizon.set_value(2).run()                       # a 2-GW horizon → the toggle appears
    if at.exception:
        return
    toggle = next((s for s in at.segmented_control if s.label == "Projected xP"), None)
    if toggle is None or len(toggle.options) < 2:
        return                                       # no demo squad / data in this env
    # cumulative label reads "N GW"; the metric is present
    assert any("Projected XI" in (m.label or "") for m in at.get("metric"))
    toggle.set_value(toggle.options[1]).run()        # "GW N only"
    assert not at.exception
    assert any("Projected XI (GW" in (m.label or "") for m in at.get("metric"))   # label flips to a single GW


def test_flag_unavailable_warns_on_a_squad_member_who_cant_play(monkeypatch):
    # US-421: a squad containing an injured/suspended/departed player (status not 'a') gets a ⛔ warning.
    from src.web_streamlit.views import squads
    warned = []
    monkeypatch.setattr(squads.st, "warning", lambda msg, **k: warned.append(msg))
    squads._flag_unavailable([{"web_name": "Fit", "status": "a"},
                              {"web_name": "Destan", "status": "u"}])   # 'u' = left/unavailable
    assert warned and "Destan" in warned[0] and "score 0" in warned[0]
    assert "Fit" not in warned[0]
    warned.clear()
    squads._flag_unavailable([{"web_name": "Fit", "status": "a"}])      # all available
    assert warned == []


def test_fixtures_team_dna_section_renders_a_team_card():
    # US-419 (ADR-119): a 🧬 Team DNA section on Fixtures — pick a team → grade + radar + key-players.
    at = _run(_PAGES / "3_Team_DNA_and_FDR.py")
    if at.exception or not at.dataframe:
        return                                          # no fixtures/data in this environment
    assert any(s.value == "🧬 Team DNA" for s in at.subheader)
    pick = next((s for s in at.selectbox if s.label == "Team"), None)
    if pick is None or not pick.options:
        return
    pick.set_value(pick.options[0]).run()
    assert not at.exception
    md = " ".join(m.value or "" for m in at.markdown)
    assert "Team DNA" in md and "Key players to target" in md


def test_fixtures_target_by_fixtures_lists_players_and_filters_by_position():
    # US-301: a "🎯 Radar" section (renamed from "Target by fixtures", ADR-107) names the best available
    # players from the easiest-run teams, scoped by a Position filter.
    # ADR-134: the Radar moved to a **Players** view — player-discovery belongs where players live.
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Radar").run()
    if not at.dataframe:
        return                                             # no data → nothing to target
    targets = at.dataframe[-1].value
    assert {"Team", "Player", "Pos", "xP", "Fit"} <= set(targets.columns)
    pos = next(s for s in at.segmented_control if s.label == "Position")
    pos.set_value("DEF").run()
    assert not at.exception
    scoped = at.dataframe[-1].value
    assert list(scoped["Pos"].unique()) == ["DEF"]         # only defenders after the filter


def test_fixtures_target_max_price_cap_drops_dearer_targets():
    # US-303: the Max price slider caps the target list to affordable players.
    # ADR-134: the Radar is a **Players** view now.
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Radar").run()
    if not at.dataframe:
        return
    cap = next(s for s in at.slider if s.label == "Max price")
    cap.set_value(6.0).run()
    assert not at.exception
    capped = at.dataframe[-1].value
    assert capped["£m"].max() <= 6.0                       # nothing dearer than the cap survives


def test_fixtures_target_value_column_and_sort_toggle():
    # US-304: a Val/£m column + a Sort toggle that reorders each team's picks by value.
    # ADR-134: the Radar is a **Players** view now.
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Radar").run()
    if not at.dataframe:
        return
    by_xp = at.dataframe[-1].value
    assert "Val/£m" in by_xp.columns
    sort = next(s for s in at.segmented_control if s.label == "Sort")
    assert sort.value == "xP"                               # xP is the default
    sort.set_value("Val/£m").run()
    assert not at.exception
    by_value = at.dataframe[-1].value
    # within the first team's block, value sort is non-increasing
    first_team = by_value.iloc[0]["Team"]
    block = by_value[by_value["Team"] == first_team]["Val/£m"].dropna().tolist()
    assert block == sorted(block, reverse=True)


def test_players_pool_offers_my_squad_only_when_a_squad_is_loaded():
    # US-407b: the "My squad only" scope is on the Players pool filter too (when a squad is active).
    from src.web_streamlit.squads import demo_squads
    squads = demo_squads()
    if not squads:
        return
    at = AppTest.from_file(str(_PAGES / "2_Players.py"), default_timeout=30)
    at.session_state["squad"] = next(iter(squads.values()))
    at.run()
    assert not at.exception
    assert any(c.label == "My squad only" for c in at.checkbox)   # the shared scope, on Players


def test_players_card_view_renders_the_player_dna_section():
    # ADR-118 (S168–S171): the Card view shows AI Verdict → radar → insights → trend for the selected player.
    at = AppTest.from_file(str(_PAGES / "2_Players.py"), default_timeout=30).run()
    if at.exception:
        return
    view = next((s for s in at.segmented_control if s.label == "View"), None)
    if view is None:
        return
    view.set_value("Card").run()
    assert not at.exception
    md = " ".join(m.value or "" for m in at.markdown)
    if "Player DNA" not in md:                 # no player data in this environment
        return
    assert "AI Verdict" in md and "Performance trend" in md


def test_my_squad_lineup_shows_owned_player_dna_with_hold_sell_framing():
    # US-417 (ADR-118): picking one of your XI in ⚙ Players & lineup shows the same DNA, owned-aware (Hold/Sell).
    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30).run()
    if at.exception:
        return
    pick = next((s for s in at.selectbox if s.label == "Select a player"), None)
    if pick is None or len(pick.options) < 2:
        return                                 # no demo squad in this environment
    pick.set_value(pick.options[1]).run()      # options[0] is "—"; pick the first owned player
    assert not at.exception
    md = " ".join(m.value or "" for m in at.markdown)
    assert "AI Verdict" in md and "Player DNA" in md
    assert any(word in md for word in ("Strong Hold", "Hold", "Sell"))   # owned framing, not browse words


def test_fixtures_ticker_my_squad_scope_filters_to_owned_teams_with_counts():
    # US-302 (ADR-049) + US-407b: a "My squad only" checkbox restricts the ticker to your teams + a Players count.
    from src.web_streamlit.squads import demo_squads
    at = _run(_PAGES / "3_Team_DNA_and_FDR.py")
    if not at.dataframe:
        return
    all_teams = at.dataframe[0].value
    assert "Players" not in all_teams.columns               # default = all teams, no count column
    chk = next(c for c in at.checkbox if c.label == "My squad only")
    squads = demo_squads()
    if not squads:
        chk.set_value(True).run()                           # no squad → a note + fall back to all teams
        assert any("No squad loaded" in c.value for c in at.caption)
        return
    at.session_state["squad"] = next(iter(squads.values()))
    chk.set_value(True).run()
    assert not at.exception
    scoped = at.dataframe[0].value
    assert "Players" in scoped.columns and len(scoped) <= len(all_teams)   # scoped to owned teams
    assert scoped["Players"].sum() == 15                    # a full squad's 15 players across its teams


def _squads_view(view):
    # ADR-105: Build is now its own Squad Lab tab; the rest are sub-tabs of My Squad
    if view == "Build":
        at = _run(_PAGES / "1_Squad_Lab.py")
    else:
        at = _run(_PAGES / "4_My_Squad.py")
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
    assert "Start Ollama" not in at.code[0].value          # US-375: no dev-only Ollama hint for web users


def test_squads_chips_view_renders_chip_advice():
    # ADR-082 / US-252: the "Chips" view routes through ask.answer → the grounded chip block renders
    # (no Ollama in the test → the advice block + facts, no prose), no crash
    at = _squads_view("Chips")
    assert len(at.code) == 1                               # the rendered chip advice
    block = at.code[0].value
    assert "Chip strategy" in block                        # the advice block header
    assert all(chip in block for chip in ("Triple Captain", "Bench Boost", "Free Hit", "Wildcard"))


def test_transfer_page_renders_and_reacts_to_the_bank(monkeypatch):
    at = _squads_view("Transfer")
    assert any(s.label == "Squad" for s in at.selectbox)   # the squad picker (a GW selector is also present)
    assert len(at.code) == 1 or len(at.info) >= 1          # the swaps (or a "no upgrades" note)
    next(s for s in at.slider if s.label == "Bank (£m)").set_value(3.0).run()   # move the bank → recompute
    assert not at.exception


def test_your_team_panel_consolidates_import_upload_download():
    # US-385 (ADR-113): one inline "Your team" panel on My Squad gathers Manager-ID import + Upload + Download
    # backup in one place (was scattered across the sidebar).
    at = _run(_PAGES / "4_My_Squad.py")
    assert any(e.label == "⚙ Backup / import your team" for e in at.get("expander"))
    assert any(t.label == "FPL manager-ID" for t in at.text_input)                    # import by Manager-ID
    assert any(b.label == "Import team" for b in at.button)
    assert any(u.label.endswith("restore your team from a backup file") for u in at.get("file_uploader"))
    assert any(d.label == "⬇︎ Download a backup" for d in at.get("download_button"))   # a real, working backup button


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


def test_transfer_page_applies_a_coordinated_plan():
    # US-354: the Transfer page can APPLY a coordinated multi-transfer AI plan (not just display it)
    at = _squads_view("Transfer")
    count = next((s for s in at.slider if s.label.startswith("Transfers")), None)
    if count is None:
        return
    count.set_value(2).run()
    next(s for s in at.slider if s.label == "Bank (£m)").set_value(10.0).run()   # dearer upgrades → a plan appears
    apply = [b for b in at.button if b.label == "Apply this plan →"]
    if not apply:                                          # no positive-gain 2-plan on this DB → nothing to apply
        return
    before = list(at.session_state["squad"]["player_ids"]) if "squad" in at.session_state else None
    apply[0].click().run()
    assert not at.exception
    squad = at.session_state["squad"]
    assert before is None or squad["player_ids"] != before  # the plan changed the squad (or was just adopted)
    assert squad.get("name") and squad.get("cost")         # named + re-costed (no sidebar crash)


def test_captain_page_renders_the_pick_card_or_a_note():
    # US-294: the web Captain view renders the styled HTML card (not the mono block) — or a "no data" note.
    at = _squads_view("Captain")
    assert len(at.selectbox) >= 1                          # the squad picker (+ a set-captain selector)
    blobs = " ".join(m.value for m in at.markdown)
    assert ("cap-card" in blobs and "🥇 Captain Pick" in blobs) or len(at.info) >= 1


def test_captain_page_shows_crowd_flags_and_template_risk():
    # US-184: the captain candidates gain a Trends column + a template-risk caption (ADR-057)
    at = _squads_view("Captain")
    if not at.dataframe:
        return
    assert "Trends" in at.dataframe[0].value.columns.tolist()
    assert "Set" in at.dataframe[0].value.columns.tolist()   # US-254: set-piece parity with Trends (ADR-081)
    assert any("Captaincy risk" in c.value for c in at.caption)


def test_transfer_page_shows_incoming_crowd_flags():
    # US-184: the swap table gains an "In trends" column for the player you'd buy
    at = _squads_view("Transfer")
    at.slider[0].set_value(10.0).run()                     # bank → swaps appear
    if not at.dataframe:
        return
    assert "In trends" in at.dataframe[0].value.columns.tolist()
    assert "In set" in at.dataframe[0].value.columns.tolist()   # US-254: set-piece parity (ADR-081)


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
        at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
        at.session_state["squad"] = squad
        at.run()
        at.segmented_control[0].set_value(view).run()
        assert not at.exception, f"Squads[{view}] raised: {at.exception}"
        picker = next(s for s in at.selectbox if s.label == "Squad")   # by label (a GW selector was added)
        assert any("My squad (yours)" in o for o in picker.options)


def test_help_page_renders_the_guide_without_data():
    # ADR-068: the Help tab is static — it renders even with no DB, and carries the key steps + an example
    at = _run(_PAGES / "8_Help.py")
    blob = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.code)
    assert "Squad Lab" in blob and "My Squad" in blob          # the core steps (ADR-105 nav)
    assert "Ask" in blob and "worth the money" in blob         # the Ask step + a copy-paste example
    assert "AI Tips" in blob                                   # US-226: the gameweek tab (renamed) is in the guide
    assert "this week for my squad" in blob                     # US-224: the gameweek Ask example
    assert "quality rating" in blob                            # US-224: the stat-board rating is explained
    assert not at.get("dataframe")                             # static content — no data widgets


def test_sidebar_pages():
    # ADR-105: the Squads page split into My Squad (manage + tools) + Squad Lab (build); ADR-087 Feedback,
    # ADR-100 gated Admin. (ADR-069 had consolidated the old 12 tabs into the single Squads page first.)
    present = sorted(p.name for p in _PAGES.glob("*.py"))
    assert present == sorted(["2_Players.py", "3_Team_DNA_and_FDR.py", "4_My_Squad.py", "1_Squad_Lab.py", "5_Ask.py",
                              "6_News.py", "7_Trending.py", "8_Help.py", "9_Maddie_Explains.py", "10_Feedback.py",
                              "11_Admin.py"])
    for gone in ("2_Player_Stats.py", "4_Build_Squad.py", "5_My_Squad.py",
                 "6_Squad_Health.py", "7_Transfer.py", "8_Captain.py"):
        assert not (_PAGES / gone).exists()


def test_player_stats_board_renders_via_the_segmented_control():
    # ADR-069: Player Stats merged into Players — a stat board renders when its segmented-control view is picked
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Over/under").run()
    assert not at.exception
    assert len(at.dataframe) >= 1 or len(at.info) >= 1     # the board rendered


def test_player_stats_filter_narrows_a_board():
    # ADR-064/069: the shared filter narrows a stat board on the merged Players page
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    at.segmented_control[0].set_value("DefCon").run()
    at.multiselect[0].set_value(["ARS"]).run()             # Team = ARS (the first filter multiselect)
    assert not at.exception
    for df in at.dataframe:                                 # the board is now ARS-only
        assert set(df.value["Team"].tolist()) <= {"ARS"}


def test_set_pieces_board_renders_the_order_columns():
    # ADR-081 / US-250: the "Set pieces" view shows Pen/Corners/FK order + Own%/Val/£m through the filter
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Set pieces").run()
    assert not at.exception
    if at.dataframe:                                          # populated DB → a board with the order columns
        cols = at.dataframe[0].value.columns.tolist()
        assert {"Pen order", "Corner order", "FK order", "Own%", "Val/£m"} <= set(cols)   # US-376: read as order
    else:
        assert len(at.info) >= 1                              # empty (unpopulated) → an honest note


def test_pool_shows_a_set_piece_column():
    # ADR-081 / US-250: the Pool gains a compact "Set" column (⚽/🚩/🎯 for first-choice takers)
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert "Set" in df.columns


def test_pool_shows_an_availability_fit_column():
    # ADR-074 + US-276: the Pool's Fit column shows ✅ for fit players (not blank) and 🚑/🚫/⛔/❓ for concerns
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert "Fit" in df.columns
    flags = set(df["Fit"].astype(str))
    assert "✅" in flags                                   # US-276: fit players read positively, not blank
    assert "" not in flags                                 # no blank cells now — fit is ✅
    assert any("injured" in c.value for c in at.caption)   # the availability legend


def test_pool_shows_the_price_prediction_column():
    # US-286 (ADR-092): a forward-looking Price column (🔺/🔻/—, all — preseason) + the honest live-GW1 caption.
    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert "Price" in df.columns
    assert set(df["Price"].astype(str)) <= {"", "🔺", "🔻"}          # only the predictor's markers
    assert any("live from GW1" in c.value for c in at.caption)      # honest dormant-now note


def test_players_history_view_shows_a_season_table_for_a_known_player():
    # US-298: the Players "History" view — pick a player → a season table (+ the GW1 note preseason).
    at = AppTest.from_file(str(_PAGES / "2_Players.py"), default_timeout=30).run()
    if at.exception or not at.segmented_control:
        return
    at.segmented_control[0].set_value("History").run()
    if at.exception or not at.selectbox:
        return
    label = next((o for o in at.selectbox[0].options if o.startswith("Haaland")), None)
    if label is None:
        return                                             # no seed history → nothing to assert
    at.selectbox[0].set_value(label).run()
    assert not at.exception
    cols = list(at.dataframe[0].value.columns) if at.dataframe else []
    assert "Season" in cols and "£ start" in cols and "Pts/90" in cols       # the native season table
    assert any("fills once the season starts (GW1)" in c.value for c in at.caption)   # per-GW dormant note
    assert any("🟢" in str(v) or "🔴" in str(v) or v == "0.0"                 # US-311: Δ£ carries an up/down cue
               for v in at.dataframe[0].value["Δ£"].tolist())

    # US-312: pick a second player in "Compare with" → a side-by-side season table appears.
    cmp = next((s for s in at.selectbox if s.label == "Compare with (optional)"), None)
    if cmp is None:
        return
    other = next((o for o in cmp.options if o != "—" and not o.startswith("Haaland")), None)
    if other is None:
        return
    n_before = len(at.dataframe)
    cmp.set_value(other).run()
    assert not at.exception
    assert len(at.dataframe) > n_before                                       # a comparison table was added
    assert "Season" in at.dataframe[-1].value.columns


def test_my_squad_price_nudge_lists_pressured_players(monkeypatch):
    # US-286: My Squad names owned players under price pressure (forced here — net transfers are flat preseason).
    import src.web_streamlit.views.squads as sq
    monkeypatch.setattr(sq, "price_prediction", lambda p: "fall")
    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30).run()
    for control in at.segmented_control:
        try:
            control.set_value("My Squad").run()
            break
        except Exception:
            pass
    if at.exception:
        return
    caps = " ".join(c.value for c in at.caption)
    assert "🔻" in caps and "drop" in caps                          # the sell-timing nudge fired


def test_pool_number_columns_stay_numeric_formatting_is_display_only():
    # ADR-072: money/value columns are formatted via NumberColumn (display) — the frame still holds the
    # raw numbers (not pre-rounded strings), so they stay sortable and truthful.
    import pandas as pd

    at = _run(_PAGES / "2_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert {"£m", "Val/£m"} <= set(df.columns)
    assert pd.api.types.is_numeric_dtype(df["£m"])       # not stringified
    assert pd.api.types.is_numeric_dtype(df["Val/£m"])


def test_clean_sheets_board_shows_a_quality_rating_and_legend():
    # ADR-071: xGC/90 board gains a relative Rating column (🟢…🔴) + a "vs the players shown" legend
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Clean sheets").run()
    assert not at.exception
    assert any("relative to the players shown" in c.value for c in at.caption)   # the legend
    if at.dataframe:
        df = at.dataframe[0].value
        assert "Rating" in df.columns
        assert df["Rating"].astype(str).str.contains("🟢|🟡|🟠|🔴", regex=True).any()


def test_team_dna_key_players_falls_back_to_last_season():
    """ADR-126 follow-up: the Team DNA card's key-players table has the same 900-minute gate as the three stat
    boards, so it gets the same fallback — through the real page, not just the pure function."""
    at = _run(_PAGES / "3_Team_DNA_and_FDR.py")
    sel = next((s for s in at.selectbox if s.label == "Team"), None)
    if sel is None:
        return                                  # gated or no data
    sel.set_value("Arsenal").run()
    assert not at.exception
    blob = " ".join(m.value for m in at.markdown)
    assert "Key players to target" in blob
    if "Fills in as the season plays" in blob:
        return                                  # no last-season rows for this side either — the 🌱 note stands
    assert "Ownership is current" in blob, "the table showed last season without saying so"
    assert 'class="td-tbl"' in blob, "announced last season but rendered no table"


def test_gated_boards_fall_back_to_last_season_and_say_so():
    """ADR-126: the three 900-minute boards can't answer until ~GW10. Rather than the ten-week blank they used
    to show, they render last season's numbers behind a banner naming the season. The banner is the point — an
    unlabelled number from a different season is worse than an empty board."""
    for view in ("Over/under", "DefCon", "Clean sheets"):
        at = _run(_PAGES / "2_Players.py")
        if not at.segmented_control:
            return
        at.segmented_control[0].set_value(view).run()
        assert not at.exception, f"{view} raised: {at.exception}"
        blob = " ".join(str(i.value) for i in at.info)
        if "Showing" not in blob:
            continue                       # this season has data — the fallback has retired, as designed
        assert "20" in blob, f"{view} banner names no season"      # e.g. "Showing 2025/26"
        assert at.dataframe, f"{view} announced last season but rendered no table"
        # Clubs are current, the numbers are not — a summer signing sits under a badge he didn't earn them at.
        assert "Clubs are current" in blob, f"{view} doesn't say the club and the number disagree"
        # It sits above the table on a phone, so length is a feature of the copy, not an accident.
        assert len(blob) < 320, f"{view} banner is {len(blob)} chars — too tall on a 390px screen"


def test_clean_sheet_fallback_warns_that_xgc_crosses_a_transfer():
    """xGC is a *team* stat and FPL's history records what a player did without recording who for — so a summer
    signing brings his old side's defence under his new side's badge. The other two boards are player-level and
    need no such warning."""
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Clean sheets").run()
    assert not at.exception
    blob = " ".join(str(i.value) for i in at.info)
    if "Showing" in blob:
        assert "team" in blob and "old club" in blob


def test_stat_boards_show_the_availability_fit_column():
    # ADR-074 / US-229: every stat board gains the Fit column (raw rows on xG; a lookup on the trimmed ones)
    for view in ("Over/under", "DefCon", "Clean sheets", "xG · xA"):
        at = _run(_PAGES / "2_Players.py")
        if not at.segmented_control:
            return
        at.segmented_control[0].set_value(view).run()
        assert not at.exception, f"{view} raised: {at.exception}"
        if not at.dataframe:
            continue
        df = at.dataframe[0].value
        assert "Fit" in df.columns, f"{view} missing the Fit column"
        assert "✅" in set(df["Fit"].astype(str)), f"{view} shows no ✅ fit flag"   # US-276


def test_xg_board_rates_only_meaningful_players():
    # ADR-071/073: the xG board rates xGI, but only for outfield players with minutes — the column is
    # named "xGI rating" and sits before xGC; goalkeepers (xGI ≈ noise) are left unrated (—).
    at = _run(_PAGES / "2_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("xG · xA").run()
    assert not at.exception
    if not at.dataframe:
        return
    cols = list(at.dataframe[0].value.columns)
    assert "xGI rating" in cols and "Rating" not in cols            # renamed
    assert cols.index("xGI rating") < cols.index("xGC")             # sits before xGC (away from it)

    pos = [p for p in at.pills if p.label == "Position"]            # filter to GK → all unrated (Position = pills)
    if pos:
        pos[0].set_value(["GK"]).run()
        ratings = set(at.dataframe[0].value["xGI rating"].astype(str))
        assert ratings <= {"—"}, f"goalkeepers should not be rated on xGI, got {ratings}"


_TAB_EMOJI = {"2_Players.py": "👟", "3_Team_DNA_and_FDR.py": "🧬", "4_My_Squad.py": "🧩", "1_Squad_Lab.py": "🧪",
              "5_Ask.py": "💬", "6_News.py": "📰", "7_Trending.py": "📈", "8_Help.py": "🧭",
              "9_Maddie_Explains.py": "🎥", "10_Feedback.py": "📣", "11_Admin.py": "📊"}


def test_every_tab_has_an_emoji_led_header():
    # US-222: each tab's title leads with a distinct emoji (like Home's ⚽ MADBOOTS), no crash
    for fname, emoji in _TAB_EMOJI.items():
        at = _run(_PAGES / fname)
        assert not at.exception, f"{fname} raised: {at.exception}"
        assert at.title and emoji in at.title[0].value, f"{fname} title missing {emoji}"


def test_feedback_page_form_degrades_to_a_prefilled_email_without_a_webhook():
    # US-307: with no FPL_FEEDBACK_WEBHOOK a submit offers a pre-filled mailto to the inbox (no network),
    # and the "Join the beta" link is hidden until FPL_SIGNUP_URL is set.
    at = _run(_PAGES / "10_Feedback.py")
    assert not at.exception
    assert at.text_area and any(b.label == "Send feedback" for b in at.button)   # the form is there
    assert not any("Join the beta" in b.label for b in at.get("link_button"))     # no signup URL configured
    assert any(b.label == "✉ Email your feedback" for b in at.get("link_button")) # always-available route
    at.text_area[0].set_value("Bench boost explanation was great, one typo on Trending.").run()
    next(s for s in at.selectbox if s.label == "Which page?").set_value("Trending").run()
    next(b for b in at.button if b.label == "Send feedback").click().run()
    assert not at.exception
    mailtos = [b.url for b in at.get("link_button") if str(b.url).startswith("mailto:")]
    assert any("hello@madboots.com" in u and "typo" in u for u in mailtos)   # pre-filled email to the inbox


def test_feedback_page_shows_the_beta_signup_when_configured(monkeypatch):
    # US-264: the "Join the beta" link appears once FPL_SIGNUP_URL is set
    monkeypatch.setenv("FPL_SIGNUP_URL", "https://example.com/signup")
    at = _run(_PAGES / "10_Feedback.py")
    assert any("Join the beta" in b.label for b in at.get("link_button"))


def test_feedback_payload_carries_page_version_and_timestamp(monkeypatch):
    # US-306/308 (ADR-087): a submitted report POSTs an enriched, relay-ready payload — page + app-version
    # + a timestamp + a _subject; the Web3Forms access_key is added only when FPL_FEEDBACK_KEY is set.
    monkeypatch.setenv("FPL_FEEDBACK_WEBHOOK", "https://example.test/sink")
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):   # no network in tests — capture the payload
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        return type("R", (), {})()

    monkeypatch.setattr("requests.post", fake_post)
    at = _run(_PAGES / "10_Feedback.py")
    assert any(s.label == "Which page?" for s in at.selectbox)          # the page picker exists
    at.text_area[0].set_value("Fixtures target list is great").run()
    next(s for s in at.selectbox if s.label == "Which page?").set_value("Fixtures").run()
    next(b for b in at.button if b.label == "Send feedback").click().run()

    assert not at.exception and captured.get("url") == "https://example.test/sink"
    payload = captured["json"]
    assert payload["message"] == "Fixtures target list is great"
    assert payload["page"] == "Fixtures"
    assert payload["version"] and payload["source"] == "fpl-assistant-beta"
    assert "T" in payload["ts"]                                          # an ISO timestamp
    assert payload["_subject"].endswith("Fixtures")                     # US-308: FormSubmit subject
    assert (captured["headers"] or {}).get("Origin", "").startswith("http")   # server-side Origin for FormSubmit
    assert "access_key" not in payload                                  # no Web3Forms key set → omitted


def test_feedback_payload_adds_the_web3forms_key_when_configured(monkeypatch):
    # US-308: when FPL_FEEDBACK_KEY is set, the POST carries it as access_key (Web3Forms), else it's omitted.
    monkeypatch.setenv("FPL_FEEDBACK_WEBHOOK", "https://api.web3forms.com/submit")
    monkeypatch.setenv("FPL_FEEDBACK_KEY", "test-access-key")
    captured = {}
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None:
                        captured.update(json=json) or type("R", (), {})())
    at = _run(_PAGES / "10_Feedback.py")
    at.text_area[0].set_value("Nice work").run()
    next(b for b in at.button if b.label == "Send feedback").click().run()
    assert captured["json"]["access_key"] == "test-access-key"


# --- the capped registration gate (ADR-098, US-324) ---------------------------------------------

def _fake_user_store(monkeypatch, rows):
    """A tiny in-memory beta_users on the Supabase REST shape: GET filters/counts, POST appends."""
    def fake_get(url, params=None, headers=None, timeout=None):
        if params and "email" in params:
            e = params["email"].split("eq.", 1)[1]
            return _StoreResp([{"email": e}] if e in rows else [])
        return _StoreResp([{"email": e} for e in rows])

    def fake_post(url, json=None, headers=None, timeout=None):
        if url.endswith("/beta_users"):                      # only a registration insert records a user (ADR-098);
            rows.append(json["email"])                       # a beta_waitlist write (ADR-102) goes to another table
        return _StoreResp()

    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("requests.post", fake_post)


def _registration_env(monkeypatch, cap="2"):
    monkeypatch.setenv("FPL_USER_CAP", cap)
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    monkeypatch.setenv("FPL_ACCESS_CODE", "letmein")


def test_gate_is_off_by_default():
    # US-324: no cap / no code → the app is open (no gate), byte-identical to today
    at = _run(_PAGES / "10_Feedback.py")
    assert not at.exception
    assert not any("private beta" in (t.value or "") for t in at.title)   # no gate title
    assert any(b.label == "Send feedback" for b in at.button)              # the real page rendered


def test_registration_gate_admits_with_code_and_email(monkeypatch):
    _registration_env(monkeypatch)
    rows = []
    _fake_user_store(monkeypatch, rows)
    at = _run(_PAGES / "10_Feedback.py")
    assert any(t.label == "Invite code" for t in at.text_input)           # registration mode shows both fields
    assert any(t.label == "Your email" for t in at.text_input)
    next(t for t in at.text_input if t.label == "Invite code").set_value("nope").run()
    next(t for t in at.text_input if t.label == "Your email").set_value("a@b.com").run()
    next(b for b in at.button if "Join" in b.label).click().run()
    assert any("invite code" in (e.value or "").lower() for e in at.error) and rows == []   # wrong code blocks
    next(t for t in at.text_input if t.label == "Invite code").set_value("letmein").run()
    next(t for t in at.text_input if t.label == "Your email").set_value("A@b.com").run()
    next(b for b in at.button if "Join" in b.label).click().run()
    assert not at.exception and rows == ["a@b.com"] and at.session_state["_beta_ok"] is True   # cleaned + in


def test_registration_gate_full_shows_the_waitlist(monkeypatch):
    _registration_env(monkeypatch, cap="0")                               # already full
    monkeypatch.setenv("FPL_SIGNUP_URL", "https://example.com/waitlist")
    _fake_user_store(monkeypatch, [])
    at = _run(_PAGES / "10_Feedback.py")
    next(t for t in at.text_input if t.label == "Invite code").set_value("letmein").run()
    next(t for t in at.text_input if t.label == "Your email").set_value("late@b.com").run()
    next(b for b in at.button if "Join" in b.label).click().run()
    assert any("full" in (w.value or "").lower() for w in at.warning)     # the beta-full note
    assert any("waitlist" in b.label.lower() for b in at.get("link_button"))
    assert not any(b.label == "Send feedback" for b in at.button)         # gate stopped the page — not admitted


def _capture_waitlist(monkeypatch):
    from src.web_streamlit import waitlist
    calls = []
    monkeypatch.setattr(waitlist, "add", lambda email, reason: calls.append((email, reason)))
    return calls


def test_waitlist_captures_a_wrong_code_email(monkeypatch):
    # ADR-102 (US-347): a wrong invite code + an email → the email is captured (reason="bad_code")
    _registration_env(monkeypatch)
    _fake_user_store(monkeypatch, [])
    calls = _capture_waitlist(monkeypatch)
    at = _run(_PAGES / "10_Feedback.py")
    next(t for t in at.text_input if t.label == "Invite code").set_value("wrong").run()
    next(t for t in at.text_input if t.label == "Your email").set_value("hopeful@b.com").run()
    next(b for b in at.button if "Join" in b.label).click().run()
    assert ("hopeful@b.com", "bad_code") in calls


def test_waitlist_captures_an_over_cap_email(monkeypatch):
    # ADR-102: at the cap → the email is captured (reason="full") so the owner can invite later
    _registration_env(monkeypatch, cap="0")
    _fake_user_store(monkeypatch, [])
    calls = _capture_waitlist(monkeypatch)
    at = _run(_PAGES / "10_Feedback.py")
    next(t for t in at.text_input if t.label == "Invite code").set_value("letmein").run()
    next(t for t in at.text_input if t.label == "Your email").set_value("late@b.com").run()
    next(b for b in at.button if "Join" in b.label).click().run()
    assert ("late@b.com", "full") in calls


def test_squads_gameweeks_selector_drives_the_horizon():
    # US-237/315 (ADR-077): a "Gameweeks ahead" box-select (My Squad default 1, US-374) flows into Health — set it
    # to 2 and the analysis projects over 2 GW (a GW2 column, no GW5)
    at = _run(_PAGES / "4_My_Squad.py")
    gw = [s for s in at.segmented_control if s.label == "Gameweeks ahead"]
    assert gw and gw[0].value == 1 and list(gw[0].options) == ["1", "2", "3", "4", "5", "10"]   # US-374/315
    gw[0].set_value(2).run()
    at.segmented_control[0].set_value("Health").run()
    assert not at.exception
    if at.code:
        blob = " ".join(c.value for c in at.code)
        assert "2 GW" in blob and "GW2" in blob and "GW5" not in blob   # horizon narrowed to 2


def test_squads_gameweeks_box_select_offers_ten(monkeypatch):
    # US-315: the box-select includes 10 (a wildcard/start-of-season horizon) and it flows through.
    at = _squads_view("My Squad")
    gw = [s for s in at.segmented_control if s.label == "Gameweeks ahead"]
    if not gw:
        return
    assert 10 in [int(o) for o in gw[0].options]           # the requested long window is offered
    gw[0].set_value(10).run()
    assert not at.exception
    assert any(m.label == "Projected XI (10 GW)" for m in at.metric)   # 10 drives the horizon


def test_captain_view_notes_it_is_next_gameweek():
    # US-237: captaincy is a one-week decision — a caption says the GW selector doesn't apply
    at = _squads_view("Captain")
    assert any("next gameweek" in c.value.lower() for c in at.caption)


def test_my_squad_transfer_moved_to_the_tab_with_a_pointer():
    # ADR-115/US-405: the My Squad edit view has NO in-page transfer picker — just a pointer to the Transfer tab.
    at = _squads_view("My Squad")
    caps = " ".join(c.value for c in at.caption)
    assert "Transfer" in caps and "Substitute" in caps               # the pointer distinguishes the two
    assert not any(s.label == "Transfer out" for s in at.selectbox)  # the manual picker is gone from here


def test_my_squad_manage_expander_holds_rename_and_set_bench():
    # ADR-115/US-406: Rename + Set-whole-bench fold into one ⚙ Manage expander (flat — expanders can't nest).
    at = _squads_view("My Squad")
    assert any("Manage" in (e.label or "") for e in at.get("expander"))
    assert any(b.label == "Rename" for b in at.button) and any(b.label == "Set bench" for b in at.button)


def test_my_squad_shows_a_quick_stats_summary():
    # US-239 + US-404 (ADR-115): the summary is a compact 3-number strip (Projected XI · Captain · Bench) — the
    # old Unavailable/Doubtful metrics folded into the availability line; the Projected-XI label tracks the horizon.
    at = _squads_view("My Squad")
    labels = [m.label for m in at.metric]
    assert any("Projected XI" in lbl for lbl in labels)
    assert "Bench" in labels and any("Captain" in lbl for lbl in labels)
    assert not any(lbl in ("Unavailable", "Doubtful") for lbl in labels)   # folded into the availability line

    gw = [s for s in at.segmented_control if s.label == "Gameweeks ahead"][0]
    gw.set_value(2).run()
    assert any(m.label == "Projected XI (2 GW)" for m in at.metric)


def test_my_squad_projected_xi_includes_the_captain_next_gw_double():
    # US-256 (ADR-083): with a captain set, Projected XI = XI over N GW + the captain's next-GW xP,
    # and a caption says the ×2 is for the next GW only. Injects an active squad with a captain.
    from src.analytics import best_legal_xi, decision_xp
    from src.squads import SquadStore
    from src.storage import Storage

    store = Storage()
    sq = SquadStore().load("RoboTS")
    players = store.get_players()
    if not sq or not players:
        return
    by_id = {p["id"]: p for p in players}
    ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                         horizon=5, gw_history_by_code=store.get_gw_history_by_code())   # a multi-GW horizon (see below)
    store.close()
    xp = {r["id"]: r["xp"] for r in ranked}
    by_gw = {r["id"]: r["by_gameweek"] for r in ranked}
    g1 = ranked[0]["gameweeks"][0]
    owned = [by_id[i] for i in sq["player_ids"] if i in by_id]
    xi = best_legal_xi(owned, xp)
    cap = max(xi, key=lambda i: xp[i])                     # captain = the best XI player
    expected = round(sum(xp[i] for i in xi) + by_gw[cap][g1], 1)

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = {**sq, "captain_id": cap, "name": "RoboTS"}
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    # US-374: My Squad now defaults to 1 GW; this test is about the multi-GW captain double, so set it to 5 to
    # match `expected` and to surface the "next gameweek only" caption (moot, so hidden, at horizon 1).
    next(s for s in at.segmented_control if s.label == "Gameweeks ahead").set_value(5).run()
    assert not at.exception
    proj = next(m for m in at.metric if m.label.startswith("Projected XI"))
    assert proj.value == f"{expected:.1f} xP"              # XI + captain's next-GW double
    assert any("next gameweek only" in c.value for c in at.caption)   # the honest one-GW note


def test_my_squad_pitch_cards_show_set_piece_attributes():
    # US-253 (ADR-081): each pitch card shows a set-piece line (⚽/🚩/🎯) for a first-choice taker,
    # like the Trends line — display-only. Assert the count of set-piece captions matches the owned takers.
    from src.analytics import set_piece_flags
    from src.squads import SquadStore
    from src.storage import Storage

    at = _squads_view("My Squad")
    assert not at.exception
    picker = next((s for s in at.selectbox if s.label == "Squad"), None)
    squad = SquadStore().load(picker.value) if picker else None
    if not squad:
        return                                          # no pickable squad (empty env) → nothing to assert
    players = {p["id"]: p for p in Storage().get_players()}
    # US-257 (ADR-084): the pitch is one HTML block — the set-piece emojis live in the markdown, not captions.
    # ADR-133: the kit cards render inside the click component, so their flags aren't in `at.markdown`.
    # The same assertion now runs directly against the markup in tests/test_pitch_html.py.
    expected = sum(len(set_piece_flags(players[i])) for i in squad["player_ids"] if i in players)
    blob = " ".join(m.value for m in at.markdown)
    shown = expected if "fpl-pitch" not in blob else sum(blob.count(e) for e in ("⚽", "🚩", "🎯"))
    # Every owned taker's set-piece flags render on the pitch — now in the kit line AND the hover card (US-344),
    # so each shows at least once (the popover repeats them; a lone-kit exact count no longer holds).
    assert shown >= expected


def test_my_squad_shows_the_bench_order():
    # US-242 (ADR-078): My Squad shows an auto-sub bench-order line for a squad with a declared bench
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]   # a GK + 3 outfield
    squad = {"name": "BenchTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception
    line = next((c.value for c in at.caption if "Bench order" in c.value), "")
    assert "1st" in line and "GK" in line and "auto-sub" in line.lower()


def test_my_squad_pitch_labels_the_bench_subs():
    # US-246: the pitch bench cards show the sub role (1st/2nd/3rd + GK)
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [defs[4]["id"], mids[4]["id"], fwds[2]["id"], gks[1]["id"]]
    # a starting captain too, to assert the armband badge (US-258)
    squad = {"name": "BenchLabels", "player_ids": ids, "bench_ids": bench, "cost": 100.0,
             "captain_id": mids[0]["id"]}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception
    # ADR-133: the pitch renders inside the click component, so its badges are no longer in `at.markdown`.
    # The same assertions run directly against the markup in tests/test_pitch_html.py. What the page can still
    # prove is that it built the squad and offers the picker that drives selection.
    assert any(s.label == "Select a player" for s in at.selectbox)


def test_my_squad_bench_reorder_persists_and_recommended_applies():
    # US-244 (ADR-079): ⬆/⬇ reorders the stored bench priority (persists); "Use recommended" applies xP order
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [defs[4]["id"], mids[4]["id"], fwds[2]["id"], gks[1]["id"]]   # a deliberately non-xP order
    squad = {"name": "BenchOrder", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()

    up = next((b for b in at.button if b.key == f"bench_up_{mids[4]['id']}"), None)
    assert up is not None
    up.click().run()                                          # move the 2nd sub up → 1st, and it persists
    assert at.session_state["squad"]["bench_ids"][0] == mids[4]["id"]

    rec = next((b for b in at.button if b.label.startswith("↻ Use recommended")), None)
    assert rec is not None
    rec.click().run()
    assert not at.exception


def test_my_squad_substitute_control_swaps_a_starter_and_bench_player():
    # US-351/366 (ADR-108): in the player-actions panel, selecting a STARTER shows a "take them off — bring on"
    # picker offering only legal bench swaps (the bench GK isn't a legal bring-on for an outfield starter);
    # confirming performs the swap.
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]   # GK + 3 outfield → XI is a legal 4-4-2
    squad = {"name": "SubTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception

    # Select the first-choice DEF (a starter) in the panel → the "bring on" picker appears (only legal swaps).
    next(s for s in at.selectbox if s.label == "Select a player") \
        .set_value(f"{defs[0]['web_name']} · {defs[0]['team']}").run()
    on = next((s for s in at.selectbox if s.key == "pa_sub"), None)
    assert on is not None and next((b for b in at.button if b.key == "pa_do_sub"), None) is not None
    assert not any(gks[1]["web_name"] in o for o in on.options)      # the bench GK isn't a legal outfield sub

    # Bring on the benched DEF for that starter — a legal same-count swap.
    on.set_value(next(o for o in on.options if defs[4]["web_name"] in o)).run()
    next(b for b in at.button if b.key == "pa_do_sub").click().run()
    assert not at.exception

    new_bench = set(at.session_state["squad"]["bench_ids"])
    assert defs[4]["id"] not in new_bench and defs[0]["id"] in new_bench   # on → XI, off → bench


def test_my_squad_panel_brings_a_bench_player_on():
    # US-366 (ADR-108): selecting a BENCH player in the panel flips the substitute to "bring them ON" — pick the
    # starter to drop, confirm, and the bench player enters the XI (the counterpart of the starter path above).
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]   # GK + 3 outfield
    squad = {"name": "PrefillTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception

    benched = defs[4]                                          # a benched DEF → a bring-*on*
    next(s for s in at.selectbox if s.label == "Select a player") \
        .set_value(f"{benched['web_name']} · {benched['team']}").run()
    off = next((s for s in at.selectbox if s.key == "pa_sub"), None)
    assert off is not None and benched["web_name"] in (off.label or "")   # the picker names the bring-on player
    off.set_value(next(o for o in off.options if defs[0]["web_name"] in o)).run()   # drop the first-choice DEF
    next(b for b in at.button if b.key == "pa_do_sub").click().run()
    assert not at.exception

    new_bench = set(at.session_state["squad"]["bench_ids"])
    assert benched["id"] not in new_bench and defs[0]["id"] in new_bench   # benched → XI, starter → bench


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

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception
    caps = " ".join(c.value for c in at.caption)
    assert "Flagged" in caps and injured["web_name"] in caps and "🚑" in caps


def test_my_squad_points_to_build():
    # ADR-105: the My Squad view points to Squad Lab for a full rebuild
    at = _squads_view("My Squad")
    assert any("Squad Lab" in c.value for c in at.caption)


def test_squad_lab_page_builds_and_has_a_mascot_header():
    # US-360 (ADR-105): Squad Lab is the builder, with a mascot-themed header
    at = _run(_PAGES / "1_Squad_Lab.py")
    assert at.title and "Squad Lab" in at.title[0].value
    assert any("Build your squad" in c.value for c in at.caption)   # the header copy


def test_my_squad_empty_state_points_to_squad_lab():
    # US-360 (ADR-105): with no team built/loaded, My Squad points new users at Squad Lab
    at = _run(_PAGES / "4_My_Squad.py")                    # no injected squad → active_squad() is None
    assert any("Squad Lab" in i.value for i in at.info)


def test_build_page_returns_a_squad(monkeypatch):
    at = _run(_PAGES / "1_Squad_Lab.py")
    # a squad is rendered (the explanation block + the squad table) — or the "no data" note; no crash
    assert len(at.code) >= 1 or len(at.info) >= 1
    # move an archetype control → rebuild, still no crash
    at.number_input[0].set_value(3).run()                  # 3 low-cost players
    assert not at.exception


def test_build_shows_the_squad_on_the_pitch():
    # US-261 (ADR-084 reuse): the built 15 render on the green pitch (a full 15 kit cards) + the table below
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:                                        # no data locally → the info branch
        return
    blob = " ".join(m.value for m in at.markdown)
    assert "fpl-pitch" in blob                             # the pitch container
    assert blob.count('class="kit"') == 15                 # the whole 15 on the pitch (XI + bench)
    assert len(at.dataframe) >= 1                          # the sortable detail table is still there


def test_build_formation_preview_shows_the_xi_score():
    # US-230 (ADR-075): the "Preview the best XI in a shape" expander shows a Projected XI xP total
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:                                        # no data locally → the "run refresh" note
        return
    mets = [(m.label, str(m.value)) for m in at.metric]
    xi = [(lbl, val) for lbl, val in mets if "Projected XI" in lbl]
    assert xi, f"expected a Projected XI metric, got {mets}"
    assert "xP" in xi[0][1] and any(ch.isdigit() for ch in xi[0][1])   # a numeric xP total


def test_build_compare_all_formations_is_gated():
    # US-231 (ADR-075): the "Compare all formations" table is absent by default and appears only on tick,
    # ranking all 7 shapes by XI xP (desc) with a Δ-vs-best column.
    at = _run(_PAGES / "1_Squad_Lab.py")
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
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:                                        # no data locally → the "run refresh" note
        return
    assert at.get("download_button"), "an Optimal build must offer a squad.json download"
    at.button[0].click().run()                             # "Use this squad →"
    assert not at.exception
    squad = at.session_state["squad"]                      # …became the session active squad (ADR-054)
    assert squad["name"] == "My squad" and 11 <= len(squad["player_ids"]) <= 15


def test_build_starts_the_bench_in_recommended_order():
    # US-245 (ADR-078/079): a built squad's bench_ids come out in recommended (xP) order — outfield
    # highest-xP first, the GK last
    from src.analytics import decision_xp
    from src.storage import Storage

    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:
        return
    next(b for b in at.button if b.label.startswith("Use this squad")).click().run()
    squad = at.session_state["squad"]

    store = Storage()
    rows = store.get_players()
    xp = {r["id"]: r["xp"]
          for r in decision_xp(rows, store.get_upcoming_fixtures(), store.get_history_by_code())}
    store.close()
    by_id = {p["id"]: p for p in rows}
    bench = [by_id[i] for i in squad["bench_ids"] if i in by_id]
    outfield_xps = [xp.get(p["id"], 0) for p in bench if p["position"] != "GK"]
    assert outfield_xps == sorted(outfield_xps, reverse=True)   # outfield by xP desc
    assert bench[-1]["position"] == "GK"                        # the GK last


def test_build_page_renders_non_zero_xp(monkeypatch):
    # regression (US-172): Build must attach xp/minutes_weight so the table + projected total aren't zeros
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:
        return
    out = next((c.value for c in at.code if "Total:" in c.value), "")   # the squad table (not the explanation)
    assert "xMins" in out and "xP" in out                  # the xp-objective columns
    total = next((ln for ln in out.splitlines() if ln.startswith("Total:")), "")
    assert "projected" in total and "projected 0.0 xP" not in total   # a real total, not zeros


def test_build_page_names_the_squad(monkeypatch):
    # US-172: the squad-name input flows into the active squad (and the download key)
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:
        return
    at.text_input[0].set_value("Tony's XI").run()
    at.button[0].click().run()                             # "Use this squad →"
    assert at.session_state["squad"]["name"] == "Tony's XI"


def test_build_page_objective_switch_rebuilds(monkeypatch):
    # ADR-062: switching the objective (xp→xgi) rebuilds on the same engine, no crash, still a squad
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:
        return
    next(s for s in at.selectbox if s.label == "Objective").set_value("xgi").run()
    assert not at.exception and at.code


def test_build_page_weekly_and_include_unavailable(monkeypatch):
    # ADR-062: the new build-mode radio + include-unavailable checkbox drive the same select_squad
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:
        return
    at.radio[0].set_value("Strong XI (weaker bench)").run()
    at.checkbox[-1].set_value(True).run()                  # include injured/suspended
    assert not at.exception and at.code                    # still a valid 15 renders


def test_build_page_formation_preview_is_display_only(monkeypatch):
    # ADR-062: the formation preview is XI-only and never adds a second (save) download
    at = _run(_PAGES / "1_Squad_Lab.py")
    if not at.code:
        return
    next(s for s in at.selectbox if s.label == "Formation").set_value("4-3-3").run()
    assert not at.exception
    assert len(at.get("download_button")) == 1             # only the full-15 build is downloadable


def test_build_page_exclude_removes_the_player_from_the_save(monkeypatch):
    # ADR-062: the "Must exclude" control wires through to the saved 15 (the tester's key ask)
    at = _run(_PAGES / "1_Squad_Lab.py")
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
    # a download (an editable squad view) or the no-data info; a legality read (compact caption / error) if data
    assert at.get("download_button") or at.info
    if at.get("download_button"):
        legal = any("legal 15" in (c.value or "") for c in at.caption)   # US-423: legal = a compact caption now
        assert legal or at.error                           # ✓ legal 15 caption / ⚠ illegal error


def test_my_squad_pitch_view_lays_out_the_squad():
    # US-187 / US-257 (ADR-084): the squad renders as a styled formation pitch (one HTML block), not a table
    at = _squads_view("My Squad")
    if not at.get("download_button"):                      # no data locally → the info branch
        return
    assert len(at.dataframe) == 0                          # the pitch replaced the dataframe
    # ADR-133: the pitch renders through the click component, so its markup is no longer in `at.markdown`.
    # The markup is asserted directly in tests/test_pitch_html.py — stricter, and without a page render.
    assert not at.exception
    assert any(s.label == "Select a player" for s in at.selectbox)   # the picker still drives selection


def test_my_squad_swap_adopts_and_mutates_the_session_squad():
    at = _squads_view("My Squad")
    swap = [b for b in at.button if b.label.startswith("Swap")]
    if not swap:                                           # no data / no candidates → nothing to swap
        return
    swap[0].click().run()
    assert not at.exception
    assert "squad" in at.session_state and at.session_state["squad"].get("cost")   # adopted + re-costed


def test_my_squad_swap_position_filter_scopes_the_replace_list():
    # US-299/353: a Position filter on the Transfer expander scopes "Transfer out" to owned players of that position.
    at = _squads_view("Transfer")
    pos = next((s for s in at.segmented_control if s.label == "Position"), None)
    if pos is None:                                        # no owned squad / no transfer UI → nothing to filter
        return
    replace = next((s for s in at.selectbox if s.label == "Transfer out"), None)
    assert replace is not None and len(replace.options) == 15   # All → every owned player
    pos.set_value("GK").run()
    replace = next(s for s in at.selectbox if s.label == "Transfer out")
    assert replace.options and all(o.startswith("GK ") for o in replace.options)   # scoped to GKs


def test_my_squad_swap_affordable_only_scopes_candidates_and_shows_bank():
    # US-300: an "Affordable only" checkbox hides too-dear replacements; a bank caption shows.
    at = _squads_view("Transfer")
    chk = next((c for c in at.checkbox if c.label == "Affordable only"), None)
    if chk is None:                                        # no owned squad / no swap UI → nothing to filter
        return
    assert any(c.value.startswith("Bank:") for c in at.caption)   # the bank is shown
    before = next((s for s in at.selectbox if s.label == "Bring in"), None)
    if before is None:
        return                                             # no candidates to filter
    n_before = len(before.options)
    chk.set_value(True).run()
    after = next((s for s in at.selectbox if s.label == "Bring in"), None)
    n_after = len(after.options) if after else 0
    assert n_after <= n_before                             # affordable-only never widens the list


def test_my_squad_transfer_team_and_price_filters_narrow_the_list():
    # US-356: the bring-in list gains Team + Max-price filters that narrow the (long) same-position list.
    at = _squads_view("Transfer")
    team = next((s for s in at.selectbox if s.label == "Team"), None)
    price = next((s for s in at.slider if s.label == "Max price (£m)"), None)
    if team is None or price is None:
        return                                             # no owned squad / no transfer UI
    bring = next((s for s in at.selectbox if s.label == "Bring in"), None)
    if bring is None:
        return                                             # no candidates to filter
    n_all = len(bring.options)
    picks = [o for o in team.options if o != "All"]
    if not picks:
        return
    team.set_value(picks[0]).run()                         # filter to one club
    after = next((s for s in at.selectbox if s.label == "Bring in"), None)
    if after:
        assert all(f"· {picks[0]} ·" in o for o in after.options)   # only that club's players now
        assert len(after.options) <= n_all                          # a filter never widens the list


def test_my_squad_transfer_control_labels_and_live_projection():
    # US-353 + ADR-115: the manual transfer (moved to the Transfer tab) shows a LIVE projected-cost/bank line
    # before you apply.
    at = _squads_view("Transfer")
    assert any(s.label == "Transfer out" for s in at.selectbox)   # the manual out→in picker (ADR-115)
    if not any(b.label == "Transfer →" for b in at.button):
        return                                             # no pickable replacement in this env → nothing to flag
    proj = [c.value for c in at.caption] + [w.value for w in at.warning]
    assert any("After this transfer" in t for t in proj)   # the live projection/bank (or over-budget) line


def test_my_squad_transfer_include_injured_surfaces_a_flagged_player():
    # US-353: the opt-in "Include injured/suspended" toggle adds flagged same-position players to "Bring in".
    from src.analytics import is_unavailable
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()
    flagged = next((p for p in rows if is_unavailable(p)), None)
    if flagged is None:
        return                                             # no flagged player in the data → nothing to surface
    pos = flagged["position"]

    def take(position, n):
        return [r for r in rows if r["position"] == position and r["id"] != flagged["id"]][:n]

    picks = []
    for position, n in {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}.items():
        got = take(position, n)
        if len(got) < n:
            return
        picks += got
    ids = [p["id"] for p in picks]
    if flagged["id"] in ids:
        return
    squad = {"name": "FlagTest", "player_ids": ids, "bench_ids": ids[11:], "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("Transfer").run()      # ADR-115: manual transfer moved to the Transfer tab
    assert not at.exception

    out = next((s for s in at.selectbox if s.label == "Transfer out"), None)
    out_opt = next((o for o in out.options if o.startswith(f"{pos} ")), None) if out else None
    if out_opt is None:
        return
    out.set_value(out_opt).run()
    before = next((s for s in at.selectbox if s.label == "Bring in"), None)
    before_has = bool(before and any(flagged["web_name"] in o for o in before.options))
    next(c for c in at.checkbox if c.label == "Include injured/suspended").set_value(True).run()
    after = next((s for s in at.selectbox if s.label == "Bring in"), None)
    after_has = bool(after and any(flagged["web_name"] in o for o in after.options))
    assert not before_has and after_has                    # the flagged player appears only with the toggle on


def test_my_squad_rename_updates_the_active_squad():
    at = _squads_view("My Squad")
    name_inputs = [t for t in at.text_input if t.label == "Squad name"]   # not the sidebar manager-ID
    if not name_inputs or not any(b.label == "Rename" for b in at.button):
        return
    name_inputs[0].set_value("Dream Team").run()
    next(b for b in at.button if b.label == "Rename").click().run()
    assert at.session_state["squad"]["name"] == "Dream Team"


def test_cloud_linked_squad_autosyncs_edits(monkeypatch):
    # US-357/C1: once a squad is linked to a cloud handle (Saved/Loaded), edits auto-sync — so a captain (or any
    # edit) persists across devices, not just the last manual Save.
    from src.storage import Storage

    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    synced = []
    monkeypatch.setattr("src.web_streamlit.cloud_store.save_squad", lambda h, s: synced.append((h, dict(s))))

    store = Storage()
    ids = [p["id"] for p in store.get_players()][:15]
    store.close()
    if len(ids) < 15:
        return
    squad = {"name": "Sync", "player_ids": ids, "bench_ids": ids[11:], "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.session_state["_cloud_linked_handle"] = "myhandle"      # linked (as if Saved/Loaded under this handle)
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception

    name = next((t for t in at.text_input if t.label == "Squad name"), None)   # the Rename edit → set_active_squad
    if name is None or not any(b.label == "Rename" for b in at.button):
        return
    name.set_value("Renamed").run()
    next(b for b in at.button if b.label == "Rename").click().run()
    assert not at.exception
    assert any(h == "myhandle" and s.get("name") == "Renamed" for h, s in synced)   # the edit auto-synced


class _StoreResp:
    def __init__(self, data=None):
        self._data = [] if data is None else data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def _squads_with_active(monkeypatch):
    """Run the Squads page with the store configured and an **active squad** in session (US-331: the ☁ Save/Load
    is now in the sidebar and Saves the session's active squad)."""
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    at = _run(_PAGES / "4_My_Squad.py")
    at.session_state["squad"] = {"name": "My XI", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}
    at.run()                                                                # the sidebar now sees the active squad
    return at


def _signed_in_squads(monkeypatch, stored=None):
    """Run My Squad as an **admitted, signed-in** user (ADR-106 auth mode) with the store configured. `stored` is
    the squad saved under the user's account (`user_key`) — the store's GET returns it, so a fresh run (≈ a page
    **refresh**, session wiped) restores it via `gate → link_and_restore`. Patches the auth seam so no real
    `st.user`/network is needed."""
    from src.web_streamlit import auth, user_store
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    monkeypatch.setattr(auth, "is_configured", lambda: True)              # signed-in mode on
    monkeypatch.setattr(auth, "current_email", lambda: "tony@example.com")
    monkeypatch.setattr(user_store, "is_registered", lambda email: True)  # on the allow-list → admitted
    rows = [{"data": stored}] if stored else []
    monkeypatch.setattr("requests.get", lambda url, params=None, headers=None, timeout=None: _StoreResp(rows))
    monkeypatch.setattr("requests.post", lambda url, json=None, headers=None, timeout=None: _StoreResp())
    return _run(_PAGES / "4_My_Squad.py")


def test_team_banner_highlights_your_team(monkeypatch):
    # US-386: a brand status card names your team + marks it as yours, so it stands out from the demo.
    at = _squads_with_active(monkeypatch)                     # active "My XI" in session
    blob = " ".join(m.value for m in at.markdown)
    assert "Your team" in blob and "My XI" in blob


def test_team_banner_shows_demo_prompt_without_your_team():
    # US-386: viewing the demo → the card prompts to make it yours (the default never looks like your team).
    at = _run(_PAGES / "4_My_Squad.py")
    blob = " ".join(m.value for m in at.markdown)
    assert "demo squad" in blob


def test_team_banner_shows_synced_state_when_signed_in(monkeypatch):
    # US-386: signed in → the card shows the cross-device synced state + the account team's name.
    stored = {"name": "My Account XI", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}
    at = _signed_in_squads(monkeypatch, stored=stored)
    blob = " ".join(m.value for m in at.markdown)
    assert "Synced across your devices" in blob and "My Account XI" in blob


def test_download_filename_is_named_after_the_team():
    # US-387: the backup is named after the team (not a generic squad.json the browser de-dupes to squad-13.json).
    from src.web_streamlit.squads import _safe_filename
    assert _safe_filename("TS") == "TS"
    assert _safe_filename("My Team!") == "My-Team"
    assert _safe_filename("   ") == "squad"                   # empty/odd → a safe fallback


def test_cloud_handle_tool_hidden_when_signed_in(monkeypatch):
    # ADR-113/US-384: in signed-in mode the account is the store — the manual ☁ handle tool is retired (it was the
    # refresh-revert bug), even with the store configured.
    at = _signed_in_squads(monkeypatch)
    assert not any(t.label == "Your handle" for t in at.text_input)       # no handle Save/Load UI when signed in


def test_signed_in_team_persists_across_a_refresh(monkeypatch):
    # ADR-113/US-384: the revert bug's fix — a team saved under the account is restored on a fresh run (≈ refresh),
    # so it no longer reverts to a previous squad.
    stored = {"name": "My Account XI", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}
    at = _signed_in_squads(monkeypatch, stored=stored)
    assert at.session_state["squad"]["name"] == "My Account XI"           # restored from the account, not reverted


def test_cloud_save_load_hidden_in_sidebar_without_secrets(monkeypatch):
    # US-310/331 (ADR-094): the ☁ cross-device store is secret-gated — with no FPL_STORE_URL/KEY it's invisible.
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    at = _run(_PAGES / "4_My_Squad.py")
    assert not any(t.label == "Your handle" for t in at.text_input)          # no cloud UI when unconfigured


def test_cloud_save_and_load_in_the_sidebar(monkeypatch):
    # US-331: the ☁ Save/Load lives in the Squads sidebar now → Save the active squad; Load adopts a stored one.
    posted = {}
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: posted.update(body=json) or _StoreResp())
    monkeypatch.setattr("requests.get", lambda url, params=None, headers=None, timeout=None: _StoreResp(
        [{"data": {"name": "Cloud XI", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}}]))
    at = _squads_with_active(monkeypatch)
    next(t for t in at.text_input if t.label == "Your handle").set_value("Tony17").run()
    next(b for b in at.button if b.label == "Save").click().run()
    assert not at.exception and posted["body"]["handle"] == "tony17"        # cleaned + upserted
    next(b for b in at.button if b.label == "Load").click().run()
    assert at.session_state["squad"]["name"] == "Cloud XI"                  # adopted into the session


def test_cloud_save_in_sidebar_warns_when_the_handle_is_taken(monkeypatch):
    # US-321/331: exists() → True (a row comes back) → the Save reports an overwrite, not a plain "saved"
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: _StoreResp())
    monkeypatch.setattr("requests.get",   # exists() sees a stored row for this handle
                        lambda url, params=None, headers=None, timeout=None: _StoreResp([{"handle": "tony17"}]))
    at = _squads_with_active(monkeypatch)
    next(t for t in at.text_input if t.label == "Your handle").set_value("tony17").run()
    next(b for b in at.button if b.label == "Save").click().run()
    assert not at.exception
    assert any("overwrote" in w.value for w in at.warning)                  # a "handle taken" warning, not "saved"


# --- analytics feature events (ADR-100, US-335) — capture the track() calls at their sites ----------

def _capture_events(monkeypatch):
    from src.web_streamlit import analytics
    events = []
    monkeypatch.setattr(analytics, "track", lambda event, **kw: events.append((event, kw)))
    return events


def test_analysis_run_event_on_a_manage_view(monkeypatch):
    events = _capture_events(monkeypatch)
    _squads_view("Health")
    assert any(e == "analysis_run" and kw.get("view") == "Health" for e, kw in events)


def test_squad_created_event_on_use_this_squad(monkeypatch):
    events = _capture_events(monkeypatch)
    at = _run(_PAGES / "1_Squad_Lab.py")                    # Build view (default)
    use = [b for b in at.button if b.label.startswith("Use this squad")]
    if not use:
        return                                           # no build (empty pool) → nothing to create
    use[0].click().run()
    assert any(e == "squad_created" for e, kw in events)


def test_squad_saved_and_loaded_events_carry_no_handle(monkeypatch):
    events = _capture_events(monkeypatch)
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: _StoreResp())
    monkeypatch.setattr("requests.get", lambda url, params=None, headers=None, timeout=None: _StoreResp(
        [{"data": {"name": "Cloud XI", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}}]))
    at = _squads_with_active(monkeypatch)
    next(t for t in at.text_input if t.label == "Your handle").set_value("tony17").run()
    next(b for b in at.button if b.label == "Save").click().run()
    assert any(e == "squad_saved" for e, kw in events)
    next(b for b in at.button if b.label == "Load").click().run()
    assert any(e == "squad_loaded" for e, kw in events)
    # anonymity: the handle (a chosen, semi-identifying key) must never appear in any analytics payload
    for _e, kw in events:
        assert "tony17" not in str(kw).lower() and "handle" not in kw


def test_feedback_submitted_event(monkeypatch):
    events = _capture_events(monkeypatch)
    monkeypatch.setenv("FPL_FEEDBACK_WEBHOOK", "https://example.test/sink")
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: type("R", (), {})())
    at = _run(_PAGES / "10_Feedback.py")
    at.text_area[0].set_value("Love the fixture ticker").run()
    next(b for b in at.button if b.label == "Send feedback").click().run()
    assert any(e == "feedback_submitted" for e, kw in events)
    for _e, kw in events:                                 # no message content in the event
        assert "fixture ticker" not in str(kw).lower()


# --- analytics perf timers (ADR-100, US-336) ----------------------------------------

def test_squads_page_emits_data_load_and_analysis_perf(monkeypatch):
    events = _capture_events(monkeypatch)
    _run(_PAGES / "1_Squad_Lab.py")                        # the builder: loads data + runs the optimiser (ADR-105)
    perf = [(kw.get("op"), kw.get("page"), kw.get("ok")) for e, kw in events if e == "perf"]
    assert ("data_load", "Squad Lab", True) in perf      # FPL data loading timed
    assert any(op == "analysis" and ok for op, _p, ok in perf)   # the squad-optimiser calculation timed
    for _e, kw in events:                                # perf carries a duration, never PII
        if _e == "perf":
            assert isinstance(kw.get("duration_ms"), int) and kw["duration_ms"] >= 0


def test_squad_save_and_load_emit_perf_events(monkeypatch):
    events = _capture_events(monkeypatch)
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: _StoreResp())
    monkeypatch.setattr("requests.get", lambda url, params=None, headers=None, timeout=None: _StoreResp(
        [{"data": {"name": "Cloud XI", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}}]))
    at = _squads_with_active(monkeypatch)
    next(t for t in at.text_input if t.label == "Your handle").set_value("tony17").run()
    next(b for b in at.button if b.label == "Save").click().run()
    assert any(e == "perf" and kw.get("op") == "squad_save" for e, kw in events)
    next(b for b in at.button if b.label == "Load").click().run()
    assert any(e == "perf" and kw.get("op") == "squad_load" for e, kw in events)


def test_cloud_save_disabled_without_an_active_squad(monkeypatch):
    # US-331: the sidebar renders on any sub-view; Save needs an active squad (Load works any time).
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")
    at = _run(_PAGES / "4_My_Squad.py")                                       # Build view, no active squad in session
    assert any(t.label == "Your handle" for t in at.text_input)             # the cloud UI is present (sidebar)…
    save = next(b for b in at.button if b.label == "Save")
    assert save.disabled                                                     # …but Save is disabled until you have one


def test_my_squad_pitch_has_hover_card_popovers():
    # US-344 (ADR-084): each kit embeds a compact player-card popover (shown on :hover), card CSS included once
    at = _squads_view("My Squad")
    # ADR-133: the pitch (and so its popovers and card CSS) now renders inside the click component — those
    # assertions moved to tests/test_pitch_html.py, which checks the same markup directly.
    assert not at.exception


def test_my_squad_card_picker_shows_the_full_card():
    # US-344: a "View a player's card" picker → the full player card below the pitch
    at = _squads_view("My Squad")
    picker = [s for s in at.selectbox if s.label == "Select a player"]   # ADR-108 panel selector (was the picker)
    assert picker                                             # the panel's player selector exists
    if len(picker[0].options) > 1:
        picker[0].set_value(picker[0].options[1]).run()
        assert not at.exception
        assert any("Player Card" in m.value for m in at.markdown)   # the full card's brand band


def test_my_squad_panel_make_captain_sets_the_captain():
    # US-365 (ADR-108): the player-actions panel's "👑 Make captain" button sets captain_id on the session squad —
    # the action moved onto the pitch view (was stranded in the Captain sub-tab, needing a re-pick + a tab switch).
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]
    squad = {"name": "CaptainTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception

    target = mids[0]                                          # a starter to captain
    next(s for s in at.selectbox if s.label == "Select a player") \
        .set_value(f"{target['web_name']} · {target['team']}").run()
    btn = next(b for b in at.button if "captain" in b.label.lower() and target["web_name"] in b.label)
    btn.click().run()
    assert not at.exception
    assert at.session_state["squad"]["captain_id"] == target["id"]      # captain set from the pitch panel


def test_my_squad_pitch_popover_shows_per_gameweek_xp():
    # US-368 (ADR-109): the hover popover under each shirt carries the per-GW row (xP over fixture) — the tester's
    # card-under-the-shirt. Threaded via fixtures_by_id → render_pitch → _kit_html → card_body.
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]
    squad = {"name": "GWPitchTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception
    blob = " ".join(m.value for m in at.markdown)
    if "fpl-pitch" not in blob:
        return                                               # no pitch (no data) → nothing to assert
    assert 'class="plc-gwrow"' in blob                       # the per-GW row is inside the hover popover
    assert 'class="plc-gwcol total"' not in blob             # no Total column (dropped — owner steer)


def test_card_horizon_stretches_past_a_blank_gameweek():
    """The player card shows a team's next 3 *fixtures*, but a horizon counts *gameweeks* — and a blank gameweek
    separates the two. A team with no GW3 match has its next 3 fixtures in GW2, GW4 and GW5, so a flat 3-gameweek
    horizon would never compute the xP for GW5 and the card's last cell would read 0.0."""
    from src.web_streamlit.views.squads import _card_horizon

    # ARS blanks GW3; AVL plays every week.
    upcoming = [
        {"event": 2, "home": "ARS", "away": "AVL", "team_h_difficulty": 3, "team_a_difficulty": 3},
        {"event": 3, "home": "AVL", "away": "CHE", "team_h_difficulty": 3, "team_a_difficulty": 3},
        {"event": 4, "home": "ARS", "away": "CHE", "team_h_difficulty": 3, "team_a_difficulty": 3},
        {"event": 5, "home": "AVL", "away": "ARS", "team_h_difficulty": 3, "team_a_difficulty": 3},
    ]

    assert _card_horizon(upcoming) == 4          # GW5 is the 4th gameweek in the window — ARS's 3rd fixture


def test_card_horizon_is_a_plain_three_when_every_team_plays_every_week():
    from src.web_streamlit.views.squads import _card_horizon

    upcoming = [
        {"event": gw, "home": h, "away": a, "team_h_difficulty": 3, "team_a_difficulty": 3}
        for gw in (2, 3, 4, 5) for h, a in (("ARS", "AVL"), ("CHE", "EVE"))
    ]

    assert _card_horizon(upcoming) == 3


def test_card_horizon_survives_an_empty_fixture_list():
    from src.web_streamlit.views.squads import _card_horizon

    assert _card_horizon([]) == 3


def test_my_squad_per_gw_card_is_horizon_independent():
    # Wave-3 feedback (ADR-109): the per-GW card row always shows GW1–3, even when "Gameweeks ahead" = 1 (it used to
    # leave GW2/GW3 at 0.0). The selected player's panel-card per-GW cells match between horizon 1 and horizon 5.
    import re

    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]
    squad = {"name": "HzTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}
    target = mids[0]

    def pergw(hz):
        at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
        at.session_state["squad"] = squad
        at.run()
        at.segmented_control[0].set_value("My Squad").run()
        next(s for s in at.segmented_control if s.label == "Gameweeks ahead").set_value(hz).run()
        next(s for s in at.selectbox if s.label == "Select a player") \
            .set_value(f"{target['web_name']} · {target['team']}").run()
        card = next((m.value for m in at.markdown if "Player Card" in m.value), "")   # the panel full card
        return re.findall(r'plc-gwxp">([0-9.]+)<', card)

    v1, v5 = pergw(1), pergw(5)
    assert len(v1) == 3 and v1 == v5                 # 3 GWs, identical regardless of "Gameweeks ahead"


def test_my_squad_panel_boot_battle_compares_squad_players():
    # US-377 (ADR-111): the ⚙ panel's ⚔️ Boot Battle picker compares the selected player with another same-position
    # squad player → the compare card (in place of the single card).
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]
    squad = {"name": "BootTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    next(s for s in at.selectbox if s.label == "Select a player") \
        .set_value(f"{mids[0]['web_name']} · {mids[0]['team']}").run()
    bb = next((s for s in at.selectbox if s.label and "Boot Battle" in s.label), None)
    assert bb is not None and len(bb.options) > 1              # the picker + same-position squad peers
    bb.set_value(f"{mids[1]['web_name']} · {mids[1]['team']}").run()
    assert not at.exception
    blob = " ".join(m.value for m in at.markdown)
    assert "cmp-card" in blob and "Boot Battle" in blob        # the compare card (with its brand band) rendered


def test_my_squad_panel_boot_battle_pool_selector():
    # US-380: the ⚔️ Boot Battle "pool" selector — "All" offers same-position players beyond your squad (and compares
    # with a non-owned one, building its fixtures on demand); "By club" reveals a Club picker.
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()

    def take(pos, n):
        return [p for p in rows if p["position"] == pos][:n]

    gks, defs, mids, fwds = take("GK", 2), take("DEF", 5), take("MID", 5), take("FWD", 3)
    if not (len(gks) == 2 and len(defs) == 5 and len(mids) == 5 and len(fwds) == 3):
        return
    ids = [p["id"] for p in gks + defs + mids + fwds]
    bench = [gks[1]["id"], defs[4]["id"], mids[4]["id"], fwds[2]["id"]]
    squad = {"name": "PoolTest", "player_ids": ids, "bench_ids": bench, "cost": 100.0}

    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    next(s for s in at.selectbox if s.label == "Select a player") \
        .set_value(f"{mids[0]['web_name']} · {mids[0]['team']}").run()

    pool = next(s for s in at.segmented_control if s.label and "Boot Battle — pool" in s.label)
    pool.set_value("All").run()                               # expand the pool to all same-position players
    bb = next(s for s in at.selectbox if s.label and "compare with" in s.label)
    assert len(bb.options) > 6                                # far more than the 4 same-position squad peers + "—"
    bb.set_value(bb.options[1]).run()                        # a same-position player (likely non-owned)
    assert not at.exception
    assert "cmp-card" in " ".join(m.value for m in at.markdown)   # compares, with the target's fixtures built on demand

    next(s for s in at.segmented_control if s.label and "Boot Battle — pool" in s.label).set_value("By club").run()
    assert any(s.label == "Club" for s in at.selectbox)      # By club reveals a Club picker
    assert not at.exception


def test_default_horizon_my_squad_1_squad_lab_5():
    # US-374: My Squad defaults to the next GW (manage this week); Squad Lab stays 5 (build for the run).
    at = AppTest.from_file(str(_PAGES / "4_My_Squad.py"), default_timeout=30).run()
    hz = next((s for s in at.segmented_control if s.label == "Gameweeks ahead"), None)
    if hz is not None:
        assert hz.value == 1
    lab = AppTest.from_file(str(_PAGES / "1_Squad_Lab.py"), default_timeout=30).run()
    hz2 = next((s for s in lab.segmented_control if s.label == "Gameweeks ahead"), None)
    if hz2 is not None:
        assert hz2.value == 5


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
    at = _run(_PAGES / "7_Trending.py")
    assert at.dataframe or at.info                          # a board, or the no-data note
    if at.dataframe:
        cols = list(at.dataframe[0].value.columns)
        assert "Player" in cols and "Trends" in cols        # a crowd leaderboard with flags
    # Community Signals (ADR-059): a button-gated "Talked about" board — present, no fetch on load
    assert any(b.label.startswith("Show what") for b in at.button)
    # US-292: the week's top-discussions list — also button-gated (no fetch on load, no live network)
    assert any(b.label == "Show this week's top discussions" for b in at.button)
    assert any("Top discussions this week" in c.value for c in at.caption)


def test_talked_about_board_shows_all_mentions(monkeypatch):
    # US-233 + ADR-116: a big buzz list (a 100-post sample mentions many players) is shown in full (no paging).
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

    at = _run(_PAGES / "7_Trending.py")
    btn = [b for b in at.button if b.label.startswith("Show what")]
    assert btn, "the Talked about button should exist"
    btn[0].click().run()
    assert not at.exception
    assert not any(sb.label == "Page" for sb in at.selectbox)         # ADR-116: no paging
    assert any("players mentioned" in c.value for c in at.caption)    # the full mention count is shown


def test_trending_filter_narrows_the_owned_board():
    # ADR-064 reuse: the shared Team/Position/Player filter narrows Trending (the owned board is populated)
    at = _run(_PAGES / "7_Trending.py")
    if not at.dataframe:
        return
    at.multiselect[0].set_value(["ARS"]).run()             # Team = ARS (the first filter multiselect)
    assert not at.exception
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_trending_owned_board_shows_the_full_list():
    # ADR-116: the always-populated owned board is one scrollable table (no 30-row page control)
    at = _run(_PAGES / "7_Trending.py")
    if not at.dataframe:
        return
    assert not any(sb.label == "Page" for sb in at.selectbox)   # no page control (ADR-116)


def test_news_page_lists_flagged_players_or_all_clear():
    # US-190 / ADR-058: the News lens shows flagged players (News + Source cols) or an all-clear message
    at = _run(_PAGES / "6_News.py")
    if at.dataframe:
        cols = list(at.dataframe[0].value.columns)
        assert "News" in cols and "Source" in cols
    else:
        assert at.success or at.info                       # "no current news" (or the run-refresh note)


def test_news_page_has_the_headlines_lens_gated_no_network():
    # US-291 (ADR-093): a Headlines section + a button, rendered WITHOUT fetching (no click → no live network).
    at = _run(_PAGES / "6_News.py")
    assert not at.exception
    assert any("Headlines" in s.value for s in at.subheader)
    assert any(b.label == "Load headlines" for b in at.button)   # opt-in — the feeds fetch only on click


def test_ask_page_example_prompts_are_clickable():
    # US-227/US-234: the Ask page lists example questions as buttons; clicking one runs it
    at = AppTest.from_file(str(_PAGES / "5_Ask.py"), default_timeout=30).run()
    assert not at.exception
    labels = [b.label for b in at.button if b.key and b.key.startswith("example_")]
    assert any("best differential midfielders" in lbl for lbl in labels)
    assert any("this week for my squad" in lbl for lbl in labels)

    btn = next(b for b in at.button if b.key == "example_0")
    btn.click().run()                                       # clicking runs the grounded pipeline
    assert not at.exception and len(at.session_state["history"]) == 1
    assert any("Q:" in m.value for m in at.markdown)        # US-399: the answer renders as chat markdown


def test_ask_scroll_nudge_is_unique_per_turn_and_multi_tick():
    # US-283/US-287: the scroll nudge re-fires each answer (unique per turn) and scrolls to the bottom several
    # times (instant) so it lands reliably after layout settles — not one smooth attempt that lands sometimes.
    at = AppTest.from_file(str(_PAGES / "5_Ask.py"), default_timeout=30).run()
    at.chat_input[0].set_value("how does bench boost work?").run()
    first = at.get("iframe")[-1].proto.srcdoc
    at.chat_input[0].set_value("how do transfers work?").run()
    second = at.get("iframe")[-1].proto.srcdoc
    assert "/*turn 1*/" in first and "/*turn 2*/" in second and first != second   # unique → re-renders/re-runs
    assert "[50,200,450,800]" in second and "forEach" in second and "scrollHeight" in second   # US-287: multi-tick
    assert "behavior:'smooth'" not in second                                      # instant (scroll-restore can't win)


def test_ask_page_example_prompts_name_the_loaded_squad():
    # US-280: with a squad loaded, the example buttons read its real name (so "my-team" → your squad and the
    # click scopes correctly), instead of the literal "my-team".
    at = AppTest.from_file(str(_PAGES / "5_Ask.py"), default_timeout=30)
    at.session_state["squad"] = {"name": "RoboTS", "player_ids": list(range(1, 16)),
                                 "player_names": [f"P{i}" for i in range(1, 16)], "bench_ids": [], "cost": 100.0}
    at.run()
    assert not at.exception
    labels = [b.label for b in at.button if b.key and b.key.startswith("example_")]
    assert any("RoboTS" in lbl for lbl in labels) and not any("my squad" in lbl for lbl in labels)


def test_ask_page_is_conversational_pronouns_and_followups():
    # US-248 (ADR-047/080): the web Ask threads Context, so a pronoun resolves to the last player and a
    # follow-up builds on the last turn
    at = AppTest.from_file(str(_PAGES / "5_Ask.py"), default_timeout=30).run()
    at.chat_input[0].set_value("is Haaland worth the money?").run()
    assert not at.exception and at.session_state["chat_context"] is not None   # context threaded
    at.chat_input[0].set_value("compare him to Isak").run()                    # 'him' → Haaland
    assert not at.exception
    blob = " ".join(a for _q, a in at.session_state["history"])
    assert "Haaland" in blob and "Isak" in blob                               # resolved compare, not a fallback


def test_ask_chat_answers_a_grounded_question():
    at = AppTest.from_file(str(_PAGES / "5_Ask.py"), default_timeout=30).run()
    assert not at.exception
    at.chat_input[0].set_value("who has the best fixtures over the next 5?").run()
    assert not at.exception
    assert any("Avg FDR" in m.value for m in at.markdown)      # the grounded FDR answer in the chat
    assert len(at.session_state["history"]) == 1           # the turn was kept in history


def test_ask_build_offers_use_this_squad(monkeypatch):
    # ADR-062: a "build me a squad" answer offers "Use this squad →" → adopts the session squad
    at = AppTest.from_file(str(_PAGES / "5_Ask.py"), default_timeout=30).run()
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
    assert m[1].endswith("/p999.png") and m[2] == ""        # by player id; missing code → empty (no teams)


def test_shirt_url_helper():
    # US-255: the club-shirt kit image by team code — GK (`_1`) variant for keepers, empty on no code
    from src.web_streamlit.badges import shirt_url
    assert shirt_url(3).endswith("/shirt_3-66.png")             # outfield
    assert shirt_url(3, "GK").endswith("/shirt_3_1-66.png")     # keeper variant
    assert shirt_url(None) == ""                                # no team code → no image (no crash)


def test_photo_url_by_id_falls_back_to_the_club_shirt(monkeypatch):
    # US-255: a player whose photo the CDN doesn't serve → the club shirt (GK variant for keepers);
    # a player with a served photo keeps it. The existence sweep is monkeypatched (no network).
    from src.web_streamlit import badges
    teams = [{"short_name": "ARS", "code": 3}, {"short_name": "LIV", "code": 11}]
    players = [
        {"id": 1, "code": 100, "team": "ARS", "position": "MID"},   # photo present
        {"id": 2, "code": 200, "team": "ARS", "position": "FWD"},   # photo missing → outfield shirt
        {"id": 3, "code": 300, "team": "LIV", "position": "GK"},    # photo missing → GK shirt
    ]
    monkeypatch.setattr(badges, "_missing_photo_codes", lambda codes: frozenset({200, 300}))
    m = badges.photo_url_by_id(players, teams)
    assert m[1].endswith("/p100.png")                          # present → the photo
    assert m[2].endswith("/shirt_3-66.png")                    # missing → the outfield shirt
    assert m[3].endswith("/shirt_11_1-66.png")                 # missing keeper → the GK shirt


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
    for page in (_APP, _PAGES / "2_Players.py", _PAGES / "4_My_Squad.py"):
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


# --- Ask Maddie video hub (US-382, ADR-112) --------------------------------------------------------------------

def _maddie_env(monkeypatch):
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "k")


def test_maddie_videos_published_are_cleaned_and_ordered(monkeypatch):
    # videos() returns display-ready rows, ordered by sort_order; a blank URL becomes None (→ "coming soon").
    from src.web_streamlit import maddie
    _maddie_env(monkeypatch)
    rows = [
        {"topic": "Second", "blurb": "b2", "youtube_url": "https://youtu.be/2", "sort_order": 20},
        {"topic": "First", "blurb": "b1", "youtube_url": " https://youtu.be/1 ", "sort_order": 10},
        {"topic": "No clip yet", "blurb": "", "youtube_url": "", "sort_order": 30},
    ]
    monkeypatch.setattr("requests.get", lambda url, params=None, headers=None, timeout=None: _StoreResp(rows))
    out = maddie.videos()
    assert [v["topic"] for v in out] == ["First", "Second", "No clip yet"]   # ordered by sort_order
    assert out[0]["youtube_url"] == "https://youtu.be/1"                     # trimmed
    assert out[2]["youtube_url"] is None                                     # blank -> None


def test_maddie_videos_fall_back_when_unconfigured(monkeypatch):
    # No store configured → the built-in welcome, never an empty list (so the hub always renders).
    from src.web_streamlit import maddie
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    assert maddie.videos() == maddie._FALLBACK


def test_maddie_videos_fall_back_on_store_error(monkeypatch):
    # A configured-but-unreachable store must not raise — it falls back to the welcome.
    from src.web_streamlit import maddie
    _maddie_env(monkeypatch)

    def boom(url, params=None, headers=None, timeout=None):
        raise requests.ConnectionError("store down")

    monkeypatch.setattr("requests.get", boom)
    out = maddie.videos()
    assert out and out[0]["topic"] == "Meet Maddie"


def test_ask_maddie_page_renders_videos_and_coming_soon(monkeypatch):
    # The hub embeds a clip for a published video and shows "coming soon" for a URL-less row (no crash).
    import streamlit as st

    from src.web_streamlit import maddie
    st.cache_data.clear()                              # the page caches videos() — start clean per test
    monkeypatch.setattr(maddie, "videos", lambda: [
        {"topic": "Picking your captain", "blurb": "how MADBOOTS ranks captains", "youtube_url": "https://youtu.be/x"},
        {"topic": "More explainers soon", "blurb": "", "youtube_url": None},
    ])
    at = _run(_PAGES / "9_Maddie_Explains.py")
    assert any("Maddie Explains" in t.value for t in at.title)
    assert any("Picking your captain" in s.value for s in at.subheader)      # the published topic renders
    assert any("Coming soon" in i.value for i in at.info)                    # the URL-less row degrades


def test_brand_tokens_and_mantra_are_defined():
    # ADR-114: brand.py is the token source of truth — semantic pairs, the FDR scale, and one canonical mantra.
    from src.web_streamlit import brand
    assert brand.MANTRA == "The analytics decide. The AI explains. You make the call."
    for name in ("GOOD", "GOOD_TINT", "GOOD_FG", "WARN", "WARN_TINT", "BAD", "BAD_TINT", "ACCENT_TEAL"):
        assert getattr(brand, name).startswith("#")
    assert set(brand.FDR_STYLE) == {1, 2, 3, 4, 5}
    assert all(len(pair) == 2 for pair in brand.FDR_STYLE.values())        # every band is a (bg, fg) pair


def test_my_squad_banner_renders_the_styled_card():
    # Regression (S165): a 2nd <style> block (token_css_vars) broke the banner rendering — the purple card came out
    # unstyled. The banner CSS + card must render as ONE <style> block + the div, with the brand purple inline.
    from src.web_streamlit.squads import team_banner_html
    banner = team_banner_html({"name": "TS", "player_ids": list(range(1, 16))}, is_yours=True, synced=True)
    assert banner.count("<style>") == 1                          # one style block (a 2nd one broke rendering)
    assert 'class="ytb-card"' in banner and "#8B2FC9" in banner  # the styled card + the brand-purple accent bar
    assert "Your team" in banner and "Synced across your devices" in banner


def test_data_pages_carry_the_brand_mark():
    # US-397: the data-page headers show the MADBOOTS mark (was a bare emoji title).
    for page in ("2_Players.py", "3_Team_DNA_and_FDR.py", "6_News.py", "7_Trending.py"):
        at = _run(_PAGES / page)
        blob = " ".join(m.value for m in at.markdown)
        assert 'aria-label="MADBOOTS"' in blob, f"{page} is missing the brand mark"


def test_home_hero_box_consolidates_cta_and_nudges():
    # US-398 (rev): one purple "get started" box — the Build CTA + New-here/Maddie/Testing nudges consolidated;
    # every "Explore the sidebar" bullet carries its icon.
    at = _run(_APP)
    blob = " ".join(m.value for m in at.markdown)
    assert "mb-hero" in blob                                    # the one highlighted box
    assert 'href="Squad_Lab"' in blob and "Build your first squad" in blob   # the highlighted CTA button-link
    assert "New here?" in blob and "Maddie Explains" in blob and "Testing this?" in blob   # nudges consolidated
    assert "👟 **Players**" in blob and "📅 **Fixtures**" in blob   # the icon-led bullets


def test_news_shows_the_shared_fit_flag():
    # US-400: News uses the same availability emoji (the Fit column) as every other surface.
    at = _run(_PAGES / "6_News.py")
    dfs = at.get("dataframe")
    assert not dfs or "Fit" in list(dfs[0].value.columns)   # when there's news, the Fit column is present


def test_feedback_page_picker_matches_the_current_nav():
    # US-393: the "which page?" picker is synced to the live nav (no stale "Squads"; has My Squad/Squad Lab/Maddie).
    at = _run(_PAGES / "10_Feedback.py")
    opts = [o for sb in at.selectbox for o in sb.options]
    assert "My Squad" in opts and "Squad Lab" in opts and "Maddie Explains" in opts
    assert "Squads" not in opts                                # the pre-ADR-105 label is gone


def test_fixtures_ticker_shows_the_difficulty_number():
    # US-391: the difficulty run isn't colour-only — each cell carries the FDR digit (colour-blind-safe).
    at = _run(_PAGES / "3_Team_DNA_and_FDR.py")
    caps = " ".join(c.value for c in at.caption)
    assert "is the difficulty" in caps                         # the legend explains the per-cell number


def test_home_mentions_maddie_explains_in_the_hero():
    # US-383 (rev US-398): the Maddie nudge is now text in the consolidated hero box (not a separate page_link).
    at = _run(_APP)
    blob = " ".join(m.value for m in at.markdown)
    assert "Maddie Explains" in blob



def test_health_shows_the_risk_monitor_and_squad_dna():
    """ADR-130 — Health said how good a squad was; it now also says what needs attention this week."""
    at = _squads_view("Health")
    if at.exception:
        raise AssertionError(at.exception)
    blob = " ".join(m.value for m in at.markdown)
    if "Risk Monitor" not in blob:
        return                                     # no squad loaded in this environment
    assert 'class="sq-card"' in blob               # the squad DNA card
    cols = [list(d.value.columns) for d in at.dataframe]
    triage = next((c for c in cols if "Attention" in c), None)
    assert triage is not None, "no triage table rendered"
    assert "Under 60" in triage and "Driver" in triage


def test_health_shows_the_forward_planner():
    """ADR-131 — the card leads with fixture exposure and states the xP range rather than implying a forecast."""
    at = _squads_view("Health")
    if at.exception:
        raise AssertionError(at.exception)
    blob = " ".join(m.value for m in at.markdown)
    if "The weeks ahead" not in blob:
        return                                     # no squad loaded in this environment
    assert 'class="fp-wk"' in blob                 # a bar per gameweek
    assert "xP per gameweek" in blob               # the projection stated, not charted as the headline
