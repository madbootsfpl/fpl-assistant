"""Captain — who to (vice-)captain from your squad this week (ADR-029), interactively.

Pick your **active squad** (built/uploaded) or a **demo** squad. Runs the SAME engine the CLI's `captain`
command does (`captain_picks` → `render_captain_picks`) on the squad's players — GK-excluded, xP-ranked,
xMins-weighted — so the web can't drift from the CLI (ADR-054).
"""

import streamlit as st

from src.analytics import baseline_rate, captain_picks, minutes_weight_from_history
from src.storage import Storage
from src.ui.captain import render_captain_picks
from src.web_streamlit.squads import render_sidebar, set_active_squad, set_captain, squad_picker

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

    # Set & persist YOUR captain (ADR-055) — stored on the session squad, shown (C) in Analyse + the
    # download. Defaults to the current captain, else the top recommendation. Editing a demo adopts a copy.
    current = squad.get("captain_id")
    if current:
        cur = next((p["web_name"] for p in owned if p["id"] == current), "?")
        st.caption(f"Your captain: **{cur} (C)**")
    labels = {f"{p['position']} {p['web_name']}": p["id"] for p in owned}
    recommended = picks[0]["id"] if picks else None
    want = current or recommended
    idx = next((i for i, pid in enumerate(labels.values()) if pid == want), 0)
    choice = st.selectbox("Set your captain", list(labels), index=idx, key="set_captain")
    if st.button("Set as captain"):
        set_active_squad(set_captain(squad, labels[choice]))
        st.success(f"Captain set: **{choice.split(' ', 1)[1]} (C)** — shown in Analyse + your download.")
        st.rerun()
