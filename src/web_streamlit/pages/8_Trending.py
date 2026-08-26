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

    # A shared filter (ADR-064): Team / Position / Player, AND-combinable — applied to every board.
    _sq = active_squad()                                    # US-407b: add a "My squad only" scope to the filter
    sel = filter_controls(players, key="trending",
                          my_squad_ids=set(_sq["player_ids"]) if _sq else None)
    st.caption(CROWD_LEGEND)                           # explain the Trends flags (e.g. what "template" means)
    # ADR-150 — the Reddit tabs moved to 📡 **Signals**. Trending is now *only* leaderboards: what the crowd
    # is **doing**, in numbers. What is being **said** is a different question with different reliability, and
    # mixing the two put a mention count beside an ownership percentage as though they were comparable.
    tabs = st.tabs([b[1] for b in _BOARDS])
    for tab, (by, label, header) in zip(tabs, _BOARDS):
        with tab:
            rows = apply_filter(trending(players, by=by, limit=len(players)), sel)   # all, filtered, paged
            if by in ("in", "out", "form") and all((r.get("trend") or 0) == 0 for r in rows):
                st.info("No transfer / form data yet — this board lights up at **GW1 (2026-08-21)**.")
            else:
                page = show_count(rows)
                _board(page, header, lambda r, by=by: _value(by, r["trend"]))
