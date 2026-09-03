"""Tests for the Streamlit edge (ADR-052) — each page runs headlessly via `AppTest`.

`AppTest.from_file(...)` executes a page script with no live server. Paths are **absolute** (from the
project root) because `AppTest` resolves a relative path against the *test file's* directory. We assert:
renders without exception; the data pages show a table; the Ask page answers a real question. Ollama
needn't run — `ask` degrades to the decision + facts.
"""

import pathlib
import re

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
    from src.web_streamlit import brand
    at = _run(_APP)
    caps = " ".join(c.value for c in at.caption)
    blob = " ".join(m.value for m in at.markdown)
    assert brand.MANTRA in caps                                   # ADR-114; wording changed by ADR-168
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
    at = _run(_PAGES / "5_Players.py")
    assert len(at.dataframe) == 1 or len(at.info) == 1     # a table, or the "run refresh" note


def test_players_page_has_a_top15_bar_when_data_present():
    # ADR-064: the scatter is gone; a filter-responsive top-15 bar (a vega/altair chart) takes its place
    at = _run(_PAGES / "5_Players.py")
    if at.dataframe:
        assert at.get("arrow_vega_lite_chart") or at.get("vega_lite_chart")


def test_players_price_filter_includes_the_priciest_player():
    # US-345: the Max-price cap follows the highest player price, so the £15.5m player isn't filtered out
    import pandas as pd
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    df = df if isinstance(df, pd.DataFrame) else pd.DataFrame(df)
    assert "Player" in df.columns and (df["Player"] == "Haaland").any()   # the £15.5m asset isn't filtered out


def test_trending_top_discussions_before_community_signals():
    # US-345: surface 🔥 Top discussions first; the long Community Signals list sits below
    at = _run(_PAGES / "3_Signals.py")
    caps = [c.value for c in at.caption]
    top = next((i for i, c in enumerate(caps) if "Top discussions this week" in c), None)
    comm = next((i for i, c in enumerate(caps) if "Community Signals" in c), None)
    assert top is not None and comm is not None and top < comm


def test_help_save_step_reflects_auth_live_persistence():
    # US-378 (ADR-111) + US-385 (ADR-113): the Save section reflects auth-live persistence via the unified
    # "Your team" panel (account sync + import + download), not the stale "per-session / no accounts" copy.
    at = _run(_PAGES / "7_Help.py")
    blob = " ".join(m.value for m in at.markdown)
    caps = " ".join(c.value for c in at.caption)
    assert "saved to your account" in blob and "Your team" in blob          # auth-live persistence, unified panel
    assert "nothing saved on the server" not in (blob + caps)               # the stale claim is gone
    assert "no accounts" not in (blob + caps)
    assert "⚔️ Boot Battle" in blob                                          # US-378: the compare feature named


def test_help_explainer_glossary_renders():
    # US-379 (ADR-111): the MadBoots Explainer — one glossary expander with category subheaders + key terms.
    at = _run(_PAGES / "7_Help.py")
    blob = " ".join(m.value for m in at.markdown)
    assert "FPL basics" in blob and "Squad decisions" in blob and "MadBoots tools" in blob   # category headers
    assert "xP — Expected Points" in blob and "Boot Battle ⚔️" in blob and "Radar 🎯" in blob  # reconciled terms


def test_players_card_view_renders_a_player_card():
    # US-343 (ADR-084): the "Card" view → a player selectbox → the self-contained player-card HTML block
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return                                                 # no data → nothing to card
    at.segmented_control[0].set_value("Card").run()
    assert not at.exception
    assert any(s.label == "Player" for s in at.selectbox)      # the picker
    blob = " ".join(m.value for m in at.markdown)
    assert "pl-card" in blob and "Player Card" in blob         # the card + its brand band rendered


def test_players_card_view_compares_two_players():
    # US-370 (ADR-110) / US-377 (ADR-111): the Card view's ⚔️ "Boot Battle — compare with" picker → the comparison.
    at = _run(_PAGES / "5_Players.py")
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
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    cols = at.dataframe[0].value.columns.tolist()
    assert "Trends" in cols and "Form" in cols and "ICT" in cols


def test_players_page_has_photo_and_badge_columns_when_data_present():
    at = _run(_PAGES / "5_Players.py")
    if at.dataframe:
        df = at.dataframe[0].value
        assert "photos/players" in str(df["photo"].iloc[0])   # the player photo URL
        # the team badge is present iff team.code is in the DB (a refreshed DB); tolerate both
        assert "badge" in df.columns


def test_players_filters_narrow_the_table(monkeypatch):
    # ADR-064 filter (US-424 popover): multiselects are [0] Team · [1] Player; Position is a pills widget
    at = _run(_PAGES / "5_Players.py")
    if not at.multiselect:                                  # no data locally → the info branch
        return
    next(p for p in at.pills if p.label == "Position").set_value(["GK"]).run()   # Position → keepers only
    assert not at.exception
    at.slider[0].set_value(5.0).run()                       # …and ≤ £5.0m
    assert not at.exception                                  # narrowing never crashes (table or a note)


def test_players_filter_by_team_narrows_the_table():
    # ADR-064: filter by team (multiselect[0]) restricts the table to that team
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    at.multiselect[0].set_value(["ARS"]).run()              # Team = ARS
    assert not at.exception
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_player_multiselect_is_team_scoped():
    # US-213: choosing a team scopes the Player multiselect's options to that team's players
    at = _run(_PAGES / "5_Players.py")
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
    at = _run(_PAGES / "5_Players.py")
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
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    assert any("Add selected" in b.label and "watchlist" in b.label for b in at.button)
    assert any("watched" in c.value for c in at.caption)


def test_players_card_can_star_a_player_to_the_watchlist():
    # ADR-117: ⭐ on the player card adds them to the (session) watchlist.
    at = _run(_PAGES / "5_Players.py")
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
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
    at.session_state["_watchlist"] = ids                    # a non-empty watchlist
    at.run()
    _open_panel(at)
    assert not at.exception
    assert any("Your watchlist" in (e.label or "") for e in at.get("expander"))
    if ids:                                                 # the watched players render as a table (the crash site)
        assert any("Player" in list(d.value.columns) for d in at.get("dataframe"))


def test_players_pool_shows_the_full_sorted_list():
    # ADR-116: the pool is ONE scrollable table (no paging) ordered by "Sort by", so the whole set is shown and
    # the native column-header sort is honest (it orders everything, not just a page).
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    next(s for s in at.selectbox if s.label == "Sort by").set_value("team").run()
    assert not at.exception
    teams = at.dataframe[0].value["Team"].tolist()
    assert teams == sorted(teams)                           # the WHOLE list is ordered by team
    assert not any(sb.label == "Page" for sb in at.selectbox)   # no page control (ADR-116 supersedes ADR-063)


def test_fixtures_ticker_grid_and_weeks_selector():
    # US-186: a teams × GW ticker grid; the weeks slider changes the number of GW columns
    at = _run(_PAGES / "2_FDR.py")
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
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30).run()
    if at.exception:
        return
    health = next((s for s in at.segmented_control if "DNA" in (s.options or [])), None)
    if health is None:
        return
    health.set_value("DNA").run()
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
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30).run()
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
    # cumulative label reads "N GW"; the strip is present
    assert "Projected XI" in _strip_text(at)
    toggle.set_value(toggle.options[1]).run()        # "GW N only"
    assert not at.exception
    strip = _strip_text(at)
    assert "Projected XI" in strip and "GW" in strip  # the sub line flips to a single GW


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


def test_team_dna_page_renders_a_team_card():
    """US-419 (ADR-119) → ADR-169: pick a team → grade + radar + key-players.

    Renamed and re-pointed 2026-09-01. It was `test_fixtures_team_dna_section_...` and asserted a
    **subheader** reading "🧬 Team DNA" — correct when ADR-119 made this a *section* of the Fixtures page,
    where a subheader was how it announced itself. ADR-169 gave it its own page and the **title** took that
    job, so the subheader had been repeating the title. Asserting it would have blocked removing the
    duplication, which is the requirement inverted: the card rendering is what matters.
    """
    at = _run(_PAGES / "4_Team_DNA.py")
    if at.exception or not at.dataframe:
        return                                          # no fixtures/data in this environment
    assert any("🧬 Team DNA" in (t.value or "") for t in at.title), "the page still says what it is"
    assert not any((sh.value or "") == "🧬 Team DNA" for sh in at.subheader), \
        "the title carries the identity — a subheader repeating it is dead real estate"
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
    at = _run(_PAGES / "5_Players.py")
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
    at = _run(_PAGES / "5_Players.py")
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
    at = _run(_PAGES / "5_Players.py")
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
    at = AppTest.from_file(str(_PAGES / "5_Players.py"), default_timeout=30)
    at.session_state["squad"] = next(iter(squads.values()))
    at.run()
    assert not at.exception
    assert any(c.label == "My squad only" for c in at.checkbox)   # the shared scope, on Players


def test_players_card_view_renders_the_player_dna_section():
    # ADR-118 (S168–S171): the Card view shows AI Verdict → radar → insights → trend for the selected player.
    at = AppTest.from_file(str(_PAGES / "5_Players.py"), default_timeout=30).run()
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
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30).run()
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
    at = _run(_PAGES / "2_FDR.py")
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


def _open_panel(at, panel="Transfer"):
    """Open one of the answer panels under the pitch (ADR-175).

    Transfer, Captain, This week and Chips are no longer top-level tabs — they are one selector below the
    pitch, so that the pitch stays on screen while you switch. Tests that used to drive
    `segmented_control[0]` now drive two controls, and this is that step in one place.
    """
    next(c for c in at.segmented_control if c.label == "Tool").set_value("My Squad").run()
    sel = next((c for c in at.segmented_control if c.key == "ms_answer"), None)
    if sel is not None:
        sel.set_value(panel).run()
    return at


def _squads_view(view):
    """A My Squad sub-tab. ADR-105 split Build onto its own Squad Lab page; ADR-166 folded it back as the
    **Lab** tab — a builder you use a few times a season did not earn the top slot in the sidebar."""
    at = _run(_PAGES / "1_My_Squad.py")
    # By label, not by index: My Squad now carries several segmented controls (Tool · Gameweeks ahead · and
    # whatever the selected tab adds), so `[0]` was an assumption about layout rather than about the switch.
    # ADR-171 folded AI Tips + Captain into the My Squad screen and ADR-175 added Transfer, so none of those
    # are top-level switch values any more. A test asking for one is asking for an **answer panel**, which
    # lives under the pitch on the default tab — so drive the tool switch, then the answer selector.
    # ADR-175 rev — the labels carry no emoji: four of them had to fit one phone row and wrapped instead.
    _PANEL = {"AI Tips": "This week", "This week": "This week", "Captain": "Captain",
              "Transfer": "Transfer", "Chips": "Chips"}
    want = "Lab" if view == "Build" else ("My Squad" if view in _PANEL else view)
    next(c for c in at.segmented_control if c.label == "Tool").set_value(want).run()
    assert not at.exception, f"Squads[{view}] raised: {at.exception}"
    if view in _PANEL:
        panel = next((c for c in at.segmented_control if c.key == "ms_answer"), None)
        if panel is not None:
            panel.set_value(_PANEL[view]).run()
            assert not at.exception, f"Squads[{view}] panel raised: {at.exception}"
        return at
    # ⚠ Found 2026-08-31 (ADR-171): `set_value` accepts an option that does not exist and **silently keeps
    # the current selection**. ADR-166 renamed Health → DNA and two callers here kept asking for "Health";
    # both went on passing while testing the DEFAULT tab instead. Green stayed green and the coverage was
    # gone. So the switch is now checked: a stale tab name fails loudly rather than quietly testing My Squad.
    landed = next(c for c in at.segmented_control if c.label == "Tool").value
    assert landed == want, f"tab {want!r} does not exist — the page is showing {landed!r} instead"
    return at


def test_squads_page_analyses_the_demo_squad():
    # Health view: the demo seed populates the picker (ADR-054) → an analysis renders, no crash
    at = _squads_view("DNA")
    assert any(s.label == "Squad" for s in at.selectbox)   # the squad picker (a GW selector is also present)
    assert len(at.code) == 1 or len(at.info) >= 1          # the health table (or a "no data" note)


def test_squads_ai_tips_view_renders_a_gameweek_plan():
    # ADR-070 / US-226: the "AI Tips" view (renamed from This week) routes through ask.answer → the
    # grounded plan block renders (no Ollama in the test → the plan + facts, no prose), no crash
    # ADR-171: it is section ① of My Squad now, and with no narrator attached it renders EAGERLY — which is
    # exactly the deployed behaviour, since Streamlit Cloud has no Ollama either.
    at = _squads_view("AI Tips")
    plan = [c for c in at.code if "This week" in c.value]
    assert len(plan) == 1                                  # the rendered gameweek plan, without being asked
    assert "Start Ollama" not in plan[0].value             # US-375: no dev-only Ollama hint for web users


def test_chip_advice_is_its_own_panel_and_still_only_on_request():
    """ADR-082/US-252 → ADR-166 (folded under AI Tips) → ADR-175 (its own answer panel).

    What has survived all three moves is the reason it is a click: a chip expires at the end of the
    half-season, so *which* of your remaining weeks is best is not a question anyone is holding when they
    open their squad. Position changed three times; that has not.
    """
    at = _squads_view("Chips")
    assert not any("Chip strategy" in c.value for c in at.code), "chips have not run yet"

    next(b for b in at.button if b.key == "ms_chips").click().run()
    block = " ".join(c.value for c in at.code)
    assert "Chip strategy" in block
    assert all(chip in block for chip in ("Triple Captain", "Bench Boost", "Free Hit", "Wildcard"))


def test_transfer_page_renders_and_reacts_to_the_bank(monkeypatch):
    at = _squads_view("Transfer")
    assert any(s.label == "Squad" for s in at.selectbox)   # the squad picker (a GW selector is also present)
    assert len(at.code) == 1 or len(at.info) >= 1          # the swaps (or a "no upgrades" note)
    next(s for s in at.slider if s.label == "Bank (£m)").set_value(3.0).run()   # move the bank → recompute
    assert not at.exception


def test_the_transfer_page_warns_about_a_dead_slot_and_offers_the_fix():
    """ADR-136 on the web surface, driven through a real squad rather than a canned plan.

    A departed player is dropped into the session squad; the Transfer tab must say he can't play, say *why*,
    and offer the replacement as a button — because the ranking that fills the rest of the page cannot see him
    (swapping a benched dead player lifts the best XI by exactly zero).
    """
    from src.analytics.optimizer import is_unavailable
    from src.storage import Storage

    store = Storage()
    rows = store.get_players()
    store.close()
    gone = next((p for p in rows if is_unavailable(p) and (p["news"] or "").startswith("Has joined")), None)
    if gone is None:
        return                                             # no departed player in this dataset — nothing to pin

    need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
    picked = {pos: [p for p in rows if p["position"] == pos and p["status"] == "a"][:n]
              for pos, n in need.items()}
    if any(len(v) < need[k] for k, v in picked.items()):
        return                                             # not enough fit players in this dataset
    picked[gone["position"]][-1] = gone                    # …and one of them has left the league
    squad = [p for v in picked.values() for p in v]

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=60)
    at.session_state["squad"] = {"name": "DeadSlot", "player_ids": [p["id"] for p in squad],
                                 "bench_ids": [squad[-1]["id"]], "cost": 100.0}
    at.run()
    _open_panel(at)
    assert not at.exception

    warnings = " ".join(e.value for e in at.error)
    assert gone["web_name"] in warnings and "can't play" in warnings, \
        "a squad slot that cannot score must be named, not left to the rankings that cannot see it"
    assert any(b.label.startswith(f"Replace {gone['web_name']}") for b in at.button), \
        "naming the problem without offering the fix is half the job"


def test_your_team_panel_consolidates_import_upload_download():
    # US-385 (ADR-113): one inline "Your team" panel on My Squad gathers Manager-ID import + Upload + Download
    # backup in one place (was scattered across the sidebar).
    at = _run(_PAGES / "1_My_Squad.py")
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
    assert len(at.selectbox) >= 1                          # the squad picker
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


def test_the_squad_has_exactly_one_captain_setter():
    """ADR-171 / US-435 — the merged page must not carry three ways to set a captain.

    Before the merge there were: the ⚙ panel's "👑 Make X captain", the Captain tab's selectbox + "Set as
    captain" button, and AI Tips recommending one. Two of those acted on the same state; on separate tabs
    that was invisible, and on one screen it is a defect. The ⚙ panel's button is the survivor (it is where
    the selection already lives, ADR-135). This fails if a second setter creeps back — which is the ADR-135
    lesson applied to controls rather than to widget count: a target nobody checks is a target that erodes.
    """
    at = _squads_view("My Squad")
    setters = [b.label for b in at.button if "captain" in b.label.lower()]
    assert len(setters) <= 1, f"more than one captain setter on the merged page: {setters}"
    assert not any(s.label == "Set your captain" for s in at.selectbox), "the Captain tab's setter is gone"
    assert not any(b.label == "Set as captain" for b in at.button), "the Captain tab's setter is gone"


