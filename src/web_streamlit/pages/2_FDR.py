"""FDR — the fixture difficulty ticker: every club's next few gameweeks, shaded by difficulty.

Split from the combined *Team DNA & FDR* page (ADR-169). They shared a **topic** (teams) but not a **moment**:
the ticker is a weekly "who has a good run?", the fingerprints are occasional research. Bundling them put a
frequent check behind the same click as an infrequent one — the same frequency argument that folded Squad Lab
*into* My Squad (ADR-166) argues for pulling these apart.

⚠️ `/Team_DNA_and_FDR` is retired by the split, so a bookmark to it breaks — the cost ADR-149 named for
`/News → /Signals`. Renumbering every other page is free: Streamlit's slug drops the number prefix.
"""

from collections import Counter

import pandas as pd
import streamlit as st

from src.analytics import fixture_ticker
from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name
from src.web_streamlit.squads import active_squad
from src.web_streamlit.status import render_data_status

st.set_page_config(**brand.page_config("FDR"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("FDR")
render_data_status()
st.title("📅 FDR")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("Every club's next few gameweeks, shaded by difficulty — easiest run first. For how **good** "
           "those clubs actually are, see 🧬 **Team DNA**.")

store = Storage()
try:
    upcoming = store.get_upcoming_fixtures()
    teams = store.get_teams()
    badges = badge_url_by_short_name(teams)
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
    # US-302 (ADR-049) / US-441 (ADR-164): one squad lens per page. It lived on Team DNA and this half read
    # it across the page boundary; separate pages means each owns its own — which is the rule, not a
    # duplication of it.
    _squad_only = st.checkbox("My squad only", key="fdr_myteam",
                              help="Show only the clubs you own players in.")
    my_counts: dict = {}
    if _squad_only:
        squad = active_squad()
        if not squad:
            st.caption("No squad loaded — build or import one on **My Squad**, then come back.")
        else:
            by_id = {p["id"]: p for p in players}
            my_counts = Counter(by_id[i]["team"] for i in squad["player_ids"] if i in by_id)

    # The ticker already comes back easiest-run-first, which is the question it exists to answer. The second
    # question is "where is *my* club?" — and scanning 20 rows ordered by difficulty to find one team is the
    # only thing this page was bad at. Two options, not three: "hardest" is this list read from the bottom,
    # and ADR-166's lesson is that a control earns its place by answering a distinct question.
    _sort = st.segmented_control(
        "Sort by", ["Easiest run", "Team A–Z"], default="Easiest run", key="fdr_sort",
        help="Easiest run first (the default), or alphabetically to find a specific club.") or "Easiest run"

    ticker = fixture_ticker(upcoming, next_n=weeks, source="fpl")
    gws = ticker["gameweeks"]
    gw_cols = [f"GW{g}" for g in gws]

    # When scoped to the squad, keep only the owned teams and add a "Players" count column.
    ticker_rows = [r for r in ticker["rows"] if r["team"] in my_counts] if my_counts else ticker["rows"]
    if _sort == "Team A–Z":
        # `team` is the short name (ARS, MCI) — what the badge column shows, so the order matches what is read.
        ticker_rows = sorted(ticker_rows, key=lambda r: r["team"])
    display_rows, diff_rows = [], []
    for r in ticker_rows:
        disp = {"badge": badges.get(r["team"], ""), "Team": r["team"]}
        if my_counts:
            disp["Players"] = my_counts.get(r["team"], 0)
        diff = {}
        for gw, col in zip(gws, gw_cols):
            cell = r["cells"].get(gw)
            # Include the difficulty digit so the run isn't colour-only (colour-blind-safe; US-391/audit).
            # A double gameweek lists both matches — the ticker is where you go to find them (ADR-129 audit).
            if cell:
                fx = cell.get("fixtures") or [cell]
                disp[col] = " + ".join(f"{f['opponent']} ({f['venue']})" for f in fx) + f" · {cell['difficulty']}"
            else:
                disp[col] = "—"
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
