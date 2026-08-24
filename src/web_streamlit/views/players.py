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
    align_seasons,
    crowd_flags,
    defcon_reliability,
    defensive_solidity,
    fit_flag,
    over_under,
    player_history,
    price_flag,
    rank_players,
    set_piece_flags,
)
from src.storage import Storage
from src.web_streamlit.filters import apply as apply_filter
from src.web_streamlit.formats import column_config
from src.web_streamlit.paginate import show_count
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
    """The player pool: sort + a filter-responsive top-15 bar + one scrollable table (ADR-057/064/116)."""
    filtered = apply_filter(rows, sel)
    if not filtered:
        st.info("No players match those filters — clear a filter or raise the price.")
        return
    sort = st.selectbox("Sort by", ["points", "value", "team", "position"],
                        help="Order the table: total points · value (points per £m) · team · position. "
                             "(Clicking a column header re-sorts the whole table too.)")
    ranked = _sorted(filtered, sort)
    # ADR-116: one scrollable, fully-sorted grid (was paged) — so the native column-header sort is honest (it
    # orders the whole set, not just a page). The top-15 bar sits below.
    page = show_count(ranked)
    table = [{"photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
              "Player": p["web_name"], "Team": p["team"], "Pos": p["position"],
              "Fit": fit_flag(p),
              "£m": p["price"], "Pts": p["total_points"], "Val/£m": p.get("value"),
              "Own%": p["selected_by"], "Price": price_flag(p), "Form": p.get("form"),
              "ICT": p.get("ict_index"), "Set": " ".join(set_piece_flags(p)),
              "Trends": " ".join(crowd_flags(p))} for p in page]
    event = st.dataframe(table, width="stretch", hide_index=True, height=560, key="players_pool",
                         selection_mode="multi-row", on_select="rerun",
                         column_config=column_config(table[0] if table else [],
                                                     help={"Fit": AVAILABILITY_LEGEND, "Set": SET_PIECE_LEGEND,
                                                           "Price": PRICE_LEGEND, "Trends": CROWD_LEGEND}))
    # ⭐ Add the selected rows to your watchlist (ADR-117). Row-select → the reliable per-row ⭐ (st.dataframe
    # can't hold per-row buttons). View the watchlist on My Squad → Transfer.
    from src.web_streamlit import watchlist
    try:
        picked_ids = [page[i]["id"] for i in event.selection.rows]
    except Exception:
        picked_ids = []
    wc1, wc2 = st.columns([1, 3], vertical_alignment="center")
    if wc1.button(f"⭐ Add selected ({len(picked_ids)}) to watchlist", key="pool_watch_add", disabled=not picked_ids):
        added = sum(1 for pid in picked_ids if watchlist.add(pid))
        st.toast(f"Added {added} — ⭐ {len(watchlist.ids())}/{watchlist.MAX} watched.")
        st.rerun()
    wc2.caption(f"⭐ **{len(watchlist.ids())}/{watchlist.MAX} watched** — tick rows above then **Add**; view them on "
                "**My Squad → Transfer**.")
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


def _board(stat_rows, columns, badges, key, col_help=None, flag=None, season=None, caveat=""):
    """A scrollable stat table (ADR-116): a team badge + the given {column: value_of} spec.

    `col_help` (optional) maps a column head → a plain-English tooltip (ADR-071). When `flag` is given
    (a row → availability emoji, ADR-074), a compact **Fit** column + a legend caption are added. Column
    formatting + alignment come from the shared convention (ADR-072) via `column_config`. `key` is retained for
    call-site compatibility (paging is retired — the grid scrolls, so the header-sort orders the whole set).

    `season` names the season the rows come from when it isn't this one (ADR-126). These boards need ~10
    matches before a per-90 rate means anything, so until then they show last season rather than nothing — and
    a banner says so, because an unlabelled number from a different season is worse than a blank board.
    `caveat` appends a board-specific warning to that banner."""
    if not stat_rows:                                   # nothing this season *and* no stored history to fall back on
        st.info("🌱 Early season — these season-to-date stats fill in as games are played. "
                "(If you've set a filter, try clearing it.)")
        return
    if season:
        # Clubs come from the *current* row while the numbers come from last season, so a summer signing sits
        # under a badge he wasn't playing for. Say it once here for every board — for the player-level boards
        # the number is still truly his, but read next to the wrong badge it invites the wrong conclusion.
        st.info(f"📅 **Showing {season}** — this season's numbers need about 10 matches before a per-90 rate "
                f"means anything, so these are last season's until then. The board switches over on its own as "
                f"players reach that mark. **Clubs shown are current; the numbers are last season's**, so a "
                f"summer signing earned his at his old club.{caveat}")
    page = show_count(stat_rows)

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
    st.dataframe(table, hide_index=True, width="stretch", height=520,
                 column_config=column_config(labels, help=help_))
    if flag is not None:
        st.caption(AVAILABILITY_LEGEND)


