"""Team DNA — how strong every club is at both ends: a percentile-vs-league fingerprint per club,
and the players to target.

Split from the combined *Team DNA & FDR* page (ADR-169). They shared a **topic** (teams) but not a **moment**:
the ticker is a weekly "who has a good run?", the fingerprints are occasional research. Bundling them put a
frequent check behind the same click as an infrequent one — the same frequency argument that folded Squad Lab
*into* My Squad (ADR-166) argues for pulling these apart.

⚠️ `/Team_DNA_and_FDR` is retired by the split, so a bookmark to it breaks — the cost ADR-149 named for
`/News → /Signals`. Renumbering every other page is free: Streamlit's slug drops the number prefix.
"""


import streamlit as st

from src.storage import Storage
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name
from src.web_streamlit.squads import active_squad
from src.web_streamlit.status import render_data_status

st.set_page_config(**brand.page_config("Team DNA"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("Team DNA")
render_data_status()
st.title("🧬 Team DNA")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("How strong every club is, both ends — a percentile-vs-league fingerprint, its grade, fixtures "
           "and the players to target. For the week-by-week difficulty grid, see 📅 **FDR**.")

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
        # ADR-176 — the shared nav primitive, defined once in `brand` (ADR-140: never pasted).
        st.markdown(brand.nav_css("dna_nav"), unsafe_allow_html=True)
        _nav = st.container(key="dna_nav")
        _sort = _nav.segmented_control("Sort the league by", ["Grade", "Fixtures"], default="Grade",
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
        # The provenance line sits here, not at the top of the page: it qualifies these dots, and a caveat
        # is easiest to trust beside the number it is about rather than three scrolls above it.
        st.caption("Dots = percentile vs the league (🟢 elite → 🔴 weak) — attack, creation and output from "
                   "our own aggregates; the defensive axes are labelled **proxies** that sharpen as the "
                   "season runs. Fixture chips are tinted by difficulty; **h**/**a** = home or away. "
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
