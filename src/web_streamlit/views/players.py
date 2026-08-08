"""Player views (ADR-069): the pool table + the four stat boards, rendered from a shared filter.

Extracted from the old Players / Player Stats pages — same behaviour, now callable so the consolidated
Players page shows only the segmented-control view that's selected (lazy). All reuse the CLI analytics;
display-only, no server writes.
"""

import altair as alt
import streamlit as st

from src.analytics import (
    AVAILABILITY_LEGEND,
    CROWD_LEGEND,
    PRICE_LEGEND,
    SET_PIECE_LEGEND,
    crowd_flags,
    defcon_reliability,
    defensive_solidity,
    fit_flag,
    over_under,
    price_flag,
    rank_players,
    set_piece_flags,
)
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.formats import column_config
from src.web_streamlit.paginate import paginate
from src.web_streamlit.ratings import LEGEND, rating_cell

_POS_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
_RATING_MIN_MINUTES = 900   # the "enough to be meaningful" bar (matches the other boards; ADR-073)


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
    table = [{"photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
              "Player": p["web_name"], "Team": p["team"], "Pos": p["position"],
              "Fit": fit_flag(p),
              "£m": p["price"], "Pts": p["total_points"], "Val/£m": p.get("value"),
              "Own%": p["selected_by"], "Price": price_flag(p), "Form": p.get("form"),
              "ICT": p.get("ict_index"), "Set": " ".join(set_piece_flags(p)),
              "Trends": " ".join(crowd_flags(p))} for p in page]
    st.dataframe(table, width="stretch", hide_index=True,
                 column_config=column_config(table[0] if table else [],
                                             help={"Fit": AVAILABILITY_LEGEND, "Set": SET_PIECE_LEGEND,
                                                   "Price": PRICE_LEGEND, "Trends": CROWD_LEGEND}))
    st.caption(AVAILABILITY_LEGEND)
    st.caption(PRICE_LEGEND)
    st.caption(CROWD_LEGEND)
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


def _fit_lookup(players):
    """A `(web_name, team) → Fit flag` map, for the trimmed stat rows that lack `status` (ADR-074).
    The full `players` list is passed to each board, so no analytics change is needed."""
    flag = {(p["web_name"], p["team"]): fit_flag(p) for p in players}
    return lambda r: flag.get((r["web_name"], r["team"]), "")


def _board(stat_rows, columns, badges, key, col_help=None, flag=None):
    """A paginated stat table: a team badge + the given {column: value_of} spec (season-to-date).

    `col_help` (optional) maps a column head → a plain-English tooltip (ADR-071). When `flag` is given
    (a row → availability emoji, ADR-074), a compact **Fit** column + a legend caption are added. Column
    formatting + alignment come from the shared convention (ADR-072) via `column_config`."""
    page = paginate(stat_rows, key=key, per_page=50)

    def _row(r):
        base = {"badge": badges.get(r["team"], ""), "Player": r["web_name"], "Team": r["team"],
                "Pos": r["position"]}
        if flag is not None:
            base["Fit"] = flag(r)                       # right after Pos, before the metrics
        base.update({head: value_of(r) for head, value_of in columns.items()})
        return base

    table = [_row(r) for r in page]
    labels = ["badge", "Player", "Team", "Pos", *(["Fit"] if flag is not None else []), *columns]
    help_ = dict(col_help or {})
    if flag is not None:
        help_["Fit"] = AVAILABILITY_LEGEND
    st.dataframe(table, hide_index=True, width="stretch", column_config=column_config(labels, help=help_))
    if flag is not None:
        st.caption(AVAILABILITY_LEGEND)


def render_set_pieces(players, sel, badges):
    """Who takes penalties / corners / free-kicks (ADR-081) — the order ints (1 = first-choice) alongside
    Own% + Val/£m, so a **low-owned taker** (a prime differential) stands out. Display-only; reuses the
    shared filter. Only players with a set-piece duty are listed."""
    st.caption("Who takes **penalties · corners · free-kicks** for each team — the **order** (1 = "
               "first-choice taker, higher = backup). A set-piece taker with a **low Own%** is a prime "
               "**differential** — sort by **Own%** ascending to surface under-owned takers. " + SET_PIECE_LEGEND)
    ranked = rank_players(players, sort_by="value")     # attach Val/£m
    takers = [p for p in ranked
              if p.get("penalties_order") or p.get("corners_order") or p.get("freekicks_order")]
    rows = apply_filter(takers, sel)
    if not rows:
        st.info("No set-piece takers match those filters — clear a filter, or run `python app.py refresh` "
                "to populate the set-piece data.")
        return
    # Default order: first-choice penalty takers first (order 1 → top), then most-owned within.
    rows = sorted(rows, key=lambda p: (p.get("penalties_order") or 99, -(p.get("selected_by") or 0)))
    _board(rows, {
        "Pen": lambda r: r.get("penalties_order"), "Corners": lambda r: r.get("corners_order"),
        "FK": lambda r: r.get("freekicks_order"),
        "Own%": lambda r: r.get("selected_by"), "Val/£m": lambda r: r.get("value")},
        badges, key="stats_setpiece",
        col_help={"Pen": "Penalty order — 1 = first-choice taker (blank = not on penalties).",
                  "Corners": "Corner / indirect free-kick order — 1 = first-choice.",
                  "FK": "Direct (shooting) free-kick order — 1 = first-choice.",
                  "Own%": "% of managers who own this player. Low + set-piece duty = a differential.",
                  "Val/£m": "Points per £1m of price — season value."},
        flag=_fit_lookup(players))


