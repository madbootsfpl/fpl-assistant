"""Sprint 052 spike — a Streamlit edge over the same engine (throwaway; ADR-051 decides its fate).

The point of the spike is to *feel* Streamlit against the FastAPI slice (Sprint 051): how much code,
how much interactivity, how it fits the architecture. Like the FastAPI edge, this imports the engine
(`ask.answer` / `rank_players` / `team_fdr`) and changes **nothing** in `src/`.

Run:  streamlit run spikes/052-streamlit/app.py
Note: Streamlit is a spike-only dependency — deliberately NOT in requirements.txt.
"""

# ruff: noqa: E402  — a spike: put the project root on sys.path *before* importing the engine.
# `streamlit run` sets sys.path[0] to the script's folder, not the project root, so we add it here.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

from src import ask
from src.analytics import rank_players, team_fdr
from src.storage import Storage
from src.ui.ask import render_ask

st.set_page_config(page_title="FPL Assistant (Streamlit spike)", page_icon="⚽")
st.title("⚽ FPL Assistant — Streamlit spike")
st.caption("A throwaway edge over the same analytics engine (Sprint 052).")

tab_ask, tab_players, tab_fixtures = st.tabs(["Ask", "Players", "Fixtures"])

with tab_ask:
    # The flagship — the same grounded answer + ✓/⚠ trust line the CLI/FastAPI show.
    q = st.text_input("Ask a question", placeholder="who has the best fixtures over the next 5?")
    if q:
        st.code(render_ask(ask.answer(q)), language=None)

with tab_players:
    # Interactivity for free: a native sortable/searchable table + live controls (no page reload).
    store = Storage()
    try:
        rows = store.get_players()
    finally:
        store.close()
    sort = st.selectbox("Sort by", ["points", "value"])
    limit = st.slider("How many", 5, 50, 20)
    ranked = rank_players(rows, sort_by=sort)[:limit]
    st.dataframe(
        [{"Player": p["web_name"], "Team": p["team"], "Pos": p["position"],
          "£m": p["price"], "Pts": p["total_points"], "Val/£m": p.get("value"),
          "Own%": p["selected_by"]} for p in ranked],
        width='stretch', hide_index=True,
    )

with tab_fixtures:
    store = Storage()
    try:
        upcoming = store.get_upcoming_fixtures()
    finally:
        store.close()
    fdr = team_fdr(upcoming, next_n=5, source="fpl")
    st.dataframe(
        [{"Team": r["team"], "Avg FDR": r["avg_difficulty"],
          "Next opponents": ", ".join(r["opponents"])} for r in fdr],
        width='stretch', hide_index=True,
    )
