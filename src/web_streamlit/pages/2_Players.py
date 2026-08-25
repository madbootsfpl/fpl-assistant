"""Players — the player pool + the stat boards in one tab (ADR-069).

A shared team/position/player filter (ADR-064) over a segmented-control sub-nav: **Pool** (the ranked,
paginated table + a top-15 bar) and the season-to-date stat boards (over/under · DefCon · clean sheets ·
xG, ADR-063). Only the selected view computes (lazy). Reuses the CLI analytics; display-only.
"""

import streamlit as st

from src.analytics import last_season_name, last_season_rows
from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.filters import filter_controls
from src.web_streamlit.squads import active_squad
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import players as views

st.set_page_config(**brand.page_config("Players"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Players")
render_data_status()
st.title("👟 Players")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("Explore the full player pool and stats — filter, sort and see who's over- or under-performing, "
           "with form, clean sheets, xG, xA, xGI, set pieces and history.")
st.caption("🎯 Looking for **who to buy**? The **Radar** view below shortlists the best players from the "
           "easiest-run teams (it moved here from the fixtures tab — ADR-134).")

store = Storage()
try:
    with analytics.timed("data_load", page="Players"):     # perf: FPL data loading (ADR-100, US-336)
        rows = store.get_players()
        teams = store.get_teams()
        # ADR-126: last season, for the three boards that need ~10 matches before they can answer.
        history = store.get_history_by_code()
        # ADR-134: the 🎯 Radar lives here now, and it ranks players by their team's upcoming run.
        upcoming = store.get_upcoming_fixtures()
        gw_history = store.get_gw_history_by_code()
    badges = badge_url_by_short_name(teams)                 # {short_name: badge URL}
    photos = photo_url_by_id(rows, teams)                   # {player id: photo, else the club shirt}
finally:
    store.close()

if not rows:
    st.info("No data yet — it's refreshing; check back shortly.")
else:
    # One shared filter (ADR-064) — applies to the pool and every stat board (price no-op on stat rows).
    _sq = active_squad()                                    # US-407b: a "My squad only" scope on the pool filter
    sel = filter_controls(rows, key="players", with_price=True,
                          my_squad_ids=set(_sq["player_ids"]) if _sq else None)
    # ADR-126: last season's numbers in player shape, so a board that can't answer from this season yet shows
    # last season rather than nothing. Computed once and shared — only the three gated boards read it.
    _last_rows = last_season_rows(rows, history)
    _last_name = last_season_name(history)
    view = st.segmented_control(
        # ADR-134: the Radar moved here from the fixtures tab, taking the list to nine. Labels shortened in the
        # same change so nine still fit the three rows that eight occupied — the move is what made it necessary.
        "View", ["Pool", "Card", "Radar", "Set pieces", "Over/under", "DefCon", "Clean sheets",
                 "xG · xA", "History"],
        default="Pool", help="The player pool, a rich **player card**, the 🎯 **Radar** (best players from the "
                             "easiest-run teams), the stat boards, and a player's season history.")

    if view == "Card":                                     # a rich, position-adaptive player card (US-343)
        views.render_card(rows, sel, teams, photos, badges)
    elif view == "Set pieces":
        views.render_set_pieces(rows, sel, badges)
    elif view == "Radar":
        views.render_radar(rows, sel, badges, upcoming, history, gw_history)
    elif view == "Over/under":
        views.render_over_under(rows, sel, badges, _last_rows, _last_name)
    elif view == "DefCon":
        views.render_defcon(rows, sel, badges, _last_rows, _last_name)
    elif view == "Clean sheets":
        views.render_cleansheet(rows, sel, badges, _last_rows, _last_name)
    elif view == "xG · xA":
        views.render_xg(rows, sel, badges)
    elif view == "History":                                 # a per-player season history (US-298)
        views.render_history(rows, sel, photos, badges)
    else:                                                   # "Pool" (default; also if the control resets)
        views.render_pool(rows, sel, photos, badges)