def render_over_under(players, sel, badges):
    st.caption("**Actual** attacking points vs **expected** (xGI-based) this season — **+** = running hot "
               "(regression risk), **−** = due a bounce. Season totals, ≥900 mins.")
    _board(apply_filter(over_under(players), sel), {
        "Mins": lambda r: r["minutes"], "Actual": lambda r: r["actual"],
        "Exp": lambda r: r["expected"], "Diff": lambda r: r["diff"]}, badges, key="stats_over",
        col_help={"Mins": "Minutes played this season.",
                  "Actual": "Actual attacking points scored (season total).",
                  "Exp": "Expected attacking points from xGI (season total).",
                  "Diff": "Actual − Expected. + = over-performing (may regress), − = under (may bounce)."},
        flag=_fit_lookup(players))


def render_defcon(players, sel, badges):
    st.caption("**Defensive Contribution per 90** vs the position threshold — **+ margin** = a reliable "
               "DefCon points source. Per-90 rate, ≥900 mins.")
    _board(apply_filter(defcon_reliability(players), sel), {
        "Mins": lambda r: r["minutes"], "DC/90": lambda r: r["per90"],
        "Thr": lambda r: r["threshold"], "Margin": lambda r: r["margin"]}, badges, key="stats_defcon",
        col_help={"Mins": "Minutes played this season.",
                  "DC/90": "Defensive Contribution actions per 90 minutes (a rate, not a total).",
                  "Thr": "The position's DefCon points threshold.",
                  "Margin": "DC/90 − threshold. + = clears the bar reliably; higher is better."},
        flag=_fit_lookup(players))


def render_cleansheet(players, sel, badges):
    st.caption("**Expected goals conceded per 90** (xGC/90) — **lower = better** clean-sheet prospects. A "
               "team stat while the player is on the pitch, per-90. DEF/GK, ≥900 mins. " + LEGEND)
    rows = apply_filter(defensive_solidity(players), sel)
    pool = [r["xgc90"] for r in rows]
    _board(rows, {
        "Mins": lambda r: r["minutes"], "xGC/90": lambda r: r["xgc90"],
        "Rating": lambda r: rating_cell(r["xgc90"], pool, higher_is_better=False)},
        badges, key="stats_clean",
        col_help={"Mins": "Minutes played this season.",
                  "xGC/90": "Expected goals the team conceded per 90 while this player was on. Lower = better.",
                  "Rating": "Quality vs the players shown (best 20% 🟢 … worst 20% 🔴), with the percentile."},
        flag=_fit_lookup(players))


def render_xg(players, sel, badges):
    st.caption("**Expected goal involvement** (xGI = xG + xA) — **higher = better**. Absolute season "
               "totals (a model's expected goals), plus expected goals conceded (xGC). " + LEGEND)
    rows = apply_filter(sorted(players, key=lambda p: (p["xgi"] or 0.0), reverse=True), sel)
    # xGI is only a real signal for outfield players who've actually played — rating a keeper (xGI ≈ 0)
    # or a 0-minute backup is meaningless (ADR-073). Rate only those, against that pool; blank the rest.
    def _rate_xgi(r):
        return r["position"] != "GK" and (r["minutes"] or 0) >= _RATING_MIN_MINUTES and r["xgi"] is not None
    pool = [r["xgi"] for r in rows if _rate_xgi(r)]
    _board(rows, {
        "xG": lambda r: r["xg"], "xA": lambda r: r["xa"], "xGI": lambda r: r["xgi"],
        "xGI rating": lambda r: rating_cell(r["xgi"], pool, higher_is_better=True) if _rate_xgi(r) else "—",
        "xGC": lambda r: r["xgc"]},
        badges, key="stats_xg",
        col_help={"xG": "Expected goals (season total).", "xA": "Expected assists (season total).",
                  "xGI": "xG + xA — expected goal involvements (season total). Higher = better.",
                  "xGI rating": "Attacking quality (xGI) vs outfield players with ≥900 mins (best 20% 🟢 … "
                                "worst 20% 🔴). Keepers & low-minutes players aren't rated (—).",
                  "xGC": "Expected goals conceded while on the pitch (season total)."},
        flag=fit_flag)   # xG uses raw player rows (they carry status)
