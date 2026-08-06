"""The Streamlit UI home (ADR-052) — a read-only view over the analytics.

Multipage: this is the landing (the sidebar's **Home** — its label is this file's name); `pages/` holds
Players · Fixtures · Analyse · Ask · Transfer · Build · Captain · My Squad. Each page imports the same
engine the CLI does and changes nothing in `src/`. Run:  python -m src.web_streamlit
"""

import streamlit as st

from src.web_streamlit.status import render_data_status

st.set_page_config(page_title="FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
st.title("⚽ FPL Assistant")
st.caption("A read-only view over the analytics — the CLI stays the engine (ADR-051/052).")
st.markdown(
    """
Use the **sidebar** to explore:

- **Players** — ranked & filterable (position, price), with photos + a price-vs-points scatter
- **Fixtures** — a **fixture ticker**: teams × gameweeks, colour-coded by difficulty (pick 1–8 weeks)
- **Build Squad** — the optimal 15 within a **budget**, with the full option set (archetypes · include /
  exclude · declared bench · objective · weekly / bench-boost · include injured)
- **My Squad** — your squad as a **pitch/formation** view; edit it (rename, swap, bench, set captain, download)
- **Squad Health** — analyse **your squad's** health over the next 5 gameweeks
- **Transfer** — the best **XI-aware** swaps for your squad (a bank slider; a coordinated plan)
- **Captain** — who to (vice-)captain from your squad this week
- **Ask** — ask a question in plain English — a grounded **chat**; every answer is checked against the data
- **News** — official FPL player news (injuries · doubts · returns), most serious first
- **Trending** — what the crowd's doing: most-owned · transferred in/out · in form, + **Community Signals**
  (💬 what r/FantasyPL is talking about — best-effort)

**Your squad:** on **Build Squad**, name it, *Download* a `squad.json` (that file is your save) and *Use
this squad*; or *Upload* one from the sidebar; or **import your real team by FPL manager-ID** (from GW1).
**Edit** it on **My Squad** (or apply a swap on Transfer / set a captain on Captain) — every change updates
your session and the download. A **demo** squad populates the pages on first visit. All per-user — no
accounts, nothing saved server-side (ADR-054/055).

The analytics decide; a local LLM (optional) only narrates. `python app.py refresh` updates the data.
"""
)
st.info("🧪 **Testing this?** Tell us what breaks or feels off → "
        "[open a GitHub issue](https://github.com/tesheridan/fpl-assistant/issues/new).")