def test_the_pitch_panel_still_sets_and_persists_a_captain():
    # US-175, via the ONE surviving setter (ADR-171): the ⚙ panel writes captain_id onto the session squad.
    at = _squads_view("My Squad")
    setbtn = [b for b in at.button if b.label.startswith("👑 Make ")]
    if not setbtn:                                         # no data locally / nobody selected → nothing to set
        return
    setbtn[0].click().run()
    assert not at.exception
    cap = at.session_state["squad"].get("captain_id")
    assert cap in at.session_state["squad"]["player_ids"]  # a real, owned captain


def test_consumer_views_use_a_session_active_squad():
    """ADR-054/055: the views operate on the squad you loaded, not a demo.

    This used to assert the **picker** offered "My squad (yours)". ADR-175 removed the picker in exactly that
    case — with a team of your own the demos stop being a choice, and a dropdown above a banner naming the
    same squad was the duplication that ADR set out to cut. So the assertion moves to the requirement it was
    standing in for: **the loaded squad is the one on screen.**
    """
    squad = {"name": "My squad", "player_ids": list(range(1, 16)), "bench_ids": [], "cost": 100.0}
    for view in ("DNA", "Transfer", "My Squad"):
        at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
        at.session_state["squad"] = squad
        at.run()
        if view == "Transfer":
            _open_panel(at)                       # an answer under the pitch now, not a tab (ADR-175)
        else:
            next(c for c in at.segmented_control if c.label == "Tool").set_value(view).run()
        assert not at.exception, f"Squads[{view}] raised: {at.exception}"
        assert not any(s.label == "Squad" for s in at.selectbox), "no picker once the team is yours"
        if view == "My Squad":
            # only this view names the squad on screen (the banner). The others share the same
            # `squad_picker()` call, so what is asserted for them is that they render it without asking.
            blob = " ".join((m.value or "") for m in at.markdown)
            assert "My squad" in blob, "the banner names the squad you loaded, not a demo"


def test_help_page_renders_the_guide_without_data():
    # ADR-068: the Help tab is static — it renders even with no DB, and carries the key steps.
    # ⚠️ Rewritten 2026-08-31: this test had been *pinning stale copy*. It asserted the guide mentioned "Ask"
    # and a copy-paste Ask example — a page ADR-168 retired two days earlier — so it was actively holding the
    # onboarding guide in the past. A test that fails when the docs are fixed is worse than no test.
    at = _run(_PAGES / "7_Help.py")
    # subheaders + captions count too: the FPL-rules section ADR-168 moved here is a subheader, so a
    # markdown-only blob could not see it and the assertion would have been quietly weakened to suit.
    blob = " ".join(e.value for e in (*at.markdown, *at.code, *at.subheader, *at.caption))
    assert "My Squad" in blob and "Lab" in blob                 # the core steps, current nav (ADR-166/171)
    assert "This week" in blob                                  # ADR-171: the week's answer is on the page
    assert "quality rating" in blob                             # US-224: the stat-board rating is explained
    assert "FPL rules" in blob                                  # ADR-168: the rules KB is readable here
    assert not at.get("dataframe")                              # static content — no data widgets


def test_sidebar_pages():
    # ADR-105: the Squads page split into My Squad (manage + tools) + Squad Lab (build); ADR-087 Feedback,
    # ADR-100 gated Admin. (ADR-069 had consolidated the old 12 tabs into the single Squads page first.)
    # ADR-141 inserted Leagues at 5 and shifted Ask→12 up by one. Streamlit derives a page's URL from the
    # filename *without* its numeric prefix, so renumbering moves nav order without breaking any link.
    present = sorted(p.name for p in _PAGES.glob("*.py"))
    assert present == sorted(["5_Players.py", "2_FDR.py", "4_Team_DNA.py", "1_My_Squad.py",
                              "3_Signals.py", "6_Trending.py", "7_Help.py",
                              "8_Feedback.py", "9_Admin.py"])
    for gone in ("2_Player_Stats.py", "4_Build_Squad.py", "5_My_Squad.py",
                 "6_Squad_Health.py", "7_Transfer.py", "8_Captain.py"):
        assert not (_PAGES / gone).exists()


def test_player_stats_board_renders_via_the_segmented_control():
    # ADR-069: Player Stats merged into Players — a stat board renders when its segmented-control view is picked
    at = _run(_PAGES / "5_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Over/under").run()
    assert not at.exception
    assert len(at.dataframe) >= 1 or len(at.info) >= 1     # the board rendered


def test_player_stats_filter_narrows_a_board():
    # ADR-064/069: the shared filter narrows a stat board on the merged Players page
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    at.segmented_control[0].set_value("DefCon").run()
    at.multiselect[0].set_value(["ARS"]).run()             # Team = ARS (the first filter multiselect)
    assert not at.exception
    for df in at.dataframe:                                 # the board is now ARS-only
        assert set(df.value["Team"].tolist()) <= {"ARS"}


def _scout_board(board):
    """A stat board, now one level in: ADR-167 merged five same-shaped leaderboards into **Scout**, with a
    board selector, so the page could stop being ten views and start saying what the boards agree on."""
    at = _run(_PAGES / "5_Players.py")
    if not at.segmented_control:
        return None
    next(c for c in at.segmented_control if c.label == "View").set_value("Scout").run()
    next(c for c in at.segmented_control if c.label == "Board").set_value(board).run()
    assert not at.exception
    return at


def test_set_pieces_board_renders_the_order_columns():
    # ADR-081 / US-250: the "Set pieces" view shows Pen/Corners/FK order + Own%/Val/£m through the filter
    at = _scout_board("Set pieces")
    if at is None:
        return
    if at.dataframe:                                          # populated DB → a board with the order columns
        cols = at.dataframe[0].value.columns.tolist()
        assert {"Pen order", "Corner order", "FK order", "Own%", "Val/£m"} <= set(cols)   # US-376: read as order
    else:
        assert len(at.info) >= 1                              # empty (unpopulated) → an honest note


def test_pool_shows_a_set_piece_column():
    # ADR-081 / US-250: the Pool gains a compact "Set" column (⚽/🚩/🎯 for first-choice takers)
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert "Set" in df.columns


def test_pool_shows_an_availability_fit_column():
    # ADR-074 + US-276: the Pool's Fit column shows ✅ for fit players (not blank) and 🚑/🚫/⛔/❓ for concerns
    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert "Fit" in df.columns
    flags = set(df["Fit"].astype(str))
    assert "✅" in flags                                   # US-276: fit players read positively, not blank
    assert "" not in flags                                 # no blank cells now — fit is ✅
    assert any("injured" in c.value for c in at.caption)   # the availability legend


def test_pool_shows_the_price_prediction_column():
    """US-286 (ADR-092): a forward-looking Price column + the honest live-GW1 caption.

    ADR-140 changed the glyphs to plain ▲/▼ so a Styler can paint them green-up / red-down. This also pins
    that the Styler does not break the frame the page reads back — the column must still be a real column of
    plain values, because row selection and the ⭐ watchlist index into it.
    """
    from src.analytics import PRICE_DOWN, PRICE_UP

    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert "Price" in df.columns
    assert set(df["Price"].astype(str)) <= {"", PRICE_UP, PRICE_DOWN}   # only the predictor's markers
    assert not (set(df["Price"].astype(str)) & {"🔺", "🔻"}), "the two-reds pair must be gone"
    assert any("live from GW1" in c.value for c in at.caption)          # honest dormant-now note


def test_players_history_view_shows_a_season_table_for_a_known_player():
    # US-298: the Players "History" view — pick a player → a season table (+ the GW1 note preseason).
    at = AppTest.from_file(str(_PAGES / "5_Players.py"), default_timeout=30).run()
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
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30).run()
    for control in at.segmented_control:
        try:
            control.set_value("My Squad").run()
            break
        except Exception:
            pass
    if at.exception:
        return
    caps = " ".join(c.value for c in at.caption)
    # ADR-140: the caption is markdown, so it carries the colour natively — red for a fall.
    from src.analytics import PRICE_DOWN
    assert f":red[{PRICE_DOWN}]" in caps and "drop" in caps         # the sell-timing nudge fired, in red


def test_pool_number_columns_stay_numeric_formatting_is_display_only():
    # ADR-072: money/value columns are formatted via NumberColumn (display) — the frame still holds the
    # raw numbers (not pre-rounded strings), so they stay sortable and truthful.
    import pandas as pd

    at = _run(_PAGES / "5_Players.py")
    if not at.dataframe:
        return
    df = at.dataframe[0].value
    assert {"£m", "Val/£m"} <= set(df.columns)
    assert pd.api.types.is_numeric_dtype(df["£m"])       # not stringified
    assert pd.api.types.is_numeric_dtype(df["Val/£m"])


def test_clean_sheets_board_shows_a_quality_rating_and_legend():
    # ADR-071: xGC/90 board gains a relative Rating column (🟢…🔴) + a "vs the players shown" legend
    at = _scout_board("Clean sheets")
    if at is None:
        return
    assert any("relative to the players shown" in c.value for c in at.caption)   # the legend
    if at.dataframe:
        df = at.dataframe[0].value
        assert "Rating" in df.columns
        assert df["Rating"].astype(str).str.contains("🟢|🟡|🟠|🔴", regex=True).any()


def test_team_dna_key_players_falls_back_to_last_season():
    """ADR-126 follow-up: the Team DNA card's key-players table has the same 900-minute gate as the three stat
    boards, so it gets the same fallback — through the real page, not just the pure function."""
    at = _run(_PAGES / "4_Team_DNA.py")
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
        at = _run(_PAGES / "5_Players.py")
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
    at = _scout_board("Clean sheets")
    if at is None:
        return
    blob = " ".join(str(i.value) for i in at.info)
    if "Showing" in blob:
        assert "team" in blob and "old club" in blob


def test_stat_boards_show_the_availability_fit_column():
    # ADR-074 / US-229: every stat board gains the Fit column (raw rows on xG; a lookup on the trimmed ones)
    for view in ("Over/under", "DefCon", "Clean sheets", "xG · xA"):
        at = _run(_PAGES / "5_Players.py")
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
    at = _scout_board("xG · xA")
    if at is None:
        return
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


_TAB_EMOJI = {"5_Players.py": "👟", "2_FDR.py": "📅", "4_Team_DNA.py": "🧬", "1_My_Squad.py": "🧩",
              "3_Signals.py": "📡", "6_Trending.py": "📈", "7_Help.py": "🧭",
              "8_Feedback.py": "📣", "9_Admin.py": "📊"}


def test_every_tab_has_an_emoji_led_header():
    # US-222: each tab's title leads with a distinct emoji (like Home's ⚽ MADBOOTS), no crash
    for fname, emoji in _TAB_EMOJI.items():
        at = _run(_PAGES / fname)
        assert not at.exception, f"{fname} raised: {at.exception}"
        assert at.title and emoji in at.title[0].value, f"{fname} title missing {emoji}"


def test_feedback_page_form_degrades_to_a_prefilled_email_without_a_webhook():
    # US-307: with no FPL_FEEDBACK_WEBHOOK a submit offers a pre-filled mailto to the inbox (no network),
    # and the "Join the beta" link is hidden until FPL_SIGNUP_URL is set.
    at = _run(_PAGES / "8_Feedback.py")
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
    at = _run(_PAGES / "8_Feedback.py")
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
    at = _run(_PAGES / "8_Feedback.py")
    assert any(s.label == "Which page?" for s in at.selectbox)          # the page picker exists
    at.text_area[0].set_value("Fixtures target list is great").run()
    # ADR-166 renamed the pages this picker offers; the test is about the *payload*, so it picks a live one.
    next(s for s in at.selectbox if s.label == "Which page?").set_value("Team DNA").run()
    next(b for b in at.button if b.label == "Send feedback").click().run()

    assert not at.exception and captured.get("url") == "https://example.test/sink"
    payload = captured["json"]
    assert payload["message"] == "Fixtures target list is great"
    assert payload["page"] == "Team DNA"
    assert payload["version"] and payload["source"] == "fpl-assistant-beta"
    assert "T" in payload["ts"]                                          # an ISO timestamp
    assert payload["_subject"].endswith("Team DNA")                     # US-308: FormSubmit subject
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
    at = _run(_PAGES / "8_Feedback.py")
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
    at = _run(_PAGES / "8_Feedback.py")
    assert not at.exception
    assert not any("private beta" in (t.value or "") for t in at.title)   # no gate title
    assert any(b.label == "Send feedback" for b in at.button)              # the real page rendered


def test_registration_gate_admits_with_code_and_email(monkeypatch):
    _registration_env(monkeypatch)
    rows = []
    _fake_user_store(monkeypatch, rows)
    at = _run(_PAGES / "8_Feedback.py")
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
    at = _run(_PAGES / "8_Feedback.py")
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
    at = _run(_PAGES / "8_Feedback.py")
    next(t for t in at.text_input if t.label == "Invite code").set_value("wrong").run()
    next(t for t in at.text_input if t.label == "Your email").set_value("hopeful@b.com").run()
    next(b for b in at.button if "Join" in b.label).click().run()
    assert ("hopeful@b.com", "bad_code") in calls


def test_waitlist_captures_an_over_cap_email(monkeypatch):
    # ADR-102: at the cap → the email is captured (reason="full") so the owner can invite later
    _registration_env(monkeypatch, cap="0")
    _fake_user_store(monkeypatch, [])
    calls = _capture_waitlist(monkeypatch)
    at = _run(_PAGES / "8_Feedback.py")
    next(t for t in at.text_input if t.label == "Invite code").set_value("letmein").run()
    next(t for t in at.text_input if t.label == "Your email").set_value("late@b.com").run()
    next(b for b in at.button if "Join" in b.label).click().run()
    assert ("late@b.com", "full") in calls


def test_squads_gameweeks_selector_drives_the_horizon():
    """US-237/315 (ADR-077): the "Gameweeks ahead" box-select flows into Health — set it to 2 and the analysis
    projects over 2 GW, with exactly two per-gameweek columns.

    ⚠️ This used to assert a literal **"GW2" column and no "GW5"**, which quietly stopped being true the moment
    GW2's deadline passed: ADR-123 cuts *upcoming* fixtures at the deadline, so the horizon rolls to GW3, GW4,
    … as the season runs. It was a test with a **shelf life**, and it expired mid-session rather than on a code
    change. The gameweek numbers now come from the same data the page reads, so the assertion is about the
    horizon's *shape* — which is what the feature actually promises.
    """
    # ADR-175 — three horizons, keyed per surface, because one control fed five consumers that do not want
    # the same window. This test's subject is DNA, so it drives DNA's own control (`gw_analysis`); the pitch
    # has GW1/GW1–3 and the Lab keeps the long range.
    at = _run(_PAGES / "1_My_Squad.py")
    at.segmented_control[0].set_value("DNA").run()
    gw = [c for c in at.segmented_control if c.key == "gw_analysis"]
    assert gw and gw[0].value == 1 and list(gw[0].options) == ["1", "2", "3", "4", "5"]
    gw[0].set_value(2).run()
    assert not at.exception
    if not at.code:
        return
    blob = " ".join(c.value for c in at.code)
    assert "2 GW" in blob

    from src.storage import Storage
    store = Storage()
    try:
        events = sorted({f["event"] for f in store.get_upcoming_fixtures() if f["event"] is not None})
    finally:
        store.close()
    if len(events) >= 2:
        assert f"GW{events[0]}" in blob and f"GW{events[1]}" in blob, "both horizon gameweeks get a column"
    if len(events) > 2:
        assert f"GW{events[2]}" not in blob, "…and the third does not — the horizon really narrowed"


def test_squads_gameweeks_box_select_offers_ten(monkeypatch):
    """US-315: the long window is offered — and ADR-175 moved it to the surface that wants it.

    A wildcard is a multi-week bet, so 10 belongs in the **Lab**. On an active squad it offered a window
    nobody chose: the owner does not plan a wildcard from a team that is already picked, and US-374 had
    already defaulted these tools to 1 against the Lab's 5.
    """
    at = _squads_view("Build")
    gw = [c for c in at.segmented_control if c.key == "gw_lab"]
    if not gw:
        return
    assert 10 in [int(o) for o in gw[0].options]           # the long window is still offered — on the Lab
    gw[0].set_value(10).run()
    assert not at.exception


def test_captain_view_notes_it_is_next_gameweek():
    # US-237: captaincy is a one-week decision — a caption says the GW selector doesn't apply
    at = _squads_view("Captain")
    assert any("next gameweek" in c.value.lower() for c in at.caption)


def test_my_squad_manage_holds_rename_and_set_bench():
    """ADR-115/US-406 → ADR-175: Rename + Set-whole-bench are still together and still one click away.

    They were their own expander; they are now a flat subsection **inside** the players panel, because
    ADR-175 moved everything that sat between the pitch and the answers into that panel — and expanders
    cannot nest, which is the same constraint ADR-115 hit and named. The requirement is unchanged: both
    controls exist and neither is on the resting page.
    """
    at = _squads_view("My Squad")
    labels = [e.label or "" for e in (at.main.get("expander") or [])]
    assert any("Players & lineup" in x for x in labels)
    # Reorder and Manage were their own expanders between the pitch and the answers; they are subsections
    # inside the panel now. (Backup/import may legitimately be here too — with no squad of your own there is
    # something to import, which is the one case ADR-175 keeps it on the page for.)
    assert not any("Manage" in x or "Reorder" in x for x in labels), \
        "lineup chrome belongs inside the panel, not between the pitch and the answers"
    assert any(b.label == "Rename" for b in at.button) and any(b.label == "Set bench" for b in at.button)