def _this_or_last(analyse, players, last_rows, sel, season_name):
    """The board's rows for this season, or last season's if this season can't answer yet (ADR-126).

    `analyse` is the board's pure function — it runs **unchanged** on last season, because `last_season_rows`
    hands it the same mapping shape `get_players()` does. Returns `(rows, season_label)`, where the label is
    None when the rows are this season's (nothing to announce) and the season name when they are not."""
    rows = apply_filter(analyse(players), sel)
    if rows:
        return rows, None
    return apply_filter(analyse(last_rows or []), sel), (season_name if last_rows else None)


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
    # US-376: headers read as **order** (a rank, 1 = first-choice), not counts — a tester read "Corners 4" as
    # "4 corners". The values are the FPL priority ints.
    _board(rows, {
        "Pen order": lambda r: r.get("penalties_order"), "Corner order": lambda r: r.get("corners_order"),
        "FK order": lambda r: r.get("freekicks_order"),
        "Own%": lambda r: r.get("selected_by"), "Val/£m": lambda r: r.get("value")},
        badges, key="stats_setpiece",
        col_help={"Pen order": "Penalty taking order — 1 = first-choice (2 = second, …); blank = not on pens.",
                  "Corner order": "Corner / indirect free-kick order — 1 = first-choice. Not a count of corners.",
                  "FK order": "Direct (shooting) free-kick order — 1 = first-choice. Not a count.",
                  "Own%": "% of managers who own this player. Low + set-piece duty = a differential.",
                  "Val/£m": "Points per £1m of price — season value."},
        flag=_fit_lookup(players))


def render_over_under(players, sel, badges, last_rows=None, season_name=None):
    st.caption("**Actual** attacking points vs **expected** (xGI-based) — **+** = running hot "
               "(regression risk), **−** = due a bounce. Season totals, ≥900 mins.")
    rows, season = _this_or_last(over_under, players, last_rows, sel, season_name)
    _board(rows, {
        "Mins": lambda r: r["minutes"], "Actual": lambda r: r["actual"],
        "Exp": lambda r: r["expected"], "Diff": lambda r: r["diff"]}, badges, key="stats_over",
        col_help={"Mins": "Minutes played in the season shown.",
                  "Actual": "Actual attacking points scored (season total).",
                  "Exp": "Expected attacking points from xGI (season total).",
                  "Diff": "Actual − Expected. + = over-performing (may regress), − = under (may bounce)."},
        flag=_fit_lookup(players), season=season)


def render_defcon(players, sel, badges, last_rows=None, season_name=None):
    st.caption("**Defensive Contribution per 90** vs the position threshold — **+ margin** = a reliable "
               "DefCon points source. Per-90 rate, ≥900 mins.")
    rows, season = _this_or_last(defcon_reliability, players, last_rows, sel, season_name)
    _board(rows, {
        "Mins": lambda r: r["minutes"], "DC/90": lambda r: r["per90"],
        "Thr": lambda r: r["threshold"], "Margin": lambda r: r["margin"]}, badges, key="stats_defcon",
        col_help={"Mins": "Minutes played in the season shown.",
                  "DC/90": "Defensive Contribution actions per 90 minutes (a rate, not a total).",
                  "Thr": "The position's DefCon points threshold.",
                  "Margin": "DC/90 − threshold. + = clears the bar reliably; higher is better."},
        flag=_fit_lookup(players), season=season)


def render_cleansheet(players, sel, badges, last_rows=None, season_name=None):
    st.caption("**Expected goals conceded per 90** (xGC/90) — **lower = better** clean-sheet prospects. A "
               "team stat while the player is on the pitch, per-90. DEF/GK, ≥900 mins. " + LEGEND)
    rows, season = _this_or_last(defensive_solidity, players, last_rows, sel, season_name)
    pool = [r["xgc90"] for r in rows]
    _board(rows, {
        "Mins": lambda r: r["minutes"], "xGC/90": lambda r: r["xgc90"],
        "Rating": lambda r: rating_cell(r["xgc90"], pool, higher_is_better=False)},
        badges, key="stats_clean",
        col_help={"Mins": "Minutes played in the season shown.",
                  "xGC/90": "Expected goals the team conceded per 90 while this player was on. Lower = better.",
                  "Rating": "Quality vs the players shown (best 20% 🟢 … worst 20% 🔴), with the percentile."},
        flag=_fit_lookup(players), season=season,
        # xGC is a *team* stat, and FPL's history records what a player did without recording who for — so a
        # summer signing brings his old side's defensive record under his new side's badge. Say so (ADR-126).
        caveat=" ⚠️ xGC is a **team** stat, so a player who changed clubs over the summer is showing his "
               "**old** team's defence here.")


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


