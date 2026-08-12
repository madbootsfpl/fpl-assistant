"""Squad Lab — build a fresh 15 (ADR-105; the old Squads → *Build* view, ADR-062).

The full `squad` optimiser (budget · objective · archetypes · include/exclude · declared bench · build modes)
→ a saveable/usable 15, with a per-fixture xP over the chosen horizon. Split to its own tab (ADR-105) so
*creating* a squad (season start · wildcard · revamp) is separate from *managing* it (My Squad). Reuses
`render_build` unchanged; no server writes (download / **Use this squad →** to keep it).
"""

from datetime import datetime, timezone

import streamlit as st

from src.storage import Storage
from src.ui.deadline import deadline_line
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import render_sidebar
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import squads as views

st.set_page_config(**brand.page_config("Squad Lab"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Squad Lab")
render_data_status()
render_sidebar()
st.title("🧪 Squad Lab")   # wave-2 feedback: a lab motif (was the boot emoji + the MADBOOTS mascot image)
st.caption("**Build your squad** — the full optimiser. New season, a wildcard, or a revamp. **Use this squad →** "
           "sends it to **My Squad** to manage.")

# The build optimises over this window (ADR-077) — longer for a wildcard / start of season.
horizon = st.segmented_control(
    "Gameweeks ahead", [1, 2, 3, 4, 5, 10], default=5,
    help="How many upcoming gameweeks the build optimises over — longer for a wildcard / start of season.") or 5

store = Storage()
try:
    with analytics.timed("data_load", page="Squad Lab"):    # perf: FPL data loading (ADR-100, US-336)
        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        history = store.get_history_by_code()
        gw_history = store.get_gw_history_by_code()          # in-season form (ADR-060; dormant now)
        teams = store.get_teams()
    photos = photo_url_by_id(players, teams)                 # photo, else the club shirt (US-255)
    badges = badge_url_by_short_name(teams)
finally:
    store.close()

_line = deadline_line(upcoming, datetime.now(timezone.utc))    # the next FPL deadline (ADR-086/US-267)
if _line:
    st.caption(_line[2])

if not players:
    st.info("No players — run `python app.py refresh` first.")
else:
    views.render_build(players, upcoming, history, gw_history, photos, badges, horizon=horizon)
