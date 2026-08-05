"""Build — the optimal 15 within a budget, shaped by archetypes (ADR-041/043/044), interactively.

Runs the SAME engine the CLI's `squad` command does — `decision_xp` (xMins-weighted xP) → `archetype_bands`
→ `select_squad` → `best_legal_xi` → `render_squad` — so the web can't drift from the CLI. The structured
result becomes a **downloadable `squad.json`** (the CLI `SquadStore` format) and can be set as this session's
**active squad** for Transfer/Analyse/Captain (ADR-054). No server writes — Download *is* your save.
"""

import datetime
import json

import streamlit as st

from src.analytics import SQUAD_15, archetype_bands, best_legal_xi, crowd_flags, decision_xp, select_squad
from src.storage import Storage
from src.ui.squad import render_squad
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import render_sidebar, set_active_squad
from src.web_streamlit.status import render_data_status
from src.web_streamlit.tables import render_player_table

_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}

st.set_page_config(page_title="Build · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
render_sidebar()
st.title("Build — the optimal 15 within a budget")

col1, col2 = st.columns(2)
budget = col1.slider("Budget (£m)", 80.0, 100.0, 100.0, step=0.5)
name = col1.text_input("Squad name", value="My squad", max_chars=40).strip() or "My squad"
cheap = col2.number_input("Low-cost (≤£4.5m)", min_value=0, max_value=8, value=0)
premium = col2.number_input("Premium (≥£9m)", min_value=0, max_value=5, value=0)
differential = col2.number_input("Differentials (≤5% owned)", min_value=0, max_value=5, value=0)

store = Storage()
try:
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    history = store.get_history_by_code()
    photos = photo_url_by_id(players)
    badges = badge_url_by_short_name(store.get_teams())
finally:
    store.close()

if not players:
    st.info("No players — run `python app.py refresh` first.")
else:
    ranked = decision_xp(players, upcoming, history)                # xMins-weighted (default)
    scores = {r["id"]: r["xp"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}
    bands = archetype_bands(cheap=cheap or None, premium=premium or None)
    result = select_squad(players, budget=budget, formation=SQUAD_15, scores=scores,
                          band_minimums=bands, min_differentials=differential or None)
    xi_ids = best_legal_xi(result["selected"], scores) if result["status"] == "Optimal" else None
    # Attach the optimised xP + xMins onto the picked players so the table (and the projected-xP total)
    # render them — the same step the CLI does before `render_squad` (cli.py cmd_squad, ADR-041/US-121).
    for p in result["selected"]:
        p["xp"] = scores.get(p["id"], 0)
        p["minutes_weight"] = weight_by_id.get(p["id"], 1.0)

    # An image table of the 15 (photos + badges), then the CLI text summary beneath (the totals /
    # XI-bench breakout / notes) — the "augment" approach (Sprint 059).
    if result["status"] == "Optimal":
        xi = set(xi_ids or [])
        render_player_table([{
            "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
            "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
            "£m": p["price"], "xP": round(p.get("xp", 0), 1),
            "Role": "XI" if p["id"] in xi else "Bench", "Trends": " ".join(crowd_flags(p)),
        } for p in sorted(result["selected"], key=lambda x: (x["id"] not in xi, _ORDER.get(x["position"], 9)))])
    st.code(render_squad(result, budget=budget, objective="xp", full=True, xi_ids=xi_ids), language=None)

    if result["status"] == "Optimal":
        selected = result["selected"]
        squad = {
            "player_ids": [p["id"] for p in selected],
            "player_names": [p["web_name"] for p in selected],
            "bench_ids": [p["id"] for p in selected if p["id"] not in set(xi_ids)],
            "cost": result["total_cost"],
            "saved_at": datetime.date.today().isoformat(),
        }
        # The download is the CLI `SquadStore` file shape (`{name: squad}`), so it drops straight into
        # `data/squads.json` and loads in the CLI too. No server write — this file is the user's own save.
        payload = json.dumps({name: squad}, indent=2)
        dl, use = st.columns(2)
        dl.download_button("⬇︎ Download squad.json", payload, file_name="squad.json",
                           mime="application/json", use_container_width=True)
        if use.button("Use this squad →", use_container_width=True):
            set_active_squad({**squad, "name": name})
            st.success(f"Set **{name}** as your active squad — open Transfer, Analyse or Captain.")
