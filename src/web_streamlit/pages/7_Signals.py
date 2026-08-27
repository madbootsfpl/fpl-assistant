"""Signals — everything that tells you something the table doesn't (ADR-150).

**One page for "what should I know?", ordered by how much the source actually knows.** Four lenses used to be
spread across two pages with no relationship to each other: official news and media headlines lived on *News*,
while Reddit's top discussions and mention counts sat on *Trending* beside ownership leaderboards — numbers
about crowd *behaviour*, which is a different question entirely. ADR-146 then added a fifth (an unexplained
transfer exodus) that had no browse surface at all.

**The ordering is the design.** These sources are not equally reliable, and putting them on one page without
saying so would present a Reddit rumour beside an injury FPL confirmed. So they descend by evidentiary
strength, and each says what it is:

1. **Official** — FPL's own `news`. A fact. Drives `status`, and therefore every xP in the app.
2. **Unexplained exodus** — our own inference (ADR-146): a heavy sell-off `status`/`news` cannot account for.
   Not a fact about the player; a fact about what other managers are doing.
3. **Headlines** — reported by named outlets (ADR-093).
4. **Community chatter** — Reddit mention counts (ADR-059). A *count*, never sentiment, never a prediction.

Trending keeps the leaderboards: **it answers what the crowd is doing, this answers what is being said.**
"""

import streamlit as st

from src.analytics.crowd import fit_flag
from src.analytics.headlines import event_phrase
from src.api.feeds import parse_feed
from src.api.media import media_headlines
from src.api.reddit import RedditError, RedditRssClient
from src.community import community_buzz
from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.filters import filter_controls
from src.web_streamlit.paginate import show_count
from src.web_streamlit.squads import active_squad
from src.web_streamlit.status import render_data_status


@st.cache_data(ttl=1800, show_spinner=False)     # ~30 min — best-effort (ADR-093); the feeds can rate-limit
def _cached_headlines():
    return media_headlines()


@st.cache_data(ttl=1800, show_spinner=False)     # cache the RSS ~30 min — respect Reddit's rate limits
def _cached_reddit_rss():
    """The r/FantasyPL RSS text, or None on any failure (ADR-059 — best-effort, degrade gracefully)."""
    try:
        return RedditRssClient().get_subreddit_rss()
    except RedditError:
        return None


@st.cache_data(ttl=1800, show_spinner=False)     # the week's top posts (US-292), cached like the buzz feed
def _cached_reddit_top():
    """The week's top r/FantasyPL posts as RSS text, or None on any failure (best-effort, degrade)."""
    try:
        return RedditRssClient().get_top_weekly()
    except RedditError:
        return None

# FPL status codes → a readable label; the order also drives severity sorting (worst first).
_STATUS = {"u": "Out", "i": "Injured", "s": "Suspended", "n": "Unavailable", "d": "Doubtful", "a": "Available"}
_SEVERITY = {"u": 0, "i": 1, "s": 2, "n": 3, "d": 4, "a": 5}

