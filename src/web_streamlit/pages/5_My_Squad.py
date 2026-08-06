"""My Squad — view & edit your active squad (ADR-055).

The edit hub for the session **active squad**: see your 15 (with **(C)**, cost and a **legality** line),
**rename** it, **swap any player** for any other in the same position (validated by `squad_15_issues` —
illegal is refused, over-budget is a soft warning), adjust the **bench**, and **Download** the result. Every
edit mutates `st.session_state` only (no server writes); Download is your save. Editing a demo squad adopts
a copy as your active squad.
"""

import datetime
import json

import streamlit as st

from src.analytics import decision_xp, is_unavailable, legal_xi_issues, squad_15_issues, team_schedule
from src.storage import Storage
from src.web_streamlit.badges import photo_url_by_id
from src.web_streamlit.pitch import render_pitch
from src.web_streamlit.squads import (
    FPL_BUDGET,
    apply_transfer,
    rename,
    render_sidebar,
    set_active_squad,
    set_bench,
    squad_picker,
)
from src.web_streamlit.status import render_data_status

_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}

st.set_page_config(page_title="My Squad · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
render_sidebar()
st.title("My Squad — view & edit")
st.caption("Tweak your squad here — rename · swap · bench · set captain · download. 🔧 To **build a fresh "
           "one** with the full option set, open **Build Squad** in the sidebar.")

squad_name, squad = squad_picker()

store = Storage()
try:
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    history = store.get_history_by_code()
    gw_history = store.get_gw_history_by_code()      # in-season form (ADR-060; dormant now)
    photos = photo_url_by_id(players)
finally:
    store.close()

if not players:
    st.info("No players — run `python app.py refresh` first.")
    st.stop()

by_id = {p["id"]: p for p in players}
owned = [by_id[i] for i in squad["player_ids"] if i in by_id]
xp_by_id = {r["id"]: r["xp"] for r in decision_xp(players, upcoming, history, gw_history_by_code=gw_history)}
bench_ids = set(squad.get("bench_ids") or [])
captain_id = squad.get("captain_id")

# --- legality + cost banner -----------------------------------------------------------------------
issues = squad_15_issues(owned)
cost = round(sum(p["price"] for p in owned), 1)
if issues:
    st.error("Not a legal 15: " + "; ".join(issues))
else:
    over = round(cost - FPL_BUDGET, 1)
    st.success(f"£{cost:.1f}m — ✓ a legal 15" if over <= 0
               else f"£{cost:.1f}m — ✓ legal, ⚠ £{over:.1f}m over the £{FPL_BUDGET:.0f}m budget")

# --- the 15 as a pitch / formation card-grid (US-187) ---------------------------------------------
# Each team's next fixture (opponent + venue) for the cards — one schedule lookup per owned team.
next_opp = {t: (team_schedule(upcoming, t) or [None])[0] for t in {p["team"] for p in owned}}
xi = [p for p in owned if p["id"] not in bench_ids]
bench = [p for p in owned if p["id"] in bench_ids]
render_pitch(xi, bench, captain_id=captain_id, xp_by_id=xp_by_id, photos=photos, next_opp=next_opp)

st.divider()
st.subheader("Edit")

# --- rename ---------------------------------------------------------------------------------------
with st.expander("Rename"):
    new_name = st.text_input("Squad name", value=squad.get("name", "My squad"), max_chars=40)
    if st.button("Rename"):
        set_active_squad(rename(squad, new_name))
        st.rerun()

# --- swap any player (same position) --------------------------------------------------------------
with st.expander("Swap a player", expanded=True):
    if owned:
        out_label = {f"{p['position']} {p['web_name']} (£{p['price']:.1f}m)": p["id"] for p in
                     sorted(owned, key=lambda x: _ORDER.get(x["position"], 9))}
        out_choice = st.selectbox("Replace", list(out_label), key="swap_out")
        out_id = out_label[out_choice]
        out = by_id[out_id]
        owned_ids = {p["id"] for p in owned}
        # candidates: any same-position player you don't own and who's available (any→any within position
        # keeps the squad legal; illegal picks are refused by the validator anyway).
        cands = sorted((p for p in players if p["position"] == out["position"]
                        and p["id"] not in owned_ids and not is_unavailable(p)),
                       key=lambda x: xp_by_id.get(x["id"], 0), reverse=True)
        in_label = {f"{p['web_name']} · {p['team']} · £{p['price']:.1f}m · "
                    f"{round(xp_by_id.get(p['id'], 0), 1)} xP": p["id"] for p in cands}
        if in_label:
            in_choice = st.selectbox("With", list(in_label), key="swap_in")
            if st.button("Swap →"):
                ok, swap_issues, warning, new = apply_transfer(squad, out_id, in_label[in_choice], players)
                if not ok:
                    st.error("Can't swap — that would leave an illegal squad: " + "; ".join(swap_issues))
                else:
                    set_active_squad(new)
                    msg = f"Swapped **{out['web_name']} → {by_id[in_label[in_choice]]['web_name']}**."
                    st.warning(f"{msg}  ⚠ {warning}") if warning else st.success(msg)
                    st.rerun()
        else:
            st.caption("No available replacements in that position.")

# --- the bench ------------------------------------------------------------------------------------
with st.expander("Set the bench (pick 4)"):
    labels = {f"{p['position']} {p['web_name']}": p["id"] for p in
              sorted(owned, key=lambda x: _ORDER.get(x["position"], 9))}
    default = [lab for lab, i in labels.items() if i in bench_ids]
    picked = st.multiselect("Bench", list(labels), default=default, max_selections=4)
    if st.button("Set bench"):
        new = set_bench(squad, [labels[lab] for lab in picked])
        xi = [by_id[i] for i in new["player_ids"] if i not in set(new["bench_ids"]) and i in by_id]
        xi_problem = legal_xi_issues(xi) if len(xi) == 11 else ["the XI isn't 11 players"]
        set_active_squad(new)
        if xi_problem:
            st.warning("Bench set — but the XI isn't legal: " + "; ".join(xi_problem))
        else:
            st.success("Bench set.")
        st.rerun()

# --- download -------------------------------------------------------------------------------------
st.divider()
save = {k: v for k, v in squad.items() if k != "name"}
save.setdefault("saved_at", datetime.date.today().isoformat())
payload = json.dumps({squad.get("name", "My squad"): save}, indent=2)
st.download_button("⬇︎ Download squad.json", payload, file_name="squad.json",
                   mime="application/json")
