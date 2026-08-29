"""My Squad — manage your team + its tools (ADR-105, split from the old Squads page, ADR-069).

A segmented-control sub-nav over the pitch/edit view + the five tools — **My Squad** (edit) · **AI Tips** ·
**Captain** · **Transfer** · **Chips** · **Health** — sharing one squad picker + horizon. Building a *new*
squad now lives in its own **Squad Lab** tab. Only the selected view computes (lazy); each reuses the CLI engine
+ renderers; no server writes (your squad lives in the session — download to keep it).
"""

from datetime import datetime, timezone

import streamlit as st

from src.storage import Storage
from src.ui.deadline import deadline_line
from src.web_streamlit import analytics, brand
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import badge_url_by_short_name, photo_url_by_id
from src.web_streamlit.squads import active_squad, render_sidebar, squad_picker
from src.web_streamlit.status import render_data_status
from src.web_streamlit.views import squads as views

st.set_page_config(**brand.page_config("My Squad"))
require_access()          # opt-in beta gate (ADR-087)
analytics.boot("My Squad")
render_data_status()
render_sidebar()
st.title("🧩 My Squad")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("Your team, all in one place — squad · captain · transfers · chips · health, over the next 1–5 GWs.")

if active_squad() is None:   # US-360: no team built/loaded yet → point new users at the builder (the views use a demo)
    st.info("🛠️ **No team yet?** The views below use a demo — build your own in the **Lab** tab above, "
            "then it lands here.")

# ADR-166 — ordered by the week you actually have, not by the order they were built.
# * **AI Tips second, not default — and that is a measurement, not a preference.** It is the *answer*, so
#   defaulting to it was the obvious call; `ask.answer` takes **4.4 s**, so every visit to this page would
#   have paid it before showing anything. The pitch renders immediately and is what the page *is*. The answer
#   is one tap away, which is the same distance it was, and the page still opens.
# * **Chips folded into AI Tips** (US-434) — both answer "what should I do", on different clocks.
# * **Health → DNA** (US-436): the Squad DNA fingerprint is the informative half, so it leads and names the tab.
# * **Lab last** (US-445): a few times a season — season start, wildcard, free hit — so it belongs at the end
#   of the squad's own workflow, not at the top of the sidebar where it sat.
view = st.segmented_control(
    "Tool", ["My Squad", "AI Tips", "Transfer", "Captain", "DNA", "Lab"], default="My Squad",
    help="**AI Tips** = your week in one answer (captain · lineup · a transfer · flags) plus when to play each "
         "chip; **My Squad** the pitch and lineup; **Transfer** the best swaps; **Captain** who to "
         "(vice-)captain; **DNA** your squad's fingerprint and health; **Lab** build a new squad from scratch.")

# The prediction horizon flows through every sub-tab (ADR-077). A box select (US-315) over a handful of
# useful windows — short for mid-season, up to 10 for a wildcard / start of season. Default 5 = today's
# behaviour; deselecting the segmented control falls back to 5.
# US-374: the squad tools default to the next GW; the **Lab** wants a long window (a wildcard is a
# multi-week bet), which is why it kept its own default of 5 as a page. Keyed per mode so each remembers its
# own setting rather than one clobbering the other — merging the pages must not merge their horizons.
_lab = view == "Lab"
horizon = st.segmented_control(
    "Gameweeks ahead", [1, 2, 3, 4, 5, 10], default=5 if _lab else 1, key=f"gw_ahead_{'lab' if _lab else 'squad'}",
    help="How many upcoming gameweeks the projections look over — short for mid-season, longer for a "
         "wildcard / start of season. (Captaincy is always the next gameweek.)") or (5 if _lab else 1)

store = Storage()
try:
    with analytics.timed("data_load", page="My Squad"):    # perf: FPL data loading (ADR-100, US-336)
        players = store.get_players()
        upcoming = store.get_upcoming_fixtures()
        history = store.get_history_by_code()
        gw_history = store.get_gw_history_by_code()   # in-season form (ADR-060; dormant now)
        teams = store.get_teams()
    photos = photo_url_by_id(players, teams)          # photo, else the club shirt (US-255)
    badges = badge_url_by_short_name(teams)
finally:
    store.close()

_line = deadline_line(upcoming, datetime.now(timezone.utc))    # the next FPL deadline (ADR-086/US-267)
if _line:
    st.caption(_line[2])                                       # the text; the emoji conveys urgency

if not players:
    st.info("No players — it's refreshing; check back shortly.")
else:
    squad_name, squad = squad_picker()      # one picker feeds the manage views
    analytics.track("analysis_run", view=view)   # usage: which manage view was run (no squad contents)
    if view == "AI Tips":
        views.render_ai_tips(squad_name, squad, horizon=horizon)
        st.divider()
        # US-434 — chips live here now: the same question on a different clock, AI Tips answering *this* week
        # and chips answering *which* week. **Behind a button**, because it is another 6.6 s of analytics and
        # ADR-141's rule holds — nothing expensive happens because someone opened a tab. Merging two views
        # must not mean paying for both every time you want one.
        st.markdown("##### 🎴 Chips — when to play each")
        if st.button("Work out my chips →", key="ms_chips",
                     help="Looks across every gameweek left before this set of chips expires (~6s)."):
            st.session_state["ms_chips_on"] = True
        if st.session_state.get("ms_chips_on"):
            views.render_chips(squad_name, squad, upcoming=upcoming)
        else:
            st.caption("A chip is a season decision, so this looks across **every gameweek left before it "
                       "expires** rather than the horizon above — which is why it is a click, not automatic.")
    elif view == "My Squad":
        views.render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos,
                              teams=teams, horizon=horizon)
    elif view == "Transfer":
        views.render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos,
                              horizon=horizon)
    elif view == "Captain":
        team_names = {t["short_name"]: t["name"] for t in teams}   # "MUN" → "Man Utd" (US-278)
        views.render_captain(squad_name, squad, players, upcoming, history, photos, badges, team_names)
    elif view == "DNA":
        team_names = {t["short_name"]: t["name"] for t in teams}
        views.render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges,
                            team_names=team_names, horizon=horizon)
    elif view == "Lab":
        # The Lab keeps the header it had as a page (US-360/ADR-105). A tab called "Lab" has to say what it
        # is: folding a page in must not cost it its identity, only its sidebar slot.
        st.subheader("🧪 Squad Lab")
        st.caption("**Build your squad** — the full optimiser. New season, a wildcard, a free hit or a total "
                   "revamp. **Use this squad →** sends it to the other tabs to manage.")
        views.render_build(players, upcoming, history, gw_history, photos, badges, teams=teams,
                           horizon=horizon)
