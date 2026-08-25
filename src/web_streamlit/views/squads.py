"""Squad views (ADR-069): Build · My Squad · Health · Transfer · Captain, rendered from shared data.

Extracted from the old separate pages — **same behaviour, same engine, same output**. The consolidated
Squads page loads data + the shared squad picker once and calls only the selected view (lazy). All reuse
the CLI analytics/renderers; every edit mutates `st.session_state` only (no server writes).
"""

import datetime
import json

import streamlit as st

from src import ask
from src.analytics import (
    SET_PIECE_LEGEND,
    SQUAD_15,
    WEEKLY_BENCH_WEIGHT,
    analyse_squad,
    archetype_bands,
    availability_flag,
    available_players,
    baseline_rate,
    bench_order,
    best_legal_xi,
    captain_picks,
    crowd_flags,
    decision_xp,
    explain_captain,
    explain_squad,
    is_unavailable,
    legal_xi_issues,
    minutes_weight_from_history,
    objective_scores,
    price_prediction,
    select_squad,
    set_piece_flags,
    squad_15_issues,
    suggest_transfer_plan,
    suggest_transfers,
    team_schedule,
)
from src.ui.analyse import render_squad_analysis
from src.ui.ask import render_ask
from src.ui.explain import MODEL_NOTE, render_explanation
from src.ui.squad import render_squad
from src.ui.transfer import render_transfer_plan, render_transfers
from src.web_streamlit import analytics
from src.web_streamlit.badges import shirt_url_by_id
from src.web_streamlit.captain_card import render_captain_card
from src.web_streamlit.pitch import render_pitch
from src.web_streamlit.squads import (
    FPL_BUDGET,
    active_squad,
    apply_transfer,
    apply_transfer_plan,
    captain_bonus,
    move_bench_sub,
    rename,
    render_your_team,
    set_active_squad,
    set_bench,
    set_captain,
    substitute,
    team_banner_html,
)
from src.web_streamlit.tables import render_player_table

_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
_BENCH_MAX = 4
_FORMATIONS = {"3-4-3": (3, 4, 3), "3-5-2": (3, 5, 2), "4-4-2": (4, 4, 2),
               "4-3-3": (4, 3, 3), "4-5-1": (4, 5, 1), "5-4-1": (5, 4, 1), "5-3-2": (5, 3, 2)}


def _formation_xi_scores(pool, budget, include, exclude, scores, display_xp):
    """Best-XI projected xP for each legal shape (display-only; ADR-075). Illegal shapes → None.

    One ILP solve per formation — the caller gates this behind a checkbox so it runs only on request."""
    out = []
    for shape, (d, m, f) in _FORMATIONS.items():
        r = select_squad(pool, budget=budget, formation={"GK": 1, "DEF": d, "MID": m, "FWD": f},
                         size=11, include_ids=include, exclude_ids=exclude, scores=scores)
        tot = sum(display_xp.get(p["id"], 0) for p in r["selected"]) if r["status"] == "Optimal" else None
        out.append((shape, tot))
    return out


# ---- Build (the full CLI `squad` options → a saveable 15; ADR-062) ---------------------------------

