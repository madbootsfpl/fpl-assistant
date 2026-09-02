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
# ADR-175 — the page caption is gone. It said "squad · captain · transfers · chips · **health**" — a name
# ADR-166 retired six days earlier — and it explained the page to someone already standing on it, beneath a
# title that names it and above tabs that list every item in the sentence. Ten blocks preceded the first
# useful thing; this was the cheapest of them to remove.

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
# ADR-175 — Transfer joins the answer selector under the pitch, so the top nav is four. Its widgets exist
# only when chosen there, which is what dissolves ADR-174's density objection to bringing it in at all.
view = st.segmented_control(
    "Tool", ["My Squad", "DNA", "Leagues", "Lab"], default="My Squad", label_visibility="collapsed",
    key="ms_tool",     # keyed: without one Streamlit identifies it positionally, so a tab that adds widgets
                       # (Leagues adds a dozen) can shift its identity and silently reset the selection.
    help="**My Squad** = your week in one screen — the answer, the pitch and lineup, then who to "
         "(vice-)captain and when to play each chip; **Transfer** the best swaps; **DNA** your squad's "
         "fingerprint and health; **Leagues** how your picks compare with your rivals'; **Lab** build a new "
         "squad from scratch.")

# ADR-175 — the horizon offers what each surface is actually used for, not one range for all of them.
# The owner: *"I don't think this analysis will be done here — yes in the Lab when you're creating your team,
# but not now when active."* US-374 had already half-agreed, defaulting the squad tools to 1 and the Lab to 5
# because a wildcard is a multi-week bet and a Tuesday is not; offering **10** on an active squad offered a
# window nobody chose.
#
# Three modes, three keys, because one control fed five consumers and they do not want the same thing:
#   * the **pitch** — this week, or the short run: GW1 · GW1–3.
#   * the **Lab** — a wildcard is a multi-week bet, so it keeps its long range (US-374, unchanged).
#   * **DNA / Leagues** — occasional analysis, where a five-week read is defensible and was never the
#     complaint. Transfer moved under the pitch (see the selector below) and reads the pitch's window.
# Keyed per mode so each remembers its own setting: merging the surfaces must not merge their horizons.
if view == "Lab":
    _opts, _default, _key, _fmt = [1, 2, 3, 4, 5, 10], 5, "gw_lab", str
elif view == "My Squad":
    _opts, _default, _key, _fmt = [1, 3], 1, "gw_pitch", (lambda n: "GW1" if n == 1 else "GW1–3")
else:
    _opts, _default, _key, _fmt = [1, 2, 3, 4, 5], 1, "gw_analysis", str
horizon = st.segmented_control(
    "Gameweeks ahead", _opts, default=_default, key=_key, format_func=_fmt, label_visibility="collapsed",
    help="How many upcoming gameweeks the projections look over. (Captaincy is always the next gameweek.)"
) or _default

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
        # ADR-175 — value first: the strip and the pitch, then **one** answer at a time.
        #
        # ADR-171 stacked This week · Captaincy · Chips down this page and led with the answer. That was right
        # on the evidence then — its measurement proved the answer *could* render here at all (123 ms, against
        # a supposed 4.4 s) — but the ordering was a judgement laid on top of that finding, and the owner has
        # since lived with it. Ten blocks preceded the first useful thing.
        #
        # A selector is not the tabs ADR-171 removed. Those took you off the page; **this keeps the pitch on
        # screen while you switch**, which is the whole difference, and it is the idiom Players, Trending and
        # Scout already use. Transfer joins it: ADR-174 declined to bring that tab in because ~10 widgets
        # would *stack* onto a 41-block page, and behind a selector they exist only when chosen.
        team_names = {t["short_name"]: t["name"] for t in teams}   # "MUN" → "Man Utd" (US-278)
        views.render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos,
                              teams=teams, horizon=horizon)

        st.divider()
        answer = st.segmented_control(
            "Answer", ["🤖 This week", "👑 Captain", "🔄 Transfer", "🎴 Chips"], default="🤖 This week",
            key="ms_answer", label_visibility="collapsed",
            help="**This week** your whole gameweek in one answer · **Captain** the 15 ranked · **Transfer** "
                 "the best swaps, a coordinated plan, or a manual one · **Chips** when to play each."
        ) or "🤖 This week"

        if answer == "🤖 This week":
            views.render_this_week(squad_name, squad, horizon=horizon, players=players)
        elif answer == "👑 Captain":
            views.render_captain(squad_name, squad, players, upcoming, history, photos, badges, team_names)
        elif answer == "🔄 Transfer":
            views.render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos,
                                  horizon=horizon)
        else:
            # Chips stays a click inside its own panel, and still not for latency: a chip expires at the end
            # of the half-season, so asking every time someone opens the panel answers a question nobody was
            # holding (ADR-166, upheld through two restructures now).
            if st.button("Work out my chips →", key="ms_chips",
                         help="Looks across every gameweek left before this set of chips expires."):
                st.session_state["ms_chips_on"] = True
            if st.session_state.get("ms_chips_on"):
                views.render_chips(squad_name, squad, upcoming=upcoming)
            else:
                st.caption("A chip is a season decision, so this looks across **every gameweek left before "
                           "it expires** rather than the horizon above — which is why it is a click.")
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
