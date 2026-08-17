"""Trending — community leaderboards from free FPL crowd data (Sprint 067, ADR-057).

Who the crowd is picking / moving: most-owned · most transferred in / out · in form — each a board over the
ingested crowd fields (`selected_by` · `transfers_*_event` · `form`), with photos, badges + the crowd flags.
A display lens, never xP. Ownership works now; the momentum/form boards light up at GW1 (2026-08-21).
"""

import streamlit as st

from src.analytics import CROWD_LEGEND, crowd_flags, trending
from src.api.feeds import parse_feed
from src.api.reddit import RedditError, RedditRssClient
from src.community import community_buzz
from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.filters import filter_controls
from src.web_streamlit.paginate import show_count
from src.web_streamlit.status import render_data_status


@st.cache_data(ttl=1800, show_spinner=False)      # cache the RSS ~30 min — respect Reddit's rate limits
def _cached_reddit_rss():
    """The r/FantasyPL RSS text, or None on any failure (ADR-059 — best-effort, degrade gracefully)."""
    try:
        return RedditRssClient().get_subreddit_rss()
    except RedditError:
        return None


@st.cache_data(ttl=1800, show_spinner=False)      # the week's top posts (US-292), cached like the buzz feed
def _cached_reddit_top():
    """The week's top r/FantasyPL posts as RSS text, or None on any failure (best-effort, degrade)."""
    try:
        return RedditRssClient().get_top_weekly()
    except RedditError:
        return None

# (by, tab label, value-column header)
_BOARDS = [
    ("owned", "Most owned", "Own%"),
    ("in", "Most transferred in", "Net in"),
    ("out", "Most transferred out", "Net out"),
    ("form", "In form", "Form"),
]

st.set_page_config(**brand.page_config("Trending"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Trending")
render_data_status()
st.title("📈 Trending")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("Free FPL crowd data — ownership · transfers · form. A community lens, not a prediction.")

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
    def _value(by, v):
        return f"{int(v):+,}" if by in ("in", "out") else f"{v:.1f}"     # signed transfers; %/form to 1dp

    def _board(rows, header, value_of):
        st.dataframe(
            [{"photo": photos.get(r["id"], ""), "badge": badges.get(r["team"], ""),
              "Player": r["web_name"], "Team": r["team"], "Pos": r["position"],
              header: value_of(r), "Trends": " ".join(crowd_flags(r))} for r in rows],
            hide_index=True, width="stretch",
            height=480,
            column_config={"photo": st.column_config.ImageColumn("", width="small"),
                           "badge": st.column_config.ImageColumn("", width="small")},
        )

    # A shared filter (ADR-064): Team / Position / Player, AND-combinable — applied to every board.
    sel = filter_controls(players, key="trending")
    st.caption(CROWD_LEGEND)                           # explain the Trends flags (e.g. what "template" means)
    tabs = st.tabs([b[1] for b in _BOARDS] + ["💬 Talked about"])
    for tab, (by, label, header) in zip(tabs, _BOARDS):
        with tab:
            rows = apply_filter(trending(players, by=by, limit=len(players)), sel)   # all, filtered, paged
            if by in ("in", "out", "form") and all((r.get("trend") or 0) == 0 for r in rows):
                st.info("No transfer / form data yet — this board lights up at **GW1 (2026-08-21)**.")
            else:
                page = show_count(rows)
                _board(page, header, lambda r, by=by: _value(by, r["trend"]))

    # Community Signals (ADR-059) — Reddit RSS buzz. Button-gated (no fetch on load) + cached; degrades.
    with tabs[-1]:
        # The week's top discussions first (US-292 / US-345) — the sharper lens; the long mention board sits below.
        st.caption("**🔥 Top discussions this week** — the highest-voted r/FantasyPL posts (a buzz lens, not a "
                   "prediction; best-effort, cached ~30 min).")
        if st.button("Show this week's top discussions",
                     help="Fetch r/FantasyPL's top posts this week (best-effort; cached ~30 min)."):
            top_rss = _cached_reddit_top()
            if top_rss is None:
                st.info("Top discussions are unavailable right now (Reddit didn't respond).")
            else:
                posts = parse_feed(top_rss, limit=10)
                if not posts:
                    st.info("No top posts found this week.")
                else:
                    for post in posts:
                        st.markdown(f"- [{post['title']}]({post['link']})")

        st.divider()
        st.caption("**Community Signals** — who r/FantasyPL is talking about across the latest **~100 posts** "
                   "(post mentions, a buzz lens — not sentiment or a prediction). Best-effort: cached, may "
                   "be unavailable on the live app.")
        if st.button("Show what's being talked about",
                     help="Fetch r/FantasyPL (the latest ~100 posts) and count player mentions "
                          "(best-effort; cached ~30 min)."):
            rss = _cached_reddit_rss()
            if rss is None:
                st.info("Community buzz is unavailable right now (Reddit didn't respond).")
            else:
                buzz = community_buzz(rss, players, limit=len(players))   # all mentioned, ranked
                if not buzz:
                    st.info("No current-player mentions in the latest r/FantasyPL posts.")
                else:
                    st.caption(f"{len(buzz)} players mentioned across the latest ~100 posts — expand a name "
                               "to read them. (Surnames can collide — the photo/badge shows who matched.)")
                    # A 100-post sample mentions many players → page like the other Trending boards (ADR-076).
                    for r in show_count(buzz):
                        c_photo, c_badge, c_body = st.columns([1, 1, 12], vertical_alignment="center")
                        if photos.get(r["id"]):
                            c_photo.image(photos[r["id"]], width=44)
                        if badges.get(r["team"]):
                            c_badge.image(badges[r["team"]], width=28)
                        with c_body.expander(f"{r['web_name']} — {r['team']} · {r['mentions']} mentions"):
                            for post in r["posts"]:
                                title = post["title"] or "(untitled post)"
                                st.markdown(f"- [{title}]({post['link']})" if post["link"]
                                            else f"- {title}")
