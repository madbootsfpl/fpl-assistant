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
from src.analytics.league import (
    captain_split,
    chip_usage,
    effective_ownership,
    last_completed_gameweek,
    league_name,
    ownership_gaps,
    standings_rows,
)
from src.api.client import FplApiError, FplClient
from src.storage import Storage
from src.web_streamlit import analytics, brand
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


c1, c2 = st.columns([2, 1], vertical_alignment="bottom")
scope = c2.segmented_control("Scan", ["My league", "Elite"], default="Elite", key="lg_scope",
                             help="Elite = the global Overall league, whose first page is the top 50 in the "
                                  "world. It is the same code, pointed at a different id.")
default_id = str(config.ELITE_LEAGUE_ID) if scope == "Elite" else ""
raw = c1.text_input("League id", value=default_id, key="lg_id",
                    help="A classic league's id — the number in its FPL URL. H2H leagues aren't supported.")

if not raw.strip().isdigit():
    st.info("Enter a classic league id to load its table. (Elite fills in the global Overall league for you.)")
    st.stop()

league_id = int(raw.strip())
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

if not st.button(f"Read {len(shown)} squads →", key="lg_load"):
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
