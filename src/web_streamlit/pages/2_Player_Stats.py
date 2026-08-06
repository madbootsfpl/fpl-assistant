"""Player Stats — the CLI's stat views in the web (ADR-063): over/under-performance, Defensive
Contribution, clean-sheet solidity, and expected goals. Reuses the SAME analytics the CLI does
(`over_under` / `defcon_reliability` / `defensive_solidity`; xG = players by xGI) — no engine change.

Stats are **season-to-date**: preseason these are last season's carryover totals (the bootstrap keeps
prior aggregates until the new season overwrites them). Team badges give context; the boards paginate.
"""

import streamlit as st

from src.analytics import defcon_reliability, defensive_solidity, over_under
from src.storage import Storage
from src.web_streamlit.badges import badge_url_by_short_name
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.filters import filter_controls
from src.web_streamlit.paginate import paginate
from src.web_streamlit.status import render_data_status

st.set_page_config(page_title="Player Stats · FPL Assistant", page_icon="⚽", layout="wide")
render_data_status()
st.title("Player Stats")
st.caption("Over/under-performance · Defensive Contribution · clean sheets · expected goals — reusing the "
           "CLI analytics. **Season-to-date** (preseason = last season's totals); ≥900 mins where noted.")

store = Storage()
try:
    players = store.get_players()
    badges = badge_url_by_short_name(store.get_teams())
finally:
    store.close()

_BADGE = {"badge": st.column_config.ImageColumn("", width="small")}


def _board(rows, columns, key):
    """Render a paginated stat table: a team badge + the given {column: value_of} spec."""
    page = paginate(rows, key=key, per_page=50)
    st.dataframe(
        [{"badge": badges.get(r["team"], ""), "Player": r["web_name"], "Team": r["team"],
          "Pos": r["position"], **{head: value_of(r) for head, value_of in columns.items()}}
         for r in page],
        hide_index=True, width="stretch", column_config=_BADGE,
    )


if not players:
    st.info("No data yet — run `python app.py refresh` first.")
else:
    # A shared filter (ADR-064): Team / Position / Player, AND-combinable — applied to every tab.
    sel = filter_controls(players, key="stats")
    over, defcon, clean, xg = st.tabs(
        ["Over / under-perf", "Defensive Contribution", "Clean sheets", "xG / xA / xGI"])

    with over:
        st.caption("Actual attacking points vs expected (xGI-based) — **+** = running hot (regression "
                   "risk), **−** = due a bounce. ≥900 mins.")
        _board(apply_filter(over_under(players), sel), {
            "Mins": lambda r: r["minutes"], "Actual": lambda r: r["actual"],
            "Exp": lambda r: r["expected"], "Diff": lambda r: f"{r['diff']:+.1f}"}, key="stats_over")

    with defcon:
        st.caption("Defensive Contribution per 90 vs the position threshold — **+ margin** = a reliable "
                   "DefCon points source. ≥900 mins.")
        _board(apply_filter(defcon_reliability(players), sel), {
            "Mins": lambda r: r["minutes"], "DC/90": lambda r: r["per90"],
            "Thr": lambda r: r["threshold"], "Margin": lambda r: f"{r['margin']:+.1f}"}, key="stats_defcon")

    with clean:
        st.caption("Expected goals conceded per 90 (lowest = best clean-sheet prospects) — DEF/GK, ≥900 mins.")
        _board(apply_filter(defensive_solidity(players), sel), {
            "Mins": lambda r: r["minutes"], "xGC/90": lambda r: r["xgc90"]}, key="stats_clean")

    with xg:
        st.caption("Expected goal involvement (xGI = xG + xA), plus expected goals conceded (xGC).")
        ranked = sorted(players, key=lambda p: (p["xgi"] or 0.0), reverse=True)
        _board(apply_filter(ranked, sel), {
            "xG": lambda r: r["xg"], "xA": lambda r: r["xa"],
            "xGI": lambda r: r["xgi"], "xGC": lambda r: r["xgc"]}, key="stats_xg")