def render_build(players, upcoming, history, gw_history, photos, badges, *, teams=None, horizon=5):
    by_label = {f"{p['web_name']} · {p['team']} · £{p['price']:.1f}m": p["id"]
                for p in sorted(players, key=lambda p: (p["web_name"] or "").lower())}
    labels = list(by_label)

    def _ids(chosen):
        return [by_label[la] for la in chosen]

    c1, c2, c3 = st.columns(3)
    budget = c1.slider("Budget (£m)", 80.0, 100.0, 100.0, step=0.5,
                       help="The most you'll spend across all 15 players.")
    name = c1.text_input("Squad name", value="My squad", max_chars=40,
                         help="A name for this squad — used in the download and as the active-squad "
                              "label.").strip() or "My squad"
    objective = c2.selectbox("Objective", ["xp", "points", "value", "xgi"],
                             help="xp = expected points (xMins-weighted); the CLI default.")
    no_xmins = c2.checkbox("Ignore expected minutes (--no-xmins)", value=False,
                           disabled=objective != "xp", help="xp objective only.")
    # ADR-137 — TWO modes, not three, and named for what they build. "Bench Boost" used to sit here as a third
    # option and produced the *same fifteen* as "Balanced": maximising `Σ score·start + 1·score·bench` is
    # maximising `Σ score` over the 15, so it could never have been a distinct build however it was wired.
    # The old labels were also backwards — "Balanced" was the max-15 (strong-bench) build.
    mode = c3.radio("Build mode", ["All-round (strong bench)", "Strong XI (cheap bench)"],
                    help="All-round maximises all 15 — a bench that can actually play. Strong XI moves that "
                         "money into the starting XI and buys a deliberately cheap bench for cover.")
    c3.caption("Playing **Bench Boost**? Use **All-round** — under the chip all 15 score, so "
               "\"maximise the XI\" and \"maximise all 15\" become the same question." if mode.startswith("All-round")
               else "Playing **Bench Boost** this week? Switch to **All-round** — under the chip all 15 score.")
    include_unavailable = c3.checkbox("Include injured/suspended", value=False,
                                      help="Also consider flagged players (off by default).")

    a1, a2, a3 = st.columns(3)
    cheap = a1.number_input("Low-cost (≤£4.5m)", min_value=0, max_value=8, value=0,
                            help="Require at least this many budget (≤£4.5m) players.")
    premium = a2.number_input("Premium (≥£9m)", min_value=0, max_value=5, value=0,
                              help="Require at least this many premium (≥£9m) players.")
    differential = a3.number_input("Differentials (≤5% owned)", min_value=0, max_value=5, value=0,
                                   help="Require at least this many low-owned (≤5%) picks.")

    include = _ids(st.multiselect("Must include", labels, help="Force these players into the squad."))
    exclude = _ids(st.multiselect("Must exclude", labels, help="Never pick these players."))
    declared_bench = _ids(st.multiselect("Declare bench (up to 4)", labels,
                                         help="Pins these to the bench; leave empty to auto-derive the XI."))

    weekly = mode == "Strong XI (cheap bench)"
    warnings = []
    if set(include) & set(exclude):
        warnings.append("A player can't be both included and excluded.")
    if len(declared_bench) > _BENCH_MAX:
        warnings.append(f"You can declare at most {_BENCH_MAX} bench players.")
    if set(declared_bench) & set(include):
        warnings.append("A player can't be both included and benched.")
    if declared_bench and weekly:
        warnings.append("Strong XI designates the bench itself — clear the declared bench.")
    for w in warnings:
        st.warning(w)

    if objective == "xp":
        ranked = decision_xp(players, upcoming, history, horizon=horizon, minutes_weighted=not no_xmins,
                             gw_history_by_code=gw_history)
        scores = {r["id"]: r["xp"] for r in ranked}
    else:
        scores = objective_scores(players, objective)
        ranked = decision_xp(players, upcoming, history, horizon=horizon,
                             gw_history_by_code=gw_history)   # xP for display
    display_xp = {r["id"]: r["xp"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}

    forced = set(include) | set(declared_bench)
    pool = players if include_unavailable else available_players(players, keep_ids=forced)[0]
    bands = archetype_bands(cheap=cheap or None, premium=premium or None)
    with analytics.timed("analysis", page="Squads"):     # perf: the squad-optimiser calculation (US-336)
        result = select_squad(
            pool, budget=budget, formation=SQUAD_15, size=15,
            include_ids=include, exclude_ids=exclude, bench_ids=declared_bench,
            scores=scores, band_minimums=bands, min_differentials=differential or None,
            bench_weight=WEEKLY_BENCH_WEIGHT if weekly else None,
        )

    if result["status"] != "Optimal":
        st.error(f"No squad fits those options within £{budget:.1f}m — relax the constraints "
                 "(archetypes / include / budget) and try again.")
        return

    selected = result["selected"]
    _flag_unavailable(selected)                      # ⛔ US-421: a forced-in player who can't play (Must include)
    if declared_bench:
        xi_ids = [p["id"] for p in selected if not p.get("bench")]
    else:
        xi_ids = best_legal_xi(selected, scores)
    xi = set(xi_ids)
    for p in selected:
        p["xp"] = display_xp.get(p["id"], 0)
        p["minutes_weight"] = weight_by_id.get(p["id"], 1.0)

    if objective != "xp":
        st.caption(f"Optimised on **{objective}**; the xP column is the forward reference metric "
                   "(xMins-weighted).")

    # Explainability (ADR-089/US-271): why this build — Confidence · Why · Risk, above the pitch, closed by
    # the shared Model note (US-278).
    st.code(render_explanation(explain_squad(selected, display_xp, weight_by_id, budget=budget,
                                             xi_ids=xi, horizon=horizon)) + "\n\n" + MODEL_NOTE, language=None)

    # The optimal 15 on the green pitch (US-261, reuses ADR-084) — the XI in formation + the bench in the
    # recommended sub order; no captain on a fresh build. The sortable table + summary sit below.
    xi_players = [p for p in selected if p["id"] in xi]
    bench_players = [p for p in selected if p["id"] not in xi]
    bench_roles = {p["id"]: role for role, p in bench_order(bench_players, display_xp)}
    next_opp = {t: (team_schedule(upcoming, t) or [None])[0] for t in {p["team"] for p in selected}}
    kits = shirt_url_by_id(selected, teams)     # the pitch shows the live club kit (ADR-084 rev), not the mugshot
    render_pitch(xi_players, bench_players, captain_id=None, xp_by_id=display_xp, photos=photos,
                 next_opp=next_opp, bench_roles=bench_roles, kits=kits)

    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
        "£m": p["price"], "xP": round(p.get("xp", 0), 1),
        "Role": "XI" if p["id"] in xi else "Bench", "Trends": " ".join(crowd_flags(p)),
        "Set": " ".join(set_piece_flags(p)),
    } for p in sorted(selected, key=lambda x: (x["id"] not in xi, _ORDER.get(x["position"], 9)))],
        help={"Set": SET_PIECE_LEGEND})
    st.code(render_squad(result, budget=budget, objective=objective, full=True,
                         xi_ids=xi_ids), language=None)

    # Start the bench in the recommended (xP) sub order (ADR-078/079) — outfield by xP, then the GK;
    # still user-reorderable in My Squad.
    bench_players = [p for p in selected if p["id"] not in xi]
    squad = {
        "player_ids": [p["id"] for p in selected],
        "player_names": [p["web_name"] for p in selected],
        "bench_ids": [pl["id"] for _role, pl in bench_order(bench_players, display_xp)],
        "cost": result["total_cost"],
        "saved_at": datetime.date.today().isoformat(),
    }
    payload = json.dumps({name: squad}, indent=2)
    dl, use = st.columns(2)
    dl.download_button("⬇︎ Download squad.json", payload, file_name="squad.json",
                       mime="application/json", use_container_width=True)
    if use.button("Use this squad →", use_container_width=True):
        set_active_squad({**squad, "name": name})
        analytics.track("squad_created", mode=mode)   # a deliberate build → active (no squad contents; just the mode)
        st.success(f"Set **{name}** as your active squad — switch to My Squad to tweak it.")

    with st.expander("🔎 Preview the best XI in a given shape (display only — not saved)"):
        shape = st.selectbox("Formation", list(_FORMATIONS), index=0,
                             help="Preview the best XI in this shape (display only — the saved build is a 15).")
        d, m, f = _FORMATIONS[shape]
        xi_pool = players if include_unavailable else available_players(players, keep_ids=set(include))[0]
        xi_result = select_squad(xi_pool, budget=budget, formation={"GK": 1, "DEF": d, "MID": m, "FWD": f},
                                 size=11, include_ids=include, exclude_ids=exclude, scores=scores)
        if xi_result["status"] != "Optimal":
            st.info(f"No legal {shape} XI within £{budget:.1f}m for those options.")
        else:
            for p in xi_result["selected"]:
                p["xp"] = display_xp.get(p["id"], 0)
                p["minutes_weight"] = weight_by_id.get(p["id"], 1.0)
            xi_xp = sum(display_xp.get(p["id"], 0) for p in xi_result["selected"])
            st.metric(f"Projected XI — {shape}", f"{xi_xp:.1f} xP",
                      help="Total projected xP of this shape's best XI. Switch the formation (or tick "
                           "'Compare all formations') to see the effect of a different shape.")
            render_player_table([{
                "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
                "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
                "£m": p["price"], "xP": round(p.get("xp", 0), 1), "Trends": " ".join(crowd_flags(p)),
                "Set": " ".join(set_piece_flags(p)),
            } for p in sorted(xi_result["selected"], key=lambda x: _ORDER.get(x["position"], 9))],
                help={"Set": SET_PIECE_LEGEND})
            st.caption(f"Best **{shape}** XI (display only) — the saveable build above is always a full 15.")

        # Compare all shapes at a glance (ADR-075) — gated: the 7 extra ILP solves run only on tick,
        # since a Streamlit expander body executes even when collapsed.
        if st.checkbox("Compare all formations", value=False,
                       help="Solve the best XI for every legal shape and rank them by projected xP "
                            "(runs only when ticked)."):
            scored = _formation_xi_scores(xi_pool, budget, include, exclude, scores, display_xp)
            best = max((t for _, t in scored if t is not None), default=None)
            scored.sort(key=lambda s: (s[1] is None, -(s[1] or 0)))    # legal by xP desc, illegal last
            st.dataframe(
                [{"Formation": shp,
                  "XI xP": round(t, 1) if t is not None else None,
                  "Δ vs best": round(t - best, 1) if (t is not None and best is not None) else None}
                 for shp, t in scored],
                hide_index=True, width="stretch",
                column_config={"XI xP": st.column_config.NumberColumn("XI xP", format="%.1f"),
                               "Δ vs best": st.column_config.NumberColumn("Δ vs best", format="%+.1f")})
            st.caption("Best XI's projected xP by shape — the same pool arranged in each legal formation "
                       "(a blank = no legal XI within your budget/options).")


# ---- My Squad (view & edit the active squad; ADR-055) ----------------------------------------------

def _flag_unavailable(members) -> None:
    """⛔ Warn if a squad contains players who can't play — injured / suspended / left the club (US-421). FPL hides
    these (status not 'a') from its picker, but MadBoots ingests the full pool, so one can slip into a squad via
    Squad Lab's **Must include**, a Manager-ID import, or an old save. Display-only; catches every entry path."""
    gone = [p for p in members if is_unavailable(p)]
    if not gone:
        return
    names = ", ".join(f"**{p['web_name']}**" for p in gone)
    st.warning(f"⛔ **Can't play — will score 0:** {names}. Injured, suspended, or left the club (FPL hides these "
               "from selection). Swap them out on the **Transfer** tab.")


_CARD_GWS = 3   # the player card's per-GW row shows a team's next 3 fixtures (ADR-109)


