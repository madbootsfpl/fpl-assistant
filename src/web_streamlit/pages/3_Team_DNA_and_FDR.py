"""Team DNA & FDR — the team-level tab (ADR-134).

Organised by *level*: team things live here, player things live on Players (which is where the 🎯 Radar moved).
The section opens on a **scan** of all 20 clubs — grade + ATT/DEF/FIX + next opponent — then drills into one
club's full DNA card, then the fixture-ticker grid (Sprint 062): teams × gameweeks, colour-coded by difficulty.

Pick how many weeks to show (1–8); teams are rows (easiest run first), gameweeks are columns, each cell the
opponent + (H/A) shaded green (easy) → red (hard). Reuses `fixture_ticker` (which reuses `team_fdr` /
`team_schedule`) — no core change, no new analytics.
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

# FPL difficulty 1–5 → the shared brand FDR scale (ADR-114): (bg, text) pairs, vibrant green→red, each with a text
# colour that clears contrast. One home for the palette (brand.FDR_STYLE) — the ticker + the card FDR pills share it.

st.set_page_config(**brand.page_config("Team DNA and FDR"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Fixtures")
render_data_status()
st.title("🧬 Team DNA & FDR")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("How strong every club is, both ends — then the difficulty ticker, week by week. "
           "Looking for **players** to buy? The 🎯 **Radar** moved to the **Players** tab.")

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
    from src.analytics import last_season_name, last_season_rows, team_dna_all, team_schedule
    from src.analytics.gw_form import team_form
    from src.web_streamlit.team_dna_card import key_players_this_or_last, render_team_dna
    st.subheader("🧬 Team DNA")
    st.caption("How strong is a team, both ends — a percentile-vs-league fingerprint, its grade, fixtures and the "
               "players to target. Attack/creation/output from our aggregates; the defensive axes are proxies "
               "(labelled) that sharpen once the season runs.")
    _names = {t["short_name"]: t["name"] for t in teams}
    _last_rows = last_season_rows(players, history)
    _all_dna = team_dna_all(players, upcoming, team_names=_names, gw_history=gw_history,
                            last_rows=_last_rows)
    # Bound before the `if _all_dna` below, because the ticker further down reads it too — and on a snapshot
    # with no DNA to draw that block never runs, which would leave the name undefined at the ticker.
    _squad_only = False
    # ADR-134 — the section opens on a SCAN of all 20 clubs, not a one-team selectbox. This answers the
    # ticker's question ("who has a good run?") while also saying how good those teams are — which a
    # difficulty grid can't: a 100th-percentile run at a C-grade side reads very differently from an A's.
    if _all_dna:
        from src.web_streamlit.team_dna_card import league_rows, your_teams_strip_html
        # US-441 (ADR-164) — ONE squad lens for the page. The filter existed only on the ticker further down,
        # so the 20-club scan above it ignored a control the reader had already set: the same page answered
        # "my squad" in one half and "the league" in the other, with nothing saying which was which.
        _my_squad = active_squad()
        _my_clubs = ({p["team"] for p in players if p["id"] in set(_my_squad["player_ids"])}
                     if _my_squad else set())
        _squad_only = st.checkbox("My squad only", key="dna_myteam", disabled=not _my_clubs,
                                  help=("Show only the clubs you own players in — on the scan AND the ticker."
                                        if _my_clubs else "Load a squad on My Squad to use this."))
        _sort = st.segmented_control("Sort the league by", ["Grade", "Fixtures"], default="Grade",
                                     key="dna_league_sort",
                                     help="Best teams first, or easiest run first.") or "Grade"
        # Three fixtures, not one: one opponent says who's next, three say whether the run the FIX percentile
        # claims actually looks like one. Tinted chips make three fit the width one text pair used.
        _nxt = {t: team_schedule(upcoming, t)[:3] for t in _all_dna}
        _scan_rows = league_rows(_all_dna, _nxt, sort_by="fixtures" if _sort == "Fixtures" else "grade")
        if _squad_only and _my_clubs:
            _scan_rows = [r for r in _scan_rows if r["team"] in _my_clubs]
        # ADR-158 — tap a row to select that club. ADR-133's gesture, on the surface the roadmap asked for it:
        # a tap that SELECTS, never one that opens a menu (that was ADR-135, and it was reverted). The picker
        # below stays, so AppTest keeps driving this page and a missing component degrades to what it was.
        from src.web_streamlit import tap
        _team_labels = {t: _names.get(t, t) for t in _all_dna}
        _tappable = tap.available()
        # Fall back to the label the selectbox will *itself* default to on a first load, or the outline and
        # the picker would disagree until the first interaction.
        _sorted_teams = sorted(_all_dna, key=lambda t: _names.get(t, t))
        _first = _names.get(_sorted_teams[0], _sorted_teams[0]) if _sorted_teams else None
        _picked_now = st.session_state.get("team_dna_pick") or _first
        _sel = next((t for t, lab in _team_labels.items() if lab == _picked_now), None)
        _scan_html = your_teams_strip_html(
            _scan_rows,
            title=("🧬 Your clubs — grade · ATT/DEF/FIX · next 3" if (_squad_only and _my_clubs)
                   else "🧬 The league at a glance — grade · ATT/DEF/FIX · next 3"),
            clickable=_tappable, selected=_sel)
        if _tappable:
            tap.select_from_html(_scan_html, select_key="team_dna_pick", label_by_id=_team_labels,
                                 key="dna_scan_tap")
        else:
            st.markdown(_scan_html, unsafe_allow_html=True)
        st.caption("Dots = percentile vs the league (🟢 elite → 🔴 weak). Fixture chips are tinted by "
                   "difficulty; **h**/**a** = home or away. "
                   + ("**Tap a row** for that club's full DNA, or pick one below."
                      if _tappable else "Pick a club below for its full DNA."))
    if _all_dna:
        _labels = {_names.get(t, t): t for t in sorted(_all_dna, key=lambda t: _names.get(t, t))}
        _picked = _labels.get(st.selectbox("Team", list(_labels), key="team_dna_pick",
                                           help="Pick a team to see its DNA fingerprint."))
        if _picked:
            _sched = team_schedule(upcoming, _picked)[:6]
            _fx = [(s["event"], s["opponent"], s["venue"], s["difficulty"]) for s in _sched]
            # ADR-126: ranking needs ~900 minutes, so fall back to last season until this one can answer.
            _kp, _kp_season = key_players_this_or_last(
                players, _picked, _last_rows, last_season_name(history))
            render_team_dna(_all_dna[_picked], fixtures=_fx, key_players=_kp, key_players_season=_kp_season,
                            form=team_form(gw_history, players, _picked))


    st.divider()
    # The ticker — the detailed week-by-week view, below the league scan (ADR-134).
    # US-440 — it had **no heading at all**: the page title said "Team DNA & FDR" and only the DNA half was
    # ever announced, so the second half of the page read as an unlabelled appendage to the first.
    st.subheader("📅 FDR — the difficulty ticker")
    st.caption("Every club's next few gameweeks, shaded by difficulty — the week-by-week detail behind the "
               "**FIX** percentile above.")
    weeks = st.slider("Weeks to show", 1, 8, 6,
                      help="How many upcoming gameweeks to show in the difficulty ticker.")
    # US-302 (ADR-049) / US-441 (ADR-164): the ticker reads the page's **one** squad lens, set above the scan,
    # rather than carrying a second checkbox that could disagree with it.
    my_counts: dict = {}
    if _squad_only:
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
