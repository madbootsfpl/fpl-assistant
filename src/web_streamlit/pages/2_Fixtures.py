"""Fixtures — a fixture-ticker grid (Sprint 062): teams × gameweeks, colour-coded by difficulty.

Pick how many weeks to show (1–8); teams are rows (easiest run first), gameweeks are columns, each cell the
opponent + (H/A) shaded green (easy) → red (hard). Reuses `fixture_ticker` (which reuses `team_fdr` /
`team_schedule`) — no core change, no new analytics.
"""

from collections import Counter

import pandas as pd
import streamlit as st

from src.analytics import decision_xp, fixture_ticker, points_per_million, target_by_fixtures, team_fdr
from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name
from src.web_streamlit.squads import active_squad
from src.web_streamlit.status import render_data_status

# FPL difficulty 1–5 → the shared brand FDR scale (ADR-114): (bg, text) pairs, vibrant green→red, each with a text
# colour that clears contrast. One home for the palette (brand.FDR_STYLE) — the ticker + the card FDR pills share it.

st.set_page_config(**brand.page_config("Fixtures"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Fixtures")
render_data_status()
st.title("📅 Fixtures")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("The difficulty ticker — teams × gameweeks, colour-coded by how hard each run is.")

store = Storage()
try:
    upcoming = store.get_upcoming_fixtures()
    badges = badge_url_by_short_name(store.get_teams())
    players = store.get_players()
    history = store.get_history_by_code()
    gw_history = store.get_gw_history_by_code()
finally:
    store.close()

if not upcoming:
    st.info("No fixtures yet — it's refreshing; check back shortly.")
else:
    weeks = st.slider("Weeks to show", 1, 8, 6,
                      help="How many upcoming gameweeks to show in the difficulty ticker.")
    # US-302 (ADR-049): focus the ticker on your own teams — which of *your* teams face a hard run.
    # US-407b: a "My squad only" checkbox — consistent with Players/News/Trending/Radar (was a segmented control).
    my_only = st.checkbox("My squad only", key="ticker_myteam",
                          help="Focus the ticker on the teams in your active squad.")
    my_counts: dict = {}
    if my_only:
        squad = active_squad()
        if not squad:
            st.caption("No squad loaded — build or import one on **My Squad**, then come back.")
        else:
            by_id = {p["id"]: p for p in players}
            my_counts = Counter(by_id[i]["team"] for i in squad["player_ids"] if i in by_id)

    ticker = fixture_ticker(upcoming, next_n=weeks, source="fpl")
    gws = ticker["gameweeks"]
    gw_cols = [f"GW{g}" for g in gws]

    # When scoped to the squad, keep only the owned teams and add a "Players" count column.
    ticker_rows = [r for r in ticker["rows"] if r["team"] in my_counts] if my_counts else ticker["rows"]
    display_rows, diff_rows = [], []
    for r in ticker_rows:
        disp = {"badge": badges.get(r["team"], ""), "Team": r["team"]}
        if my_counts:
            disp["Players"] = my_counts.get(r["team"], 0)
        diff = {}
        for gw, col in zip(gws, gw_cols):
            cell = r["cells"].get(gw)
            # Include the difficulty digit so the run isn't colour-only (colour-blind-safe; US-391/audit).
            disp[col] = f"{cell['opponent']} ({cell['venue']}) · {cell['difficulty']}" if cell else "—"
            diff[col] = cell["difficulty"] if cell else None
        display_rows.append(disp)
        diff_rows.append(diff)

    disp_df = pd.DataFrame(display_rows)
    diff_df = pd.DataFrame(diff_rows)

    def _shade(_):
        # A same-shaped CSS frame: colour the GW cells by their difficulty; leave badge/Team blank.
        css = pd.DataFrame("", index=disp_df.index, columns=disp_df.columns)
        for col in gw_cols:
            css[col] = [f"background-color: {brand.FDR_STYLE[d][0]}; color: {brand.FDR_STYLE[d][1]}"
                        if d in brand.FDR_STYLE else "" for d in diff_df[col]]
        return css

    st.caption("Easiest run first · green = easy, red = hard · the **· N** in each cell is the difficulty "
               "(1 easy – 5 hard) · (H)ome / (A)way.")
    st.dataframe(
        disp_df.style.apply(_shade, axis=None),
        hide_index=True, width="stretch",
        column_config={"badge": st.column_config.ImageColumn("", width="small")},
    )

    # 🎯 Radar (US-301; renamed ADR-107) — turn "which teams have a good run" into "who to buy" for a new
    # squad / wildcard: the best available players from the easiest-run teams, ranked by the app's xP.
    st.divider()
    st.subheader("🎯 Radar")                           # MADBOOTS vocab (ADR-107): players to watch
    st.caption("Players on your radar — the best available from the easiest-run teams over your window, "
               "for planning a new squad or a wildcard.")
    position = st.segmented_control(
        "Position", ["All", "GK", "DEF", "MID", "FWD"], default="All", key="target_pos",
        help="Filter the targets to one position (e.g. which defenders have the best runs).")
    # US-303: a budget cap — show only targets you can afford (for a wildcard / a tight new squad).
    max_price = st.slider("Max price", 4.0, 15.5, 15.5, step=0.5, key="target_max_price",
                          help="Show only targets at or below this price (£m). Full range = show all.")
    # US-304: rank each team's picks by xP (default) or Val/£m (points per £m, ADR-042 — bang-for-buck).
    sort_label = st.segmented_control("Sort", ["xP", "Val/£m"], default="xP", key="target_sort",
                                      help="Rank each team's targets by expected points, or by value per £m.")
    # US-407b: a "My squad only" scope — which of *your* players sit on the radar (good runs to hold), consistent
    # with Players/News/Trending/Fixtures.
    radar_mine = st.checkbox("My squad only", key="radar_myteam",
                             help="Show only players from your active squad on the Radar.")
    ranked = decision_xp(players, upcoming, history, horizon=weeks, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    value_by_id = {p["id"]: points_per_million(p["total_points"], p["price"]) for p in players}
    targets = target_by_fixtures(
        team_fdr(upcoming, next_n=weeks), players, xp_by_id, position=position, max_price=max_price,
        sort_by="value" if sort_label == "Val/£m" else "xp", value_by_id=value_by_id)
    if radar_mine:
        _sq = active_squad()
        _owned = set(_sq["player_ids"]) if _sq else set()
        targets = [t for t in targets if t["id"] in _owned]
    if targets:
        target_rows = [{
            "Team": t["team"],
            "FDR": t["avg_difficulty"],
            "Next": ", ".join(t["opponents"]),
            "Player": t["web_name"],
            "Pos": t["position"],
            "£m": t["price"],
            "Own%": t["selected_by"],
            "Fit": t["fit"],
            "xP": t["xp"],
            "Val/£m": t["value"],
        } for t in targets]
        st.dataframe(
            pd.DataFrame(target_rows), hide_index=True, width="stretch",
            column_config={
                "FDR": st.column_config.NumberColumn("FDR", format="%.1f", help="Average fixture difficulty"),
                "£m": st.column_config.NumberColumn("£m", format="£%.1fm"),
                "Own%": st.column_config.NumberColumn("Own%", format="%.1f"),
                "xP": st.column_config.NumberColumn("xP", format="%.1f", help="Expected points (the app's one metric)"),
                "Val/£m": st.column_config.NumberColumn("Val/£m", format="%.1f", help="Points per £m (value)"),
            },
        )
    else:
        st.caption("No available targets for that position in the top-run teams.")
