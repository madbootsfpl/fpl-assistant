"""Build Squad — the optimal 15 within a budget, with the full CLI `squad` options (ADR-062).

Runs the SAME engine the CLI's `squad` command does — `decision_xp` / `objective_scores` → `select_squad`
→ `best_legal_xi` → `render_squad` — so the web can't drift from the CLI. Exposes the full option set as
form widgets (include/exclude/bench/objective/no-xmins/weekly/bench-boost/include-unavailable + the existing
budget/archetypes). The **saveable** build is always a full **15** (Download → `SquadStore` shape, or set as
the session **active squad** for My Squad / Transfer / Analyse / Captain, ADR-054). No server writes.
`--formation` shapes an XI (11), not a 15, so it lives in a display-only "best XI shape" preview.
"""

import datetime
import json

import streamlit as st

from src.analytics import (
    SQUAD_15,
    WEEKLY_BENCH_WEIGHT,
    archetype_bands,
    available_players,
    best_legal_xi,
    crowd_flags,
    decision_xp,
    objective_scores,
    select_squad,
)
from src.storage import Storage
from src.ui.squad import render_squad
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import render_sidebar, set_active_squad
from src.web_streamlit.status import render_data_status
from src.web_streamlit.tables import render_player_table

_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
_BENCH_MAX = 4
_FORMATIONS = {"3-4-3": (3, 4, 3), "3-5-2": (3, 5, 2), "4-4-2": (4, 4, 2),
               "4-3-3": (4, 3, 3), "4-5-1": (4, 5, 1), "5-4-1": (5, 4, 1), "5-3-2": (5, 3, 2)}

st.set_page_config(page_title="Build Squad · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
render_sidebar()
st.title("Build Squad — the optimal 15 within a budget")

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
    st.stop()

# A label → id map so include/exclude/bench pick a *specific* player (web_names can repeat).
_by_label = {f"{p['web_name']} · {p['team']} · £{p['price']:.1f}m": p["id"]
             for p in sorted(players, key=lambda p: (p["web_name"] or "").lower())}
_labels = list(_by_label)


def _ids(labels):
    return [_by_label[la] for la in labels]


# ---- controls ---------------------------------------------------------------
c1, c2, c3 = st.columns(3)
budget = c1.slider("Budget (£m)", 80.0, 100.0, 100.0, step=0.5,
                   help="The most you'll spend across all 15 players.")
name = c1.text_input("Squad name", value="My squad", max_chars=40,
                     help="A name for this squad — used in the download and as the active-squad "
                          "label.").strip() or "My squad"
objective = c2.selectbox("Objective", ["xp", "points", "value", "xgi"],
                         help="xp = expected points (xMins-weighted); the CLI default.")
no_xmins = c2.checkbox("Ignore expected minutes (--no-xmins)", value=False,
                       disabled=objective != "xp", help="xp objective only.")
mode = c3.radio("Build mode", ["Balanced", "Weekly (playing bench)", "Bench Boost"],
                help="Weekly maximises the XI + a cheap playing bench; Bench Boost maximises all 15.")
include_unavailable = c3.checkbox("Include injured/suspended", value=False,
                                  help="Also consider flagged players (off by default).")

a1, a2, a3 = st.columns(3)
cheap = a1.number_input("Low-cost (≤£4.5m)", min_value=0, max_value=8, value=0,
                        help="Require at least this many budget (≤£4.5m) players.")
premium = a2.number_input("Premium (≥£9m)", min_value=0, max_value=5, value=0,
                          help="Require at least this many premium (≥£9m) players.")
differential = a3.number_input("Differentials (≤5% owned)", min_value=0, max_value=5, value=0,
                               help="Require at least this many low-owned (≤5%) picks.")

include = _ids(st.multiselect("Must include", _labels,
                              help="Force these players into the squad."))
exclude = _ids(st.multiselect("Must exclude", _labels,
                              help="Never pick these players."))
declared_bench = _ids(st.multiselect("Declare bench (up to 4)", _labels,
                                     help="Pins these to the bench; leave empty to auto-derive the XI."))

# ---- validation (soft — mirrors the CLI's validate_*) -----------------------
weekly = mode == "Weekly (playing bench)"
bench_boost = mode == "Bench Boost"
warnings = []
if set(include) & set(exclude):
    warnings.append("A player can't be both included and excluded.")
if len(declared_bench) > _BENCH_MAX:
    warnings.append(f"You can declare at most {_BENCH_MAX} bench players.")
if set(declared_bench) & set(include):
    warnings.append("A player can't be both included and benched.")
if declared_bench and (weekly or bench_boost):
    warnings.append("Weekly / Bench Boost designate the bench themselves — clear the declared bench.")
for w in warnings:
    st.warning(w)

# ---- score (the SAME split as the CLI) --------------------------------------
if objective == "xp":
    ranked = decision_xp(players, upcoming, history, minutes_weighted=not no_xmins,
                         gw_history_by_code=gw_history)
    scores = {r["id"]: r["xp"] for r in ranked}
else:
    scores = objective_scores(players, objective)
    ranked = decision_xp(players, upcoming, history, gw_history_by_code=gw_history)   # xP for display
display_xp = {r["id"]: r["xp"] for r in ranked}
weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}

