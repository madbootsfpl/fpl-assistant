"""My Squad — manage your team + its tools (ADR-105, split from the old Squads page, ADR-069).

A segmented-control sub-nav over the pitch/edit view + the five tools — **My Squad** (edit) · **AI Tips** ·
**Captain** · **Transfer** · **Chips** · **Health** — sharing one squad picker + horizon. Building a *new*
squad now lives in its own **Squad Lab** tab. Only the selected view computes (lazy); each reuses the CLI engine
+ renderers; no server writes (your squad lives in the session — download to keep it).
"""

from datetime import datetime, timezone

import streamlit as st

from src.storage import Storage
from src.ui.deadline import deadline_line
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import active_squad, render_sidebar, squad_picker
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import squads as views

st.set_page_config(**brand.page_config("My Squad"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("My Squad")
render_data_status()
render_sidebar()
st.title("🧩 My Squad")
st.caption("Your team in one place — see it, tweak it, and get this week's plan. Build a fresh one in **Squad Lab**.")

if active_squad() is None:   # US-360: no team built/loaded yet → point new users at the builder (the views use a demo)
    st.info("🛠️ **No team yet?** The views below use a demo — build your own in the **🥾 Squad Lab** tab "
            "(in the sidebar), then it lands here.")

view = st.segmented_control(
    "Tool", ["My Squad", "AI Tips", "Captain", "Transfer", "Chips", "Health"], default="My Squad",
    help="Manage the squad you're working on. **AI Tips** = a grounded gameweek plan (captain · lineup · a "
         "transfer · flags); **Captain** who to (vice-)captain; **Transfer** the best swaps; **Chips** when to "
         "play each chip; **Health** the 5-GW analysis. (Build a *new* squad in the **Squad Lab** tab.)")

# The prediction horizon flows through every sub-tab (ADR-077). A box select (US-315) over a handful of
# useful windows — short for mid-season, up to 10 for a wildcard / start of season. Default 5 = today's
# behaviour; deselecting the segmented control falls back to 5.
horizon = st.segmented_control(
    "Gameweeks ahead", [1, 2, 3, 4, 5, 10], default=5,
    help="How many upcoming gameweeks the projections look over — short for mid-season, longer for a "
         "wildcard / start of season. (Captaincy is always the next gameweek.)") or 5

store = Storage()
try:
    with analytics.timed("data_load", page="My Squad"):    # perf: FPL data loading (ADR-100, US-336)
        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        history = store.get_history_by_code()
        gw_history = store.get_gw_history_by_code()   # in-season form (ADR-060; dormant now)
        teams = store.get_teams()
    photos = photo_url_by_id(players, teams)          # photo, else the club shirt (US-255)
    badges = badge_url_by_short_name(teams)
finally:
    store.close()

_line = deadline_line(upcoming, datetime.now(timezone.utc))    # the next FPL deadline (ADR-086/US-267)
if _line:
    st.caption(_line[2])                                       # the text; the emoji conveys urgency

if not players:
    st.info("No players — run `python app.py refresh` first.")
else:
    squad_name, squad = squad_picker()      # one picker feeds the manage views
    analytics.track("analysis_run", view=view)   # usage: which manage view was run (no squad contents)
    if view == "My Squad":
        views.render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos,
                              teams=teams, horizon=horizon)
    elif view == "AI Tips":
        views.render_ai_tips(squad_name, squad, horizon=horizon)
    elif view == "Captain":
        team_names = {t["short_name"]: t["name"] for t in teams}   # "MUN" → "Man Utd" (US-278)
        views.render_captain(squad_name, squad, players, upcoming, history, photos, badges, team_names)
    elif view == "Transfer":
        views.render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos,
                              horizon=horizon)
    elif view == "Chips":
        views.render_chips(squad_name, squad, horizon=horizon)
    elif view == "Health":
        views.render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges,
                            horizon=horizon)
