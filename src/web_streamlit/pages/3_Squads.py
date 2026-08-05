"""Analyse — your squad's health over the next N gameweeks (ADR-031), interactively.

Pick your **active squad** (built/uploaded) or a **demo** squad. Runs the SAME engine the CLI's `analyse`
command does (`decision_xp` → `best_legal_xi` → `analyse_squad` → `render_squad_analysis`) on the squad
**dict** — so an uploaded squad works and the web can't drift from the CLI (ADR-054).
"""

import streamlit as st

from src.analytics import analyse_squad, best_legal_xi, decision_xp
from src.storage import Storage
from src.ui.analyse import render_squad_analysis
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import render_sidebar, squad_picker
from src.web_streamlit.status import render_data_status
from src.web_streamlit.tables import render_player_table

_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}

st.set_page_config(page_title="Analyse · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
render_sidebar()
st.title("Analyse — your squad's health")

squad_name, squad = squad_picker()

store = Storage()
try:
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    history = store.get_history_by_code()
    photos = photo_url_by_id(players)
    badges = badge_url_by_short_name(store.get_teams())
finally:
    store.close()

owned = [p for p in players if p["id"] in set(squad["player_ids"])]

if not players:
    st.info("No players — run `python app.py refresh` first.")
elif not owned:
    st.info(f"Squad '{squad_name}' has no current players to analyse.")
else:
    ranked = decision_xp(players, upcoming, history)            # xMins-weighted (default)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    # The XI: the declared bench's complement, else the best legal XI (shared with the CLI via
    # best_legal_xi, so they can't diverge — ADR-031/040).
    bench_ids = set(squad.get("bench_ids") or [])
    xi_ids = ({p["id"] for p in owned if p["id"] not in bench_ids} if bench_ids
              else best_legal_xi(owned, xp_by_id))
    analysis = analyse_squad(
        owned, xi_ids, xp_by_id,
        by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
        gameweeks=ranked[0]["gameweeks"] if ranked else [],
        weight_by_id={r["id"]: r["minutes_weight"] for r in ranked},
    )
    # An image table of the squad (XI then bench, (C) marked), then the health summary beneath (Sprint 059).
    captain_id = squad.get("captain_id")
    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"] + (" (C)" if p["id"] == captain_id else ""),
        "Team": p["team"], "£m": p["price"], "xP": round(xp_by_id.get(p["id"], 0), 1),
        "Role": "XI" if p["id"] in xi_ids else "Bench",
    } for p in sorted(owned, key=lambda x: (x["id"] not in xi_ids, _ORDER.get(x["position"], 9)))])
    st.code(render_squad_analysis(analysis, squad_name, show_xmins=True,
                                  captain_id=captain_id), language=None)
