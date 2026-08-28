"""Leagues — import a league, then compare your picks against what it is actually doing (ADR-141).

**The number this page exists for is effective ownership.** Across the top 20 managers in the world in GW1,
Palmer sat at 90% EO while his *global* ownership was 11.9%. Every other surface here reads that 11.9% and
calls him a differential; among the people winning, he was template. Those are opposite decisions and no
other page can tell them apart.

**Two layers, priced apart, and the split is the design.** The league table is ONE call (standings already
carry `rank`, `last_rank`, `total` and `event_total`, so "who is climbing" is free). The insight layer costs
one call *per manager* — so it never happens on page load, only on an explicit button. Nothing that costs N
network calls should happen because someone opened a tab.

**Why it is affordable at all: a completed gameweek's picks are immutable.** Once the deadline has passed
those picks can never change, so they are cached with no expiry; only the in-flight gameweek gets a TTL.
"""

import time

import streamlit as st

from src import config
from src.analytics import decision_xp
from src.analytics.h2h import catch_up_note, h2h_gap
from src.analytics.league import (
    captain_split,
    chip_usage,
    effective_ownership,
    last_completed_gameweek,
    league_name,
    manager_name,
    my_leagues,
    ownership_gaps,
    standings_rows,
)
from src.api.client import FplApiError, FplClient
from src.storage import Storage
from src.web_streamlit import analytics, brand, prefs
from src.web_streamlit.access import require_access
from src.web_streamlit.badges import photo_url_by_id
from src.web_streamlit.status import render_data_status

st.set_page_config(**brand.page_config("Leagues"))
require_access()
analytics.boot("Leagues")
render_data_status()
st.title("🏆 Leagues")
st.markdown(brand.mark_html(badge_px=15, font_px=11), unsafe_allow_html=True)
st.caption("Import a mini-league by its id, or scan the **elite** — then see what it is actually doing: "
           "**effective ownership** against the wider game, the captain split, and which chips were played. "
           "EO is the number that decides whether a pick is a differential or just keeping up.")

MAX_MANAGERS = 50          # one standings page. A cap that is stated, never silent (ADR-141).


@st.cache_data(ttl=1800, show_spinner=False)          # 30 min — ranks move; the ADR-093 feed convention
def _standings(league_id: int):
    return FplClient().get_league_standings(league_id)


@st.cache_data(ttl=1800, show_spinner=False)
def _entry(manager_id: int):
    """A manager's public entry — used only for the league list it carries (ADR-141 rev)."""
    return FplClient().get_entry(manager_id)


@st.cache_data(show_spinner=False)                    # NO ttl — see below
def _picks(entries: tuple, gameweek: int):
    """Fetch each manager's picks, throttled. Cached **forever** for a completed gameweek.

    That is the whole economics of this page: once a deadline has passed, those picks are immutable, so a
    re-visit is free and a season of gameweeks accumulates without refetching one. The caller only calls this
    for a finished gameweek; the in-flight one is not offered.

    A manager whose fetch fails is simply absent from the result. A partial league still gives a usable EO,
    and the caller says how many it is standing on — an exception here would throw away 49 good fetches
    because of one bad id.
    """
    client, out = FplClient(), {}
    bar = st.progress(0.0, text=f"Reading {len(entries)} squads…")
    for i, entry in enumerate(entries, start=1):
        try:
            out[entry] = client.get_entry_picks(entry, gameweek)
        except FplApiError:
            pass
        bar.progress(i / len(entries), text=f"Reading {len(entries)} squads… {i}/{len(entries)}")
        time.sleep(config.HISTORY_THROTTLE)           # the same courtesy the history backfill pays (ADR-027)
    bar.empty()
    return out


# ADR-141 rev — **the manager id is the handle people actually have.** The first cut asked for a league id,
# which appears only in a URL you have to go and find: the owner opened the page with their own manager id to
# hand and could not get in. `/entry/{id}/` already lists every league behind that id, so this costs one call
# the app was making anyway. "By league id" stays for anyone who does have one.
scope = st.segmented_control(
    "Find a league", ["My leagues", "By league id", "Elite"], default="My leagues", key="lg_scope",
    help="Your leagues, looked up from your FPL manager id · a league id directly · or the global Overall "
         "league, whose first page is the top 50 in the world.")

league_id = None
if scope == "Elite":
    league_id = config.ELITE_LEAGUE_ID
elif scope == "By league id":
    raw = st.text_input("League id", key="lg_id",
                        help="The number in a classic league's FPL URL. H2H leagues aren't supported.")
    if not raw.strip().isdigit():
        st.info("Enter a classic league id — or switch to **My leagues** and use your manager id instead.")
        st.stop()
    league_id = int(raw.strip())