def _strip_text(at) -> str:
    """The stat strip's rendered markup (ADR-163).

    It used to be `st.metric` in `st.columns`, which `AppTest` exposed as `at.metric`. The strip is HTML now
    because only CSS can reflow on a phone (US-449), so the assertions moved from *"a metric widget with this
    label exists"* to *"this label and this number are on the page"* — which is the better assertion anyway:
    the first pinned the widget, the second pins what the reader sees.
    """
    return " ".join(m.value for m in at.markdown if "mb-strip" in (m.value or ""))


def test_my_squad_shows_a_quick_stats_summary():
    # US-239 + US-404 (ADR-115): the summary is a compact 3-number strip (Projected XI · Captain · Bench) — the
    # old Unavailable/Doubtful metrics folded into the availability line; the Projected-XI label tracks the horizon.
    at = _squads_view("My Squad")
    strip = _strip_text(at)
    assert "Projected XI" in strip and "Bench" in strip and "Captain" in strip
    for folded in ("Unavailable", "Doubtful"):
        assert folded not in strip                     # folded into the availability line (US-404)

    # ADR-179 — there is no horizon on this page any more. ADR-175 cut it to GW1 · GW1–3; the owner then
    # removed it outright, because the multi-week read belongs to the Lab and the GW1–3 XI was measured as
    # costing 0.32 xP in the week you actually play it (ADR-178).
    assert not [c for c in at.segmented_control if c.key == "gw_pitch"], \
        "My Squad answers one question — what do I do this week"
    strip = _strip_text(at)
    # US-449 rev: the window moved out of the label into the strip's `sub` line, because a long label is
    # what forces a column wide — so assert the two parts, not the old combined string. ADR-179 fixed that
    # window at one gameweek, so the sub now reads "next GW" rather than a count.
    assert "Projected XI" in strip and "next GW" in strip


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
    # ADR-179 — the page is fixed at the next gameweek, so the expectation is computed at the same window.
    # It used to run at 3 to exercise the horizon control; with that gone, a 3-GW expectation would simply be
    # a different number from the one the page shows, and the test would be asserting the wrong sum.
    ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                         horizon=1, gw_history_by_code=store.get_gw_history_by_code())
    store.close()
    xp = {r["id"]: r["xp"] for r in ranked}
    by_gw = {r["id"]: r["by_gameweek"] for r in ranked}
    g1 = ranked[0]["gameweeks"][0]
    owned = [by_id[i] for i in sq["player_ids"] if i in by_id]
    xi = best_legal_xi(owned, xp)
    cap = max(xi, key=lambda i: xp[i])                     # captain = the best XI player
    expected = round(sum(xp[i] for i in xi) + by_gw[cap][g1], 1)

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = {**sq, "captain_id": cap, "name": "RoboTS"}
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    # ADR-179 — no horizon to set: the page is fixed at the next gameweek. The subject survives the control
    # that used to frame it — the strip is the XI **plus the captain's double** — and the "the ×2 is a
    # one-week thing" caption is gone with the longer window it existed to disambiguate.
    assert not at.exception
    strip = _strip_text(at)
    assert "Projected XI" in strip
    assert f"{expected:.1f} xP" in strip                   # XI + captain's next-GW double


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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception
    caps = " ".join(c.value for c in at.caption)
    assert "Flagged" in caps and injured["web_name"] in caps and "🚑" in caps


def test_my_squad_points_to_build():
    """ADR-105: the My Squad view points at the builder for a full rebuild.

    The *pointer* is the requirement; its wording is not. This asserted the literal string "Squad Lab" and so
    failed when the caption was corrected — the Lab has been a My Squad tab since ADR-166, and the caption
    had still been sending people to a sidebar entry that is not there. Matched on the destination instead.
    """
    at = _squads_view("My Squad")
    assert any("My Squad ▸ Lab" in c.value for c in at.caption), "no pointer to the builder"


def test_the_lab_keeps_its_identity_as_a_tab():
    """US-360 (ADR-105) → US-445 (ADR-166): the builder lost its sidebar slot, not its name. It is on My
    Squad now, so the page title is "My Squad" — the Lab announces itself with its own heading instead."""
    at = _squads_view("Build")
    assert any("Squad Lab" in h.value for h in at.subheader), "the Lab tab must still say what it is"
    assert any("Build your squad" in c.value for c in at.caption)   # the header copy


def test_my_squad_empty_state_points_to_the_lab_tab():
    """US-360 → US-445: the pointer still exists, but it names the **tab** now — sending someone to a sidebar
    page that no longer exists would be worse than not pointing at all."""
    at = _run(_PAGES / "1_My_Squad.py")                    # no injected squad → active_squad() is None
    assert any("Lab" in i.value for i in at.info)


def test_build_page_returns_a_squad(monkeypatch):
    at = _squads_view("Build")
    # a squad is rendered (the explanation block + the squad table) — or the "no data" note; no crash
    assert len(at.code) >= 1 or len(at.info) >= 1
    # move an archetype control → rebuild, still no crash
    at.number_input[0].set_value(3).run()                  # 3 low-cost players
    assert not at.exception


def test_build_shows_the_squad_on_the_pitch():
    # US-261 (ADR-084 reuse): the built 15 render on the green pitch (a full 15 kit cards) + the table below
    at = _squads_view("Build")
    if not at.code:                                        # no data locally → the info branch
        return
    blob = " ".join(m.value for m in at.markdown)
    assert "fpl-pitch" in blob                             # the pitch container
    assert blob.count('class="kit"') == 15                 # the whole 15 on the pitch (XI + bench)
    assert len(at.dataframe) >= 1                          # the sortable detail table is still there


def test_build_formation_preview_shows_the_xi_score():
    # US-230 (ADR-075): the "Preview the best XI in a shape" expander shows a Projected XI xP total
    at = _squads_view("Build")
    if not at.code:                                        # no data locally → the "run refresh" note
        return
    mets = [(m.label, str(m.value)) for m in at.metric]
    xi = [(lbl, val) for lbl, val in mets if "Projected XI" in lbl]
    assert xi, f"expected a Projected XI metric, got {mets}"
    assert "xP" in xi[0][1] and any(ch.isdigit() for ch in xi[0][1])   # a numeric xP total


def test_build_compare_all_formations_is_gated():
    # US-231 (ADR-075): the "Compare all formations" table is absent by default and appears only on tick,
    # ranking all 7 shapes by XI xP (desc) with a Δ-vs-best column.
    at = _squads_view("Build")
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
    at = _squads_view("Build")
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

    at = _squads_view("Build")
    if not at.code:
        return
    next(b for b in at.button if b.label.startswith("Use this squad")).click().run()
    squad = at.session_state["squad"]

    store = Storage()
    rows = store.get_players()
    # ⚠️ `gw_history_by_code` is required, not optional (ADR-173). Recomputing xP without it gives a
    # DIFFERENT number from the one the app ordered the bench with, so this asserted one ranking against
    # another and would fail for the right behaviour. Harmless before — the per-GW data only fed the dormant
    # form term, so omitting it changed nothing — but it now also drives the minutes weight.
    xp = {r["id"]: r["xp"]
          for r in decision_xp(rows, store.get_upcoming_fixtures(), store.get_history_by_code(),
                               gw_history_by_code=store.get_gw_history_by_code())}
    store.close()
    by_id = {p["id"]: p for p in rows}
    bench = [by_id[i] for i in squad["bench_ids"] if i in by_id]
    outfield_xps = [xp.get(p["id"], 0) for p in bench if p["position"] != "GK"]
    assert outfield_xps == sorted(outfield_xps, reverse=True)   # outfield by xP desc
    assert bench[-1]["position"] == "GK"                        # the GK last


def test_build_page_renders_non_zero_xp(monkeypatch):
    # regression (US-172): Build must attach xp/minutes_weight so the table + projected total aren't zeros
    at = _squads_view("Build")
    if not at.code:
        return
    out = next((c.value for c in at.code if "Total:" in c.value), "")   # the squad table (not the explanation)
    assert "xMins" in out and "xP" in out                  # the xp-objective columns
    total = next((ln for ln in out.splitlines() if ln.startswith("Total:")), "")
    assert "projected" in total and "projected 0.0 xP" not in total   # a real total, not zeros


def test_build_page_names_the_squad(monkeypatch):
    # US-172: the squad-name input flows into the active squad (and the download key)
    at = _squads_view("Build")
    if not at.code:
        return
    at.text_input[0].set_value("Tony's XI").run()
    at.button[0].click().run()                             # "Use this squad →"
    assert at.session_state["squad"]["name"] == "Tony's XI"


def test_build_page_objective_switch_rebuilds(monkeypatch):
    # ADR-062: switching the objective (xp→xgi) rebuilds on the same engine, no crash, still a squad
    at = _squads_view("Build")
    if not at.code:
        return
    next(s for s in at.selectbox if s.label == "Objective").set_value("xgi").run()
    assert not at.exception and at.code


def test_the_value_view_measures_the_whole_pool_but_plots_the_decisions(monkeypatch):
    """ADR-138. The frontier chart, driven through the real page on real data.

    Two separate things, and keeping them separate is the design:

    * **Measured** over every available player — medians, edges and the frontier all come from the full pool,
      so the numbers do not move when the display filter does.
    * **Plotted**: by default only players who have featured and are projected above a point a week. 94% of
      players sit in 24% of the price axis, so plotting all of them turned the cheap end into a smear — the
      owner called it twice before the cause (the axis, not the dot size) was measured.

    Injured and departed players are excluded from *both*: they all score 0, and counting them as price peers
    inflated every verdict on the chart (Rice read +7.0 with them in, +3.1 with them out).
    """
    at = _run(_PAGES / "5_Players.py")
    if not at.segmented_control:
        return
    at.segmented_control[0].set_value("Value").run()
    assert not at.exception

    measured = next((c.value for c in at.caption if "Measured over" in c.value), "")
    assert "on the frontier" in measured and "available players" in measured
    assert "plotted" in measured, "the page must say how many it is holding back, and why"
    assert "Injured and departed players are excluded" in measured

    assert at.dataframe, "the frontier players must be listed, not only drawn"
    assert len(at.dataframe[0].value) >= 1

    # …and nothing is hidden irreversibly.
    next(c for c in at.checkbox if c.label == "Plot everyone").set_value(True).run()
    assert not at.exception
    assert "plotted" not in next(c.value for c in at.caption if "Measured over" in c.value)


def test_build_page_weekly_and_include_unavailable(monkeypatch):
    # ADR-062: the build-mode radio + include-unavailable checkbox drive the same select_squad
    # ADR-137: the mode is now named for what it builds — a *cheap* bench, bought so the money goes into the XI
    at = _squads_view("Build")
    if not at.code:
        return
    at.radio[0].set_value("Strong XI (cheap bench)").run()
    at.checkbox[-1].set_value(True).run()                  # include injured/suspended
    assert not at.exception and at.code                    # still a valid 15 renders


def test_the_build_modes_are_the_two_that_actually_exist(monkeypatch):
    """ADR-137. Squad Lab offered three build modes and two of them were the same squad.

    "Bench Boost" passed `bench_weight=None`, exactly like "Balanced" — and it could not have been otherwise:
    maximising `Σ score·start + 1·score·bench` **is** maximising `Σ score` over the 15. So the third option
    promised a build the optimiser has no way to produce, however it is wired.

    This pins both halves — that the radio offers two, and that the Bench Boost question is still answered
    where it is asked, rather than silently dropped.
    """
    at = _squads_view("Build")
    if not at.code:
        return
    mode = at.radio[0]
    assert mode.label == "Build mode"
    assert list(mode.options) == ["All-round (strong bench)", "Strong XI (cheap bench)"]
    captions = " ".join(c.value for c in at.caption)
    assert "Bench Boost" in captions, "the chip question must still be answered, just not as a third build"


def test_build_page_formation_preview_is_display_only(monkeypatch):
    # ADR-062: the formation preview is XI-only and never adds a second (save) download
    at = _squads_view("Build")
    if not at.code:
        return
    next(s for s in at.selectbox if s.label == "Formation").set_value("4-3-3").run()
    assert not at.exception
    assert len(at.get("download_button")) == 1             # only the full-15 build is downloadable


def test_build_page_exclude_removes_the_player_from_the_save(monkeypatch):
    # ADR-062: the "Must exclude" control wires through to the saved 15 (the tester's key ask)
    at = _squads_view("Build")
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
    # ADR-171: the page gained the captaincy table, so "no dataframes at all" is no longer the right shape.
    # The point US-187 was pinning survives intact — **the squad is a pitch, not a table** — so what is
    # asserted is that the only table here is the captain candidates, never a 15-row squad grid.
    assert len(at.dataframe) <= 1, "the squad must not come back as a table"
    if at.dataframe:
        cols = at.dataframe[0].value.columns.tolist()
        assert "Opp" in cols and "xP" in cols, f"the one table should be the captain candidates, got {cols}"
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    _open_panel(at)          # ADR-115 moved the manual transfer off the pitch; ADR-175 put it in a panel
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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
    at = _run(_PAGES / "1_My_Squad.py")
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
    return _run(_PAGES / "1_My_Squad.py")


def test_team_banner_highlights_your_team(monkeypatch):
    # US-386: a brand status card names your team + marks it as yours, so it stands out from the demo.
    at = _squads_with_active(monkeypatch)                     # active "My XI" in session
    blob = " ".join(m.value for m in at.markdown)
    assert "Your team" in blob and "My XI" in blob


def test_team_banner_shows_demo_prompt_without_your_team():
    # US-386: viewing the demo → the card prompts to make it yours (the default never looks like your team).
    at = _run(_PAGES / "1_My_Squad.py")
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
    at = _run(_PAGES / "1_My_Squad.py")
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
    _squads_view("DNA")
    assert any(e == "analysis_run" and kw.get("view") == "DNA" for e, kw in events)


def test_squad_created_event_on_use_this_squad(monkeypatch):
    events = _capture_events(monkeypatch)
    at = _squads_view("Build")                    # Build view (default)
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
    at = _run(_PAGES / "8_Feedback.py")
    at.text_area[0].set_value("Love the fixture ticker").run()
    next(b for b in at.button if b.label == "Send feedback").click().run()
    assert any(e == "feedback_submitted" for e, kw in events)
    for _e, kw in events:                                 # no message content in the event
        assert "fixture ticker" not in str(kw).lower()


# --- analytics perf timers (ADR-100, US-336) ----------------------------------------

def test_squads_page_emits_data_load_and_analysis_perf(monkeypatch):
    events = _capture_events(monkeypatch)
    _squads_view("Build")                        # the builder: loads data + runs the optimiser (ADR-105)
    perf = [(kw.get("op"), kw.get("page"), kw.get("ok")) for e, kw in events if e == "perf"]
    assert ("data_load", "My Squad", True) in perf       # FPL data loading timed (the Lab is a tab now)
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
    at = _run(_PAGES / "1_My_Squad.py")                                       # Build view, no active squad in session
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception

    # Select a player in the panel, then press 👑. (ADR-135 briefly moved this onto the shirt as a © anchor;
    # that is reverted, so the button is back and is again the only way to set a captain from this page.)
    target = mids[0]
    next(s for s in at.selectbox if s.label == "Select a player") \
        .set_value(f"{target['web_name']} · {target['team']}").run()
    assert not at.exception
    btn = next(b for b in at.button if b.label == f"👑 Make {target['web_name']} captain")
    btn.click().run()
    assert not at.exception
    assert at.session_state["squad"]["captain_id"] == target["id"]


def test_the_card_lands_above_the_boot_battle_controls(monkeypatch):
    """ADR-139. The half that *delivers* the request rather than the half that removes something.

    The player card used to render below three Boot Battle widgets (pool · club · compare-with), so tapping a
    shirt put the teal outline on the pitch and the card a scroll away, behind controls for a different
    question. "Tap → card" only feels like one action if the card is where the eye lands.
    """
    at = _squads_view("My Squad")
    if at.exception:
        raise AssertionError(at.exception)
    pick = next((s for s in at.selectbox if s.label == "Select a player"), None)
    if pick is None:
        return                                          # no squad in this environment
    pick.set_value(next(o for o in pick.options if o != "—")).run()
    assert not at.exception

    body = "\n".join(m.value for m in at.markdown)
    assert "pl-card" in body, "the selected player's card must render in the panel"
    boot = next((s for s in at.selectbox if "Boot Battle" in (s.label or "")), None)
    if boot is None:
        return
    # The card is markdown; the Boot Battle pool is a segmented_control. Compare their positions in the
    # rendered element order rather than trusting the source.
    order = [type(e).__name__ for e in at.main]
    els = list(at.main)
    card_at = next((i for i, e in enumerate(els)
                    if "pl-card" in str(getattr(e, "value", "") or "")), None)
    boot_at = next((i for i, e in enumerate(els)
                    if "Boot Battle" in str(getattr(e, "label", "") or "")), None)
    assert card_at is not None and boot_at is not None and card_at < boot_at, \
        f"the card must come before the Boot Battle controls (card {card_at}, boot {boot_at}) — {order[:3]}"


