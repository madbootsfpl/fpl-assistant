"""The Streamlit UI home (ADR-052) — a read-only view over the analytics.

Multipage: this is the landing page; `pages/` holds Players · Fixtures · Squads · Ask (Streamlit builds
the sidebar nav from them). Each page imports the same engine the CLI does and changes nothing in `src/`.
Run:  python -m src.web_streamlit
"""

import streamlit as st

st.set_page_config(page_title="FPL Assistant", page_icon="⚽", layout="wide")
st.title("⚽ FPL Assistant")
st.caption("A read-only view over the analytics — the CLI stays the engine (ADR-051/052).")
st.markdown(
    """
Use the **sidebar** to explore:

- **Players** — ranked, sortable/searchable, filterable
- **Fixtures** — fixture difficulty (FDR) over the next 5
- **Squads** — analyse a saved squad
- **Ask** — ask a question in plain English (grounded; every answer checked against the data)

The analytics decide; a local LLM (optional) only narrates. Data comes from the local cache
(`python app.py refresh` updates it).
"""
)