def _card_horizon(upcoming, card_gws: int = _CARD_GWS) -> int:
    """How many **global** gameweeks the card's per-team next-`card_gws` fixtures actually span.

    A horizon counts gameweeks from the front of `upcoming`; the card counts fixtures per team. Those agree only
    while every team has a fixture in every gameweek — so they part company at a **blank gameweek**, where a team
    with no match has its next three fixtures spread over four. Asking for a flat 3-gameweek horizon then leaves
    the card's third cell at 0.0, because the xP was never computed for the gameweek the card is showing.

    Returns the 1-based position of the furthest gameweek any team's next-`card_gws` reaches, so an xP computed to
    that horizon fills every cell. Pure; `card_gws` at minimum when there's nothing to measure."""
    events = sorted({f["event"] for f in upcoming if f["event"] is not None})
    if not events:
        return card_gws
    rank = {e: i + 1 for i, e in enumerate(events)}     # gameweek → how deep a horizon must reach to include it
    teams_ = {t for f in upcoming for t in (f["home"], f["away"])}
    reach = [rank[s["event"]] for t in teams_ for s in team_schedule(upcoming, t)[:card_gws]
             if s["event"] in rank]
    return max([card_gws, *reach])


def render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos, *, teams=None, horizon=5):
    # US-423 (density): the "on the pitch — pick a player…" caption dropped (the pitch + ⚙ panel are discoverable)
    # so the pitch sits higher on mobile.
    # US-386: a brand status card so your team stands out + Save/backup is signposted. "Yours" = the shown squad is
    # your session's active squad (not a demo); "synced" = signed-in mode (the account is the store, ADR-113).
    from src.web_streamlit import auth
    _mine = active_squad()
    _is_yours = _mine is not None and (squad is _mine or squad.get("player_ids") == _mine.get("player_ids"))
    st.markdown(team_banner_html(squad, is_yours=_is_yours, synced=auth.is_configured()), unsafe_allow_html=True)
    render_your_team(squad, is_yours=_is_yours)   # US-385/386: the one Your-team panel — import · back up (ADR-113)
    by_id = {p["id"]: p for p in players}
    owned = [by_id[i] for i in squad["player_ids"] if i in by_id]
    _flag_unavailable(owned)                         # ⛔ US-421: a member who can't play (injured/suspended/left)
    ranked = decision_xp(players, upcoming, history, horizon=horizon, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    team_names = {t["short_name"]: t["name"] for t in (teams or [])}   # short → friendly name (the card, US-344)
    by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}     # per-GW xP (ADR-032) for the captain
    next_gw = ranked[0]["gameweeks"][0] if ranked and ranked[0]["gameweeks"] else None
    # Per-GW fixtures + xP for the player card (ADR-109): each owned player's next-≤3 fixtures with the xP for that
    # gameweek (aligned by `event` number). Feeds the ⚙ panel card (US-367) + the pitch hover popover (US-368).
    # The card row **always shows 3 gameweeks, independent of the page horizon** (wave-3 feedback: a horizon of 1
    # used to leave GW2/GW3 at 0). Reuse `ranked` when it already spans far enough; else compute a wider view just
    # for the card.
    #
    # "Far enough" is not a flat 3. The card's 3 gameweeks are counted **per team**, but a horizon is counted
    # **globally**, and a blank gameweek pulls the two apart: a team sitting one out has its next 3 fixtures spread
    # over 4 gameweeks, so a flat-3 horizon never computes the xP its third cell needs. Sizing the horizon by the
    # furthest gameweek any team's next-3 actually reaches keeps every cell populated.
    card_horizon = _card_horizon(upcoming)
    card_bg_by_id = by_gameweek_by_id if horizon >= card_horizon else {
        r["id"]: r["by_gameweek"]
        for r in decision_xp(players, upcoming, history, horizon=card_horizon, gw_history_by_code=gw_history)}

    def _pergw_fixtures(p):
        """A player's next-≤3 **gameweeks** with the per-GW xP (ADR-109). Works for **any** player
        (`card_bg_by_id` covers the whole pool) — so a Boot Battle target from All/By-club has its card row too
        (US-380).

        Grouped by gameweek, not by fixture (ADR-129 audit). Taking the next three *fixtures* gave a double
        gameweek two of the three slots and filled each with the same already-doubled `by_gameweek` value — the
        card read 25 xP where the player's real three-week total was 15, and lost a week of forward view. One
        cell per gameweek, both opponents named in it, the doubled xP counted once."""
        _bg = card_bg_by_id.get(p["id"], {})
        by_event: dict = {}
        for s in team_schedule(upcoming, p["team"]):
            by_event.setdefault(s["event"], []).append(s)
        cells = []
        for event in sorted(by_event)[:3]:
            fx = by_event[event]
            cells.append({"opp": fx[0]["opponent"], "home": fx[0]["venue"] == "H",
                          # A double is only as easy as its harder half — the cell is FDR-tinted by it.
                          "fdr": max((f.get("difficulty") for f in fx if f.get("difficulty") is not None),
                                     default=fx[0].get("difficulty")),
                          "xp": _bg.get(event),
                          "opps": [(f["opponent"], f["venue"] == "H") for f in fx]})
        return cells

    fixtures_by_id = {p["id"]: _pergw_fixtures(p) for p in owned}   # for the pitch popover + the panel card
    bench_ids = set(squad.get("bench_ids") or [])
    captain_id = squad.get("captain_id")

    xi = [p for p in owned if p["id"] not in bench_ids]
    bench = [p for p in owned if p["id"] in bench_ids]

    issues = squad_15_issues(owned)
    cost = round(sum(p["price"] for p in owned), 1)
    if issues:
        st.error("Not a legal 15: " + "; ".join(issues))
    else:
        over = round(cost - FPL_BUDGET, 1)
        # US-423 (density): a compact caption, not a full green success box, so the pitch sits higher.
        st.caption(f"£{cost:.1f}m · ✓ a legal 15" if over <= 0
                   else f"£{cost:.1f}m · ✓ legal · ⚠ £{over:.1f}m over the £{FPL_BUDGET:.0f}m budget")

    # A quick-view team summary (US-239) — reuses the horizon-aware xP + availability; display-only.
    # The projected XI is the declared XI (if a bench is set) else the best legal XI — same as Health.
    xi_ids = ({p["id"] for p in owned} - bench_ids) if bench_ids else best_legal_xi(owned, xp_by_id)

    # US-422 (ADR-121): a per-GW xP toggle — show the cumulative horizon (as today) OR just the horizon's last
    # gameweek, from the already-computed by_gameweek (ADR-032). Display-only: the XI/captain SELECTION above stays
    # cumulative; only the shown numbers + the pitch chips switch. Offered only when the horizon spans >1 GW.
    gws = ranked[0]["gameweeks"] if ranked and ranked[0]["gameweeks"] else []
    target_gw = gws[-1] if gws else None
    per_gw = False
    if horizon > 1 and target_gw is not None:
        _opts = [f"GW{gws[0]}–{target_gw} (cumulative)", f"GW{target_gw} only"]
        per_gw = st.segmented_control(
            "Projected xP", _opts, default=_opts[0], key="myteam_xp_view",
            help="Cumulative = total xP over the horizon; 'GW only' = just that gameweek — for last-minute, "
                 "GW-by-GW planning as transfers roll in.") == _opts[1]
    display_xp = ({p["id"]: by_gameweek_by_id.get(p["id"], {}).get(target_gw, 0.0) for p in owned}
                  if per_gw else xp_by_id)
    cap_gw = target_gw if per_gw else next_gw
    gw_label = f"GW{target_gw}" if per_gw else ("next GW" if horizon == 1 else f"{horizon} GW")

    xi_xp = sum(display_xp.get(i, 0) for i in xi_ids)
    bench_xp = sum(display_xp.get(p["id"], 0) for p in owned if p["id"] not in xi_ids)
    # Captaincy is a next-GW decision → the projected XI adds the captain's double for the shown gameweek,
    # and only when the captain is in the XI (a benched captain isn't doubled). ADR-083.
    cap_next = captain_bonus(captain_id, xi_ids, by_gameweek_by_id, cap_gw)
    projected_xi = xi_xp + cap_next
    captain_benched = captain_id is not None and captain_id not in xi_ids
    # US-404: a compact 3-number strip (was a 5-across metric wall that slivered on mobile — Unavailable/Doubtful
    # were their own metrics, but the flagged line below already names them).
    m1, m2, m3 = st.columns(3)
    m1.metric(f"Projected XI ({gw_label})", f"{projected_xi:.1f} xP",
              help="Your starting XI's projected points over the selected horizon, plus your captain's "
                   "double for the next gameweek (the ×2 is a one-week thing).")
    m2.metric("Captain (2×)", f"{cap_next * 2:.1f} xP" if cap_next else "—",
              help="Your captain's next-gameweek points, doubled. Captaincy is re-chosen each week, so the "
                   "bonus counts for the next GW only. Set/change one on the Captain tab.")
    m3.metric("Bench", f"{bench_xp:.1f} xP", help="Your bench's projected points (bench strength).")
    # Be explicit that the ×2 is a one-week thing when a longer horizon is selected (owner steer, ADR-083).
    cap_name = by_id[captain_id]["web_name"] if captain_id in by_id else None
    if cap_next and per_gw:
        st.caption(f"⚡ Showing **GW{target_gw}** only — captain **{cap_name}**'s double is applied to that "
                   "gameweek (captaincy is re-picked weekly).")
    elif cap_next and horizon > 1:
        st.caption(f"⚡ Captain **{cap_name}** is doubled for the **next gameweek only** (+{cap_next:.1f} xP); "
                   f"the other {horizon - 1} GW count once — captaincy is re-picked each week.")
    elif captain_benched:
        st.caption("⚡ Your captain is on the **bench** — not doubled in the projected XI (FPL would auto-sub "
                   "to your vice).")

    # US-404: availability + price folded into ONE line (was two caption walls). ❓ carries the chance%; price is
    # directional pressure from net transfers (US-286/ADR-092), not exact timing.
    flagged = [(p, availability_flag(p)) for p in owned if availability_flag(p)]
    avail = ("⚠ **Flagged:** " + " · ".join(f"{p['web_name']} {flag}" for p, flag in flagged) + " — see **News**"
             if flagged else "✓ All 15 available")
    falling = [p["web_name"] for p in owned if price_prediction(p) == "fall"]
    rising = [p["web_name"] for p in owned if price_prediction(p) == "rise"]
    pbits = []
    if falling:
        pbits.append("🔻 " + ", ".join(falling) + " may drop")
    if rising:
        pbits.append("🔺 " + ", ".join(rising) + " rising")
    price = " · ".join(pbits) if pbits else "💷 no price moves (flat preseason)"
    st.caption(f"{avail}  ·  {price}")

    # Bench order (US-242/244/246) — the auto-sub priority (the stored order, ADR-079), reorderable (⬆/⬇).
    bench_ordered = [by_id[i] for i in (squad.get("bench_ids") or []) if i in by_id]
    outfield_subs = [p for p in bench_ordered if p["position"] != "GK"]
    gk_sub = next((p for p in bench_ordered if p["position"] == "GK"), None)
    _SUB_LABEL = ("1st", "2nd", "3rd", "4th")
    # id → sub role, so the pitch can label the bench cards (US-246).
    bench_roles = {p["id"]: _SUB_LABEL[i] for i, p in enumerate(outfield_subs)}
    if gk_sub:
        bench_roles[gk_sub["id"]] = "GK"

    next_opp = {t: (team_schedule(upcoming, t) or [None])[0] for t in {p["team"] for p in owned}}
    kits = shirt_url_by_id(owned, teams)        # the pitch shows the live club kit (ADR-084 rev), not the mugshot
    # ADR-133 — tapping a shirt selects that player, writing the same state the picker below uses. Must come
    # before the selectbox is created. Degrades to the ordinary pitch if the component isn't available.
    # ADR-133 — tapping a shirt selects that player, writing the same state the picker below uses. The action
    # **menu** that briefly lived here (ADR-135) is reverted: every tap costs a full rerun plus a decision_xp
    # recompute, so a floating menu — and especially a two-tap flow costing two round-trips — felt slower and
    # messier than the widgets it replaced. Selection is one round-trip and genuinely replaces a dropdown.
    from src.web_streamlit.tap import render_tappable_pitch
    _label = lambda p: f"{p['web_name']} · {p['team']}"      # noqa: E731 — matches the picker's option text
    _sel_now = st.session_state.get("pa_pick")
    _sel_id = next((p["id"] for p in owned if _label(p) == _sel_now), None)
    render_tappable_pitch(
        xi, bench, select_key="pa_pick", label_for=_label,
        captain_id=captain_id, xp_by_id=display_xp, photos=photos, next_opp=next_opp,
        team_names=team_names, bench_roles=bench_roles, kits=kits, selected_id=_sel_id,
        fixtures_by_id=fixtures_by_id)                      # ADR-109: per-GW row in the hover popover

    # ⚙ Player actions (ADR-108, US-365/366) — one selection drives the **full card** + **Make captain** +
    # **Substitute**, together, in one panel on the golden page (consolidates the old card picker + Substitute
    # expander + the stranded Captain-tab set control). Native selectbox+button → it works on phone/tablet, and
    # gives mobile the full card the desktop-only hover popover never could. Reuses the card renderer +
    # `set_captain` + `substitute` — no analytics change.
    from src.web_streamlit.player_card import render_player_card, render_player_compare
    st.subheader("⚙ Players & lineup")
    # ADR-133: name the tap only when it's actually live. The fallback is invisible by design, so this caption
    # is both the user-facing hint that the gesture exists and the signal that the component loaded.
    from src.web_streamlit.tap import available as _tap_available
    st.caption(("**Tap a shirt** on the pitch, or pick below → " if _tap_available() else "Pick a player → ")
               + "view their card, ⚔️ Boot Battle (compare), make them captain, or substitute. "
                 "Works on phone too (the pitch hover is desktop-only).")
    owned_by_label = {f"{p['web_name']} · {p['team']}": p for p in owned}
    picked = owned_by_label.get(st.selectbox("Select a player", ["—", *owned_by_label], key="pa_pick",
                                             help="Or hover a shirt on the pitch (desktop only)."))
    if picked:
        short = picked["team"]
        # ADR-139 — the CARD FIRST. It used to render below three Boot Battle widgets, so a tap put the teal
        # outline on the shirt and the card a scroll away, behind controls for a different question. Tap → card
        # only feels like one action if the card is where the eye lands. This is the half of ADR-139 that
        # *delivers* the request; removing the hover popover alone would have taken something away without
        # putting anything in its place.
        # Read *last* run's Boot Battle pick to decide whether the card or the comparison goes here. It has
        # to be read before the widget is created, because the card renders above it — that is the whole point
        # of the reorder. Streamlit has already applied any interaction to session_state by now, so this is the
        # current choice, not a stale one.
        _comparing = st.session_state.get("pa_boot", "—") != "—"
        if not _comparing:
            render_player_card(picked, team_name=team_names.get(short, short), photo_url=photos.get(picked["id"]),
                               fixtures=fixtures_by_id.get(picked["id"]),   # ADR-109 per-GW row (no Total col)
                               projected_xp=xp_by_id.get(picked["id"]))

        # ⚔️ Boot Battle (US-377/380, ADR-110/111) — compare the selected player with another **same-position** player,
        # side by side (winner-tinted). A **pool** selector (US-380): My team (owned) · All players · By club. Reuses
        # `render_player_compare`; the target's per-GW fixtures build on demand (`xp_by_id`/`card_bg_by_id` cover all).
        bb_pool = st.segmented_control("⚔️ Boot Battle — pool", ["My team", "All", "By club"],
                                       default="My team", key="pa_boot_pool") or "My team"
        if bb_pool == "By club":
            club_labels = {team_names.get(t, t): t
                           for t in sorted({q["team"] for q in players if q["position"] == picked["position"]})}
            club = club_labels.get(st.selectbox("Club", list(club_labels), key="pa_boot_club"))
            base = [q for q in players if q["team"] == club]
        elif bb_pool == "All":
            base = players
        else:                                                    # My team (same-position squad players)
            base = owned
        cands = sorted((q for q in base if q["position"] == picked["position"] and q["id"] != picked["id"]),
                       key=lambda q: q["web_name"] or "")
        bb_by_label = {f"{q['web_name']} · {q['team']}": q for q in cands}
        bb = bb_by_label.get(st.selectbox("⚔️ Boot Battle — compare with…", ["—", *bb_by_label], key="pa_boot",
                                          help="Type to search a same-position player to compare side by side."))
        if bb:
            cshort = bb["team"]
            render_player_compare(
                picked, bb, a_team=team_names.get(short, short), b_team=team_names.get(cshort, cshort),
                a_photo=photos.get(picked["id"]), b_photo=photos.get(bb["id"]),
                a_fixtures=_pergw_fixtures(picked), b_fixtures=_pergw_fixtures(bb),
                a_xp=xp_by_id.get(picked["id"]), b_xp=xp_by_id.get(bb["id"]))
        elif _comparing:
            # The stored comparison no longer resolves — usually because the selection moved to another
            # position, so the remembered opponent isn't in this pool. Without this the card was skipped above
            # *and* no comparison renders, and the panel silently shows nothing about the player you tapped.
            render_player_card(picked, team_name=team_names.get(short, short), photo_url=photos.get(picked["id"]),
                               fixtures=fixtures_by_id.get(picked["id"]),
                               projected_xp=xp_by_id.get(picked["id"]))

        # 👑 Make captain — one click; ×2 next GW. (Briefly moved onto the shirt by ADR-135 and moved back:
        # a button here costs the same rerun without a floating menu or a hover collision.)
        if picked["id"] == captain_id:
            st.caption(f"👑 **{picked['web_name']}** is already your captain (×2 next gameweek).")
        elif st.button(f"👑 Make {picked['web_name']} captain", key="pa_captain"):
            set_active_squad(set_captain(squad, picked["id"]))
            st.success(f"Captain set: **{picked['web_name']} (C)** — they score ×2 next gameweek.")
            st.rerun()

        # 🔁 Substitute (US-366, ADR-108) — the selected player is one side of the swap; pick the other. Only
        # legal swaps are offered (substitute() returns no issues: GK↔GK, a swap that keeps a legal formation).
        # A benched pick brings them ON (choose the starter to drop); a starter takes them OFF (choose the bench
        # player). Reuses substitute(); folds in the old standalone expander + the _sub_prefill_for seed. The
        # static pitch card still can't hold a working button (S139), so this selection-driven panel is the path.
        pid = picked["id"]

        def _do_sub(off_id, on_id):
            new, issues = substitute(squad, off_id, on_id, by_id)
            if issues:      # belt-and-braces: the option lists already exclude illegal swaps
                st.error("Can't substitute — that leaves an illegal XI: " + "; ".join(issues))
            else:
                set_active_squad(new)
                st.success(f"Subbed **{by_id[off_id]['web_name']} → {by_id[on_id]['web_name']}** — "
                           "the bench updates too.")
                st.rerun()

        # The picker is unconditional again. ADR-135 hid it at rest (the shirt's 🔁 armed the flow); that menu is
        # reverted, so this is the only path to a substitution and must always be on the page.
        if pid in bench_ids:                                   # a bench player → bring them ON for a starter
            legal = {f"{p['position']} {p['web_name']}": p["id"]
                     for p in sorted(xi, key=lambda x: _ORDER.get(x["position"], 9))
                     if not substitute(squad, p["id"], pid, by_id)[1]}
            if legal:
                off = st.selectbox(f"🔁 Bring {picked['web_name']} on — take off", list(legal), key="pa_sub",
                                   help="The starter to move to the bench — only legal swaps are shown.")
                if st.button("Substitute →", key="pa_do_sub"):
                    _do_sub(legal[off], pid)
            else:
                st.caption(f"No legal swap brings **{picked['web_name']}** on (no starter keeps a legal XI).")
        elif bench:                                              # a starter → take them OFF for a bench player
            legal = {f"{p['position']} {p['web_name']} · {round(xp_by_id.get(p['id'], 0), 1)} xP": p["id"]
                     for p in bench if not substitute(squad, pid, p["id"], by_id)[1]}
            if legal:
                on = st.selectbox(f"🔁 Take {picked['web_name']} off — bring on", list(legal), key="pa_sub",
                                  help="The bench player to bring into your XI — only legal swaps are shown.")
                if st.button("Substitute →", key="pa_do_sub"):
                    _do_sub(pid, legal[on])
            else:
                why = ("the bench GK only covers your keeper" if picked["position"] == "GK"
                       else "no bench player keeps a legal formation")
                st.caption(f"No legal swap for **{picked['web_name']}** — {why}.")

        if not bb:      # 🧬 Player DNA (ADR-118, US-417) — the same section as Players ▸ Card, owned-aware
            # (Hold/Sell), below the actions. Skipped while Boot-Battle comparing. Reuses the panel's xp_by_id +
            # gw_history; display-only, no decision_xp change.
            from src.analytics import last_season_name, last_season_rows
            from src.web_streamlit.player_dna_view import render_player_dna
            # ADR-126: the DNA peer pool needs 450 mins, so hand it last season to rank against until ~GW5.
            render_player_dna(picked, players, xp_by_id, gw_history=gw_history, owned=True,
                              last_rows=last_season_rows(players, history),
                              season_name=last_season_name(history))

    if bench_ordered:
        line = " · ".join(f"**{_SUB_LABEL[i]}** {p['web_name']} ({round(xp_by_id.get(p['id'], 0), 1)} xP)"
                          for i, p in enumerate(outfield_subs))
        if gk_sub:
            line += f" · **GK** {gk_sub['web_name']}"
        st.caption(f"🔁 **Bench order** (auto-subs): {line} — FPL brings on the first that keeps a legal XI; "
                   "the bench GK only covers your keeper.")
        with st.expander("Reorder the bench (auto-sub priority)"):
            for i, p in enumerate(outfield_subs):
                c_name, c_up, c_down = st.columns([6, 1, 1])
                c_name.write(f"**{_SUB_LABEL[i]}** {p['web_name']} · "
                             f"{round(xp_by_id.get(p['id'], 0), 1)} xP")
                if c_up.button("⬆", key=f"bench_up_{p['id']}", disabled=(i == 0),
                               help="Move this sub up the priority."):
                    set_active_squad(move_bench_sub(squad, p["id"], "up", by_id))
                    st.rerun()
                if c_down.button("⬇", key=f"bench_down_{p['id']}", disabled=(i == len(outfield_subs) - 1),
                                 help="Move this sub down the priority."):
                    set_active_squad(move_bench_sub(squad, p["id"], "down", by_id))
                    st.rerun()
            if st.button("↻ Use recommended (xP) order",
                         help="Order the outfield subs by expected points (highest first)."):
                rec_ids = ([p["id"] for role, p in bench_order(bench_ordered, xp_by_id) if role != "GK"]
                           + ([gk_sub["id"]] if gk_sub else []))
                set_active_squad(set_bench(squad, rec_ids))
                st.rerun()

    st.divider()
    # US-405 (ADR-115): transfers live on the **Transfer tab** — the in-page expander that duplicated it is gone.
    st.caption("🔄 **Make a transfer** — bring in a **new** player — on the **Transfer** tab above (it sells one "
               "of your 15 for a same-position replacement). *(🔁 **Substitute**, above, just swaps your XI ↔ bench.)*")

    # US-406 (ADR-115): the secondary edits fold into one collapsed **⚙ Manage** — flat subsections, because
    # Streamlit expanders can't nest.
    with st.expander("⚙ Manage — rename · set the whole bench"):
        st.markdown("**✏️ Rename**")
        new_name = st.text_input("Squad name", value=squad.get("name", "My squad"), max_chars=40, key="mng_rename",
                                 help="Rename this squad (shown in the download and as the active label).")
        if st.button("Rename", key="mng_rename_btn"):
            set_active_squad(rename(squad, new_name))
            st.rerun()

        st.markdown("**🪑 Set the whole bench (pick 4)**")
        st.caption("Bulk edit — re-pick all four bench players. For a single swap, use **🔁 Substitute** above.")
        bench_labels = {f"{p['position']} {p['web_name']}": p["id"] for p in
                        sorted(owned, key=lambda x: _ORDER.get(x["position"], 9))}
        bench_default = [lab for lab, i in bench_labels.items() if i in bench_ids]
        bench_pick = st.multiselect("Bench", list(bench_labels), default=bench_default, max_selections=4,
                                    key="mng_setbench", help="Pick your 4 bench players; the other 11 are your XI.")
        if st.button("Set bench", key="mng_setbench_btn"):
            new = set_bench(squad, [bench_labels[lab] for lab in bench_pick])
            new_xi = [by_id[i] for i in new["player_ids"] if i not in set(new["bench_ids"]) and i in by_id]
            xi_problem = legal_xi_issues(new_xi) if len(new_xi) == 11 else ["the XI isn't 11 players"]
            set_active_squad(new)
            if xi_problem:
                st.warning("Bench set — but the XI isn't legal: " + "; ".join(xi_problem))
            else:
                st.success("Bench set.")
            st.rerun()