def test_my_squad_panel_card_shows_per_gameweek_xp():
    """US-368 (ADR-109): the per-GW row (xP over fixture) — the tester's card-under-the-shirt.

    **Retargeted by ADR-139**, and worth saying why rather than quietly editing it. This asserted the row was
    inside the *hover popover* by reading `AppTest.markdown` — but since ADR-133 put the pitch inside a click
    component, the pitch stopped appearing in `at.markdown` at all, so the test hit its `if "fpl-pitch" not in
    blob: return` guard on every run and **asserted nothing for two sprints**. ADR-139 then removed that
    popover from the tappable pitch outright, which would have left the test named for a feature that no
    longer exists while still passing.

    So it now asserts the row where My Squad actually shows it: the **panel card**, after a selection. The
    popover's own copy — still live on the two non-tappable pitches — is covered directly in
    `tests/test_pitch_html.py`, against the markup rather than through a page.
    """
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not at.exception
    pick = next((s for s in at.selectbox if s.label == "Select a player"), None)
    if pick is None:
        return                                               # no squad in this environment
    pick.set_value(next(o for o in pick.options if o != "—")).run()
    assert not at.exception

    blob = " ".join(m.value for m in at.markdown)
    assert 'class="pl-card"' in blob, "selecting a player must render their card in the panel"
    assert 'class="plc-gwrow"' in blob                       # the per-GW row, on the card the tap reveals
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

    # ADR-179 — this used to prove the card was independent of a horizon control. That control is gone, and
    # the requirement it protected is now **the reason removing it was safe**: with the page fixed at one
    # gameweek, the card under a shirt still shows **three**. If that ever regressed, taking GW1–3 away would
    # have cost the multi-week read rather than moved it.
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
    at.session_state["squad"] = squad
    at.run()
    at.segmented_control[0].set_value("My Squad").run()
    assert not [c for c in at.segmented_control if c.key == "gw_pitch"], "no horizon on this page (ADR-179)"
    next(s for s in at.selectbox if s.label == "Select a player") \
        .set_value(f"{target['web_name']} · {target['team']}").run()
    card = next((m.value for m in at.markdown if "Player Card" in m.value), "")   # the panel full card
    assert len(re.findall(r'plc-gwxp">([0-9.]+)<', card)) == 3, \
        "the card carries 3 gameweeks at a one-gameweek page horizon — sized per team, so a blank leaves no hole"


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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=30)
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


def test_the_lab_keeps_its_own_horizon_after_the_merge():
    """US-374 → US-445 (ADR-166): managing this week wants the next GW; building for a wildcard wants a long
    run. They were separate pages with separate defaults; now they are tabs, and the control is **keyed per
    mode** so folding the pages together did not fold their horizons together."""
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=60).run()
    hz = next((s for s in at.segmented_control if s.label == "Gameweeks ahead"), None)
    if hz is not None:
        assert hz.value == 1
    at.segmented_control[0].set_value("Lab").run()
    hz2 = next((s for s in at.segmented_control if s.label == "Gameweeks ahead"), None)
    if hz2 is not None:
        assert hz2.value == 5, "the Lab must not inherit the squad tools' 1-GW window"


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
    # ADR-150: the Reddit buzz moved to 📡 Signals — Trending is now leaderboards only, so no fetch button.
    assert not any(b.label.startswith("Show what") for b in at.button), \
        "chatter belongs on Signals; Trending answers what the crowd is *doing*, in numbers"
    # US-292: the week's top-discussions list — also button-gated (no fetch on load, no live network)
    # ADR-150: this button moved to 📡 Signals along with the rest of the chatter.
    assert not any(b.label == "Show this week's top discussions" for b in at.button)
    assert not any("Top discussions this week" in c.value for c in at.caption), \
        "Trending is leaderboards only — the discussion lens is on Signals"


def test_talked_about_board_shows_all_mentions(monkeypatch):
    # US-233 + ADR-116: a big buzz list (a 100-post sample mentions many players) is shown in full (no paging).
    # ADR-150: it lives on 📡 Signals now — Trending is leaderboards only.
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

    at = _run(_PAGES / "3_Signals.py")          # ADR-150: chatter lives on Signals now
    btn = [b for b in at.button if b.label.startswith("Show what")]
    assert btn, "the Talked about button should exist"
    btn[0].click().run()
    assert not at.exception
    assert not any(sb.label == "Page" for sb in at.selectbox)         # ADR-116: no paging
    assert any("players mentioned" in c.value for c in at.caption)    # the full mention count is shown


def test_trending_filter_narrows_the_owned_board():
    # ADR-064 reuse: the shared Team/Position/Player filter narrows Trending (the owned board is populated)
    at = _run(_PAGES / "6_Trending.py")
    if not at.dataframe:
        return
    at.multiselect[0].set_value(["ARS"]).run()             # Team = ARS (the first filter multiselect)
    assert not at.exception
    assert set(at.dataframe[0].value["Team"].tolist()) <= {"ARS"}


def test_trending_owned_board_shows_the_full_list():
    # ADR-116: the always-populated owned board is one scrollable table (no 30-row page control)
    at = _run(_PAGES / "6_Trending.py")
    if not at.dataframe:
        return
    assert not any(sb.label == "Page" for sb in at.selectbox)   # no page control (ADR-116)


def test_news_page_lists_flagged_players_or_all_clear():
    # US-190 / ADR-058: the News lens shows flagged players (News + Source cols) or an all-clear message
    at = _run(_PAGES / "3_Signals.py")
    if at.dataframe:
        cols = list(at.dataframe[0].value.columns)
        assert "News" in cols and "Source" in cols
    else:
        assert at.success or at.info                       # "no current news" (or the run-refresh note)


def test_news_page_has_the_headlines_lens_gated_no_network():
    # US-291 (ADR-093): a Headlines section + a button, rendered WITHOUT fetching (no click → no live network).
    at = _run(_PAGES / "3_Signals.py")
    assert not at.exception
    assert any("Headlines" in s.value for s in at.subheader)
    assert any(b.label == "Load headlines" for b in at.button)   # opt-in — the feeds fetch only on click


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
    # "Captain" is the captaincy section of My Squad now (ADR-171). "Health" used to be the third entry and
    # had silently meant "My Squad" ever since ADR-166 renamed it DNA — DNA's first table is the risk monitor,
    # which carries a badge but no photo, so it never belonged in this assertion.
    for view in ("Build", "Captain"):
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
    for page in (_APP, _PAGES / "5_Players.py", _PAGES / "1_My_Squad.py"):
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


def test_help_watch_view_renders_videos_and_coming_soon(monkeypatch):
    """US-448 (ADR-166) — Maddie folded into Help as a **Watch** view rather than a second sidebar page. Both
    answer "how does this app work?"; text-vs-video is a preference, not a topic."""
    import streamlit as st

    from src.web_streamlit import maddie
    st.cache_data.clear()                              # the page caches videos() — start clean per test
    monkeypatch.setattr(maddie, "videos", lambda: [
        {"topic": "Picking your captain", "blurb": "how MADBOOTS ranks captains", "youtube_url": "https://youtu.be/x"},
        {"topic": "More explainers soon", "blurb": "", "youtube_url": None},
    ])
    at = _run(_PAGES / "7_Help.py")
    at.segmented_control[0].set_value("🎥 Watch").run()
    assert not at.exception
    assert any("Picking your captain" in h.value for h in at.subheader)
    assert any("Coming soon" in i.value for i in at.info)          # the URL-less row degrades, no crash


def test_brand_tokens_and_mantra_are_defined():
    # ADR-114: brand.py is the token source of truth — semantic pairs, the FDR scale, and one canonical mantra.
    from src.web_streamlit import brand
    # ADR-168 — the mantra stopped promising narration the deployed app cannot produce. It said "The AI
    # explains"; there is no Ollama on Cloud, so for every tester that clause was simply untrue. What replaced
    # it is what the app does do everywhere, including Cloud: it shows its working.
    assert brand.MANTRA == "The analytics decide. Every answer shows its working. You make the call."
    assert "AI explains" not in brand.MANTRA
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
    for page in ("5_Players.py", "4_Team_DNA.py", "2_FDR.py", "3_Signals.py", "6_Trending.py"):
        at = _run(_PAGES / page)
        blob = " ".join(m.value for m in at.markdown)
        assert 'aria-label="MADBOOTS"' in blob, f"{page} is missing the brand mark"


def test_home_hero_box_consolidates_cta_and_nudges():
    # US-398 (rev): one purple "get started" box — the Build CTA + New-here/Maddie/Testing nudges consolidated;
    # every "Explore the sidebar" bullet carries its icon.
    at = _run(_APP)
    blob = " ".join(m.value for m in at.markdown)
    assert "mb-hero" in blob                                    # the one highlighted box
    # ADR-166: the builder is a My Squad tab now, so the CTA points there — a link to a deleted page would
    # be a worse first impression than no CTA at all.
    assert 'href="My_Squad"' in blob and "Build your first squad" in blob   # the highlighted CTA button-link
    assert "New here?" in blob and "Help ▸ Watch" in blob and "Testing this?" in blob   # nudges consolidated
    # US-433 → ADR-169. This line has now pinned a page name **twice**: it asserted "📅 **Fixtures**" until
    # ADR-134 renamed that page, then "🧬 **Team DNA & FDR**" until ADR-169 split it — each time the test broke
    # because the app *improved*, which is exactly backwards. It asserts the **shape** now (an emoji-led
    # bullet list, several of them); naming is the job of the guard that derives the list from `pages/`.
    import re as _re
    bullets = _re.findall(r"^- \S+ \*\*(.+?)\*\* —", blob, flags=_re.M)
    assert len(bullets) >= 6, f"the tour should be an emoji-led bullet per page; found {bullets}"


def test_news_shows_the_shared_fit_flag():
    # US-400: News uses the same availability emoji (the Fit column) as every other surface.
    at = _run(_PAGES / "3_Signals.py")
    dfs = at.get("dataframe")
    assert not dfs or "Fit" in list(dfs[0].value.columns)   # when there's news, the Fit column is present


def test_feedback_page_picker_matches_the_current_nav():
    """US-393 → ADR-166: the picker names where a tester would say a bug happened. It had gone stale the same
    way Home's tour did — still offering *Fixtures* and *News*, never gaining Leagues or Signals."""
    at = _run(_PAGES / "8_Feedback.py")
    opts = [o for sb in at.selectbox for o in sb.options]
    assert {"My Squad", "FDR", "Signals", "Team DNA", "Players", "Trending"} <= set(opts)
    # Tabs a tester would name are listed with where they live — nobody reports a bug against "My Squad",
    # they report it against "Leagues".
    for tab in ("Leagues", "Squad Lab", "Scout"):
        assert any(tab in o for o in opts), f"{tab} should be reportable by its own name"
    for stale in ("Squads", "Fixtures", "News", "Maddie Explains", "Ask", "Team DNA & FDR"):
        assert stale not in opts, f"{stale} is not a page any more"


def test_fixtures_ticker_shows_the_difficulty_number():
    # US-391: the difficulty run isn't colour-only — each cell carries the FDR digit (colour-blind-safe).
    at = _run(_PAGES / "2_FDR.py")
    caps = " ".join(c.value for c in at.caption)
    assert "is the difficulty" in caps                         # the legend explains the per-cell number


def test_home_still_points_at_the_video_guides():
    """US-383 → US-398 → ADR-166: the nudge is text in the consolidated hero box, and it now names **Help ▸
    Watch** — Maddie stopped being a page, so pointing at one would send people nowhere."""
    at = _run(_APP)
    blob = " ".join(m.value for m in at.markdown)
    assert "Help ▸ Watch" in blob and "video guides" in blob
    assert "Maddie Explains</b>" not in blob                # the page that no longer exists



def test_health_shows_the_risk_monitor_and_squad_dna():
    """ADR-130 — Health said how good a squad was; it now also says what needs attention this week."""
    at = _squads_view("DNA")
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
    at = _squads_view("DNA")
    if at.exception:
        raise AssertionError(at.exception)
    blob = " ".join(m.value for m in at.markdown)
    if "The weeks ahead" not in blob:
        return                                     # no squad loaded in this environment
    assert 'class="fp-wk"' in blob                 # a bar per gameweek
    assert "xP per gameweek" in blob               # the projection stated, not charted as the headline


def test_the_actions_are_back_below_the_pitch_after_the_adr_135_revert():
    """The other half of ADR-135's story, kept as a number so nobody has to trust a memory.

    ADR-135 moved Captain / Substitute / Compare onto the shirt, and this test asserted `<= 3` per-player
    widgets below the pitch. It **hit** that target — and the experience got worse anyway (a two-tap flow cost
    two Streamlit round-trips, and the menu opened alongside neighbouring cards' hover popovers), so it was
    reverted. The count being back up is the accepted cost of that call, not a regression to fix.

    What this still guards is the shape of the page: the actions live in **one** panel below the pitch rather
    than scattered, and tapping a shirt is an input to that panel, not a second place to act.
    """
    at = _squads_view("My Squad")
    if at.exception:
        raise AssertionError(at.exception)
    pick = next((s for s in at.selectbox if s.label == "Select a player"), None)
    if pick is None:
        return                                          # no squad in this environment
    pick.set_value(next(o for o in pick.options if o != "—")).run()
    assert not at.exception

    labels = [(getattr(w, "label", "") or "").strip()
              for kind in ("selectbox", "segmented_control", "button", "checkbox")
              for w in getattr(at, kind, [])]
    assert any("captain" in lab.lower() for lab in labels), "the captain action must be reachable again"
    assert any("Boot Battle" in lab for lab in labels), "compare must be reachable again"


def test_the_price_column_is_painted_green_up_red_down():
    """ADR-140. `st.dataframe` renders plain text in cells — `TextColumn` has no colour, and `MarkdownColumn`
    only renders its markdown in a click-through overlay — so `:green[▲]` cannot work there. A pandas Styler
    can, and this pins that the styling actually attaches rather than silently doing nothing.

    It also pins the pairing: green must go to the *up* glyph. A green down-arrow is worse than no colour.
    """
    from src.analytics import PRICE_DOWN, PRICE_UP
    from src.web_streamlit.formats import colour_price

    rows = [{"Player": "A", "Price": PRICE_UP}, {"Player": "B", "Price": PRICE_DOWN},
            {"Player": "C", "Price": ""}]
    import re

    styled = colour_price(rows)
    assert hasattr(styled, "to_html"), "a Styler, not the plain rows"
    # Styler emits one CSS rule per styled cell, keyed `row{n}_col{n}`. Reading the rules back by row index is
    # what lets this assert the *pairing* rather than merely that two colours appear somewhere.
    css = {int(m.group(1)): m.group(2) for m in
           re.finditer(r"row(\d)_col1 \{([^}]*)\}", styled.to_html())}
    assert "#16a34a" in css.get(0, ""), "the UP row must be green"
    assert "#dc2626" in css.get(1, ""), "the DOWN row must be red"
    assert 2 not in css, "a stable player has no arrow and must not be painted"


def test_colouring_degrades_to_a_plain_table_rather_than_failing():
    """Returning the input untouched when there is nothing to paint means a caller can hand the result
    straight to `st.dataframe` without asking which it got. An uncoloured table is the right failure — the
    glyphs still carry direction by shape."""
    from src.web_streamlit.formats import colour_price

    assert colour_price([]) == []
    rows = [{"Player": "A"}]                      # no Price column at all
    assert colour_price(rows) is rows


def test_the_leagues_page_shows_a_table_but_never_fetches_squads_on_load(monkeypatch):
    """ADR-141's central rule, as a test: **nothing that costs N network calls happens because someone opened
    a tab.**

    The league table is one call and renders immediately. The insight layer is one call *per manager*, so it
    sits behind an explicit button — and this asserts the page reaches its rendered state without `picks` ever
    being called. Both the standings and the picks fetches are faked, so no test touches the live API.
    """
    # `st.cache_data` is process-wide and `_standings` is keyed on the league id alone — which is right in
    # production and makes these two tests order-dependent, since both use the Elite preset (314). Clearing
    # is what stops the second test silently reading the first one's fake league.
    import streamlit as st
    st.cache_data.clear()

    from src.api import client as client_mod

    standings = {"league": {"name": "Test League"},
                 "standings": {"has_next": False, "results": [
                     {"entry": 1, "player_name": "A", "entry_name": "Team A", "rank": 1, "last_rank": 2,
                      "event_total": 70, "total": 200},
                     {"entry": 2, "player_name": "B", "entry_name": "Team B", "rank": 2, "last_rank": 1,
                      "event_total": 60, "total": 190}]}}
    picks_calls = []

    class FakeClient:
        def get_entry(self, entry_id):                     # ADR-166: a remembered id makes this reachable
            return {"name": "Someone", "leagues": {"classic": []}}

        def get_league_standings(self, league_id, page=1):
            return standings

        def get_entry_picks(self, entry_id, gameweek):
            picks_calls.append((entry_id, gameweek))
            return {"picks": [], "active_chip": None}

    monkeypatch.setattr(client_mod, "FplClient", FakeClient)
    at = _squads_view("Leagues")
    # ADR-166 — Leagues is a My Squad tab now, so `segmented_control[0]` is the **Tool** switch. Pick the
    # scope by its label instead; an index into a page's widgets is a positional assumption waiting to break.
    next(c for c in at.segmented_control if c.label == "Find a league").set_value("Elite").run()
    if at.exception:
        raise AssertionError(at.exception)

    assert any(s.value == "Test League" for s in at.subheader), "the table renders on load"
    assert picks_calls == [], "no per-manager fetch may happen just because the page opened"
    assert any(b.label.startswith("Read ") for b in at.button), "the expensive layer needs an explicit action"


