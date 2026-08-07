"""A formation "pitch" view for the Streamlit edge (Sprint 062, US-187).

A robust, native card-grid — position rows (GK / DEF / MID / FWD) + a bench row — not a custom-CSS pitch
(owner's call: robustness first). Each card keeps the info the table showed: photo · name (+ **(C)**) ·
team · £ · xP · next opponent (H/A) · crowd flags. Pure presentation over data the page already holds.
"""

import streamlit as st

from src.analytics import crowd_flags

_ROWS = ("GK", "DEF", "MID", "FWD")
_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}


def _card(player, *, captain_id, xp_by_id, photos, next_opp, sub_role=None) -> None:
    with st.container(border=True):
        url = photos.get(player["id"], "")
        if url:
            # Centre the photo within the card (US-188) — a nested [1,2,1] column, robust + native
            # (no custom CSS); one level of nesting inside the row column, allowed by Streamlit.
            _, mid, _ = st.columns([1, 2, 1])
            mid.image(url, width=54)
        name = player["web_name"] + (" **(C)**" if player["id"] == captain_id else "")
        st.markdown(f"**{name}**")
        if sub_role:   # a bench card's auto-sub priority (US-246): "🔁 1st sub" / "🔁 GK sub"
            st.caption("🔁 GK sub" if sub_role == "GK" else f"🔁 {sub_role} sub")
        opp = next_opp.get(player["team"])
        opp_str = f"{opp['opponent']} ({opp['venue']})" if opp else "—"
        st.caption(f"{player['team']} · £{player['price']:.1f}m · "
                   f"{round(xp_by_id.get(player['id'], 0), 1)} xP · {opp_str}")
        flags = crowd_flags(player)
        if flags:
            st.caption(" ".join(flags))


_ROLE_ORDER = {"1st": 0, "2nd": 1, "3rd": 2, "4th": 3, "GK": 4}


def render_pitch(xi, bench, *, captain_id, xp_by_id, photos, next_opp, bench_roles=None) -> None:
    """Lay out the XI by position rows + a bench row, each player a card (US-187).

    `xi` / `bench` are player rows; `next_opp` maps a team short_name → its next fixture cell
    (`{opponent, venue, ...}`) or None. `bench_roles` (optional, US-246) maps id → sub role
    ("1st"/"2nd"/"3rd"/"GK"); when given, the bench row is ordered by that priority and each card is
    labelled. Native `st.columns`/`st.container` — themeable + headless-testable.
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
        if bench_roles:   # priority order (1st → GK) + labelled cards (US-246)
            ordered = sorted(bench, key=lambda p: _ROLE_ORDER.get(bench_roles.get(p["id"]), 9))
        else:
            ordered = sorted(bench, key=lambda p: _ORDER.get(p["position"], 9))
        for col, player in zip(st.columns(len(ordered)), ordered):
            with col:
                _card(player, sub_role=(bench_roles or {}).get(player["id"]), **kw)