# ---- Health (analyse the squad over the next 5 GW; ADR-031) ----------------------------------------

def render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges, *,
                  team_names=None, horizon=5):
    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    if not owned:
        st.info(f"Squad '{squad_name}' has no current players to analyse.")
        return
    ranked = decision_xp(players, upcoming, history, horizon=horizon, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    bench_ids = set(squad.get("bench_ids") or [])
    xi_ids = ({p["id"] for p in owned if p["id"] not in bench_ids} if bench_ids
              else best_legal_xi(owned, xp_by_id))
    analysis = analyse_squad(
        owned, xi_ids, xp_by_id, horizon=horizon,
        by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
        gameweeks=ranked[0]["gameweeks"] if ranked else [],
        weight_by_id={r["id"]: r["minutes_weight"] for r in ranked},
    )
    captain_id = squad.get("captain_id")
    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"] + (" (C)" if p["id"] == captain_id else ""),
        "Team": p["team"], "£m": p["price"], "xP": round(xp_by_id.get(p["id"], 0), 1),
        "Role": "XI" if p["id"] in xi_ids else "Bench", "Trends": " ".join(crowd_flags(p)),
        "Set": " ".join(set_piece_flags(p)),
    } for p in sorted(owned, key=lambda x: (x["id"] not in xi_ids, _ORDER.get(x["position"], 9)))],
        help={"Set": SET_PIECE_LEGEND})
    st.code(render_squad_analysis(analysis, squad_name, show_xmins=True, captain_id=captain_id), language=None)

    # 🧬 Your teams (ADR-119, US-420) — the team-strength health check behind your squad: each of your clubs'
    # grade + attack/defence/fixture read + your players, drilling into the full Team DNA. Reuses players/upcoming.
    st.divider()
    from src.analytics import last_season_name, last_season_rows
    from src.analytics.forward_plan import forward_plan
    from src.analytics.player_dna import player_dna_this_or_last
    from src.analytics.squad_risk import squad_dna, squad_risk_rows
    from src.analytics.team_dna import team_dna_all
    from src.web_streamlit.squad_risk_card import (
        render_forward_plan,
        render_risk_monitor,
        render_squad_dna,
    )
    from src.web_streamlit.team_dna_card import render_your_teams

    # ADR-130 — the two questions Health couldn't answer: what needs attention this week, and how the 15 look
    # together. Both reuse existing engines (xMins · Player DNA · Team DNA); no new analytics.
    _last = last_season_rows(players, history)
    _name = last_season_name(history)
    st.divider()
    render_risk_monitor(squad_risk_rows(owned, upcoming, gw_history=gw_history, history=history), badges)
    _dna_by_id = {p["id"]: player_dna_this_or_last(p, players, _last, _name)[0] for p in owned}
    _tdna = team_dna_all(players, upcoming, gw_history=gw_history, last_rows=_last)
    render_squad_dna(squad_dna(owned, _dna_by_id, _tdna))
    # ADR-131 — what's coming, led by fixture exposure (which varies) rather than xP (which barely does).
    _ranked = decision_xp(players, upcoming, history, horizon=6, gw_history_by_code=gw_history)
    render_forward_plan(
        forward_plan(owned, upcoming, {r["id"]: r["by_gameweek"] for r in _ranked}, horizon=6), len(owned))
    st.divider()
    # ADR-126: the key-players table needs ~900 minutes to rank anyone, so hand it last season to fall back on.
    render_your_teams(squad, players, upcoming, team_names=team_names,
                      last_rows=_last, season_name=_name, gw_history=gw_history)