# ---- build (a full 15) ------------------------------------------------------
forced = set(include) | set(declared_bench)
pool = players if include_unavailable else available_players(players, keep_ids=forced)[0]
bands = archetype_bands(cheap=cheap or None, premium=premium or None)
result = select_squad(
    pool, budget=budget, formation=SQUAD_15, size=15,
    include_ids=include, exclude_ids=exclude, bench_ids=declared_bench,
    scores=scores, band_minimums=bands, min_differentials=differential or None,
    bench_weight=WEEKLY_BENCH_WEIGHT if weekly else None,
)

if result["status"] != "Optimal":
    st.error(f"No squad fits those options within £{budget:.1f}m — relax the constraints "
             "(archetypes / include / budget) and try again.")
    st.stop()

selected = result["selected"]
# The XI/bench split: a declared bench pins it, else the best legal XI (the breakout the CLI shows).
if declared_bench:
    xi_ids = [p["id"] for p in selected if not p.get("bench")]
else:
    xi_ids = best_legal_xi(selected, scores)
xi = set(xi_ids)
for p in selected:                       # attach the reference xP + xMins for the table (ADR-041/US-121)
    p["xp"] = display_xp.get(p["id"], 0)
    p["minutes_weight"] = weight_by_id.get(p["id"], 1.0)

if objective != "xp":
    st.caption(f"Optimised on **{objective}**; the xP column is the forward reference metric (xMins-weighted).")

render_player_table([{
    "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
    "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
    "£m": p["price"], "xP": round(p.get("xp", 0), 1),
    "Role": "XI" if p["id"] in xi else "Bench", "Trends": " ".join(crowd_flags(p)),
} for p in sorted(selected, key=lambda x: (x["id"] not in xi, _ORDER.get(x["position"], 9)))])
st.code(render_squad(result, budget=budget, objective=objective, full=True,
                     xi_ids=xi_ids, bench_boost=bench_boost), language=None)

# ---- save (always the full 15) ----------------------------------------------
squad = {
    "player_ids": [p["id"] for p in selected],
    "player_names": [p["web_name"] for p in selected],
    "bench_ids": [p["id"] for p in selected if p["id"] not in xi],
    "cost": result["total_cost"],
    "saved_at": datetime.date.today().isoformat(),
}
payload = json.dumps({name: squad}, indent=2)
dl, use = st.columns(2)
dl.download_button("⬇︎ Download squad.json", payload, file_name="squad.json",
                   mime="application/json", use_container_width=True)
if use.button("Use this squad →", use_container_width=True):
    set_active_squad({**squad, "name": name})
    st.success(f"Set **{name}** as your active squad — tweak it in My Squad, or open Transfer / Analyse.")

# ---- best-XI-shape preview (display only — an XI is 11, not a saveable 15) ---
with st.expander("🔎 Preview the best XI in a given shape (display only — not saved)"):
    shape = st.selectbox("Formation", list(_FORMATIONS), index=0,
                         help="Preview the best XI in this shape (display only — the saved build is a 15).")
    d, m, f = _FORMATIONS[shape]
    xi_pool = players if include_unavailable else available_players(players, keep_ids=set(include))[0]
    xi_result = select_squad(xi_pool, budget=budget, formation={"GK": 1, "DEF": d, "MID": m, "FWD": f},
                             size=11, include_ids=include, exclude_ids=exclude, scores=scores)
    if xi_result["status"] != "Optimal":
        st.info(f"No legal {shape} XI within £{budget:.1f}m for those options.")
    else:
        for p in xi_result["selected"]:
            p["xp"] = display_xp.get(p["id"], 0)
            p["minutes_weight"] = weight_by_id.get(p["id"], 1.0)
        render_player_table([{
            "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
            "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
            "£m": p["price"], "xP": round(p.get("xp", 0), 1), "Trends": " ".join(crowd_flags(p)),
        } for p in sorted(xi_result["selected"], key=lambda x: _ORDER.get(x["position"], 9))])
        st.caption(f"Best **{shape}** XI (display only) — the saveable build above is always a full 15.")