else:
    # ADR-147 — remembered across sessions **and devices**, because a manager id you have to re-type every
    # visit undercuts the feature it belongs to. Three sources, best first: what you stored (per-user, follows
    # you anywhere), then the Manager-ID import on My Squad (ADR-113) if it was used this session, then empty.
    _remembered = prefs.recall()
    prefill = str(_remembered.get("manager_id") or st.session_state.get("manager_id") or "").strip()
    raw = st.text_input("Your FPL manager id", value=prefill, key="lg_manager", placeholder="e.g. 1234567",
                        help="The number in your FPL team URL. The same id the My Squad import uses.")
    if not raw.strip().isdigit():
        st.info("Enter your **manager id** and every league you're in appears below — no league ids needed. "
                "It's the number in your FPL team URL, the same one the My Squad import takes.")
        st.stop()
    prefs.remember(manager_id=raw.strip())      # only writes when it actually changed
    try:
        entry = _entry(int(raw.strip()))
    except FplApiError:
        st.error(f"Couldn't find manager #{raw.strip()} — check the id, or try again in a moment.")
        st.stop()

    leagues = my_leagues(entry)
    if not leagues:
        st.warning(f"**{manager_name(entry) or 'That manager'}** isn't in any classic leagues yet.")
        st.stop()
    labels = {f"{'👥' if lg['private'] else '🌍'} {lg['name']}  ·  {lg['size']:,} managers": lg["id"]
              for lg in leagues}
    st.caption(f"**{manager_name(entry)}** — 👥 your own leagues first, then 🌍 the ones FPL puts everyone in "
               "(your club, region, Overall).")
    # Open on the league you looked at last, if it is still one of yours.
    _last = _remembered.get("league_id")
    _names = list(labels)
    _index = next((i for i, lbl in enumerate(_names) if str(labels[lbl]) == str(_last)), 0)
    league_id = labels[st.selectbox("Your leagues", _names, index=_index, key="lg_pick")]
    prefs.remember(league_id=league_id)

try:
    payload = _standings(league_id)
except FplApiError:
    st.error(f"Couldn't reach FPL for league #{league_id} — check the id, or try again in a moment.")
    st.stop()

rows = standings_rows(payload)
if not rows:
    st.warning(f"League #{league_id} has no standings yet — classic leagues fill in after the first deadline.")
    st.stop()

st.subheader(league_name(payload) or f"League #{league_id}")
has_next = bool((payload.get("standings") or {}).get("has_next"))
shown = rows[:MAX_MANAGERS]
st.caption(f"**{len(shown)}** managers"
           + (f" — the top {MAX_MANAGERS} of a larger league (this page reads one standings page)."
              if has_next else ".")
           + " ▲ / ▼ is movement since last gameweek.")

st.dataframe(
    [{"#": r["rank"], "Team": r["team"], "Manager": r["manager"],
      "Move": ("—" if r["movement"] is None else
               f"▲ {r['movement']}" if r["movement"] > 0 else
               f"▼ {abs(r['movement'])}" if r["movement"] < 0 else "="),
      "GW": r["gw_points"], "Total": r["total"]} for r in shown],
    hide_index=True, width="stretch", height=min(420, 38 * len(shown) + 40))

# ---- the insight layer: N calls, so it never runs on page load ------------------------
store = Storage()
players = store.get_players()
last_gw = last_completed_gameweek(store.get_upcoming_fixtures())
store.close()

st.divider()
if last_gw is None:
    st.info("No completed gameweek yet — effective ownership needs everyone's finished picks.")
    st.stop()

st.markdown(f"#### What this league is doing — GW{last_gw}")
st.caption(f"Reads one squad per manager ({len(shown)} calls, throttled — about "
           f"{len(shown) * (config.HISTORY_THROTTLE + 0.05):.0f}s the first time). A finished gameweek's "
           "picks never change, so it's cached and instant afterwards.")

# The button LATCHES, per league (US-431). `st.button` is True only on the run it was clicked, so before this
# any widget below it — the head-to-head rival picker — re-ran the page, found False, and collapsed the whole
# section back to the button. Latching on the league id rather than a bare flag matters: switching leagues must
# ask again, because loading is N network calls and nobody should spend them by changing a dropdown.
if st.button(f"Read {len(shown)} squads →", key="lg_load"):
    st.session_state["lg_loaded_for"] = league_id
if st.session_state.get("lg_loaded_for") != league_id:
    st.stop()

picks = _picks(tuple(r["entry"] for r in shown), last_gw)
if not picks:
    st.error("Couldn't read any squads for this league — FPL may be busy. Try again in a moment.")
    st.stop()
if len(picks) < len(shown):
    st.warning(f"Read **{len(picks)} of {len(shown)}** squads — the rest didn't respond. The numbers below "
               "are over the ones that did.")

photos = photo_url_by_id(players)
by_id = {p["id"]: p for p in players}
eo = effective_ownership(picks)

st.markdown("##### Effective ownership vs the wider game")
st.caption("EO counts a captain twice, because that is what it costs you. A **positive gap** means this "
           "league is *more* exposed than everyone else — owning that player is keeping up, not getting "
           "ahead. A **negative gap** is where a differential actually is.")
