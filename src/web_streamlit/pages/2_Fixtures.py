"""Fixtures — the league fixture-difficulty ranking (easiest over the next 5)."""

import streamlit as st

from src.analytics import team_fdr
from src.storage import Storage

st.set_page_config(page_title="Fixtures · FPL Assistant", page_icon="⚽", layout="wide")
st.title("Fixtures — difficulty over the next 5")

store = Storage()
try:
    upcoming = store.get_upcoming_fixtures()
finally:
    store.close()

if not upcoming:
    st.info("No fixtures yet — run `python app.py refresh` first.")
else:
    fdr = team_fdr(upcoming, next_n=5, source="fpl")
    st.dataframe(
        [{"Team": r["team"], "Avg FDR": r["avg_difficulty"],
          "Next opponents": ", ".join(r["opponents"])} for r in fdr],
        width="stretch", hide_index=True,
    )
