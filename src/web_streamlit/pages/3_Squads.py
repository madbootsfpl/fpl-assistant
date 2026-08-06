"""Squads — build & manage your team in one tab (ADR-069).

A segmented-control sub-nav over the five squad tools: **Build** (the full `squad` options → a saveable 15),
then **My Squad** (edit) · **Health** (analyse) · **Transfer** (XI-aware swaps) · **Captain** — the four
manage views sharing one squad picker. Only the selected view computes (lazy). Each reuses the CLI engine +
renderers; no server writes (your squad lives in the session — download to keep it).
"""

import streamlit as st

from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import render_sidebar, squad_picker
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import squads as views

st.set_page_config(page_title="Squads · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
render_sidebar()
st.title("Squads")

view = st.segmented_control(
    "Tool", ["Build", "My Squad", "Health", "Transfer", "Captain"], default="Build",
    help="Build a new squad, then manage the one you're working on (My Squad · Health · Transfer · Captain).")

store = Storage()
try:
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    history = store.get_history_by_code()
    gw_history = store.get_gw_history_by_code()      # in-season form (ADR-060; dormant now)
    photos = photo_url_by_id(players)
    badges = badge_url_by_short_name(store.get_teams())
finally:
    store.close()

if not players:
    st.info("No players — run `python app.py refresh` first.")
elif view == "Build":
    views.render_build(players, upcoming, history, gw_history, photos, badges)
else:
    squad_name, squad = squad_picker()      # one picker feeds the four manage views
    if view == "My Squad":
        views.render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos)
    elif view == "Health":
        views.render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges)
    elif view == "Transfer":
        views.render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos)
    elif view == "Captain":
        views.render_captain(squad_name, squad, players, upcoming, history, photos, badges)
