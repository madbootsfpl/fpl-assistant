"""News — the official FPL player news (Phase 6 Tier 2, ADR-058).

A read-only lens over the `news` we already ingest (injuries · doubts · return dates) + a source link.
Degrades to "no current news" when everyone's fit. No external calls, no xP — display only.
"""

import streamlit as st

from src.analytics.crowd import fit_flag
from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.media import media_headlines
from src.web_streamlit.status import render_data_status


@st.cache_data(ttl=1800, show_spinner=False)     # ~30 min — best-effort (ADR-093); the feeds can rate-limit
def _cached_headlines():
    return media_headlines()

# FPL status codes → a readable label; the order also drives severity sorting (worst first).
_STATUS = {"u": "Out", "i": "Injured", "s": "Suspended", "n": "Unavailable", "d": "Doubtful", "a": "Available"}
_SEVERITY = {"u": 0, "i": 1, "s": 2, "n": 3, "d": 4, "a": 5}

st.set_page_config(**brand.page_config("News"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("News")
render_data_status()
st.title("📰 News")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
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
    st.info("No data yet — it's refreshing; check back shortly.")
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
              "Fit": fit_flag(p),   # US-400: the shared availability emoji (⛔🚑❓), used on every surface
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

# --- Headlines lens (Sprint 115, ADR-093) — public RSS/Atom, opt-in, cached, degrade-gracefully -------------
st.divider()
st.subheader("📰 Headlines — FPL analysis & football news")
st.caption("FPL-relevant public feeds (Fantasy Football Scout · BBC Football). Fetched on demand; titles link "
           "to the source. A community/media lens — not a prediction, and never part of xP.")
if st.button("Load headlines", help="Fetch the latest FPL/football headlines (best-effort; cached ~30 min)."):
    with st.spinner("Fetching feeds…"):
        groups = _cached_headlines()
    if not groups:
        st.info("Couldn't reach the feeds right now — they can rate-limit; try again shortly.")
    else:
        for source, items in groups.items():
            st.markdown(f"**{source}**")
            for it in items:
                when = f"  ·  _{it['published'][:16]}_" if it.get("published") else ""
                st.markdown(f"- [{it['title']}]({it['link']}){when}")
