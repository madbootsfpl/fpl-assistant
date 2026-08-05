"""Captain — who to (vice-)captain from your squad this week (ADR-029), interactively.

Pick your **active squad** (built/uploaded) or a **demo** squad. Runs the SAME engine the CLI's `captain`
command does (`captain_picks` → `render_captain_picks`) on the squad's players — GK-excluded, xP-ranked,
xMins-weighted — so the web can't drift from the CLI (ADR-054).
"""

import streamlit as st

from src.analytics import baseline_rate, captain_picks, minutes_weight_from_history
from src.storage import Storage
from src.ui.captain import render_captain_picks
from src.web_streamlit.squads import render_sidebar, squad_picker

st.set_page_config(page_title="Captain · FPL Assistant", page_icon="⚽", layout="wide")
render_sidebar()
st.title("Captain — who to captain this week")

squad_name, squad = squad_picker()

store = Storage()
try:
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    history = store.get_history_by_code()
finally:
    store.close()

owned = [p for p in players if p["id"] in set(squad["player_ids"])]

if not players:
    st.info("No players — run `python app.py refresh` first.")
elif not owned:
    st.info(f"Squad '{squad_name}' has no current players to captain.")
else:
    baseline_by_code = {code: baseline_rate(rows) for code, rows in history.items()}
    minutes_weight = minutes_weight_from_history(history)      # xMins v0 (ADR-038), default-on
    picks = captain_picks(owned, upcoming, baseline_by_code=baseline_by_code,
                          minutes_weight=minutes_weight, history_by_code=history)
    st.code(render_captain_picks(picks, squad_name=squad_name, show_xmins=True), language=None)
