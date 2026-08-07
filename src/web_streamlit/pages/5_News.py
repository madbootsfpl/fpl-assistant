"""News — the official FPL player news (Phase 6 Tier 2, ADR-058).

A read-only lens over the `news` we already ingest (injuries · doubts · return dates) + a source link.
Degrades to "no current news" when everyone's fit. No external calls, no xP — display only.
"""

import streamlit as st

from src.storage import Storage
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.status import render_data_status

# FPL status codes → a readable label; the order also drives severity sorting (worst first).
_STATUS = {"u": "Out", "i": "Injured", "s": "Suspended", "n": "Unavailable", "d": "Doubtful", "a": "Available"}
_SEVERITY = {"u": 0, "i": 1, "s": 2, "n": 3, "d": 4, "a": 5}

st.set_page_config(page_title="News · FPL Assistant", page_icon="⚽", layout="wide")
require_access()          # opt-in beta gate (ADR-087)
render_data_status()
st.title("📰 News")
st.caption("Official FPL player news — injuries, doubts and returns, most serious first.")

store = Storage()
try:
    players = store.get_players()
    teams = store.get_teams()
    photos = photo_url_by_id(players, teams)          # photo, else the club shirt (US-255)
    badges = badge_url_by_short_name(teams)
finally:
    store.close()

if not players:
    st.info("No data yet — run `python app.py refresh` first.")
else:
    flagged = [p for p in players if p["news"]]        # a player carries `news` only when there's an issue
    if not flagged:
        st.success("No current news — everyone's available. 🎉")
    else:
        flagged.sort(key=lambda p: (_SEVERITY.get(p["status"], 9), p["web_name"]))
        st.caption(f"{len(flagged)} players with news — injuries, doubts and returns (most serious first).")
        st.dataframe(
            [{"photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
              "Player": p["web_name"], "Team": p["team"],
              "Status": _STATUS.get(p["status"], p["status"]),
              "Chance": (f"{p['chance']}%" if p["chance"] is not None else "—"),
              "News": p["news"], "Source": p["scout_news_link"] or None}
             for p in flagged],
            width="stretch", hide_index=True,
            column_config={
                "photo": st.column_config.ImageColumn("", width="small"),
                "badge": st.column_config.ImageColumn("", width="small"),
                "Source": st.column_config.LinkColumn("Source", display_text="read more"),
            },
        )
