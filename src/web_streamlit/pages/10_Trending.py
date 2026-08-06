"""Trending — community leaderboards from free FPL crowd data (Sprint 067, ADR-057).

Who the crowd is picking / moving: most-owned · most transferred in / out · in form — each a board over the
ingested crowd fields (`selected_by` · `transfers_*_event` · `form`), with photos, badges + the crowd flags.
A display lens, never xP. Ownership works now; the momentum/form boards light up at GW1 (2026-08-21).
"""

import streamlit as st

from src.analytics import crowd_flags, trending
from src.api.reddit import RedditError, RedditRssClient
from src.community import community_buzz
from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.status import render_data_status


@st.cache_data(ttl=1800, show_spinner=False)      # cache the RSS ~30 min — respect Reddit's rate limits
def _cached_reddit_rss():
    """The r/FantasyPL RSS text, or None on any failure (ADR-059 — best-effort, degrade gracefully)."""
    try:
        return RedditRssClient().get_subreddit_rss()
    except RedditError:
        return None

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

    def _board(rows, header, value_of):
        st.dataframe(
            [{"photo": photos.get(r["id"], ""), "badge": badges.get(r["team"], ""),
              "Player": r["web_name"], "Team": r["team"], "Pos": r["position"],
              header: value_of(r), "Trends": " ".join(crowd_flags(r))} for r in rows],
            hide_index=True, width="stretch",
            column_config={"photo": st.column_config.ImageColumn("", width="small"),
                           "badge": st.column_config.ImageColumn("", width="small")},
        )

    tabs = st.tabs([b[1] for b in _BOARDS] + ["💬 Talked about"])
    for tab, (by, label, header) in zip(tabs, _BOARDS):
        with tab:
            rows = trending(players, by=by, limit=count)
            if by in ("in", "out", "form") and all((r.get("trend") or 0) == 0 for r in rows):
                st.info("No transfer / form data yet — this board lights up at **GW1 (2026-08-21)**.")
            else:
                _board(rows, header, lambda r, by=by: _value(by, r["trend"]))

    # Community Signals (ADR-059) — Reddit RSS buzz. Button-gated (no fetch on load) + cached; degrades.
    with tabs[-1]:
        st.caption("**Community Signals** — who r/FantasyPL is talking about right now (post mentions, a "
                   "buzz lens — not sentiment or a prediction). Best-effort: cached, may be unavailable "
                   "on the live app.")
        if st.button("Show what's being talked about"):
            rss = _cached_reddit_rss()
            if rss is None:
                st.info("Community buzz is unavailable right now (Reddit didn't respond).")
            else:
                buzz = community_buzz(rss, players, limit=count)
                if not buzz:
                    st.info("No current-player mentions in the latest r/FantasyPL posts.")
                else:
                    _board(buzz, "Mentions", lambda r: r["mentions"])