def _delta_cell(change) -> str:
    """The season price move as a signed value + an up/down cue (US-311): `+0.5 🟢` (rise) / `−0.3 🔴` (fall);
    a flat or unknown move → a plain dash. Pure/display."""
    if change is None:
        return "—"
    if change > 0:
        return f"+{change:.1f} 🟢"
    if change < 0:
        return f"−{abs(change):.1f} 🔴"      # a real minus sign, not a hyphen
    return "0.0"


def render_history(rows, sel, photos, badges):
    """A player's season history on the web (US-298, ADR-027/060) — pick a player → a season table + a per-GW
    trend + the price move. Reuses `analytics.player_history`; the per-GW half is empty preseason (fills at
    GW1). Display-only; an on-demand `Storage` read per selection (no server writes)."""
    st.caption("A player's season-by-season record (points · minutes · **Pts/90** · xGI/xGC · price). "
               "The per-gameweek trend fills once the season starts (GW1).")
    # US-427: the History player picker respects the shared filter (was ignoring it — render_history never took
    # `sel`) — scope the list by team/position/etc. so it's short and relevant.
    pool = apply_filter(rows, sel)
    if not pool:
        st.info("No players match the filter.")
        return
    by_label = {f"{p['web_name']} · {p['team']}": p for p in sorted(pool, key=lambda p: p["web_name"] or "")}
    label = st.selectbox("Player", list(by_label), help="Pick a player to see their history.")
    player = by_label.get(label)
    if not player:
        return

    store = Storage()                                        # a short-lived read for the selected player only
    try:
        hist = player_history(player, store.get_history_past(player["code"]),
                              store.get_history(player["code"]))
    finally:
        store.close()

    c_photo, c_name = st.columns([1, 9], vertical_alignment="center")
    if photos.get(player["id"]):
        c_photo.image(photos[player["id"]], width=52)
    c_name.markdown(f"### {player['web_name']} · {player['team']} · {player['position']}")

    seasons, gws = hist["seasons"], hist["gameweeks"]
    if not seasons and not gws:
        st.info(f"No history stored for {player['web_name']} yet — run `python app.py history --backfill` "
                "(past-season data; per-GW form fills once the season starts).")
        return

    if seasons:
        table = [{"Season": s["season"], "Pts": s["points"], "Mins": s["minutes"], "Starts": s["starts"],
                  "Pts/90": s["pp90"], "xGI": s["xgi"], "xGC": s["xgc"],
                  "£ start": s["start_cost"], "£ end": s["end_cost"], "Δ£": _delta_cell(s["change"])}
                 for s in seasons]
        st.dataframe(table, width="stretch", hide_index=True,
                     column_config=column_config(table[0]))
    if gws:
        st.caption(f"This season — points per gameweek ({len(gws)} played):")
        st.line_chart([{"GW": g["round"], "Points": g["points"]} for g in gws], x="GW", y="Points")
    else:
        st.caption("📈 Per-gameweek form fills once the season starts (GW1).")

    # US-312: optionally overlay a second player's season points (real past-season data now).
    others = {lbl: p for lbl, p in by_label.items() if p["id"] != player["id"]}
    cmp_label = st.selectbox("Compare with (optional)", ["—", *others],
                             help="Overlay a second player's season points, side by side.")
    cmp_player = others.get(cmp_label)
    if cmp_player:
        store = Storage()
        try:
            hist2 = player_history(cmp_player, store.get_history_past(cmp_player["code"]),
                                   store.get_history(cmp_player["code"]))
        finally:
            store.close()
        a_name, b_name = player["web_name"], cmp_player["web_name"]
        if b_name == a_name:                                 # disambiguate two same-named players
            b_name = f"{cmp_player['web_name']} ({cmp_player['team']})"
        rows_c = align_seasons(hist, hist2, key="points")
        if rows_c:
            table_c = [{"Season": r["season"], a_name: r["a"], b_name: r["b"]} for r in rows_c]
            st.caption(f"Season points — **{a_name}** vs **{b_name}**")
            st.dataframe(table_c, width="stretch", hide_index=True)
            st.line_chart(table_c, x="Season", y=[a_name, b_name])
        else:
            st.caption(f"No season history to compare for {a_name} and {b_name}.")