# ---- Transfer (best XI-aware swaps; ADR-046) -------------------------------------------------------

def render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos, *, horizon=5):
    col1, col2 = st.columns(2)
    bank = col1.slider("Bank (£m)", 0.0, 10.0, 0.0, step=0.5,
                       help="Spare money you can add on top of selling a player.")
    count = col2.slider("Transfers (a coordinated plan)", 1, 3, 1,
                        help="How many swaps to plan together (they share the bank).")

    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    if not owned:
        st.info(f"Squad '{squad_name}' has no current players to improve.")
        return
    ranked = decision_xp(players, upcoming, history, horizon=horizon, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    bench_ids = squad.get("bench_ids", [])

    # ⛔ Dead slots (ADR-136) — FIRST, above even the timing question. A slot that cannot score is not a
    # matter of when; it is a hole in the 15 with no auto-sub cover, and it is invisible to every ranking on
    # this page because replacing a benched dead player lifts the best XI by exactly zero. Renders nothing at
    # all when the squad is whole, so this costs no space for the managers it doesn't apply to.
    from datetime import UTC, datetime

    from src.analytics.transfer import replace_dead
    dead = replace_dead(owned, players, xp_by_id, upcoming, bench_ids=bench_ids, bank=bank,
                        horizon=horizon, today=datetime.now(UTC).date())
    for i, d in enumerate(dead):
        st.error(f"⛔ **{d['out']['web_name']} ({d['out']['team']}) can't play — {d['reason']}.** "
                 f"That's a squad slot scoring nothing for the next {horizon} gameweeks, with no bench cover. "
                 f"→ **{d['in']['web_name']}** ({d['in']['team']}, £{d['in']['price']:.1f}) "
                 f"recovers **{d['gain']:.1f} xP**.")
        if st.button(f"Replace {d['out']['web_name']} →", key=f"dead_apply_{i}",
                     help="Make this swap on your session squad."):
            ok, issues, warning, new = apply_transfer(squad, d["out"]["id"], d["in"]["id"], players)
            if not ok:
                st.error("Can't apply — that would leave an illegal squad: " + "; ".join(issues))
            else:
                set_active_squad(new)
                done = (f"Applied **{d['out']['web_name']} → {d['in']['web_name']}** — "
                        f"new cost £{new['cost']:.1f}m.")
                st.warning(f"{done}  ⚠ {warning}") if warning else st.success(done)
                st.rerun()

    # ADR-132 — the timing question, above the moves themselves: use the free transfer, bank it, or take the
    # hit. Arithmetic over FPL's own rules, not a search — the roadmap's path/tree was scoped out on evidence.
    from src.analytics.transfer_timing import transfer_timing
    _plan = suggest_transfer_plan(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, count=2)
    _next_gw = ranked[0]["gameweeks"][0] if ranked and ranked[0]["gameweeks"] else None
    _bg = {r["id"]: r["by_gameweek"] for r in ranked}
    _delay = None
    if _plan and _next_gw is not None:
        _delay = round(_bg.get(_plan[0]["in"]["id"], {}).get(_next_gw, 0.0)
                       - _bg.get(_plan[0]["out"]["id"], {}).get(_next_gw, 0.0), 2)
    _free = st.number_input("Free transfers you hold", 0, 5, 1,
                            help="FPL gives one a week and rolls unused ones up to five.")
    _timing = transfer_timing(_plan, free=_free, next_gw_gain=_delay, horizon=horizon)
    st.info(_timing["headline"])
    st.caption(_timing["hit_verdict"])

    # ⭐ Watchlist (ADR-117) — your kept shortlist (⭐ them on the Players tab); the manual transfer below brings
    # one in. Shows each watched player's next fixture · xP · form.
    from src.web_streamlit import watchlist
    _all_by_id = {p["id"]: dict(p) for p in players}       # dict() — `players` are sqlite3.Row (no .get())
    watched = [_all_by_id[i] for i in watchlist.ids() if i in _all_by_id]
    with st.expander(f"⭐ Your watchlist ({len(watched)})", expanded=bool(watched)):
        if not watched:
            st.caption("No players watched yet — ⭐ star them on the **Players** tab (the pool or a player card), "
                       "then bring one in here.")
        else:
            st.dataframe(
                [{"photo": photos.get(p["id"], ""), "Player": p["web_name"], "Team": p["team"],
                  "Pos": p["position"],
                  "Next": (f"{_n['opponent']} ({_n['venue']})"
                           if (_n := (team_schedule(upcoming, p["team"]) or [None])[0]) else "—"),
                  "£m": p["price"], "xP": round(xp_by_id.get(p["id"], 0), 1), "Form": p.get("form")}
                 for p in watched],
                hide_index=True, width="stretch",
                column_config={"photo": st.column_config.ImageColumn("", width="small"),
                               "£m": st.column_config.NumberColumn("£m", format="£%.1fm"),
                               "xP": st.column_config.NumberColumn("xP", format="%.1f")})
            _rlabels = {f"{p['web_name']} · {p['team']}": p["id"] for p in watched}
            _r = st.selectbox("★ Remove from watchlist", ["—", *_rlabels], key="watch_remove")
            if _r != "—" and st.button("★ Remove", key="watch_remove_btn"):
                watchlist.remove(_rlabels[_r])
                st.rerun()
            st.caption("Bring one in with **✋ Manual transfer** below (a same-position swap).")

    if count > 1:
        plan = suggest_transfer_plan(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, count=count)
        st.code(render_transfer_plan(
            plan, squad_name, bank=bank, horizon=horizon,
            by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
            gameweeks=ranked[0]["gameweeks"] if ranked else [], show_xmins=True, has_dead=bool(dead),
        ), language=None)
        # US-354: accept the whole coordinated plan (not just a single swap) — all transfers at once, legality +
        # a soft over-budget flag, then set it as the session squad. Mirrors the single-swap apply below.
        if plan:
            net = round(sum(m["in"]["price"] - m["out"]["price"] for m in plan), 1)
            gain = round(sum(m["gain"] for m in plan), 1)
            st.caption(f"Applying this makes **{len(plan)}** transfer(s) at once — net spend "
                       f"£{net:+.1f}m · +{gain:.1f} projected xP.")
            if st.button("Apply this plan →", key="apply_plan",
                         help="Make all of these transfers on your session squad in one step."):
                ok, issues, warning, new = apply_transfer_plan(squad, plan, players)
                if not ok:
                    st.error("Can't apply — that would leave an illegal squad: " + "; ".join(issues))
                else:
                    set_active_squad(new)
                    done = f"Applied **{len(plan)}** transfer(s) — new cost £{new['cost']:.1f}m."
                    st.warning(f"{done}  ⚠ {warning}") if warning else st.success(done)
                    st.rerun()
    else:
        swaps = suggest_transfers(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, limit=5)
        by_id = {p["id"]: p for p in players}
        render_player_table([{
            "out": photos.get(s["out"]["id"], ""), "Out": s["out"]["web_name"],
            "in": photos.get(s["in"]["id"], ""), "In": s["in"]["web_name"],
            "Pos": s["position"], "+xP": s["gain"],
            "In trends": " ".join(crowd_flags(by_id.get(s["in"]["id"], {}))),
            "In set": " ".join(set_piece_flags(by_id.get(s["in"]["id"], {}))),
        } for s in swaps], help={"In set": SET_PIECE_LEGEND})
        st.code(render_transfers(swaps, squad_name, bank=bank, horizon=horizon, show_xmins=True,
                                 has_dead=bool(dead)), language=None)

        if swaps:
            labels = [f"{s['out']['web_name']} → {s['in']['web_name']}  (+{s['gain']} xP)" for s in swaps]
            choice = st.selectbox("Apply a swap to your squad", labels, key="apply_swap",
                                  help="Pick one suggested swap to apply to your active squad.")
            if st.button("Apply this transfer →"):
                chosen = swaps[labels.index(choice)]
                ok, issues, warning, new = apply_transfer(
                    squad, chosen["out"]["id"], chosen["in"]["id"], players)
                if not ok:
                    st.error("Can't apply — that would leave an illegal squad: " + "; ".join(issues))
                else:
                    set_active_squad(new)
                    done = (f"Applied **{chosen['out']['web_name']} → {chosen['in']['web_name']}** — "
                            f"new cost £{new['cost']:.1f}m.")
                    st.warning(f"{done}  ⚠ {warning}") if warning else st.success(done)
                    st.rerun()

    # ✋ Manual transfer (moved here from the My Squad edit view — ADR-115). The block above **suggests** the best
    # swaps; this lets you pick the **exact** out→in yourself (a punt, or a specific target the ranker didn't top).
    # Same-position only (a fixed 2/5/5/3); team/price/affordable filters; a live overspend flag. Reuses
    # `apply_transfer` — no analytics change.
    st.divider()
    with st.expander("✋ Manual transfer — pick the exact swap"):
        by_id = {p["id"]: p for p in players}
        cost = round(sum(p["price"] for p in owned), 1)
        # Filter which of your players to swap out by position (US-299) — a swap is same-position.
        pos_filter = st.segmented_control(
            "Position", ["All", "GK", "DEF", "MID", "FWD"], default="All", key="swap_pos",
            help="Filter which of your players to swap out by position.")
        real_bank = round(FPL_BUDGET - cost, 1)            # a swap fits when in.price ≤ out.price + bank (US-300)
        st.caption(f"Bank: £{real_bank:.1f}m")
        c_aff, c_flag = st.columns(2)
        affordable_only = c_aff.checkbox(
            "Affordable only", value=False, key="swap_affordable",
            help="Hide replacements that would push you over budget (the transfer still checks on apply).")
        include_flagged = c_flag.checkbox(
            "Include injured/suspended", value=False, key="swap_flagged",
            help="Also list flagged (injured/suspended/unavailable) replacements — off by default.")
        out_pool = [p for p in owned if pos_filter in (None, "All") or p["position"] == pos_filter]
        if not out_pool:
            st.caption(f"No {pos_filter} players in your squad.")
        else:
            out_label = {f"{p['position']} {p['web_name']} (£{p['price']:.1f}m)": p["id"] for p in
                         sorted(out_pool, key=lambda x: (_ORDER.get(x["position"], 9), x["web_name"]))}
            out_choice = st.selectbox("Transfer out", list(out_label), key="swap_out", help="The player to sell.")
            out_id = out_label[out_choice]
            out = by_id[out_id]
            owned_ids = {p["id"] for p in owned}
            cands = sorted((p for p in players if p["position"] == out["position"] and p["id"] not in owned_ids
                            and (include_flagged or not is_unavailable(p))),
                           key=lambda x: xp_by_id.get(x["id"], 0), reverse=True)
            # US-356: the same-position list is long — narrow it by team + a max price.
            c_team, c_price = st.columns(2)
            team_filter = c_team.selectbox("Team", ["All", *sorted({p["team"] for p in cands})], key="swap_team",
                                           help="Filter the bring-in list to one club.")
            cand_hi = max([p["price"] for p in cands], default=15.0)
            price_cap = c_price.slider("Max price (£m)", 0.0, cand_hi, cand_hi, step=0.5, key="swap_maxprice",
                                       help="Only show replacements at or below this price.")
            cands = [p for p in cands if (team_filter in (None, "All") or p["team"] == team_filter)
                     and p["price"] <= price_cap]
            budget_in = out["price"] + real_bank           # the most a replacement can cost and still fit
            shown = [p for p in cands if p["price"] <= budget_in] if affordable_only else cands
            in_label = {f"{p['web_name']} · {p['team']} · £{p['price']:.1f}m · "
                        f"{round(xp_by_id.get(p['id'], 0), 1)} xP": p["id"] for p in shown}
            if in_label:
                in_choice = st.selectbox("Bring in", list(in_label), key="swap_in",
                                         help="The same-position player to bring in (ranked by xP).")
                in_id = in_label[in_choice]
                proj = round(cost - out["price"] + by_id[in_id]["price"], 1)   # US-353: live overspend flag
                if proj > FPL_BUDGET:
                    st.warning(f"⚠ After this transfer: £{proj:.1f}m — **£{proj - FPL_BUDGET:.1f}m over** the "
                               f"£{FPL_BUDGET:.0f}m budget (allowed — prices drift — but flagged).")
                else:
                    st.caption(f"After this transfer: £{proj:.1f}m · bank £{FPL_BUDGET - proj:.1f}m.")
                if st.button("Transfer →", key="swap_apply"):
                    ok, swap_issues, warning, new = apply_transfer(squad, out_id, in_id, players)
                    if not ok:
                        st.error("Can't transfer — that would leave an illegal squad: " + "; ".join(swap_issues))
                    else:
                        set_active_squad(new)
                        msg = f"Transferred **{out['web_name']} → {by_id[in_id]['web_name']}**."
                        st.warning(f"{msg}  ⚠ {warning}") if warning else st.success(msg)
                        st.rerun()
            elif affordable_only and cands:
                st.caption(f"No affordable replacement (≤ £{budget_in:.1f}m) — untick to see all.")
            else:
                st.caption("No replacements match — try a different **Team** / a higher **Max price** "
                           "(or untick *Affordable only*).")


# ---- Captain (who to (vice-)captain; ADR-029) ------------------------------------------------------

def render_captain(squad_name, squad, players, upcoming, history, photos, badges, team_names=None):
    st.caption("Captaincy is always the **next gameweek** (a one-week decision) — the *Gameweeks ahead* "
               "selector doesn't change it.")
    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    if not owned:
        st.info(f"Squad '{squad_name}' has no current players to captain.")
        return
    baseline_by_code = {code: baseline_rate(rows) for code, rows in history.items()}
    minutes_weight = minutes_weight_from_history(history)
    picks = captain_picks(owned, upcoming, baseline_by_code=baseline_by_code,
                          minutes_weight=minutes_weight, history_by_code=history)
    owned_by_id = {p["id"]: p for p in owned}
    render_player_table([{
        "photo": photos.get(pk["id"], ""), "badge": badges.get(pk["team"], ""),
        "Player": pk["web_name"], "Team": pk["team"], "Opp": pk.get("opponent", ""),
        "xP": round(pk.get("xp", 0), 1), "Trends": " ".join(crowd_flags(owned_by_id.get(pk["id"], {}))),
        "Set": " ".join(set_piece_flags(owned_by_id.get(pk["id"], {}))),
    } for pk in picks], help={"Set": SET_PIECE_LEGEND})
    st.caption("Captaincy risk: a **🟦 template** captain is safe (most managers own them); a "
               "**💎 differential** captain is a bigger rank swing — upside and downside.")
    explanation = explain_captain(picks, owned_by_id)   # grounded Why/Risk/Confidence (ADR-089)
    render_captain_card(picks, explanation, scope=f"from squad '{squad_name}'",   # a styled card (US-294)
                        team_names=team_names)

    current = squad.get("captain_id")
    if current:
        cur = next((p["web_name"] for p in owned if p["id"] == current), "?")
        st.caption(f"Your captain: **{cur} (C)**")
    labels = {f"{p['position']} {p['web_name']}": p["id"] for p in owned}
    recommended = picks[0]["id"] if picks else None
    want = current or recommended
    idx = next((i for i, pid in enumerate(labels.values()) if pid == want), 0)
    choice = st.selectbox("Set your captain", list(labels), index=idx, key="set_captain",
                          help="Choose your captain — they score double; shown as (C).")
    if st.button("Set as captain"):
        set_active_squad(set_captain(squad, labels[choice]))
        st.success(f"Captain set: **{choice.split(' ', 1)[1]} (C)** — shown in Health + your download.")
        st.rerun()


# ---- AI Tips (a grounded gameweek plan; ADR-070, labelled "AI Tips" per US-226) ---------------------
def render_ai_tips(squad_name, squad, *, horizon=5):
    """A grounded gameweek recommendation for the picked squad — captain · lineup · a transfer · flags.

    Shown under the **AI Tips** tab. Routes through `ask.answer` (analytics decide, the LLM narrates,
    every figure/name checked, ADR-037), reusing the session squad. `horizon` (ADR-077) sets the
    lineup/transfer window; the captain is always next-GW. Degrades without Ollama. No server writes.
    """
    st.caption("Your whole week in one view — who to **captain**, any **lineup** change, one **transfer** "
               "to consider, and any **flagged** players. The analytics decide; the answer is checked "
               "against the data (✓/⚠).")
    result = ask.answer(f"what should I do this week for {squad_name}?", active_squad=squad, horizon=horizon)
    st.code(render_ask(result, ollama_hint=False), language=None)   # US-375: no "Start Ollama" hint for web users


# ---- Chips (a grounded chip-strategy advisor; ADR-082) ----------------------------------------------
def render_chips(squad_name, squad, *, horizon=5):
    """A grounded chip-strategy recommendation for the picked squad — when to play each chip.

    Shown under the **Chips** tab. Routes through `ask.answer` (analytics decide, the LLM narrates, every
    figure/name checked, ADR-037), reusing the session squad. `horizon` (ADR-077) sets the window it looks
    over. Fixture-run + xP based — double/blank gameweeks and mini-league position sharpen it in-season.
    Degrades without Ollama. No server writes.
    """
    st.caption("When to play each chip — **Triple Captain · Bench Boost · Free Hit · Wildcard** — from your "
               "squad's projected points over the selected horizon. The analytics decide; the answer is "
               "checked against the data (✓/⚠). Double/blank gameweeks and mini-league position sharpen this "
               "in-season (live from GW1).")
    result = ask.answer(f"which chip should I use for {squad_name}?", active_squad=squad, horizon=horizon)
    st.code(render_ask(result, ollama_hint=False), language=None)   # US-375: no "Start Ollama" hint for web users
