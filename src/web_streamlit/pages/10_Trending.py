"""Trending — community leaderboards from free FPL crowd data (Sprint 067, ADR-057).

Who the crowd is picking / moving: most-owned · most transferred in / out · in form — each a board over the
ingested crowd fields (`selected_by` · `transfers_*_event` · `form`), with photos, badges + the crowd flags.
A display lens, never xP. Ownership works now; the momentum/form boards light up at GW1 (2026-08-21).
"""

import streamlit as st

from src.analytics import crowd_flags, trending
from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.status import render_data_status

# (by, tab label, value-column header)
_BOARDS = [
    ("owned", "Most owned", "Own%"),
    ("in", "Most transferred in", "Net in"),
    ("out", "Most transferred out", "Net out"),
    ("form", "In form", "Form"),
]

st.set_page_config(page_title="Trending · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
st.title("Trending — what the crowd is doing")
st.caption("Free FPL crowd data — ownership · transfers · form. A community lens, not a prediction.")

store = Storage()
try:
    players = store.get_players()
    photos = photo_url_by_id(players)
    badges = badge_url_by_short_name(store.get_teams())
finally:
    store.close()

if not players:
    st.info("No data yet — run `python app.py refresh` first.")
else:
    count = st.slider("How many", 5, 30, 15)

    def _value(by, v):
        return f"{int(v):+,}" if by in ("in", "out") else f"{v:.1f}"     # signed transfers; %/form to 1dp

    for tab, (by, label, header) in zip(st.tabs([b[1] for b in _BOARDS]), _BOARDS):
        with tab:
            rows = trending(players, by=by, limit=count)
            if by in ("in", "out", "form") and all((r.get("trend") or 0) == 0 for r in rows):
                st.info("No transfer / form data yet — this board lights up at **GW1 (2026-08-21)**.")
                continue
            st.dataframe(
                [{"photo": photos.get(r["id"], ""), "badge": badges.get(r["team"], ""),
                  "Player": r["web_name"], "Team": r["team"], "Pos": r["position"],
                  header: _value(by, r["trend"]), "Trends": " ".join(crowd_flags(r))} for r in rows],
                hide_index=True, width="stretch",
                column_config={"photo": st.column_config.ImageColumn("", width="small"),
                               "badge": st.column_config.ImageColumn("", width="small")},
            )