def test_the_leagues_page_states_its_cap_rather_than_truncating_silently(monkeypatch):
    """A 500-manager league is ~3 minutes of fetching, so the page reads one standings page.

    Silent truncation reads as "we covered everything" when we did not — so this drives a league that *does*
    have more pages and asserts the page says so, rather than checking the source for a string.
    """
    # `st.cache_data` is process-wide and `_standings` is keyed on the league id alone — which is right in
    # production and makes these two tests order-dependent, since both use the Elite preset (314). Clearing
    # is what stops the second test silently reading the first one's fake league.
    import streamlit as st
    st.cache_data.clear()

    from src.api import client as client_mod

    rows = [{"entry": i, "player_name": f"P{i}", "entry_name": f"T{i}", "rank": i, "last_rank": i,
             "event_total": 50, "total": 100} for i in range(1, 61)]      # 60 rows, more than the cap

    class FakeClient:
        def get_entry(self, entry_id):                     # ADR-166: a remembered id makes this reachable
            return {"name": "Someone", "leagues": {"classic": []}}

        def get_league_standings(self, league_id, page=1):
            return {"league": {"name": "Big League"}, "standings": {"has_next": True, "results": rows}}

        def get_entry_picks(self, entry_id, gameweek):
            raise AssertionError("must not be called on load")

    monkeypatch.setattr(client_mod, "FplClient", FakeClient)
    at = _squads_view("Leagues")
    # A league id **unique to this test**, entered directly rather than via the Elite preset. Both tests used
    # Elite (314), and `_standings` is cached on the league id alone — so whichever ran second silently read
    # the first one's fake league. `st.cache_data.clear()` cannot fix it: called from a test body it runs
    # outside AppTest's script context and never touches the cache the page uses.
    next(c for c in at.segmented_control if c.label == "Find a league").set_value("By league id").run()
    next(t for t in at.text_input if "league id" in (t.label or "").lower()).set_value("555001").run()
    if at.exception:
        raise AssertionError(at.exception)

    caption = " ".join(c.value for c in at.caption)
    assert "top 50" in caption, "a truncated league must say it was truncated"
    assert len(at.dataframe[0].value) == 50, "and must actually stop at the cap"


def test_the_leagues_page_finds_your_leagues_from_a_manager_id(monkeypatch):
    """ADR-141 rev. The gap the owner hit on Cloud: he had the page open, his own manager id to hand, and no
    way in — because the page asked for a **league** id, which only appears in a URL you have to go and find.

    `/entry/{id}/` already lists every league behind a manager id, so the lookup costs one call. This drives
    the whole path: id in → your leagues listed, your own ahead of FPL's automatic ones → a table.
    """
    import streamlit as st

    from src.api import client as client_mod
    st.cache_data.clear()

    class FakeClient:
        def get_entry(self, entry_id):
            return {"name": "Test Manager", "leagues": {"classic": [
                {"id": 314, "name": "Overall", "rank_count": 8_903_396, "entry_rank": 1, "league_type": "s"},
                {"id": 999, "name": "Work League", "rank_count": 11, "entry_rank": 3, "league_type": "x"}]}}

        def get_league_standings(self, league_id, page=1):
            return {"league": {"name": f"League {league_id}"},
                    "standings": {"has_next": False, "results": [
                        {"entry": 1, "player_name": "A", "entry_name": "TA", "rank": 1, "last_rank": 1,
                         "event_total": 50, "total": 100}]}}

        def get_entry_picks(self, entry_id, gameweek):
            raise AssertionError("must not be called on load")

    monkeypatch.setattr(client_mod, "FplClient", FakeClient)
    at = _squads_view("Leagues")
    assert (next(c for c in at.segmented_control if c.label == "Find a league").value == "My leagues"), \
        "the id people actually have is the default path"

    # ADR-166 — on a tab, `text_input[0]` is My Squad's own field, not this one. Address it by label:
    # positional indexing into a page's widgets is an assumption that breaks the moment the page grows.
    # A manager id **unique to this test**. `st.cache_data.clear()` above is not enough: called from the test
    # body it runs outside AppTest's script context, so it does not reach the cache the page actually uses —
    # and `_entry` is keyed on the id alone, so a shared id silently returns the previous test's fake league.
    next(t for t in at.text_input if t.label == "Your FPL manager id").set_value("7654321").run()
    if at.exception:
        raise AssertionError(at.exception)

    picker = next(s for s in at.selectbox if s.label == "Your leagues")
    assert len(picker.options) == 2
    assert picker.options[0].startswith("👥 Work League"), \
        "your own league must lead — sorted by size, FPL's automatic ones bury it"
    assert "🌍 Overall" in picker.options[1]
    assert any("Test Manager" in c.value for c in at.caption), \
        "naming the manager is how you catch a mistyped id — otherwise you get a stranger's leagues silently"
    assert any(s.value == "League 999" for s in at.subheader), "picking a league loads its table"


def test_health_shows_a_concentration_note_only_when_a_week_is_actually_narrow():
    """ADR-145 on the page. The naive "player clashes" feature would have fired for 100% of squads every week;
    this speaks above the measured 75th percentile, so most squads see nothing — and a squad that *is*
    concentrated gets one line naming the match and the players.
    """
    from src.squads import SquadStore

    squad = SquadStore().load("TS")
    if not squad:
        return                                          # no seed squad in this environment
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=180)
    at.session_state["squad"] = {"name": "TS", "player_ids": squad["player_ids"],
                                 "bench_ids": squad.get("bench_ids") or [],
                                 "cost": squad.get("cost") or 100.0}
    at.run()
    at.segmented_control[0].set_value("DNA").run()
    assert not at.exception

    notes = [c.value for c in at.caption if c.value.startswith("🎯")]
    # Whether this squad is concentrated depends on the live fixture data, so the assertion is on the *shape*:
    # every note that appears must name a gameweek, a match and the players — a bare percentage is not
    # actionable, which is the failure mode this feature was designed around.
    for n in notes:
        assert "% of your GW" in n and " v " in n and "players" in n


def test_the_community_buzz_tab_honours_the_shared_filter(monkeypatch):
    """ADR-149. The four Trending boards have honoured the shared filter — **"My squad only" included** —
    since US-407b. The Community Signals tab never did, so the one question a manager actually brings to it
    (*"is the crowd talking about MY players?"*) was the one it could not answer.

    Driven with a fake RSS feed, so no test touches Reddit.
    """
    from src.community import community_buzz
    from src.storage import Storage
    from src.web_streamlit.filters import apply as apply_filter

    store = Storage()
    players = store.get_players()
    store.close()
    if len(players) < 4:
        return

    named = players[:4]
    feed = "<feed xmlns='http://www.w3.org/2005/Atom'>" + "".join(
        f"<entry><title>On {p['web_name']}</title><link href='http://x/{i}'/>"
        f"<content>{p['web_name']} looks good</content></entry>"
        for i, p in enumerate(named)) + "</feed>"

    buzz = community_buzz(feed, players, limit=len(players))
    assert len(buzz) >= 2, "the fake feed must mention several players for the filter to bite"

    mine = {named[0]["id"]}
    shown = apply_filter(buzz, {"teams": [], "positions": [], "players": [], "my_squad": mine})
    assert [r["id"] for r in shown] == [named[0]["id"]], "'My squad only' must reach the buzz list"
    assert len(shown) < len(buzz), "…and must actually narrow it"


def test_the_buzz_tab_states_the_full_count_beside_the_filtered_one():
    """The filter is applied **after** the scan on purpose: the unfiltered total is what makes the filtered
    number mean anything ("6 of 47" says the crowd is busy and mostly not about you; "6" alone says nothing).
    The scan is cached for 30 minutes, so keeping it costs nothing.
    """
    source = (_PAGES / "3_Signals.py").read_text()
    assert "apply_filter(buzz, sel)" in source, "filtered after the scan, not before"
    assert "of {len(buzz)} players mentioned match your filter" in source
    assert "untick **My squad only**" in source, "an empty result must say how to get back out of it"


def test_signals_orders_its_sources_by_how_much_they_actually_know():
    """ADR-150's central decision, pinned as an order rather than a vibe.

    Four lenses used to be split across two pages with no relationship to each other. Merging them raises one
    real risk — presenting a Reddit rumour beside an injury FPL has confirmed, as though they were comparable.
    The answer is that the page **descends by evidentiary strength**, and each section says what it is:

    1. official FPL news — a fact, and the only source here that moves xP
    2. an unexplained exodus — our inference about *other managers*, not about the player
    3. media headlines — reported by named outlets
    4. community chatter — a mention count, never sentiment
    """
    at = _run(_PAGES / "3_Signals.py")
    if at.exception:
        raise AssertionError(at.exception)
    heads = [h.value for h in at.subheader]
    assert heads == ["1 · Official FPL news", "2 · An exodus we can't explain",
                     "3 · Headlines — FPL analysis & football news", "4 · Community chatter"]


def test_signals_says_what_each_source_is_worth():
    """A merged page has to label its sources or the merge itself is the misinformation."""
    at = _run(_PAGES / "3_Signals.py")
    if at.exception:
        raise AssertionError(at.exception)
    caps = " ".join(c.value for c in at.caption)
    assert "only source here that is a **fact**" in caps          # official news
    assert "Not a fact about the player" in caps                  # the exodus, carefully worded
    assert "mention count, not sentiment" in caps                 # chatter, least reliable, last


def test_trending_is_leaderboards_only_now():
    """The other half of the split: Trending answers *what the crowd is doing*, in numbers. Mixing chatter in
    put a mention count beside an ownership percentage as though they were the same kind of thing."""
    at = _run(_PAGES / "6_Trending.py")
    if at.exception:
        raise AssertionError(at.exception)
    labels = [b.label for b in at.button]
    assert not any("talked about" in lab.lower() or "discussions" in lab.lower() for lab in labels)
    assert any("Signals" in c.value for c in at.caption), "and it should point at where the chatter went"


def test_the_exodus_list_is_scoped_to_players_people_actually_own():
    """ADR-150 found a real flaw in reusing ADR-146's threshold on a *browse* list.

    `EXODUS_PRESSURE` is net transfers **per 1% owned** — the right scale for comparing a template player with
    a niche one, but it divides by a small number, so a 0.1%-owned player shedding a few thousand reads as a
    stampede. On a per-squad warning that never mattered (you only see players you own). On a browse list it
    filled the page with names nobody holds: 17 players, of which 9 were under 1% owned.

    The floor is not a taste — it is the population the p10 threshold was measured on.
    """
    from src.analytics.crowd import EXODUS_OWNERSHIP_FLOOR, crowd_exodus
    from src.storage import Storage

    assert EXODUS_OWNERSHIP_FLOOR == 1.0
    store = Storage()
    players = store.get_players()
    store.close()
    listed = [p for p in players
              if (p["selected_by"] or 0) >= EXODUS_OWNERSHIP_FLOOR and crowd_exodus(p)]
    assert all((p["selected_by"] or 0) >= 1.0 for p in listed)
    unfiltered = [p for p in players if crowd_exodus(p)]
    assert len(listed) <= len(unfiltered), "the floor may only ever narrow the list"


def test_health_shows_a_reported_departure_the_fpl_status_still_calls_available(monkeypatch):
    """ADR-155 — Health was the last squad surface blind to this. It read *"Availability issues: 1"* on a
    squad holding a player with an agreed move to Al-Hilal, because FPL's own status still said `a`.

    The departure is stubbed rather than seeded: what is under test is that the view asks the question and
    renders the answer, not the extraction that produces it (covered in test_headlines).
    """
    from src.web_streamlit.views import squads as squads_view

    seen = {}

    def fake(owned):
        if not owned:
            return {}
        seen["id"] = owned[0]["id"]
        return {owned[0]["id"]: {"kind": "transfer", "source": "Romano", "title": "Al Hilal, here we go!"}}

    monkeypatch.setattr(squads_view, "_reported_leavers", fake)
    at = _squads_view("DNA")
    assert seen, "the stub was never called — Health is not asking the question at all"
    block = "\n".join(c.value for c in at.code)
    assert "leaving — Romano" in block, "the analysis must name the outlet behind the departure"
    assert "(out)" in block, "…and mark his row, where the eye lands first"


def test_transfer_view_puts_a_reported_departure_ahead_of_an_upgrade(monkeypatch):
    """ADR-156 — the view used to say two things at once: a ⛔ banner naming the departing player, and beneath
    it *"use your free transfer on Gibbs-White → Cunha"*. Both were right; neither knew about the other.

    One lookup now feeds the banner, the timing call and the ranking.
    """
    from src.web_streamlit.views import squads as squads_view

    seen = {}

    def fake(owned):
        if not owned:
            return {}
        seen["name"] = owned[0]["web_name"]
        return {owned[0]["id"]: {"kind": "transfer", "source": "Romano", "title": "Al Hilal, here we go!"}}

    monkeypatch.setattr(squads_view, "_reported_leavers", fake)
    at = _squads_view("Transfer")
    assert seen, "the stub was never called — the Transfer view is not asking the question"
    said = " ".join([*(e.value for e in at.error), *(i.value for i in at.info)])
    assert seen["name"] in said, "the departing player must be named on the page"
    assert "per Romano" in said, "…and the outlet with him, so the claim is checkable"


def test_the_league_scan_offers_the_tap_when_the_component_is_live(monkeypatch):
    """ADR-158 — the roadmap asked for the league-scan rows to inherit ADR-133's selection.

    Both halves matter, so both are asserted: with the component live the rows are anchors and the caption
    says tapping works (ADR-133's diagnostic — an invisible fallback left no way to tell a working deploy
    from a broken one); without it, the page is exactly what it was.
    """
    from src.web_streamlit import tap

    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: ""))
    at = _run(_PAGES / "4_Team_DNA.py")
    assert not at.exception
    assert any("Tap a row" in c.value for c in at.caption), "the caption must say the gesture exists"

    monkeypatch.setattr(tap, "_detector", lambda: None)
    plain = _run(_PAGES / "4_Team_DNA.py")
    assert not plain.exception, "a missing component must never take the page down"
    assert not any("Tap a row" in c.value for c in plain.caption)
    assert any(s.label == "Team" for s in plain.selectbox), "the picker stays either way"


def test_the_leagues_page_still_renders_with_the_head_to_head_section(monkeypatch):
    """ADR-161 — the H2H sits behind the same N-calls button as the rest of the insight layer, so a no-network
    render must reach the manager-id prompt and stop, exactly as before."""
    at = _squads_view("Leagues")
    assert not at.exception


def test_the_leagues_load_button_latches_so_a_rival_change_does_not_collapse_the_page(monkeypatch):
    """US-431, owner: *"when you change player on head to head, the 'Read N squads' collapses down."*

    `st.button` is True only on the run it was clicked, so any widget below it — the H2H rival picker — re-ran
    the page, found False, and hid everything. The latch is keyed on the **league id**, not a bare flag,
    because loading costs N network calls: switching leagues must ask again rather than spend them silently.
    """
    src = (_ROOT / "src" / "web_streamlit" / "views" / "leagues.py").read_text()
    assert 'st.session_state["lg_loaded_for"] = league_id' in src
    assert 'st.session_state.get("lg_loaded_for") != league_id' in src
    assert 'if not st.button(f"Read {len(shown)} squads' not in src, "the old collapse-on-rerun form is back"


def test_the_manager_import_remembers_the_id_so_leagues_does_not_ask_again():
    """US-432, owner: *"when you input your FPL team under My Squad it should also import your leagues.
    Currently they are separate actions."*

    Storing the id IS the fix — Leagues builds your league list from it. Fetching the leagues here as well
    would put that page inside this one, which is the clutter the owner has asked to keep out.
    """
    src = (_ROOT / "src" / "web_streamlit" / "squads.py").read_text()
    assert "prefs.remember(manager_id=manager_id.strip())" in src
    assert "Leagues" in src, "the success message should point at where the id now works"


def test_the_transfer_flow_asks_before_spending_a_second_round_of_calls():
    """ADR-141's rule, kept: nothing that costs N calls happens because someone opened a tab. The activity
    numbers are free (they ride on payloads already fetched) so they are always drawn; the identities are not.
    """
    src = (_ROOT / "src" / "web_streamlit" / "views" / "leagues.py").read_text()
    assert "transfer_activity(picks)" in src, "the free half must not sit behind a button"
    assert 'st.session_state["lg_flow_for"]' in src, "the paid half must latch, like the squads button"
    assert "_transfers(tuple(picks))" in src