st.set_page_config(**brand.page_config("Signals"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Signals")
render_data_status()
st.title("📡 Signals")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("Everything that tells you something the table doesn't — **most reliable first**: official FPL "
           "news, then a sell-off we can't explain, then media headlines, then community chatter. "
           "**Trending** is the other half: what the crowd is *doing*, in numbers.")

st.subheader("1 · Official FPL news")
st.caption("FPL's own `news` field — injuries, doubts and returns, most serious first. This is the only "
           "source here that is a **fact**, and the only one that moves a player's expected points.")

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
        # US-407b: filter the news to your squad / a team / position / player (the shared filter, ADR-064).
        _sq = active_squad()
        sel = filter_controls(players, key="news",
                              my_squad_ids=set(_sq["player_ids"]) if _sq else None)
        flagged = apply_filter(flagged, sel)
        flagged.sort(key=lambda p: (_SEVERITY.get(p["status"], 9), p["web_name"]))
        if not flagged:
            st.info("No news for that filter — clear a filter to see everyone with news.")
        else:
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

# --- 2 · An exodus we can't explain (ADR-146) ---------------------------------------------------------------
# ADR-146 built this signal but gave it only *per-squad* surfaces (the Risk Monitor, the gameweek flags). Here
# it is a **discovery** list: who is the crowd dumping that our own data cannot account for — which is the
# question you ask before you own someone, not after.
st.divider()
st.subheader("2 · An exodus we can't explain")
st.caption("Players being sold heavily while FPL's own `news` and `status` say nothing is wrong. **Not a fact "
           "about the player** — a fact about what other managers are doing, which is our only route to news "
           "the feed doesn't carry (a move abroad, a row, a press conference).")
if players:
    from src.analytics.crowd import EXODUS_OWNERSHIP_FLOOR, crowd_exodus
    _ex = [(p, e) for p in players
           if (p["selected_by"] or 0) >= EXODUS_OWNERSHIP_FLOOR and (e := crowd_exodus(p))]
    # ADR-151 — a sell-off with a headline behind it is no longer "unexplained"; it is *explained by the
    # press*. Shown first, because a sourced cause is the most useful thing on this page.
    _store2 = Storage()
    _ev = _store2.headline_events_by_id()
    _store2.close()
    _explained = [(p, e, _ev[p["id"]]) for p, e in _ex if p["id"] in _ev]
    for p, e, evs in _explained:
        st.info(f"📰 **{p['web_name']}** — {abs(e['net']):,} sold this gameweek, and "
                f"{event_phrase(evs[0])}")
    if not _ex:
        st.success("Nothing unexplained — every heavy sell-off right now has an injury or a status behind it.")
    else:
        st.dataframe(
            [{"photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
              "Player": p["web_name"], "Team": p["team"], "Pos": p["position"],
              "Own%": p["selected_by"], "Sold this GW": abs(e["net"]), "Mins": p["minutes"]}
             for p, e in sorted(_ex, key=lambda t: t[1]["pressure"])],
            hide_index=True, width="stretch",
            column_config={"photo": st.column_config.ImageColumn("", width="small"),
                           "badge": st.column_config.ImageColumn("", width="small"),
                           "Own%": st.column_config.NumberColumn("Own%", format="%.1f%%"),
                           "Sold this GW": st.column_config.NumberColumn("Sold this GW", format="%d")})
        st.caption(f"Owned by **{EXODUS_OWNERSHIP_FLOOR}%+** of managers — the population the threshold was "
                   "measured on. Below that, a few thousand sales look like an exodus and aren't.")

# --- 3 · Headlines (Sprint 115, ADR-093) — public RSS/Atom, opt-in, cached, degrade-gracefully ---------------
st.divider()
st.subheader("3 · Headlines — FPL analysis & football news")
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


# --- 4 · Community chatter (ADR-059) — Reddit RSS. Button-gated (no fetch on load) + cached; degrades. -------
st.divider()
st.subheader("4 · Community chatter")
st.caption("What r/FantasyPL is talking about. **A mention count, not sentiment and not a prediction** — the "
           "least reliable source on this page, which is why it sits last. Best-effort: fetched on demand, "
           "cached ~30 min, and simply absent if Reddit doesn't answer.")
    
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
        # US-4xx / ADR-149 — the shared filter reaches this tab too, **"My squad only" included**.
        # The four boards above have honoured it since US-407b; this one never did, so the one
        # question a manager actually has here — *"is the crowd talking about MY players?"* — was the
        # one it could not answer. Filtered **after** the scan, not before: the full count is what
        # makes the filtered count mean something ("6 of 47"), and the scan is cached for 30 minutes
        # anyway, so it costs nothing to keep.
        shown = apply_filter(buzz, sel)
        if not buzz:
            st.info("No current-player mentions in the latest r/FantasyPL posts.")
        elif not shown:
            st.info(f"None of the **{len(buzz)}** players mentioned match your filter — "
                    "clear it, or untick **My squad only**, to see the rest.")
        else:
            scope = (f"**{len(shown)}** of {len(buzz)} players mentioned match your filter"
                     if len(shown) != len(buzz) else f"{len(buzz)} players mentioned")
            st.caption(f"{scope} across the latest ~100 posts — expand a name to read them. "
                       "(Surnames can collide — the photo/badge shows who matched.)")
            # A 100-post sample mentions many players → page like the other Trending boards (ADR-076).
            for r in show_count(shown):
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
