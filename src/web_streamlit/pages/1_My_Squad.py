"""My Squad — manage your team + its tools (ADR-105, split from the old Squads page, ADR-069).

ADR-171 merged three of those views into one screen: **My Squad** now carries ① the week's answer, the pitch
and ⚙ panel, ② captaincy inline, and ③ chips behind a button — so the decision and the squad it is about are
on the same page. The sub-nav is what is left: **My Squad · Transfer · DNA · Leagues · Lab**, sharing one squad
picker + horizon. Only the selected view computes (lazy); each reuses the CLI engine + renderers; no server
writes (your squad lives in the session — download to keep it).
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

# ADR-166 ordered these by how often you need them; ADR-171 removed two of them entirely.
# * **AI Tips and Captain are no longer tabs** (US-435) — they are sections ① and ② of My Squad. ADR-166 kept
#   AI Tips off the default because `ask.answer` cost **4.4 s**; re-measured 2026-08-31 that is **123 ms** on
#   Cloud, where nobody has Ollama, and **27 s** on a dev box that does. The barrier was real and it was a
#   fact about one machine — so the tab order was carrying a laptop's latency into everyone's navigation.
# * **Chips stays a click** (③) — not for latency, but because a chip is a season decision on a different
#   clock and should not fire because someone opened a page (ADR-166's substantive half, unchanged).
# * **Health → DNA** (US-436): the Squad DNA fingerprint is the informative half, so it leads and names the tab.
# * **Lab last** (US-445): a few times a season — season start, wildcard, free hit — so it belongs at the end
#   of the squad's own workflow, not at the top of the sidebar where it sat.
view = st.segmented_control(
    "Tool", ["My Squad", "Transfer", "DNA", "Leagues", "Lab"], default="My Squad",
    key="ms_tool",     # keyed: without one Streamlit identifies it positionally, so a tab that adds widgets
                       # (Leagues adds a dozen) can shift its identity and silently reset the selection.
    help="**My Squad** = your week in one screen — the answer, the pitch and lineup, then who to "
         "(vice-)captain and when to play each chip; **Transfer** the best swaps; **DNA** your squad's "
         "fingerprint and health; **Leagues** how your picks compare with your rivals'; **Lab** build a new "
         "squad from scratch.")

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
    if view == "My Squad":
        # ADR-171 — the golden page, in the order the week is actually decided:
        #   ① the answer · the pitch + ⚙ panel it is about · ② captaincy · ③ chips.
        # Transfer is deliberately NOT folded in: US-435 did not ask for it, and it is the one view here that
        # is a genuinely different task rather than another angle on this week.
        team_names = {t["short_name"]: t["name"] for t in teams}   # "MUN" → "Man Utd" (US-278)
        views.render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos,
                              teams=teams, horizon=horizon,
                              this_week=lambda: views.render_this_week(squad_name, squad, horizon=horizon,
                                                                       players=players))

        st.divider()
        st.markdown("##### 👑 Captaincy")
        views.render_captain(squad_name, squad, players, upcoming, history, photos, badges, team_names)

        st.divider()
        # ③ Chips — a click on BOTH paths, and not because it is slow. A chip expires at the end of the
        # half-season, so the question is *which* of your remaining weeks is best; asking it every time
        # someone opens their squad answers a question nobody was holding (ADR-166, upheld).
        st.markdown("##### 🎴 Chips — when to play each")
        if st.button("Work out my chips →", key="ms_chips",
                     help="Looks across every gameweek left before this set of chips expires."):
            st.session_state["ms_chips_on"] = True
        if st.session_state.get("ms_chips_on"):
            views.render_chips(squad_name, squad, upcoming=upcoming)
        else:
            st.caption("A chip is a season decision, so this looks across **every gameweek left before it "
                       "expires** rather than the horizon above — which is why it is a click, not automatic.")
    elif view == "Transfer":
        views.render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos,
                              horizon=horizon)
    elif view == "DNA":
        team_names = {t["short_name"]: t["name"] for t in teams}
        views.render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges,
                            team_names=team_names, horizon=horizon)
    elif view == "Leagues":
        # US-437 (ADR-166) — the owner: *"Leagues is tightly associated with your squad."* It is: every number
        # there measures YOUR picks against other people's, which is this page's subject, not a neighbouring
        # one. It loads its own data (a different API), so it takes nothing from the shared load above.
        from src.web_streamlit.views.leagues import render_leagues
        render_leagues()
    elif view == "Lab":
        # The Lab keeps the header it had as a page (US-360/ADR-105). A tab called "Lab" has to say what it
        # is: folding a page in must not cost it its identity, only its sidebar slot.
        st.subheader("🧪 Squad Lab")
        st.caption("**Build your squad** — the full optimiser. New season, a wildcard, a free hit or a total "
                   "revamp. **Use this squad →** sends it to the other tabs to manage.")
        views.render_build(players, upcoming, history, gw_history, photos, badges, teams=teams,
                           horizon=horizon)