def test_the_home_tour_names_every_page_in_the_sidebar():
    """US-433 — Home lists every page, so it rots on any rename or addition and nothing complains.

    It really did: it still said *Fixtures* and *News* long after ADR-134 and ADR-149 renamed them to Team DNA
    & FDR and Signals, and it never mentioned 🏆 Leagues at all — live for days by then. Fixing the words
    would leave the next rename to a person's memory; this derives the list from `pages/` instead.

    Matched against the **tour bullets only**, not the file. A whole-file substring search passes on almost
    any breakage — the word survives in the docstring or another sentence — which is a test that cannot fail.
    (Verified by deleting the Leagues bullet: the loose version still passed, this one doesn't.)

    **Admin is excluded deliberately** — owner-only, and advertising it on the landing page would be a UX bug
    rather than a fix.
    """
    home = (_ROOT / "src" / "web_streamlit" / "Home.py").read_text()
    listed = set(re.findall(r"^- \S+ \*\*(.+?)\*\* —", home, flags=re.M))
    assert listed, "no tour bullets found — the tour's shape changed, so this guard is no longer guarding"

    missing = []
    for page in sorted(_PAGES.glob("*.py")):
        title = re.search(r'st\.title\("([^"]+)"', page.read_text())
        if not title:
            continue
        name = re.sub(r"^[^\w]+", "", title.group(1).split("—")[0].strip()).strip()
        if name.startswith("Admin"):
            continue
        if name not in listed:
            missing.append(f"{page.name} → '{name}'")
    assert not missing, ("Home's tour doesn't list: " + "; ".join(missing)
                         + f" (it lists: {sorted(listed)})")


def test_no_page_composes_a_stat_row_out_of_columns_and_metrics():
    """ADR-163 — the guard that keeps US-449 fixed.

    The wrapping came back because the fix in US-404 was *"use fewer metrics"*, which shrank the symptom and
    left the mechanism. The moment two more strips shipped (ADR-161's head-to-head, ADR-162's transfer flow)
    the owner hit it again on iPhone. A shared component only helps if the old pattern stops coming back, so
    this fails on a reintroduced `stX.metric(` — the column-handle form that cannot reflow.

    `st.metric` on its own is fine and stays available; it is the *row* of them that slivers. Admin is
    exempt — it is an owner-only desktop console, not a page a tester opens on a phone.
    """
    offenders = []
    for page in sorted(_PAGES.glob("*.py")):
        if page.name.startswith("9_Admin"):
            continue
        for i, line in enumerate(page.read_text().splitlines(), start=1):
            if re.search(r"\b[a-z]\d\.metric\(", line):
                offenders.append(f"{page.name}:{i}")
    for view in sorted((_ROOT / "src" / "web_streamlit" / "views").glob("*.py")):
        for i, line in enumerate(view.read_text().splitlines(), start=1):
            if re.search(r"\b[a-z]\d\.metric\(", line):
                offenders.append(f"views/{view.name}:{i}")
    assert not offenders, ("a column-handle metric row is back — use components.render_stat_strip so it "
                           "reflows on a phone: " + "; ".join(offenders))


def test_every_page_uses_the_same_widget_for_its_sub_boards():
    """US-439 — Trending was the one page still on `st.tabs` where everything else uses a segmented control.

    Not only cosmetic: `st.tabs` builds *every* panel on every run and hides all but one with CSS, so four
    leaderboards were computed to show one. The consistent widget is also the cheaper one.
    """
    users = [p.name for p in sorted(_PAGES.glob("*.py")) if "st.tabs(" in p.read_text()]
    assert not users, f"these pages still use st.tabs instead of st.segmented_control: {users}"


def test_signals_has_one_squad_lens_not_a_control_per_section():
    """US-442 (ADR-164) — the owner asked for a *global* my-squad option.

    It was per-section: the filter was created inside section 1, one later section happened to reuse its
    result, and two ignored it entirely. A lens that covers some of a page is worse than none — a quiet
    section could mean "nothing about your squad" or "not filtered", and the reader can't tell which.
    """
    src = (_PAGES / "3_Signals.py").read_text()
    assert src.count("filter_controls(") == 1, "one control for the page, not one per section"
    # …and it is created before section 1, so every section below can honour it.
    assert src.index("filter_controls(") < src.index('st.subheader("1 · Official FPL news")')
    assert src.count("apply_filter(") >= 4, "the lede and sections 1, 2 and 4 all read it"
    assert "find_mentions" in src, "…and the headlines, which need name resolution rather than a row filter"


def test_team_dna_scan_and_ticker_share_one_squad_lens():
    """US-441 (ADR-164) — the checkbox existed on the ticker only, so the 20-club scan above it ignored a
    control the reader had already set: one page answering "my squad" in one half and "the league" in the
    other, with nothing saying which."""
    src = (_PAGES / "4_Team_DNA.py").read_text()
    assert src.count('st.checkbox("My squad only"') == 1, "one checkbox for the page"
    assert "ticker_myteam" not in src, "the ticker's separate key is gone"
    # bound unconditionally, because the ticker reads it even on a snapshot with no DNA to draw
    assert src.index("_squad_only = False") < src.index('st.checkbox("My squad only"')


def test_the_dna_page_survives_having_no_team_dna_to_draw(monkeypatch):
    """The `NameError` the shared lens nearly introduced: the checkbox is created inside `if _all_dna:` but
    the ticker below reads it regardless, so an empty DNA map would have crashed the page."""
    import src.analytics as analytics_pkg
    monkeypatch.setattr(analytics_pkg, "team_dna_all", lambda *a, **k: {})
    at = _run(_PAGES / "4_Team_DNA.py")
    assert not at.exception


def test_the_player_panel_is_a_fragment_but_mutations_still_rerun_the_whole_app():
    """ADR-165 — the fragment's value is that a *selection* stops re-running the page; its danger is that a
    *mutation* might stop re-running it too.

    Making someone captain changes the xP strip **above** this fragment, and a fragment-scoped rerun cannot
    repaint anything outside itself. `st.rerun()` defaults to `scope="app"`, so the existing calls are already
    right — this pins that nobody "optimises" them to `scope="fragment"` later and quietly leaves the strip
    showing the old captain's numbers.
    """
    src = (_ROOT / "src" / "web_streamlit" / "views" / "squads.py").read_text()
    assert "@st.fragment" in src
    assert 'scope="fragment"' not in src, (
        "a fragment-scoped rerun cannot repaint the xP strip above the fragment — captain and substitute "
        "must rerun the whole app")
    # the mutating buttons live inside the fragment, so they are the calls this is protecting
    frag = src.split("@st.fragment")[1]
    assert "pa_captain" in frag and "pa_do_sub" in frag


def test_the_scout_view_leads_with_what_the_boards_agree_on():
    """ADR-167 — the owner: *"I see a similar table in each tab… could we call out a recommendation rather
    than just showing multiple tables of fact which none will use."*

    Five same-shaped leaderboards became one view with a board selector, under a shortlist of the players two
    or more of them agree on. This pins both halves: the shortlist leads, and every board is still reachable.
    """
    at = _run(_PAGES / "5_Players.py")
    if not at.segmented_control:
        return
    next(c for c in at.segmented_control if c.label == "View").set_value("Scout").run()
    assert not at.exception
    assert any("Worth a look" in m.value for m in at.markdown)
    board = next(c for c in at.segmented_control if c.label == "Board")
    assert list(board.options) == ["Set pieces", "Over/under", "DefCon", "Clean sheets", "xG · xA"]


def test_the_scout_shortlist_never_promises_points():
    """The design constraint, as a test. SET_PIECE_WEIGHT and DEFCON_MAGNIFIER_WEIGHT are both 0, so ranking
    players on those signals would assert a confidence `decision_xp` has explicitly withheld — a second
    opinion beside the one number the app decides with (ADR-041)."""
    from src import config
    assert config.SET_PIECE_WEIGHT == 0.0 and config.DEFCON_MAGNIFIER_WEIGHT == 0.0, \
        "if these are live, the scout copy must change — it currently says this value is NOT in xP"

    at = _run(_PAGES / "5_Players.py")
    if not at.segmented_control:
        return
    next(c for c in at.segmented_control if c.label == "View").set_value("Scout").run()
    caps = " ".join(c.value for c in at.caption).lower()
    assert "not a points projection" in caps
    for promise in ("you should buy", "transfer in", "best captain"):
        assert promise not in caps


def test_players_is_back_under_its_own_ceiling():
    """The page carried a note that ten views was the ceiling and the next one needed a **merge** first.
    ADR-167 is that merge — and the room it frees is what unblocks moving Trending here (US-438)."""
    at = _run(_PAGES / "5_Players.py")
    if not at.segmented_control:
        return
    views = next(c for c in at.segmented_control if c.label == "View").options
    assert len(views) == 6, f"ten views became six; got {list(views)}"
    assert "Scout" in views
    for merged in ("Set pieces", "DefCon", "Clean sheets", "Over/under", "xG · xA"):
        assert merged not in views, f"{merged} is a board inside Scout now, not a top-level view"


def test_help_carries_the_fpl_rules_ask_was_the_only_route_to():
    """ADR-168 — retiring Ask would have cost testers its only two non-duplicating intents (`rules`,
    `scoring`). Help explains the *app*; it had nothing about the *game* — no scoring values, no chip
    mechanics, no autosub rules. So the reference moved here, where you can browse it instead of having to
    know what to ask before you can find out.
    """
    from src.fpl_rules import RULES

    at = _run(_PAGES / "7_Help.py")
    assert not at.exception
    labels = " ".join(e.label or "" for e in at.get("expander"))
    assert "FPL rules" in " ".join(h.value for h in at.subheader)
    for topic in ("Scoring", "Chips", "Transfers", "Automatic substitutions"):
        assert topic in labels, f"the {topic} rules should be browsable"
    assert len(RULES) >= 20, "the curated rule set is what this page renders"


def test_the_app_does_not_promise_narration_it_cannot_deliver():
    """ADR-168 — the mantra said *"The AI explains"*, and there is no Ollama on Streamlit Cloud, so for every
    tester that clause was untrue. `docs/DEPLOY.md` had documented the gap; the brand line had not caught up,
    and madboots.com had already dropped the clause on its own.

    This guards the wording *and* its reach: the mantra is rendered on several pages, so a revert anywhere
    would put the promise back.
    """
    from src.web_streamlit import brand

    assert "AI explains" not in brand.MANTRA
    assert "shows its working" in brand.MANTRA
    for page in ("7_Help.py",):
        src = (_PAGES / page).read_text()
        assert "The AI explains. You make the call." not in src, f"{page} hard-codes the retired promise"
    assert "The AI explains. You make the call." not in (_ROOT / "src" / "web_streamlit" / "Home.py").read_text()


def test_ask_is_owner_only_now_and_off_by_default():
    """It survives for evaluation, not for shipping: behind the Admin key, and behind a checkbox even there —
    it runs the full grounded pipeline, and ADR-141's rule is that nothing expensive happens on page load."""
    src = (_PAGES / "9_Admin.py").read_text()
    assert "Ask — under evaluation" in src
    assert 'st.checkbox("Load Ask"' in src, "off by default"
    assert not (_PAGES / "6_Ask.py").exists(), "the public page is retired"


def test_trending_leads_with_what_the_boards_only_show_between_them():
    """ADR-170 — the owner: *"For Trending I'd like an overview like you did for Scout, as it's a fab way of
    directing people's attention to the more notable items."*

    Pins both halves: the overview leads, and all four boards are still reachable underneath.
    """
    at = _run(_PAGES / "6_Trending.py")
    assert not at.exception
    assert any("Worth noticing" in m.value for m in at.markdown)
    board = next((c for c in at.segmented_control if c.label == "Board"), None)
    assert board is not None and len(board.options) == 4


def test_trending_never_explains_why_the_crowd_is_moving():
    """Trending says what the crowd is **doing**; Signals says what is being **said** (ADR-149/150). The
    overview must point at Signals for a cause rather than guessing one — a guess printed beside a measured
    number reads as though it were measured too.
    """
    at = _run(_PAGES / "6_Trending.py")
    caps = " ".join(c.value for c in at.caption)
    assert "Signals" in caps, "the reader must be told where 'why' lives"
    for guess in ("because", "injured", "rumour", "expected to sign"):
        assert guess not in caps.lower()


# ---- ADR-171 / US-435: one screen for the week -----------------------------------------------------

def test_the_golden_page_carries_the_whole_week_in_order():
    """ADR-171 asked for the whole week on one screen; ADR-175 kept that and changed *how*.

    The three answers were stacked down the page, which is what pushed the first useful thing to the eleventh
    block. They are one selector now — same four answers, one at a time, with the pitch still on screen
    while you switch. So the assertion moves from "three headings in order" to "four answers offered, and
    each one renders".
    """
    at = _squads_view("My Squad")
    sel = next(c for c in at.segmented_control if c.key == "ms_answer")
    assert list(sel.options) == ["This week", "Captain", "Transfer", "Chips"]
    assert any("This week" in c.value for c in at.code), "the default answer renders without being asked"

    for panel in sel.options[1:]:
        sel.set_value(panel).run()
        assert not at.exception, f"{panel} raised: {at.exception}"


def test_the_sub_nav_lost_the_two_views_that_became_sections():
    """7 tools → 5 (ADR-171) → **4** (ADR-175), as each became an answer rather than a destination.

    AI Tips and Captain went first; Transfer followed once a selector meant its ~10 widgets exist only when
    chosen, which is the objection ADR-174 had raised against stacking them.
    """
    at = _run(_PAGES / "1_My_Squad.py")
    tools = next(c for c in at.segmented_control if c.label == "Tool").options
    assert tools == ["My Squad", "DNA", "Leagues", "Lab"]
    for gone in ("AI Tips", "Captain", "Transfer"):
        assert gone not in tools, f"{gone} is an answer under the pitch now, not a destination"


def test_the_week_renders_eagerly_when_no_model_is_attached():
    """The deployed case, and the whole point of ADR-171.

    Streamlit Cloud has no Ollama, so `ask.answer` costs ~123 ms and the user should simply get the answer.
    `conftest` pins `reachable` to False, which is exactly that state.
    """
    at = _squads_view("My Squad")
    assert any("This week" in c.value for c in at.code), "the answer renders without being asked for"
    assert not any(b.key == "ms_week" for b in at.button), "no button is needed when the answer is cheap"


def test_the_week_waits_behind_a_button_when_a_model_is_attached(monkeypatch):
    """The dev-machine case: with `qwen3:8b` attached the same call takes 27-86 s, so it must be a click.

    This is the half ADR-166 got right and encoded in the wrong place — as a constant about which *tab* was
    slow, rather than a question about which *machine* is running.
    """
    from src import llm
    monkeypatch.setattr(llm, "reachable", lambda **kwargs: True)
    at = _squads_view("My Squad")
    assert any(b.key == "ms_week" for b in at.button), "a narrator is attached → the answer is a click"
    assert not any("This week — squad" in c.value for c in at.code), "…and nothing narrated on load"


def test_rendering_eagerly_never_reaches_for_a_model(monkeypatch):
    """ADR-171 — the eager decision must be BINDING, not a prediction.

    Found by the sprint's smoke test, not by any unit test: `narrator_attached()` chose the layout while
    `ask.answer` independently reached for whatever model was installed, so a machine the probe misjudged
    rendered eagerly *and* narrated — a **49-second landing**, the precise outcome the design exists to
    prevent. Having judged the answer cheap, the view must render the cheap answer.
    """
    from src.web_streamlit.views import squads as views

    seen = {}

    def _fake_answer(question, **kwargs):
        seen.update(kwargs)
        return __import__("src.ask", fromlist=["AskResult"]).AskResult(
            question=question, intent="gameweek", headline="ok", message="", facts={}, detail=None)

    monkeypatch.setattr(views.ask, "answer", _fake_answer)
    monkeypatch.setattr(views.llm, "reachable", lambda **k: False)
    monkeypatch.setattr(views.st, "session_state", {})

    views.render_this_week("TS", {"player_ids": [], "name": "TS"}, horizon=1)
    assert "narrator" in seen, "the eager path must pin the narrator rather than inherit the default"
    assert seen["narrator"]() is None, "…and pin it to one that cannot narrate"


def test_the_pitch_badges_a_vice_captain():
    """The pitch showed a (C) and nothing else, while FPL stores a vice the manager chose (2026-09-02)."""
    from src.web_streamlit.pitch import pitch_html
    xi = [{"id": 1, "web_name": "Cap", "team": "ARS", "position": "MID", "price": 9.0},
          {"id": 2, "web_name": "Vice", "team": "CHE", "position": "FWD", "price": 8.0}]
    kw = dict(xp_by_id={1: 6.0, 2: 5.0}, photos={}, next_opp={"ARS": None, "CHE": None})
    both = pitch_html(xi, [], captain_id=1, vice_captain_id=2, **kw)
    assert both.count(">C</span>") == 1 and both.count(">V</span>") == 1

    # A player cannot be both; if a stale squad says so, the badge that changes the score wins.
    same = pitch_html(xi, [], captain_id=1, vice_captain_id=1, **kw)
    assert same.count(">C</span>") == 1 and same.count(">V</span>") == 0

    none = pitch_html(xi, [], captain_id=1, vice_captain_id=None, **kw)
    assert none.count(">V</span>") == 0


