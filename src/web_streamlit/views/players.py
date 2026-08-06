"""Player views (ADR-069): the pool table + the four stat boards, rendered from a shared filter.

Extracted from the old Players / Player Stats pages — same behaviour, now callable so the consolidated
Players page shows only the segmented-control view that's selected (lazy). All reuse the CLI analytics;
display-only, no server writes.
"""

import altair as alt
import streamlit as st

from src.analytics import (
    crowd_flags,
    defcon_reliability,
    defensive_solidity,
    over_under,
    rank_players,
)
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.paginate import paginate

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
_BADGE = {"badge": st.column_config.ImageColumn("", width="small")}


def _sorted(players, sort_by):
    """Order players by the chosen key. Always go through `rank_players` first (it returns dicts with a
    computed `value`); then for team/position re-sort those dicts (points desc within each group)."""
    ranked = rank_players(players, sort_by="points" if sort_by in ("team", "position") else sort_by)
    if sort_by in ("points", "value"):
        return ranked
    key = (lambda p: (str(p["team"] or ""), -(p["total_points"] or 0))) if sort_by == "team" else \
          (lambda p: (_POS_ORDER.get(p["position"], 9), -(p["total_points"] or 0)))
    return sorted(ranked, key=key)


def render_pool(rows, sel, photos, badges):
    """The player pool: sort + a filter-responsive top-15 bar + the paginated table (ADR-057/063/064)."""
    filtered = apply_filter(rows, sel)
    if not filtered:
        st.info("No players match those filters — clear a filter or raise the price.")
        return
    sort = st.selectbox("Sort by", ["points", "value", "team", "position"],
                        help="Order the table: total points · value (points per £m) · team · position.")
    ranked = _sorted(filtered, sort)
    # The table first (it's what matters most) — page through all matches; the top-15 bar sits below.
    page = paginate(ranked, key="players", per_page=50)
    st.dataframe(
        [{"photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
          "Player": p["web_name"], "Team": p["team"], "Pos": p["position"],
          "£m": p["price"], "Pts": p["total_points"], "Val/£m": p.get("value"),
          "Own%": p["selected_by"], "Form": p.get("form"), "ICT": p.get("ict_index"),
          "Trends": " ".join(crowd_flags(p))} for p in page],
        width="stretch", hide_index=True,
        column_config={"photo": st.column_config.ImageColumn("", width="small"),
                       "badge": st.column_config.ImageColumn("", width="small")},
    )
    by_value = sort == "value"
    field, bar_label = ("value", "Val/£m") if by_value else ("total_points", "Pts")
    top = sorted(ranked, key=lambda p: -((p.get(field) or 0)))[:15]
    bar_data = [{"Player": p["web_name"], "metric": round(p.get(field) or 0, 1)} for p in top]
    st.caption(f"Top {len(top)} of {len(filtered)} filtered players — by {bar_label}")
    st.altair_chart(
        alt.Chart(alt.Data(values=bar_data)).mark_bar().encode(
            x=alt.X("metric:Q", title=bar_label),
            y=alt.Y("Player:N", sort="-x", title=None),
            tooltip=[alt.Tooltip("Player:N"), alt.Tooltip("metric:Q", title=bar_label)],
        ).properties(height=28 * len(bar_data) or 28),
        width="stretch",
    )


def _board(stat_rows, columns, badges, key):
    """A paginated stat table: a team badge + the given {column: value_of} spec (season-to-date)."""
    page = paginate(stat_rows, key=key, per_page=50)
    st.dataframe(
        [{"badge": badges.get(r["team"], ""), "Player": r["web_name"], "Team": r["team"],
          "Pos": r["position"], **{head: value_of(r) for head, value_of in columns.items()}}
         for r in page],
        hide_index=True, width="stretch", column_config=_BADGE,
    )


def render_over_under(players, sel, badges):
    st.caption("Actual attacking points vs expected (xGI-based) — **+** = running hot (regression risk), "
               "**−** = due a bounce. ≥900 mins.")
    _board(apply_filter(over_under(players), sel), {
        "Mins": lambda r: r["minutes"], "Actual": lambda r: r["actual"],
        "Exp": lambda r: r["expected"], "Diff": lambda r: f"{r['diff']:+.1f}"}, badges, key="stats_over")


def render_defcon(players, sel, badges):
    st.caption("Defensive Contribution per 90 vs the position threshold — **+ margin** = a reliable DefCon "
               "points source. ≥900 mins.")
    _board(apply_filter(defcon_reliability(players), sel), {
        "Mins": lambda r: r["minutes"], "DC/90": lambda r: r["per90"],
        "Thr": lambda r: r["threshold"], "Margin": lambda r: f"{r['margin']:+.1f}"}, badges, key="stats_defcon")


def render_cleansheet(players, sel, badges):
    st.caption("Expected goals conceded per 90 (lowest = best clean-sheet prospects) — DEF/GK, ≥900 mins.")
    _board(apply_filter(defensive_solidity(players), sel), {
        "Mins": lambda r: r["minutes"], "xGC/90": lambda r: r["xgc90"]}, badges, key="stats_clean")


def render_xg(players, sel, badges):
    st.caption("Expected goal involvement (xGI = xG + xA), plus expected goals conceded (xGC).")
    ranked = sorted(players, key=lambda p: (p["xgi"] or 0.0), reverse=True)
    _board(apply_filter(ranked, sel), {
        "xG": lambda r: r["xg"], "xA": lambda r: r["xa"],
        "xGI": lambda r: r["xgi"], "xGC": lambda r: r["xgc"]}, badges, key="stats_xg")
