"""Transfer — the best XI-aware swaps for your squad (ADR-046), interactively.

Pick your **active squad** (built/uploaded) or a **demo** squad, set the bank, choose a single shortlist
or an N-move plan. Reuses the SAME engine + renderer the CLI's `transfer` command does
(`suggest_transfers` / `suggest_transfer_plan`), run on the squad **dict** — so an uploaded squad works and
the web can't drift from the CLI's logic (ADR-054).
"""

import streamlit as st

from src.analytics import decision_xp, suggest_transfer_plan, suggest_transfers
from src.storage import Storage
from src.ui.transfer import render_transfer_plan, render_transfers
from src.web_streamlit.squads import apply_transfer, render_sidebar, set_active_squad, squad_picker

st.set_page_config(page_title="Transfer · FPL Assistant", page_icon="⚽", layout="wide")
render_sidebar()
st.title("Transfer — best XI-aware swaps")

col1, col2 = st.columns(2)
with col1:
    squad_name, squad = squad_picker()
bank = col1.slider("Bank (£m)", 0.0, 10.0, 0.0, step=0.5)
count = col2.slider("Transfers (a coordinated plan)", 1, 3, 1)

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
    st.info(f"Squad '{squad_name}' has no current players to improve.")
else:
    ranked = decision_xp(players, upcoming, history)          # xMins-weighted (default)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    bench_ids = squad.get("bench_ids", [])
    if count > 1:
        plan = suggest_transfer_plan(owned, players, xp_by_id, bench_ids=bench_ids,
                                     bank=bank, count=count)
        st.code(render_transfer_plan(
            plan, squad_name, bank=bank,
            by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
            gameweeks=ranked[0]["gameweeks"] if ranked else [], show_xmins=True,
        ), language=None)
    else:
        swaps = suggest_transfers(owned, players, xp_by_id, bench_ids=bench_ids,
                                  bank=bank, limit=5)
        st.code(render_transfers(swaps, squad_name, bank=bank, show_xmins=True), language=None)

        # Apply a suggested swap to your squad (ADR-055) — mutates the session active squad (a copy of
        # the picked squad), so a demo squad becomes yours on first edit. No server write.
        if swaps:
            labels = [f"{s['out']['web_name']} → {s['in']['web_name']}  (+{s['gain']} xP)" for s in swaps]
            choice = st.selectbox("Apply a swap to your squad", labels, key="apply_swap")
            if st.button("Apply this transfer →"):
                chosen = swaps[labels.index(choice)]
                ok, issues, warning, new = apply_transfer(
                    squad, chosen["out"]["id"], chosen["in"]["id"], players)
                if not ok:
                    st.error("Can't apply — that would leave an illegal squad: " + "; ".join(issues))
                else:
                    set_active_squad(new)
                    done = (f"Applied **{chosen['out']['web_name']} → {chosen['in']['web_name']}** — "
                            f"new cost £{new['cost']:.1f}m.")
                    st.warning(f"{done}  ⚠ {warning}") if warning else st.success(done)
                    st.rerun()                        # recompute suggestions on the updated squad
