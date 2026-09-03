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
from src.analytics.h2h import catch_up_note, chip_name, h2h_gap, reverts_next_gameweek
from src.analytics.league import (
    captain_split,
    chip_usage,
    effective_ownership,
    flow_rows,
    last_completed_gameweek,
    league_name,
    manager_name,
    my_leagues,
    ownership_gaps,
    standings_rows,
    transfer_activity,
    transfer_flow,
)
from src.api import client as _client
from src.api.client import FplApiError
from src.storage import Storage
from src.web_streamlit import prefs
from src.web_streamlit.badges import photo_url_by_id
from src.web_streamlit.components import render_stat_strip


def render_leagues():
    """The Leagues view, as a **My Squad tab** (ADR-166).

    ⚠️ **The client is reached through the module (`_client.FplClient()`), not imported by name**, and that is
    not style. A *page* is re-imported on every run, so `from … import FplClient` re-bound each time and a
    test could swap it; a *view module* is imported **once**, so the name would keep whatever was installed
    the first time it loaded — in practice, the first test's fake, for the rest of the session. Resolving the
    attribute per call restores the behaviour the page had.

    Was a sidebar page. The owner: *"Leagues is tightly associated with your squad"* — and it is: every number
    here is *your* picks measured against other people's, which is the same subject as every other tab on that
    page rather than a neighbouring one.

    ⚠️ **The nine `st.stop()` calls became `return`s, and that is the whole risk of the move.** `st.stop()`
    halts the *entire script*; as a page that meant "stop drawing Leagues", but inside a tab it would have
    meant "stop drawing My Squad" — every guard clause silently truncating the page it now lives on. They are
    guard clauses, so `return` is the exact equivalent; nothing else about the flow changed.
    """
    st.subheader("🏆 Leagues")
    st.caption("Import a mini-league by its id, or scan the **elite** — then see what it is actually doing: "
               "**effective ownership** against the wider game, the captain split, and which chips were played. "
               "EO is the number that decides whether a pick is a differential or just keeping up.")

    MAX_MANAGERS = 50          # one standings page. A cap that is stated, never silent (ADR-141).


    @st.cache_data(ttl=1800, show_spinner=False)          # 30 min — ranks move; the ADR-093 feed convention
    def _standings(league_id: int):
        return _client.FplClient().get_league_standings(league_id)


    @st.cache_data(ttl=1800, show_spinner=False)
    def _entry(manager_id: int):
        """A manager's public entry — used only for the league list it carries (ADR-141 rev)."""
        return _client.FplClient().get_entry(manager_id)


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
        client, out = _client.FplClient(), {}
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


    @st.cache_data(ttl=900, show_spinner=False)           # 15 min — unlike picks, this list GROWS mid-gameweek
    def _transfers(entries: tuple):
        """Each manager's season transfer list, throttled (ADR-162).

        Deliberately **not** cached forever the way `_picks` is: a completed gameweek's picks are immutable, but a
        manager can transfer at any moment before the next deadline, so this list keeps growing. A short ttl is
        the difference between "cheap" and "wrong".
        """
        client, out = _client.FplClient(), {}
        bar = st.progress(0.0, text=f"Reading {len(entries)} transfer histories…")
        for i, entry in enumerate(entries, start=1):
            try:
                out[entry] = client.get_entry_transfers(entry)
            except FplApiError:
                pass
            bar.progress(i / len(entries), text=f"Reading transfers… {i}/{len(entries)}")
            time.sleep(config.HISTORY_THROTTLE)
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
            return
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
            return
        prefs.remember(manager_id=raw.strip())      # only writes when it actually changed
        try:
            entry = _entry(int(raw.strip()))
        except FplApiError:
            st.error(f"Couldn't find manager #{raw.strip()} — check the id, or try again in a moment.")
            return

        leagues = my_leagues(entry)
        if not leagues:
            st.warning(f"**{manager_name(entry) or 'That manager'}** isn't in any classic leagues yet.")
            return
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
        return

    rows = standings_rows(payload)
    if not rows:
        st.warning(f"League #{league_id} has no standings yet — classic leagues fill in after the first deadline.")
        return

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
        return

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
        return

    picks = _picks(tuple(r["entry"] for r in shown), last_gw)
    if not picks:
        st.error("Couldn't read any squads for this league — FPL may be busy. Try again in a moment.")
        return
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

    # ---- Transfer flow (ADR-162) ----------------------------------------------------------
    # Two halves, split by what they cost. The activity numbers ride on the picks payloads already fetched —
    # FPL puts `entry_history` on every one of them — so they are free and always shown. WHICH players moved is
    # one more call per manager, so it asks first, exactly as the squads above did.
    st.divider()
    st.markdown(f"##### 🔄 Transfer flow — GW{last_gw}")
    _activity = transfer_activity(picks)
    # ADR-163 — the shared strip: four across on a laptop, reflowing rather than slivering on a phone.
    render_stat_strip([
        {"label": "Moved", "sub": f"of {_activity['managers']}", "value": _activity["movers"],
         "help": "Managers who made at least one transfer."},
        {"label": "Transfers", "value": _activity["transfers"]},
        {"label": "Hits", "tone": "down" if _activity["hit_points"] else "mute",
         "value": f"−{_activity['hit_points']}" if _activity["hit_points"] else "0",
         "sub": f"{_activity['hits']} manager(s)",
         "help": "Points spent taking transfers beyond the free one."},
        {"label": "Bench pts", "value": _activity["bench_points"],
         "help": "Points their benched players scored — the cost of getting the XI wrong."},
    ])

    if _activity["transfers"] == 0:
        st.caption(f"**Nobody transferred in GW{last_gw}** — which is expected in the first gameweek of a season, "
                   "when everyone's squad is still their opening pick. This fills in from GW2.")
    else:
        st.caption(f"Average bank across the league: £{_activity['bank']:.1f}m. "
                   if _activity["bank"] is not None else "")
        if st.button(f"Read {len(picks)} transfer histories →", key="lg_flow"):
            st.session_state["lg_flow_for"] = (league_id, last_gw)
        if st.session_state.get("lg_flow_for") == (league_id, last_gw):
            _flow = transfer_flow(_transfers(tuple(picks)), last_gw)
            _rows = flow_rows(_flow, players)
            if not _rows:
                st.info("No transfers landed in this gameweek for the managers we could read.")
            else:
                st.dataframe(
                    [{"photo": photos.get(r["id"], ""), "Player": r["player"], "Team": r["team"],
                      "Pos": r["position"], "In": r["in"], "Out": r["out"], "Net": r["net"]} for r in _rows],
                    hide_index=True, width="stretch",
                    column_config={"photo": st.column_config.ImageColumn("", width="small"),
                                   "Net": st.column_config.NumberColumn("Net", format="%+d",
                                                                        help="In minus out across the league.")})
                st.caption("Sorted by the **size** of the net move, in either direction. A player with a big "
                           "**In** *and* a big **Out** is churning, not popular — the net says which, and one "
                           "table shows it where two top-tens would have listed him twice and explained neither.")
        else:
            st.caption(f"Which players moved needs one more call per manager "
                       f"(~{len(picks) * (config.HISTORY_THROTTLE + 0.05):.0f}s). The numbers above are free — "
                       "they come from the squads already read.")

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
        _rival_short = _rival_label.split(" · ")[0][:14]

        def _forward_squad(payload, entry, who):
            """The squad they will actually own next gameweek, and a line saying so (ADR-177).

            Bench Boost and Triple Captain change how the *same* fifteen were scored, so the projection
            simply drops the chip and nothing needs fetching. **Free Hit is the exception**: that squad is
            discarded at the deadline and the previous one returns, so the honest read is the gameweek before
            — one extra call, only in the week it applies.
            """
            _chip = (payload or {}).get("active_chip")
            if reverts_next_gameweek(payload):
                _prior = _picks((entry,), last_gw - 1).get(entry) if last_gw > 1 else None
                if _prior:
                    return _prior, (f"{who} played **Free Hit** in GW{last_gw}. That squad is discarded at "
                                    f"the deadline, so this reads the **GW{last_gw - 1}** squad it reverts to.")
                return None, (f"{who} played **Free Hit** in GW{last_gw}. That squad is discarded at the "
                              "deadline and FPL does not publish the one it reverts to — so this comparison "
                              "cannot honestly be made. Try another rival.")
            if _chip:
                return payload, (f"{who} played **{chip_name(_chip)}** in GW{last_gw} — that is spent, so "
                                 "this projects the eleven, not the chipped side.")
            return payload, None

        # My own picks may sit outside the standings page we read, so fetch them if they aren't already in hand.
        _mine = picks.get(_my_entry) or _picks((_my_entry,), last_gw).get(_my_entry)
        _theirs = picks.get(_rival)
        if not _mine:
            st.warning(f"Couldn't read your own squad (manager #{_my_entry}) for GW{last_gw}.")
        elif not _theirs:
            st.warning("Couldn't read that rival's squad — try another, or reload.")
        else:
            # ADR-177: what each side will actually OWN next gameweek, which is not always what they fielded.
            _mine, _my_note = _forward_squad(_mine, _my_entry, "You")
            _theirs, _their_note = _forward_squad(_theirs, _rival, _rival_short)
            _chip_notes = [n for n in (_my_note, _their_note) if n]

            # The season standing, before the projection — the two were read as one number by the owner, and
            # the card is the half that does not say which it is (ADR-177).
            _totals = {r["entry"]: r["total"] for r in shown}
            _my_total, _their_total = _totals.get(_my_entry), _totals.get(_rival)
            if _my_total is not None and _their_total is not None:
                _season = _my_total - _their_total
                _lead = (f"you are **{_season} points ahead**" if _season > 0 else
                         f"**{_rival_short} is {-_season} points ahead**" if _season < 0 else
                         "**you are level**")
                # Both totals are labelled by name. "(165 v 188)" after "Micka is 23 points ahead" reads as
                # though the 165 is theirs — the sentence's subject and the bracket's order disagreed.
                st.caption(f"On the season so far, {_lead} — you **{_my_total}**, "
                           f"{_rival_short} **{_their_total}**. "
                           f"Everything below is **GW{last_gw + 1} only** — a projection, not the table.")

            for _note in _chip_notes:
                st.caption(_note)

            if _mine and _theirs:                     # a declined Free Hit has already said why above
                _st2 = Storage()
                try:
                    _ranked = decision_xp(players, _st2.get_upcoming_fixtures(), _st2.get_history_by_code(),
                                          horizon=1, gw_history_by_code=_st2.get_gw_history_by_code())
                finally:
                    _st2.close()
                _xp = {r["id"]: r["xp"] for r in _ranked}
                _gap = h2h_gap(_mine, _theirs, _xp, players)

                render_stat_strip([
                    {"label": "You", "value": f"{_gap['mine']['xp']:.1f}"},
                    {"label": _rival_short, "value": f"{_gap['theirs']['xp']:.1f}"},
                    {"label": "Gap", "value": f"{_gap['gap']:+.1f}",
                     "tone": "up" if _gap["gap"] >= 0 else "down",
                     "help": "Positive means you are ahead on projection."},
                ])
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

                st.caption(f"⚠️ These are **GW{last_gw} squads** — FPL only publishes picks after a deadline, "
                           f"so this reads the team they had and projects GW{last_gw + 1}. They can still "
                           "transfer and change their captain. A chip played in "
                           f"GW{last_gw} is **not** projected forward: it is spent, so the eleven is derived "
                           "from the bench order, not from how last week was scored. xP is the same "
                           "projection every other page decides with; it is an average, **not a win "
                           "probability** — a 2-point projected lead is not a 2-point certainty.")