st.dataframe(
    [{"photo": photos.get(g["id"], ""), "Player": g["player"]["web_name"], "Team": g["player"]["team"],
      "Pos": g["player"]["position"], "EO in league": g["eo"], "Global own%": g["global"], "Gap": g["gap"]}
     for g in ownership_gaps(eo, players)],
    hide_index=True, width="stretch",
    column_config={"photo": st.column_config.ImageColumn("", width="small"),
                   "EO in league": st.column_config.NumberColumn("EO in league", format="%.0f%%"),
                   "Global own%": st.column_config.NumberColumn("Global own%", format="%.1f%%"),
                   "Gap": st.column_config.NumberColumn("Gap", format="%+.0f",
                                                        help="EO in this league minus global ownership.")})

c3, c4 = st.columns(2)
with c3:
    st.markdown("##### Captain split")
    caps = [(by_id[i]["web_name"], n) for i, n in captain_split(picks) if i in by_id]
    if caps:
        st.dataframe([{"Player": w, "Captains": n, "Share": round(n / len(picks) * 100)} for w, n in caps],
                     hide_index=True, width="stretch",
                     column_config={"Share": st.column_config.NumberColumn("Share", format="%d%%")})
        st.caption("A 6 / 5 / 4 spread is a completely different week from 18 / 1 / 1 — the shape is the point.")
with c4:
    st.markdown("##### Chips played")
    st.dataframe([{"Chip": c, "Managers": n} for c, n in chip_usage(picks)],
                 hide_index=True, width="stretch")
    st.caption("`none` = no chip that week. A consensus here is worth noticing.")

# ---- Head-to-head: what would it take to catch one rival (ADR-161) --------------------
# The league view answers "what is everyone doing"; this answers "what do I need to do about HIM". They are
# different questions and the second one needs per-manager projections, not per-player ones.
st.divider()
st.markdown("##### ⚔️ Head to head")

_my_entry = None
_remembered_id = str(prefs.recall().get("manager_id") or st.session_state.get("manager_id") or "").strip()
if _remembered_id.isdigit():
    _my_entry = int(_remembered_id)

_rivals = {f"{r['team']} · {r['manager']}": r["entry"] for r in shown if r["entry"] != _my_entry}
if _my_entry is None:
    st.info("Switch to **My leagues** above (or import your manager id on My Squad) and this compares your "
            "squad with any rival's.")
elif not _rivals:
    st.caption("No one else in this league to compare against yet.")
else:
    _rival_label = st.selectbox("Compare against", list(_rivals), key="lg_h2h")
    _rival = _rivals[_rival_label]
    # My own picks may sit outside the standings page we read, so fetch them if they aren't already in hand.
    _mine = picks.get(_my_entry) or _picks((_my_entry,), last_gw).get(_my_entry)
    _theirs = picks.get(_rival)
    if not _mine:
        st.warning(f"Couldn't read your own squad (manager #{_my_entry}) for GW{last_gw}.")
    elif not _theirs:
        st.warning("Couldn't read that rival's squad — try another, or reload.")
    else:
        _st2 = Storage()
        try:
            _ranked = decision_xp(players, _st2.get_upcoming_fixtures(), _st2.get_history_by_code(),
                                  horizon=1, gw_history_by_code=_st2.get_gw_history_by_code())
        finally:
            _st2.close()
        _xp = {r["id"]: r["xp"] for r in _ranked}
        _gap = h2h_gap(_mine, _theirs, _xp, players)

        m1, m2, m3 = st.columns(3)
        m1.metric("You project", f"{_gap['mine']['xp']:.1f}")
        m2.metric(_rival_label.split(" · ")[0][:18], f"{_gap['theirs']['xp']:.1f}")
        m3.metric("Gap", f"{_gap['gap']:+.1f}", help="Positive means you are ahead on projection.")
        st.caption(catch_up_note(_gap, my_name="you", their_name="they"))

        d1, d2 = st.columns(2)
        for _col, _rows, _title, _why in (
                (d1, _gap["their_edge"], "What they have that you don't",
                 "Catching them runs through these."),
                (d2, _gap["my_edge"], "What you have that they don't",
                 "This is your lead, such as it is.")):
            with _col:
                st.markdown(f"**{_title}**")
                if not _rows:
                    st.caption("Nothing — identical on this side.")
                    continue
                st.dataframe(
                    [{"photo": photos.get(r["id"], ""), "Player": r["web_name"], "Team": r["team"],
                      "Pos": r["position"], "xP": r["xp"],
                      "": "©" if r["multiplier"] > 1 else ""} for r in _rows],
                    hide_index=True, width="stretch",
                    column_config={"photo": st.column_config.ImageColumn("", width="small"),
                                   "xP": st.column_config.NumberColumn("xP", format="%.1f"),
                                   "": st.column_config.TextColumn("", width="small",
                                                                   help="A captain's extra copy.")})
                st.caption(_why)

        st.caption(f"⚠️ These are **GW{last_gw} squads** — FPL only publishes picks after a deadline, so this "
                   "projects the team they had, not the one they will field. They can still transfer and "
                   "change their captain. xP is the same projection every other page decides with; it is an "
                   "average, "
                   "**not a win probability** — a 2-point projected lead is not a 2-point certainty.")
