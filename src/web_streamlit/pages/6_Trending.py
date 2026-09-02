"""Trending — community leaderboards from free FPL crowd data (Sprint 067, ADR-057).

Who the crowd is picking / moving: most-owned · most transferred in / out · in form — each a board over the
ingested crowd fields (`selected_by` · `transfers_*_event` · `form`), with photos, badges + the crowd flags.
A display lens, never xP. Ownership works now; the momentum/form boards light up at GW1 (2026-08-21).
"""

import streamlit as st

from src.analytics import CROWD_LEGEND, crowd_flags, trending
from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.filters import filter_controls
from src.web_streamlit.paginate import show_count
from src.web_streamlit.squads import active_squad
from src.web_streamlit.status import render_data_status

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
st.caption("Free FPL crowd data — ownership · transfers · form. A community lens, not a prediction. "
           "For what people are *saying* — official news, headlines and Reddit chatter — see 📡 **Signals**.")

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

    # ---- 👀 Worth noticing (ADR-170) — the signals that live BETWEEN the boards -------------------
    # Each board below ranks one number. The useful patterns need two at once: a player can top none of the
    # four and still be the most interesting name here. Same shape as Players ▸ Scout, and the same
    # discipline — crowd data is a lens that never enters xP, so this says what other managers are **doing**,
    # never why. The "why" is 📡 Signals' half of the ADR-149/150 doing-vs-saying axis.
    from src.analytics.crowd_watch import watch_note, worth_noticing
    from src.web_streamlit.components import render_banner

    st.markdown("##### 👀 Worth noticing")
    _groups = worth_noticing(players)
    st.caption(watch_note(_groups))
    for _g in _groups:
        st.markdown(f"**{_g['label']}**")
        for _r in _g["players"]:
            _price = f" · £{_r['price']:.1f}m" if _r.get("price") is not None else ""
            render_banner(f"<b>{_r['web_name']}</b> ({_r['team']} {_r['position']}{_price}) — {_r['reason']}",
                          kind="signal", icon="👀")
    st.divider()

    # A shared filter (ADR-064): Team / Position / Player, AND-combinable — applied to every board.
    _sq = active_squad()                                    # US-407b: add a "My squad only" scope to the filter
    sel = filter_controls(players, key="trending",
                          my_squad_ids=set(_sq["player_ids"]) if _sq else None)
    st.caption(CROWD_LEGEND)                           # explain the Trends flags (e.g. what "template" means)
    # ADR-150 — the Reddit tabs moved to 📡 **Signals**. Trending is now *only* leaderboards: what the crowd
    # is **doing**, in numbers. What is being **said** is a different question with different reliability, and
    # mixing the two put a mention count beside an ownership percentage as though they were comparable.
    # US-439 (ADR-163) — a **segmented control**, like every other page. This was the one screen still using
    # `st.tabs`, and the inconsistency is not only cosmetic: `st.tabs` renders every board on every run (all
    # four are built, three are hidden with CSS), while a segmented control builds only the chosen one. The
    # consistent widget is also the cheaper one.
    _labels = {b[1]: b for b in _BOARDS}
    # ADR-176 — the shared nav primitive: the same purple, full-width selector the
    # golden page uses. Defined once in `brand`, never pasted (ADR-140).
    st.markdown(brand.nav_css("trending_nav"), unsafe_allow_html=True)
    _nav = st.container(key="trending_nav")
    _chosen = _nav.segmented_control("Board", list(_labels), default=_BOARDS[0][1], key="trend_board",
                                   help="Which leaderboard to show.") or _BOARDS[0][1]
    by, label, header = _labels[_chosen]
    rows = apply_filter(trending(players, by=by, limit=len(players)), sel)   # all, filtered, paged
    if by in ("in", "out", "form") and all((r.get("trend") or 0) == 0 for r in rows):
        st.info("No transfer / form data yet — this board lights up once a gameweek has been played.")
    else:
        page = show_count(rows)
        _board(page, header, lambda r, by=by: _value(by, r["trend"]))
