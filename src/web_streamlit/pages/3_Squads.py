"""Squads — analyse a saved squad (the same `analyse` decision, via `ask`, so it reads identically)."""

import streamlit as st

from src import ask
from src.squads import SquadStore
from src.ui.ask import render_ask

st.set_page_config(page_title="Squads · FPL Assistant", page_icon="⚽", layout="wide")
st.title("Squads — analyse a saved squad")

names = SquadStore().names()
if not names:
    st.info("No saved squads yet. Save one from the CLI: "
            "`python app.py squad --full --save my-team`.")
else:
    squad = st.selectbox("Squad", names)
    if squad:
        st.code(render_ask(ask.answer(f"analyse {squad}")), language=None)
