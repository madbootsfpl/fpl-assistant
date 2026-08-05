"""The Streamlit UI home (ADR-052) — a read-only view over the analytics.

Multipage: this is the landing (the sidebar's **Home** — its label is this file's name); `pages/` holds
Players · Fixtures · Squads · Transfer · Build · Ask. Each page imports the same engine the CLI does and
changes nothing in `src/`. Run:  python -m src.web_streamlit
"""

import streamlit as st

st.set_page_config(page_title="FPL Assistant", page_icon="⚽", layout="wide")
st.title("⚽ FPL Assistant")
st.caption("A read-only view over the analytics — the CLI stays the engine (ADR-051/052).")
st.markdown(
    """
Use the **sidebar** to explore:

- **Players** — ranked & filterable (position, price), with photos + a price-vs-points scatter
- **Fixtures** — fixture difficulty (FDR): a table + a bar chart, with team badges
- **Squads** — analyse a saved squad over the next 5 gameweeks
- **Transfer** — the best **XI-aware** swaps for a squad (a bank slider; a coordinated plan)
- **Build** — the optimal 15 within a **budget**, shaped by archetypes (cheap / premium / differential)
- **Ask** — ask a question in plain English — a grounded **chat**; every answer is checked against the data

The analytics decide; a local LLM (optional) only narrates. `python app.py refresh` updates the data.
"""
)
