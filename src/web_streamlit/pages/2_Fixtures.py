"""Fixtures — a fixture-ticker grid (Sprint 062): teams × gameweeks, colour-coded by difficulty.

Pick how many weeks to show (1–8); teams are rows (easiest run first), gameweeks are columns, each cell the
opponent + (H/A) shaded green (easy) → red (hard). Reuses `fixture_ticker` (which reuses `team_fdr` /
`team_schedule`) — no core change, no new analytics.
"""

import pandas as pd
import streamlit as st

from src.analytics import fixture_ticker
from src.storage import Storage
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name
from src.web_streamlit.status import render_data_status

# FPL difficulty 1–5 → a green→red band (mirrors the fixture-ticker palette).
_DIFF_COLOR = {1: "#166534", 2: "#22c55e", 3: "#b7791f", 4: "#ef4444", 5: "#991b1b"}

st.set_page_config(page_title="Fixtures · FPL Assistant", page_icon="⚽", layout="wide")
require_access()          # opt-in beta gate (ADR-087)
render_data_status()
st.title("📅 Fixtures")
st.caption("The difficulty ticker — teams × gameweeks, colour-coded by how hard each run is.")

store = Storage()
try:
    upcoming = store.get_upcoming_fixtures()
    badges = badge_url_by_short_name(store.get_teams())
finally:
    store.close()

if not upcoming:
    st.info("No fixtures yet — run `python app.py refresh` first.")
else:
    weeks = st.slider("Weeks to show", 1, 8, 6,
                      help="How many upcoming gameweeks to show in the difficulty ticker.")
    ticker = fixture_ticker(upcoming, next_n=weeks, source="fpl")
    gws = ticker["gameweeks"]
    gw_cols = [f"GW{g}" for g in gws]

    display_rows, diff_rows = [], []
    for r in ticker["rows"]:
        disp = {"badge": badges.get(r["team"], ""), "Team": r["team"]}
        diff = {}
        for gw, col in zip(gws, gw_cols):
            cell = r["cells"].get(gw)
            disp[col] = f"{cell['opponent']} ({cell['venue']})" if cell else "—"
            diff[col] = cell["difficulty"] if cell else None
        display_rows.append(disp)
        diff_rows.append(diff)

    disp_df = pd.DataFrame(display_rows)
    diff_df = pd.DataFrame(diff_rows)

    def _shade(_):
        # A same-shaped CSS frame: colour the GW cells by their difficulty; leave badge/Team blank.
        css = pd.DataFrame("", index=disp_df.index, columns=disp_df.columns)
        for col in gw_cols:
            css[col] = [f"background-color: {_DIFF_COLOR[d]}; color: white" if d in _DIFF_COLOR else ""
                        for d in diff_df[col]]
        return css

    st.caption("Easiest run first · green = easy, red = hard · (H)ome / (A)way.")
    st.dataframe(
        disp_df.style.apply(_shade, axis=None),
        hide_index=True, width="stretch",
        column_config={"badge": st.column_config.ImageColumn("", width="small")},
    )