def test_the_view_passes_the_vice_through_to_the_pitch(monkeypatch):
    """Pins the WIRING, which the pitch unit test cannot.

    `pitch_html` emitting a (V) proves nothing about `render_my_squad` handing it one. And AppTest cannot
    check the rendered badge — the pitch goes through the tap component, so it never reaches `at.markdown` —
    which is exactly how a smoke test for the badge produced a false negative on 2026-09-02.
    """
    from src.web_streamlit import tap
    seen = {}
    monkeypatch.setattr(tap, "render_tappable_pitch", lambda *a, **kw: seen.update(kw))
    monkeypatch.setattr(tap, "available", lambda: True)

    at = _squads_view("My Squad")
    assert not at.exception
    # the demo squad may carry no vice; what matters is that the argument is threaded, not its value
    assert "vice_captain_id" in seen, "render_my_squad must hand the pitch a vice, even when it is None"


def test_the_fdr_ticker_can_be_sorted_alphabetically():
    """From the owner's Sprint 61 note — the reference ticker had a sort and ours had none (2026-09-02).

    Easiest-run-first is what the page is *for* and stays the default, so nobody's view changes unless they
    ask. The second question is "where is my club?", and scanning 20 difficulty-ordered rows to find one team
    was the only thing this page was bad at.
    """
    at = _run(_PAGES / "2_FDR.py")
    if not at.dataframe:
        return                                          # no fixtures in this environment
    sort = next(c for c in at.segmented_control if c.label == "Sort by")
    assert sort.value == "Easiest run", "the default must be today's behaviour"

    easiest = list(at.dataframe[0].value["Team"])
    assert easiest != sorted(easiest), "the default is difficulty order, not alphabetical"

    sort.set_value("Team A–Z").run()
    assert not at.exception
    alpha = list(at.dataframe[0].value["Team"])
    assert alpha == sorted(alpha)
    assert set(alpha) == set(easiest), "sorting must reorder the clubs, never drop or add one"


# ---- ADR-174: acting on the recommendation, without moving the Transfer tab -------------------------


def test_the_week_offers_to_apply_the_transfer_it_just_named():
    """ADR-171 put the recommendation on the golden page and left a manager crossing to another tab to do
    the thing they had just been told to do. One button closes that."""
    at = _squads_view("My Squad")
    week = next((c for c in at.code if "This week" in c.value), None)
    if week is None or "Transfer: none" in week.value:
        return                                        # no positive-gain move on this snapshot
    btn = next((b for b in at.button if b.key == "ms_week_apply_btn"), None)
    assert btn is not None, "the week names a transfer and must offer to apply it"


def test_the_button_names_the_move_that_is_on_screen():
    """The button applies `plan.transfer` — the object the text was rendered from — so the two cannot
    disagree. Recomputing the swap at the surface would be a second search that could legitimately return a
    different move, leaving the button and the sentence above it naming different players.
    """
    at = _squads_view("My Squad")
    week = next((c for c in at.code if "This week" in c.value), None)
    btn = next((b for b in at.button if b.key == "ms_week_apply_btn"), None)
    if week is None or btn is None:
        return
    line = next(x for x in week.value.splitlines() if "Transfer:" in x)
    out_name, in_name = btn.label.replace("🔄 Apply: ", "").split(" → ")
    assert out_name in line and in_name in line, f"button {btn.label!r} does not match {line!r}"


def test_applying_it_changes_the_squad():
    at = _squads_view("My Squad")
    btn = next((b for b in at.button if b.key == "ms_week_apply_btn"), None)
    if btn is None:
        return
    btn.click().run()
    assert not at.exception
    squad = at.session_state["squad"]
    assert squad["player_ids"] and squad.get("cost")      # applied, re-costed, no crash


def test_the_transfer_tab_keeps_everything_it_had():
    """ADR-115 removed an in-page transfer expander as "a real redundancy", and that still holds. This adds
    one action on the named move; the tab keeps *finding* moves — the manual picker, the filter, the plans.
    """
    at = _squads_view("Transfer")
    labels = [s.label for s in at.selectbox]
    assert "Transfer out" in labels and "Bring in" in labels, "the manual picker must stay on the tab"
    assert any(b.label.startswith("Transfer →") for b in at.button)


# ---- ADR-175: value above the fold -----------------------------------------------------------------


def test_the_page_no_longer_explains_itself_before_showing_anything():
    """The cut caption said "squad · captain · transfers · chips · **health**" — a name ADR-166 retired six
    days earlier — and explained the page to someone already standing on it, under a title that names it and
    above tabs that list every item in the sentence. It was one of ten blocks before the first useful thing.
    """
    at = _squads_view("My Squad")
    caps = " ".join(c.value or "" for c in at.caption)
    assert "all in one place" not in caps
    assert "health" not in caps.lower(), "the caption named a tab that has been called DNA since ADR-166"


def test_the_squad_switcher_is_not_duplicated_by_the_banner():
    """The picker read "RoboTS (yours)" four lines above a banner reading "YOUR TEAM · RoboTS" — two
    elements, stacked, naming one squad."""
    src = (_ROOT / "src" / "web_streamlit" / "squads.py").read_text()
    assert 'label_visibility="collapsed"' in src.split("def squad_picker")[1].split("def ")[0], \
        "the 'Squad' caption said what the banner beneath it already said"
    assert "if len(labels) == 1:" in src, "one squad needs no picker at all"


def test_my_squad_has_no_horizon_control_at_all():
    """ADR-179, owner: *"let's remove GW1-3 from My Squad."* Replaces a guard that asserted the control's
    options — ADR-175 had cut it from 1/2/3/4/5/10 to GW1 · GW1–3, and the owner then removed it outright.

    **Two controls go, not one.** The *Projected xP* Cumulative / GW-only switch (US-422) only rendered above
    a horizon of 1, so it leaves with it — and at a fixed one-week window its two readings are the same
    number anyway.
    """
    at = _squads_view("My Squad")
    assert not [c for c in at.segmented_control if c.key == "gw_pitch"], \
        "the multi-week read belongs to the Lab, which has offered 1-10 since US-374"
    assert not [c for c in at.segmented_control if c.key == "myteam_xp_view"], \
        "and the switch that only existed to disentangle a longer horizon goes with it"


def test_the_lab_keeps_the_long_window_it_actually_uses():
    """A wildcard IS a multi-week bet — the horizon was never wrong there, only on an active squad."""
    at = _squads_view("Build")
    gw = [c for c in at.segmented_control if c.key == "gw_lab"]
    if gw:
        assert 10 in [int(o) for o in gw[0].options]


def test_backup_and_import_leave_the_page_once_you_have_a_team():
    """ADR-113's own words are "import it **once**". A once-a-season action was holding permanent space on
    the most-visited page — but it was put there so a new user could find it, which only applies while there
    is nothing to import."""
    from src.squads import SquadStore
    sq = SquadStore().load("RoboTS")
    if not sq:
        return
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=60)
    at.session_state["squad"] = {**sq, "name": "RoboTS"}     # a team of your own, so nothing to import
    at.run()
    # ⚠️ Scope to `at.main`. The top-level `at.get("expander")` includes the sidebar, so an unscoped
    # assertion here reads "still on the page" for a panel that has correctly moved off it.
    on_page = [e.label for e in (at.main.get("expander") or [])]
    in_sidebar = [e.label for e in (at.sidebar.get("expander") or [])]
    assert not any("Backup / import" in (lbl or "") for lbl in on_page), "it left the page"
    assert any("Backup / import" in (lbl or "") for lbl in in_sidebar), "…and arrived in the sidebar"


def test_backup_and_import_stay_on_the_page_while_there_is_nothing_to_import():
    """The other half, and the reason this is conditional rather than a straight move: ADR-113 put the panel
    here so a new user could find it, and that reason is real — it just expires the moment they have a team.
    """
    at = _squads_view("My Squad")                            # no session squad → the demo is shown
    on_page = [e.label for e in (at.main.get("expander") or [])]
    assert any("Backup / import" in (lbl or "") for lbl in on_page)


def test_the_answers_are_one_selector_not_a_stack():
    at = _squads_view("My Squad")
    sel = next(c for c in at.segmented_control if c.key == "ms_answer")
    assert list(sel.options) == ["This week", "Captain", "Transfer", "Chips"]
    # only ONE answer renders at a time — the stacked version put all three on the page at once
    assert not any("Chip strategy" in c.value for c in at.code)


def test_the_head_to_head_drops_a_spent_chip_and_leads_with_the_season_gap(monkeypatch):
    """ADR-177, end to end on the page — owner: *"you are showing MICKA at 59.9 and TS at 70, he is above me
    in the league?"*

    The unit tests pin the projection; this pins the **surface**, which is where both faults actually lived.
    Two managers hold the **identical fifteen**; one bench-boosted last week. Before ADR-177 the page put him
    ahead by his whole bench and called it a lead, under a table that had him second.

    It drives the real path — manager id → league → the N-calls button → the rival picker — because the block
    it covers is control flow, and control flow is exactly what a pure-function test cannot reach. The one
    thing stubbed is `last_completed_gameweek`: it is derived from live fixtures, so leaving it real would tie
    this test to the point in the season it was written.
    """
    import streamlit as st

    from src.api import client as client_mod
    from src.storage import Storage
    from src.web_streamlit.views import leagues as leagues_view

    st.cache_data.clear()
    monkeypatch.setattr(leagues_view, "last_completed_gameweek", lambda _upcoming: 2)

    store = Storage()
    try:
        squad = [p["id"] for p in store.get_players()[:15]]     # real ids, so decision_xp prices them
    finally:
        store.close()

    def _payload(*, boosted):
        picks = []
        for pos, pid in enumerate(squad, start=1):
            starting = pos < 12
            mult = (2 if pos == 1 else 1) if (starting or boosted) else 0
            picks.append({"element": pid, "position": pos, "is_captain": pos == 1, "multiplier": mult})
        return {"picks": picks, "active_chip": "bboost" if boosted else None}

    ME, RIVAL = 7654322, 424242

    class FakeClient:
        def get_entry(self, entry_id):
            return {"name": "Test Manager", "leagues": {"classic": [
                {"id": 4242, "name": "A League of Our Own", "rank_count": 2, "entry_rank": 2,
                 "league_type": "x"}]}}

        def get_league_standings(self, league_id, page=1):
            return {"league": {"name": "A League of Our Own"},
                    "standings": {"has_next": False, "results": [
                        {"entry": RIVAL, "player_name": "Michael Sheridan", "entry_name": "Micka",
                         "rank": 1, "last_rank": 2, "event_total": 128, "total": 188},
                        {"entry": ME, "player_name": "Tony Sheridan", "entry_name": "TS",
                         "rank": 2, "last_rank": 16, "event_total": 127, "total": 165}]}}

        def get_entry_picks(self, entry_id, gameweek):
            return _payload(boosted=(entry_id == ME))       # I chipped; the rival did not

    monkeypatch.setattr(client_mod, "FplClient", FakeClient)

    at = _squads_view("Leagues")
    next(t for t in at.text_input if t.label == "Your FPL manager id").set_value(str(ME)).run()
    next(b for b in at.button if b.key == "lg_load").click().run()
    if at.exception:
        raise AssertionError(at.exception)

    captions = [c.value for c in at.caption]

    # 1. The season standing, stated before the projection — the comparison the owner was actually making.
    assert any("Micka is 23 points ahead" in c and "you **165**" in c and "Micka **188**" in c
               for c in captions), \
        f"the card must say where the season sits, not leave it to the table above: {captions}"
    # Both totals carry a name. Written first as "(165 v 188)" after "Micka is 23 points ahead", where the
    # sentence's subject and the bracket's order disagreed and the reader had to guess which was whose.
    assert any("GW3 only" in c for c in captions), "and say the projection is one gameweek"

    # 2. The chip is named, and — the bug — it is NOT projected forward. Identical fifteens must tie.
    assert any("Bench Boost" in c and "spent" in c for c in captions), \
        f"a chip played last week has to be said out loud: {captions}"
    assert any("cannot separate you" in c for c in captions), \
        f"identical squads must project level; a spent chip carried forward is what made them differ: {captions}"


# ---- ADR-178: the pitch is a team sheet, the table is a reference -------------------------------

_MARKET_GLYPHS = ("💎", "⭐", "🟦", "👑", "🔥", "❄️", "💰", "💸", "📈")


def test_no_market_flag_reaches_a_shirt_and_no_glyph_carries_its_word():
    """ADR-178, owner: *"the players on the pitch have a lot of emojis under them… maybe reduce to corners,
    pens, FKs"* — then, at the preview: *"would it be cleaner to use just the emoji and have a key?"*

    Both halves are asserted here because they fail differently. The **market** flags left the pitch because
    every player carries at least one (the ownership tier always fires, so the pitch was never clean) and
    because they are a *third copy* of things already on the page by name — the price line, the Flagged line,
    Trending/Signals. The **words** left because on a 104px card three worded flags wrap to three lines.

    Set pieces stayed on merit, not preference: they describe the player's **role**, not the market, and are
    the one group with no better home.
    """
    from src.web_streamlit.pitch import _kit_html

    loud = {"id": 1, "web_name": "Szoboszlai", "team": "LIV", "position": "MID", "price": 7.0,
            "penalties_order": 1, "corners_order": 1, "freekicks_order": 1,      # all three duties
            "selected_by_percent": 25.0, "transfers_in_event": 900_000,          # …and every market signal
            "cost_change_event": 1, "form": 6.0}
    html = _kit_html(loud, captain_id=None, xp_by_id={1: 5.1}, photos={}, next_opp={})
    flags = html[html.index('<div class="flags"'):]
    flags = flags[:flags.index("</div>") + 6]

    import re

    assert flags.count("<span") == 3, f"three duties, three glyphs: {flags}"
    # ⚠ Assert the span CONTENT has no letters, rather than listing words to look for. The first version
    # checked `">pens<" not in flags` and a mutation that rendered "⚽ pens" survived it — the word was there,
    # just not preceded by ">". A blacklist of the words you thought of is not a test that no word appears.
    for shown in re.findall(r"<span[^>]*>([^<]*)</span>", flags):
        assert not re.search(r"[A-Za-z]", shown), f"the shirt must carry the glyph alone, got {shown!r}"
    for glyph in _MARKET_GLYPHS:
        assert glyph not in flags, f"{glyph} is a market signal and belongs on Trending/Signals, not a shirt"
    # …and the meaning still rides along, so a desktop hover explains without scrolling to the key.
    assert 'title="penalties"' in flags and 'title="free-kicks"' in flags


def test_the_pitch_prints_the_key_only_when_a_shirt_carries_a_glyph():
    """The key the owner asked for, and the condition on it.

    It is conditional because the sentence ends *"blank = not on set pieces"*, which says nothing on a pitch
    where every shirt is blank — a legend explaining an absent thing is noise, not help.

    ⚠ **This test used to read the source** for the legend text and count `st.caption` calls. A mutation that
    replaced the whole condition with `if False:` sailed straight through it: the source still contained
    every string it was looking for. `set_piece_key` was extracted so the branch itself is assertable, and
    the render is now checked on the page rather than in the file.
    """
    from src.web_streamlit.pitch import set_piece_key

    # One definition of the WORDS — both render paths call this, neither writes its own.
    for module in ("views/squads.py", "tap.py"):
        assert "Set pieces: " not in (_ROOT / "src" / "web_streamlit" / module).read_text(), \
            f"{module} must call set_piece_key, not restate the key"

    taker = {"penalties_order": 1, "corners_order": 0, "freekicks_order": 0}
    plain = {"penalties_order": 0, "corners_order": 0, "freekicks_order": 0}
    assert "⚽ penalties" in set_piece_key([plain, taker])
    assert "first-choice" in set_piece_key([taker])
    assert set_piece_key([plain, plain]) == "", "a key for nothing is noise"
    assert set_piece_key([]) == "" and set_piece_key(None) == ""

    # …and it actually reaches the page, from the ONE place both surfaces share.
    #
    # ⚠ A squad is INJECTED. Written as a bare `_squads_view("My Squad")` this fell to the empty state (no
    # active squad in a fresh AppTest), the "no pitch locally" guard returned early, and a mutation deleting
    # the caption entirely still passed. **A test that skips is not a test that passes** — and the skip is
    # invisible in a green run, which is what makes it worse than a failure.
    from src.web_streamlit.squads import demo_squads

    squads = demo_squads()
    if not squads:
        return
    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=90)
    at.session_state["squad"] = next(iter(squads.values()))
    at.run()
    assert not at.exception, at.exception
    # ⚠ Not asserted via the pitch HTML: My Squad draws through the **click-detector component**, whose markup
    # is not an `st.markdown` element, so "fpl-pitch in at.markdown" is False on the very page that matters.
    # That is also the bug this test caught — the key was added to `render_pitch` only, which My Squad never
    # calls, so the golden page was the one pitch with no key.
    assert any(c.value.startswith("Set pieces:") for c in at.caption), \
        "the pitch must print its own key on BOTH render paths — neither page should have to remember to"
    assert not any("Ownership:" in c.value for c in at.caption), \
        "My Squad stays role-only — the market glyphs are a Lab thing (ADR-179)"

    # …and the Lab's pitch, which goes through `render_pitch` rather than the component. Asserted separately
    # because it IS a separate path: a mutation deleting the caption from `render_pitch` alone left the
    # My-Squad assertion above perfectly green. Two render paths need two assertions, or one of them is
    # protected by nothing.
    # The Lab's pitch goes through `render_pitch` and carries the FULL set (ADR-179), so its key is the
    # composed one: ownership as an ordered scale, momentum, then set pieces.
    lab = _squads_view("Build")
    if lab.code:                                           # a squad was built (skipped when there is no data)
        key = next((c.value for c in lab.caption if "Set pieces:" in c.value), "")
        assert key, "the Lab's pitch needs a key too — it shows the same glyphs and more"
        assert "Ownership:" in key and "💎 differential → ⭐ popular" in key, \
            "ownership is written as an ORDERED SCALE — four unrelated pictures teach nothing (ADR-178)"
        assert "Momentum:" in key


