"""A formation "pitch" view for the Streamlit edge (Sprint 062, US-187).

A robust, native card-grid — position rows (GK / DEF / MID / FWD) + a bench row — not a custom-CSS pitch
(owner's call: robustness first). Each card keeps the info the table showed: photo · name (+ **(C)**) ·
team · £ · xP · next opponent (H/A) · crowd flags. Pure presentation over data the page already holds.
"""

import streamlit as st

from src.analytics import crowd_flags

_ROWS = ("GK", "DEF", "MID", "FWD")
_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def _card(player, *, captain_id, xp_by_id, photos, next_opp) -> None:
    with st.container(border=True):
        url = photos.get(player["id"], "")
        if url:
            # Centre the photo within the card (US-188) — a nested [1,2,1] column, robust + native
            # (no custom CSS); one level of nesting inside the row column, allowed by Streamlit.
            _, mid, _ = st.columns([1, 2, 1])
            mid.image(url, width=54)
        name = player["web_name"] + (" **(C)**" if player["id"] == captain_id else "")
        st.markdown(f"**{name}**")
        opp = next_opp.get(player["team"])
        opp_str = f"{opp['opponent']} ({opp['venue']})" if opp else "—"
        st.caption(f"{player['team']} · £{player['price']:.1f}m · "
                   f"{round(xp_by_id.get(player['id'], 0), 1)} xP · {opp_str}")
        flags = crowd_flags(player)
        if flags:
            st.caption(" ".join(flags))


def render_pitch(xi, bench, *, captain_id, xp_by_id, photos, next_opp) -> None:
    """Lay out the XI by position rows + a bench row, each player a card (US-187).

    `xi` / `bench` are player rows; `next_opp` maps a team short_name → its next fixture cell
    (`{opponent, venue, ...}`) or None. Native `st.columns`/`st.container` — themeable + headless-testable.
    """
    kw = dict(captain_id=captain_id, xp_by_id=xp_by_id, photos=photos, next_opp=next_opp)
    for pos in _ROWS:
        line = [p for p in xi if p["position"] == pos]
        if not line:
            continue
        for col, player in zip(st.columns(len(line)), line):
            with col:
                _card(player, **kw)

    if bench:
        st.caption("— Bench —")
        ordered = sorted(bench, key=lambda p: _ORDER.get(p["position"], 9))
        for col, player in zip(st.columns(len(ordered)), ordered):
            with col:
                _card(player, **kw)
