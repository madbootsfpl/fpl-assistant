"""Players — the player pool + the stat boards in one tab (ADR-069).

A shared team/position/player filter (ADR-064) over a segmented-control sub-nav: **Pool** (the ranked,
paginated table + a top-15 bar) and the season-to-date stat boards (over/under · DefCon · clean sheets ·
xG, ADR-063). Only the selected view computes (lazy). Reuses the CLI analytics; display-only.
"""

import streamlit as st

from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.filters import filter_controls
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import players as views

st.set_page_config(page_title="Players · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
st.title("Players")

store = Storage()
try:
    rows = store.get_players()
    badges = badge_url_by_short_name(store.get_teams())     # {short_name: badge URL}
    photos = photo_url_by_id(rows)                          # {player id: photo URL}
finally:
    store.close()

if not rows:
    st.info("No data yet — run `python app.py refresh` first.")
else:
    # One shared filter (ADR-064) — applies to the pool and every stat board (price no-op on stat rows).
    sel = filter_controls(rows, key="players", with_price=True)
    view = st.segmented_control(
        "View", ["Pool", "Over / under-perf", "Defensive Contribution", "Clean sheets", "xG / xA / xGI"],
        default="Pool", help="Switch between the player pool and the season-to-date stat boards.")

    if view == "Over / under-perf":
        views.render_over_under(rows, sel, badges)
    elif view == "Defensive Contribution":
        views.render_defcon(rows, sel, badges)
    elif view == "Clean sheets":
        views.render_cleansheet(rows, sel, badges)
    elif view == "xG / xA / xGI":
        views.render_xg(rows, sel, badges)
    else:                                                   # "Pool" (default; also if the control resets)
        views.render_pool(rows, sel, photos, badges)