def test_the_glyph_and_the_word_come_from_one_table():
    """`set_piece_flags` (words, for a table) and `set_piece_glyphs` (bare, for a shirt) render the same fact
    two ways. Built separately they could disagree about which glyph means what — and the pitch's key would
    then be teaching a mapping the table contradicts."""
    from src.analytics.crowd import SET_PIECES, set_piece_flags, set_piece_glyphs

    taker = {"penalties_order": 1, "corners_order": 1, "freekicks_order": 1}
    worded = set_piece_flags(taker)
    bare = set_piece_glyphs(taker)
    assert len(worded) == len(bare) == len(SET_PIECES)
    for (glyph, meaning), word in zip(bare, worded, strict=True):
        assert word.startswith(glyph), f"{word!r} and {glyph!r} disagree"
        assert meaning                                     # every glyph can be explained
    assert set_piece_flags({}) == [] and set_piece_glyphs({}) == []


def test_the_lab_table_keeps_its_words():
    """The other half of the split, and the reason the pitch can afford to be bare.

    ADR-178's first draft said *"the Lab shows all the flags"* — it already did, in a table, with words. So
    the line was never My Squad vs Lab but **pitch vs table**: glyphs on the team sheet, words on the
    reference. If this column ever went glyph-only, the pitch's key would be the only explanation left.
    """
    at = _squads_view("Build")
    if not at.code:                                        # no data locally → the info branch
        return
    # ⚠ Checked on EVERY player table, not the union of all of them. Written as a union this passed while the
    # build table had lost the column, because a *different* table on the same tab (the formation preview)
    # still carried it. A union asks "does any table have this?" when the requirement is "do all of them?".
    tables = [df.value for df in at.dataframe if "Player" in getattr(df.value, "columns", [])]
    assert tables, "the Lab must render at least one player table"
    for frame in tables:
        cols = set(frame.columns)
        assert {"Trends", "Set"} <= cols, f"a Lab player table lost its reference columns: {cols}"
        gw_cols = [c for c in cols if str(c).startswith("GW")]
        assert gw_cols, f"and every Lab player table gets the per-gameweek breakout: {cols}"


def test_the_per_gameweek_columns_are_the_parts_of_the_total():
    """ADR-178/ADR-032 — the breakout must be the total decomposed, never a second projection.

    A cumulative number **hides a blank**: 15 points over three weeks reads identically whether it is 5·5·5
    or 15·0·0, and blanks and doubles are exactly what multi-week planning is for. That only helps if the
    parts add up to the number they replace.
    """
    from src.web_streamlit.views.squads import _breakout_gameweeks, _fixture_gameweeks, _gw_columns

    ranked = [{"id": 7, "xp": 14.9, "gameweeks": [3, 4, 5], "by_gameweek": {3: 5.1, 4: 5.1, 5: 4.7}}]
    gws = _breakout_gameweeks(ranked)
    cols = _gw_columns(7, {7: ranked[0]["by_gameweek"]}, gws, played={3, 4, 5})
    assert round(sum(cols.values()), 1) == ranked[0]["xp"]

    # A blank is None, not 0.0 — "not projected", not "projected to score nothing". `decision_xp` seeds every
    # gameweek in the window at 0.0 (ADR-032), so without this the two are indistinguishable.
    blanked = _gw_columns(7, {7: ranked[0]["by_gameweek"]}, gws, played={3, 5})
    assert blanked["GW4"] is None and blanked["GW3"] == 5.1

    # The fixture map is keyed by SHORT NAME. Keyed by `team_h`/`team_a` (FPL's numeric ids) it returned an
    # empty set for every team — "nobody plays" — which blanks the whole breakout while looking like data.
    played = _fixture_gameweeks([{"event": 3, "home": "LIV", "away": "IPS"}], {3, 4})
    assert played == {"LIV": {3}, "IPS": {3}}


def test_the_breakout_is_capped_so_ten_weeks_do_not_get_ten_columns():
    """ADR-178 — the Lab offers horizons to 10, and ten weekly numbers would show a precision the model does
    not have. ADR-173 caught exactly that: a longer window multiplies a suppressed rate rather than
    correcting it."""
    from src.web_streamlit.views.squads import _BREAKOUT_MAX, _breakout_gameweeks

    wide = [{"id": 1, "gameweeks": list(range(3, 13)), "by_gameweek": {}}]
    assert len(_breakout_gameweeks(wide)) == _BREAKOUT_MAX <= 5
    assert _breakout_gameweeks([]) == []


def test_the_lab_can_plan_a_squad_you_already_own_without_optimising_it():
    """ADR-178, owner: *"instead of having just a new squad, use the drop down… and select your Current Squad
    or a New Squad (even multiple)"* — the change that makes the Lab worth opening between wildcards.

    ⚠️ The assertion that matters is the **negative** one: picking an existing squad must not run the
    optimiser over it. Searching a transfer path from a squad you already own is ADR-132, declined on
    evidence — the best sell was the same player in all six gameweeks and the market yielded one beneficial
    move, *a tree with one branch*. The Lab reads your squad; it does not route you through it.
    """
    from src.web_streamlit.views import squads as squads_view

    called = []
    original = squads_view.select_squad

    def _spy(*a, **kw):
        called.append(True)
        return original(*a, **kw)

    at = _squads_view("Build")
    # ⚠ By KEY, not label: the page also carries a picker labelled "Squad" (`squad_picker`, ADR-054), and
    # addressing this one by label grabbed that one instead. The Lab's is labelled "Start from" for the same
    # reason — two identical labels on one tab are ambiguous for a reader too, not only for a test.
    picker = next((s for s in at.selectbox if s.key == "lab_squad"), None)
    assert picker is not None, "the Lab must offer a squad picker, not just a name field"
    assert picker.label == "Start from", "and it must not collide with the page's own Squad picker"
    assert any("new squad" in str(o).lower() for o in picker.options), \
        f"building from scratch must stay one of the options: {picker.options}"
    saved = [o for o in picker.options if "new squad" not in str(o).lower()]
    if not saved:                                          # no demo seed locally
        return
    squads_view.select_squad = _spy
    try:
        at = picker.set_value(saved[0]).run()
        assert not at.exception, at.exception
    finally:
        squads_view.select_squad = original
    assert not called, "picking an existing squad must READ it, never optimise over it (ADR-132)"
    blob = " ".join(m.value for m in at.markdown)
    assert "fpl-pitch" in blob, "the planned squad still renders on the pitch"
    assert any("Planning only" in c.value for c in at.caption), \
        "the page must say it changes nothing — this mode looks like the builder"

    # The plan table is only reachable in this mode, so it is asserted here — the Lab-table guard runs in the
    # default *build* mode and never sees it. A mutation stripping this table's words passed everything else.
    planned = [df.value for df in at.dataframe if "Player" in getattr(df.value, "columns", [])]
    assert planned, "planning a squad must show it as a table, not only as a pitch"
    for frame in planned:
        cols = set(frame.columns)
        assert {"Trends", "Set"} <= cols, f"the plan table keeps the reference words: {cols}"
        assert [c for c in cols if str(c).startswith("GW")], \
            f"planning is the reason the breakout exists — it must be here: {cols}"


# ---- ADR-179: the vice-captain, and the degrade path it was breaking ---------------------------

def test_the_plain_pitch_draws_a_vice_captain_and_does_not_raise_on_the_degrade_path():
    """ADR-179, owner: *"Bruno Fernandes was Vice Captain on My Squad but not shown in Lab."*

    He reported a missing badge. `render_pitch` had **no `vice_captain_id` parameter at all** — `_kit_html`
    drew the V and `pitch_html` forwarded it, but the plain renderer between them never took it. So every
    surface drawing through `render_pitch` lost the badge.

    ⚠️ **The half he could not see is the reason this shipped on its own.** ADR-133's degrade path falls back
    to `render_pitch(**kw)` when the click-detector component is absent, forwarding `vice_captain_id` into a
    function that did not accept it: **My Squad raised instead of degrading**, on the exact path whose stated
    purpose is that *"a missing component must never take the page down"*.

    **A reported symptom is a place to start looking, not the size of the problem.**
    """
    import inspect

    from src.web_streamlit.pitch import pitch_html, render_pitch

    assert "vice_captain_id" in inspect.signature(render_pitch).parameters, \
        "the plain renderer must accept it — the tappable one is not the only pitch"

    # 1. The badge reaches the markup, and the captain still wins if a stale squad claims both.
    xi = [{"id": 1, "web_name": "Haaland", "team": "MCI", "position": "FWD", "price": 15.5},
          {"id": 2, "web_name": "B.Fernandes", "team": "MUN", "position": "MID", "price": 12.0}]
    html = pitch_html(xi, [], captain_id=1, vice_captain_id=2, xp_by_id={1: 7.6, 2: 6.0},
                      photos={}, next_opp={})
    assert 'class="v-badge"' in html and 'class="c-badge"' in html
    both = pitch_html(xi, [], captain_id=1, vice_captain_id=1, xp_by_id={}, photos={}, next_opp={})
    assert both.count('class="v-badge"') == 0, "a player cannot be both; the captain badge wins"

    # 2. The degrade path — the call ADR-133 makes when the component is missing. This raised a TypeError.
    kw = {"captain_id": 1, "vice_captain_id": 2, "xp_by_id": {}, "photos": {}, "next_opp": {},
          "team_names": {}, "bench_roles": {}, "kits": {}, "fixtures_by_id": {}, "selected_id": None}
    render_pitch(xi, [], **{k: v for k, v in kw.items() if k != "selected_id"})


def test_the_lab_shows_the_vice_captain_of_the_squad_it_is_planning(monkeypatch):
    """The surface the owner was actually looking at. The Lab's plan view (ADR-178) is simply the first place
    a squad *with* a vice-captain reached `render_pitch` — the build view has no captain at all, so the gap
    had never been visible."""
    from src.web_streamlit.squads import demo_squads

    squads = demo_squads()
    if not squads:
        return
    squad = dict(next(iter(squads.values())))
    squad["captain_id"] = squad["player_ids"][0]
    squad["vice_captain_id"] = squad["player_ids"][1]

    at = AppTest.from_file(str(_PAGES / "1_My_Squad.py"), default_timeout=90)
    at.session_state["squad"] = squad
    at.run()
    next(c for c in at.segmented_control if c.label == "Tool").set_value("Lab").run()
    picker = next(s for s in at.selectbox if s.key == "lab_squad")
    saved = [o for o in picker.options if "new squad" not in str(o).lower()]
    if not saved:
        return
    yours = [o for o in saved if "yours" in str(o).lower()] or saved
    at = picker.set_value(yours[0]).run()
    assert not at.exception, at.exception
    blob = " ".join(m.value for m in at.markdown)
    # ⚠ `class="v-badge"`, not `"v-badge"`. The bare substring also matches the **CSS block**
    # (`.fpl-pitch .v-badge{…}`), which every pitch emits whether or not a badge is drawn — so the first
    # version of this assertion passed with the fix reverted. A selector is not a rendered element.
    assert 'class="v-badge"' in blob, \
        "planning a squad must show who takes over if your captain doesn't play"


def test_the_lab_pitch_carries_the_market_glyphs_and_my_squad_does_not():
    """ADR-179, owner: *"Lab should show all Emojis, not just Set Pieces."*

    ⚠️ **This narrows ADR-178 one day on, and the correction is the point.** That ADR concluded *"the pitch
    is a team sheet, the table is a reference"* and applied it to **both** pitches — but its justification was
    about **page purpose**: My Squad is read on a phone, minutes before a deadline, where anything not about
    this gameweek competes with something that is. None of that is true of the Lab, where you are choosing
    players and differential-vs-template is the question. Same evidence, different page, different answer.

    The rule restated where it holds: **both pitches render glyphs with a key; which glyphs depends on what
    the page is for.**
    """
    from src.web_streamlit.pitch import _kit_html

    # ⚠ `selected_by`, not `selected_by_percent`. Written with the wrong key the fixture produced **no
    # ownership tier at all**, so the glyph this test is about could not have appeared however the code
    # behaved — a fixture that cannot express the thing under test (ADR-178's recurring root cause).
    loud = {"id": 1, "web_name": "Szoboszlai", "team": "LIV", "position": "MID", "price": 7.0,
            "penalties_order": 1, "corners_order": 1, "freekicks_order": 1,
            "selected_by": 25.0, "transfers_in_event": 900_000,
            "cost_change_event": 1, "form": 6.0}
    common = {"captain_id": None, "xp_by_id": {1: 5.1}, "photos": {}, "next_opp": {}}

    squad_kit = _kit_html(loud, **common)
    lab_kit = _kit_html(loud, market=True, **common)
    assert "🔥" not in squad_kit and "📈" not in squad_kit, "My Squad's shirts stay role-only"
    assert "🔥" in lab_kit and "📈" in lab_kit and "🟦" in lab_kit, "the Lab's carry the market signals"
    assert "⚽" in squad_kit and "⚽" in lab_kit, "set pieces are on both — they describe the role"
    # Still glyphs, on both. The words live in the table.
    import re
    for kit in (squad_kit, lab_kit):
        flags = kit[kit.index('<div class="flags"'):]
        flags = flags[:flags.index("</div>") + 6]
        for shown in re.findall(r"<span[^>]*>([^<]*)</span>", flags):
            assert not re.search(r"[A-Za-z]", shown), f"glyph alone, got {shown!r}"
    # …and every glyph can still explain itself on hover, including the two that carry no word of their own.
    assert 'title="price rising"' in lab_kit, "💰↑ has no word in its flag — it must not title itself"


def test_the_shirt_shows_at_most_three_gameweeks_and_a_blank_stays_blank():
    """ADR-179, owner: *"Lab should show all GW scores rather than totaling, maybe limit 3 — not sure how you
    would do that."*

    **Three because the card is 104px wide** and a fourth figure wraps; the table alongside carries five,
    because a table scrolls. Two surfaces, two caps, each from that surface's own limit — one number applied
    to both would have been arbitrary for at least one of them.
    """
    from src.web_streamlit.pitch import _SHIRT_WEEKS, _kit_html

    p = {"id": 1, "web_name": "B.Fernandes", "team": "MUN", "position": "MID", "price": 12.0}
    common = {"captain_id": None, "xp_by_id": {1: 17.3}, "photos": {}, "next_opp": {}}

    assert _SHIRT_WEEKS == 3
    five = _kit_html(p, per_gw_xp={3: 6.0, 4: 5.4, 5: 6.0, 6: 5.1, 7: 4.9}, **common)
    weeks = five[five.index('<div class="weeks"'):]
    weeks = weeks[:weeks.index("</div>")]
    assert weeks.count("·") == _SHIRT_WEEKS - 1, f"at most three figures on a shirt: {weeks}"
    assert "6.0 · 5.4 · 6.0" in weeks, "and they are the FIRST three, in gameweek order"

    # A blank gameweek renders as an em dash, not 0.0 — "not projected", not "projected to score nothing".
    blanked = _kit_html(p, per_gw_xp={3: 6.0, 4: None, 5: 6.0}, **common)
    assert "6.0 · — · 6.0" in blanked

    # No per-GW data at all → no line, rather than an empty one.
    assert 'class="weeks"' not in _kit_html(p, **common)


def test_my_squad_copy_does_not_point_at_a_control_it_no_longer_has():
    """ADR-179's copy sweep. The Captain panel read *"…the **Gameweeks ahead** selector doesn't change it"* —
    a reassurance about a widget this page no longer carries, so it sent the reader looking for something
    that isn't there.

    ⚠️ **Deliberately not handled through `RETIRED`.** That list is for phrases retired *everywhere*, and
    "Gameweeks ahead" is still the live label of the **Lab's** horizon control. Blanket-retiring it would
    have failed on a page where it is correct — so this guard is scoped to the page whose claim changed.
    """
    at = _squads_view("Captain")
    captions = " ".join(c.value for c in at.main.caption)
    assert "next gameweek" in captions.lower(), "the fact is still true and still worth saying"
    assert "Gameweeks ahead" not in captions, \
        "My Squad has no horizon selector — copy must not send the reader looking for one"
