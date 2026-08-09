"""Squads — build & manage your team in one tab (ADR-069).

A segmented-control sub-nav over the five squad tools: **Build** (the full `squad` options → a saveable 15),
then **My Squad** (edit) · **Health** (analyse) · **Transfer** (XI-aware swaps) · **Captain** — the four
manage views sharing one squad picker. Only the selected view computes (lazy). Each reuses the CLI engine +
renderers; no server writes (your squad lives in the session — download to keep it).
"""

from datetime import datetime, timezone

import streamlit as st

from src.storage import Storage
from src.ui.deadline import deadline_line
from src.web_streamlit import analytics
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import render_sidebar, squad_picker
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import squads as views

st.set_page_config(page_title="Squads · FPL Assistant", page_icon="⚽", layout="wide")
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Squads")
render_data_status()
render_sidebar()
st.title("🧩 Squads")
st.caption("Everything for your team in one place — build it, tweak it, and get this week's plan.")

view = st.segmented_control(
    "Tool", ["Build", "My Squad", "AI Tips", "Chips", "Health", "Transfer", "Captain"], default="Build",
    help="Build a new squad, then manage the one you're working on. **AI Tips** = a grounded gameweek "
         "plan (captain · lineup · a transfer · flags) for your squad. **Chips** = when to play each chip "
         "(Triple Captain · Bench Boost · Free Hit · Wildcard).")

# The prediction horizon flows through every sub-tab (ADR-077). A box select (US-315) over a handful of
# useful windows — short for mid-season, up to 10 for a wildcard / start of season. Default 5 = today's
# behaviour; deselecting the segmented control falls back to 5.
horizon = st.segmented_control(
    "Gameweeks ahead", [1, 2, 3, 4, 5, 10], default=5,
    help="How many upcoming gameweeks the projections look over — short for mid-season, longer for a "
         "wildcard / start of season. (Captaincy is always the next gameweek.)") or 5

store = Storage()
try:
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    history = store.get_history_by_code()
    gw_history = store.get_gw_history_by_code()      # in-season form (ADR-060; dormant now)
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
elif view == "Build":
    views.render_build(players, upcoming, history, gw_history, photos, badges, horizon=horizon)
else:
    squad_name, squad = squad_picker()      # one picker feeds the four manage views
    analytics.track("analysis_run", view=view)   # usage: which manage view was run (no squad contents)
    if view == "My Squad":
        views.render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos,
                              horizon=horizon)
    elif view == "AI Tips":
        views.render_ai_tips(squad_name, squad, horizon=horizon)
    elif view == "Chips":
        views.render_chips(squad_name, squad, horizon=horizon)
    elif view == "Health":
        views.render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges,
                            horizon=horizon)
    elif view == "Transfer":
        views.render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos,
                              horizon=horizon)
    elif view == "Captain":
        team_names = {t["short_name"]: t["name"] for t in teams}   # "MUN" → "Man Utd" (US-278)
        views.render_captain(squad_name, squad, players, upcoming, history, photos, badges, team_names)
