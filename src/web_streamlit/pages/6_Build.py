"""Build — the optimal 15 within a budget, shaped by archetypes (ADR-041/043/044), interactively.

The sliders build a plain-English request and hand it to the SAME `build_squad` `ask` intent the CLI/`ask`
use — so it runs the exact optimiser + archetype constraints + the XI/bench breakout, grounded and
verified. Zero of an archetype simply drops that constraint.
"""

import streamlit as st

from src import ask
from src.ui.ask import render_ask

st.set_page_config(page_title="Build · FPL Assistant", page_icon="⚽", layout="wide")
st.title("Build — the optimal 15 within a budget")

col1, col2 = st.columns(2)
budget = col1.slider("Budget (£m)", 80.0, 100.0, 100.0, step=0.5)
cheap = col2.number_input("Low-cost (≤£4.5m)", min_value=0, max_value=8, value=0)
premium = col2.number_input("Premium (≥£9m)", min_value=0, max_value=5, value=0)
differential = col2.number_input("Differentials (≤5% owned)", min_value=0, max_value=5, value=0)

# Build a plain-English request from the controls — only the archetypes you asked for.
extras = []
if cheap:
    extras.append(f"{cheap} low cost players")
if premium:
    extras.append(f"{premium} premium players")
if differential:
    extras.append(f"{differential} differentials")
query = f"build me a squad for £{budget:.0f}m"
if extras:
    query += " with " + ", ".join(extras)

st.caption(f"Request: _{query}_")
st.code(render_ask(ask.answer(query)), language=None)
