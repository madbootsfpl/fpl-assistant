"""Players — the player pool + the stat boards in one tab (ADR-069).

A shared team/position/player filter (ADR-064) over a segmented-control sub-nav: **Pool** (the ranked,
paginated table + a top-15 bar) and the season-to-date stat boards (over/under · DefCon · clean sheets ·
xG, ADR-063). Only the selected view computes (lazy). Reuses the CLI analytics; display-only.
"""

import streamlit as st

from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.filters import filter_controls
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import players as views

st.set_page_config(**brand.page_config("Players"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Players")
render_data_status()
st.title("👟 Players")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("The whole player pool + the stat boards — filter, sort, and see who's over/under-performing.")
st.caption("🎯 Looking for **who to buy**? The **Radar** (on the **Fixtures** tab) shortlists the best players "
           "from the easiest-run teams.")

store = Storage()
try:
    with analytics.timed("data_load", page="Players"):     # perf: FPL data loading (ADR-100, US-336)
        rows = store.get_players()
        teams = store.get_teams()
    badges = badge_url_by_short_name(teams)                 # {short_name: badge URL}
    photos = photo_url_by_id(rows, teams)                   # {player id: photo, else the club shirt}
finally:
    store.close()

if not rows:
    st.info("No data yet — it's refreshing; check back shortly.")
else:
    # One shared filter (ADR-064) — applies to the pool and every stat board (price no-op on stat rows).
    sel = filter_controls(rows, key="players", with_price=True)
    view = st.segmented_control(
        "View", ["Pool", "Card", "Set pieces", "Over / under-perf", "Defensive Contribution", "Clean sheets",
                 "xG / xA / xGI", "History"],
        default="Pool", help="Switch between the player pool, a rich **player card**, the stat boards, and a "
                             "player's season history.")

    if view == "Card":                                     # a rich, position-adaptive player card (US-343)
        views.render_card(rows, sel, teams, photos, badges)
    elif view == "Set pieces":
        views.render_set_pieces(rows, sel, badges)
    elif view == "Over / under-perf":
        views.render_over_under(rows, sel, badges)
    elif view == "Defensive Contribution":
        views.render_defcon(rows, sel, badges)
    elif view == "Clean sheets":
        views.render_cleansheet(rows, sel, badges)
    elif view == "xG / xA / xGI":
        views.render_xg(rows, sel, badges)
    elif view == "History":                                 # a per-player season history (US-298)
        views.render_history(rows, photos, badges)
    else:                                                   # "Pool" (default; also if the control resets)
        views.render_pool(rows, sel, photos, badges)