def _card_fixtures(store, short, n=3):
    """The next `n` fixtures for a team → `[{opp, home, fdr}]` for the card's FDR pills. Empty-safe."""
    out = []
    for f in store.get_upcoming_fixtures(short)[:n]:
        home = f["home"] == short                            # `home`/`away` are the short names (ADR-004)
        opp = f["away"] if home else f["home"]
        out.append({"opp": opp, "home": home,
                    "fdr": f["team_h_difficulty"] if home else f["team_a_difficulty"]})
    return out


def render_card(rows, sel, teams, photos, badges):
    """A rich, position-adaptive **player card** (US-343, ADR-084): pick a player -> their card (photo, badge,
    3-GW FDR fixtures, our **Projected xP**, ownership/set-piece flags, position-adaptive stats). Scoped by the
    shared filter; a short-lived Storage read + one decision_xp compute per selection (timed). Display-only."""
    from src.analytics import decision_xp
    from src.web_streamlit import analytics
    from src.web_streamlit.player_card import render_player_card, render_player_compare

    pool = apply_filter(rows, sel)
    if not pool:
        st.info("No players match the filter.")
        return
    by_label = {f"{p['web_name']} · {p['team']}": p for p in sorted(pool, key=lambda p: p["web_name"] or "")}
    player = by_label.get(st.selectbox("Player", list(by_label), help="Pick a player to see their card."))
    if not player:
        return

    # ⭐ Watchlist (ADR-117) — star this player; view them on My Squad → Transfer.
    from src.web_streamlit import watchlist
    _wc1, _wc2 = st.columns([1, 3], vertical_alignment="center")
    if watchlist.contains(player["id"]):
        if _wc1.button("★ Watching — remove", key="card_watch"):
            watchlist.remove(player["id"])
            st.rerun()
    elif watchlist.is_full():
        _wc1.button("⭐ Add to watchlist", key="card_watch", disabled=True,
                    help=f"Watchlist is full ({watchlist.MAX}) — remove one first.")
    elif _wc1.button("⭐ Add to watchlist", key="card_watch"):
        watchlist.add(player["id"])
        st.rerun()
    _wc2.caption(f"⭐ {len(watchlist.ids())}/{watchlist.MAX} on your watchlist — view them on **My Squad → Transfer**.")

    # US-370 (ADR-110): compare with another **same-position** player, side by side. A searchable picker (Streamlit
    # selectboxes filter as you type) scoped to the same position (across all players, not just the filter) so the
    # stat rows always align. "—" = the single card.
    same_pos = sorted((p for p in rows if p["position"] == player["position"] and p["id"] != player["id"]),
                      key=lambda p: p["web_name"] or "")
    cmp_by_label = {f"{p['web_name']} · {p['team']}": p for p in same_pos}
    cmp = cmp_by_label.get(st.selectbox("⚔️ Boot Battle — compare with (same position)", ["—", *cmp_by_label],
                                        help="Type to search a same-position player to compare side by side."))

    short = player["team"]
    team_names = {t["short_name"]: t["name"] for t in teams}
    store = Storage()                                        # short-lived: fixtures + our projected xP
    try:
        with analytics.timed("analysis", page="Players"):    # perf: the decision_xp compute (ADR-100)
            gwh = store.get_gw_history_by_code()              # {code: [rows]} — empty preseason; drives the trend
            ranked = decision_xp(rows, store.get_upcoming_fixtures(), store.get_history_by_code(),
                                 horizon=1, gw_history_by_code=gwh)
        xp = {r["id"]: r["xp"] for r in ranked}
        fixtures = _card_fixtures(store, short)
        cmp_fixtures = _card_fixtures(store, cmp["team"]) if cmp else None
    finally:
        store.close()

    if cmp:                                                  # the two-player comparison (ADR-110)
        cshort = cmp["team"]
        render_player_compare(
            player, cmp,
            a_team=team_names.get(short, short), b_team=team_names.get(cshort, cshort),
            a_photo=photos.get(player["id"]), b_photo=photos.get(cmp["id"]),
            a_fixtures=fixtures, b_fixtures=cmp_fixtures,
            a_xp=xp.get(player["id"]), b_xp=xp.get(cmp["id"]))
    else:
        render_player_card(player, team_name=team_names.get(short, short),
                           photo_url=photos.get(player["id"]), badge_url=badges.get(short),
                           fixtures=fixtures, projected_xp=xp.get(player["id"]))

        # 🧬 Player DNA (ADR-118) — the reusable section: AI Verdict → radar → insights → trend. Reuses the
        # decision_xp + gw_history already loaded; display-only (no new store read, no decision_xp change).
        from src.web_streamlit.player_dna_view import render_player_dna
        render_player_dna(player, rows, xp, gw_history=gwh)
