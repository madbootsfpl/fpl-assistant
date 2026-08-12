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
from src.web_streamlit import analytics, cloud_store
from src.web_streamlit.captain_card import render_captain_card
from src.web_streamlit.pitch import render_pitch
from src.web_streamlit.squads import (
    FPL_BUDGET,
    apply_transfer,
    apply_transfer_plan,
    captain_bonus,
    move_bench_sub,
    rename,
    set_active_squad,
    set_bench,
    set_captain,
    substitute,
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

def render_build(players, upcoming, history, gw_history, photos, badges, *, horizon=5):
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
    mode = c3.radio("Build mode", ["Balanced", "Weekly (playing bench)", "Bench Boost"],
                    help="Weekly maximises the XI + a cheap playing bench; Bench Boost maximises all 15.")
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

    weekly = mode == "Weekly (playing bench)"
    bench_boost = mode == "Bench Boost"
    warnings = []
    if set(include) & set(exclude):
        warnings.append("A player can't be both included and excluded.")
    if len(declared_bench) > _BENCH_MAX:
        warnings.append(f"You can declare at most {_BENCH_MAX} bench players.")
    if set(declared_bench) & set(include):
        warnings.append("A player can't be both included and benched.")
    if declared_bench and (weekly or bench_boost):
        warnings.append("Weekly / Bench Boost designate the bench themselves — clear the declared bench.")
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
    render_pitch(xi_players, bench_players, captain_id=None, xp_by_id=display_xp, photos=photos,
                 next_opp=next_opp, bench_roles=bench_roles)

    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
        "£m": p["price"], "xP": round(p.get("xp", 0), 1),
        "Role": "XI" if p["id"] in xi else "Bench", "Trends": " ".join(crowd_flags(p)),
        "Set": " ".join(set_piece_flags(p)),
    } for p in sorted(selected, key=lambda x: (x["id"] not in xi, _ORDER.get(x["position"], 9)))],
        help={"Set": SET_PIECE_LEGEND})
    st.code(render_squad(result, budget=budget, objective=objective, full=True,
                         xi_ids=xi_ids, bench_boost=bench_boost), language=None)

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

def render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos, *, teams=None, horizon=5):
    st.caption("Tweak your squad here — rename · swap · bench · download. 🔧 To **build a fresh one** with "
               "the full option set, switch to **Build**.")
    by_id = {p["id"]: p for p in players}
    owned = [by_id[i] for i in squad["player_ids"] if i in by_id]
    ranked = decision_xp(players, upcoming, history, horizon=horizon, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    team_names = {t["short_name"]: t["name"] for t in (teams or [])}   # short → friendly name (the card, US-344)
    by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}     # per-GW xP (ADR-032) for the captain
    next_gw = ranked[0]["gameweeks"][0] if ranked and ranked[0]["gameweeks"] else None
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
        st.success(f"£{cost:.1f}m — ✓ a legal 15" if over <= 0
                   else f"£{cost:.1f}m — ✓ legal, ⚠ £{over:.1f}m over the £{FPL_BUDGET:.0f}m budget")

    # A quick-view team summary (US-239) — reuses the horizon-aware xP + availability; display-only.
    # The projected XI is the declared XI (if a bench is set) else the best legal XI — same as Health.
    gw_label = "next GW" if horizon == 1 else f"{horizon} GW"
    xi_ids = ({p["id"] for p in owned} - bench_ids) if bench_ids else best_legal_xi(owned, xp_by_id)
    xi_xp = sum(xp_by_id.get(i, 0) for i in xi_ids)
    bench_xp = sum(xp_by_id.get(p["id"], 0) for p in owned if p["id"] not in xi_ids)
    # Captaincy is a next-GW decision → the projected XI adds the captain's double for the next GW only,
    # and only when the captain is in the XI (a benched captain isn't doubled). ADR-083.
    cap_next = captain_bonus(captain_id, xi_ids, by_gameweek_by_id, next_gw)
    projected_xi = xi_xp + cap_next
    captain_benched = captain_id is not None and captain_id not in xi_ids
    unavailable = sum(1 for p in owned if is_unavailable(p))
    doubtful = sum(1 for p in owned if p["status"] == "d")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(f"Projected XI ({gw_label})", f"{projected_xi:.1f} xP",
              help="Your starting XI's projected points over the selected horizon, plus your captain's "
                   "double for the next gameweek (the ×2 is a one-week thing).")
    m2.metric("Captain (2×)", f"{cap_next * 2:.1f} xP" if cap_next else "—",
              help="Your captain's next-gameweek points, doubled. Captaincy is re-chosen each week, so the "
                   "bonus counts for the next GW only. Set/change one on the Captain tab.")
    m3.metric("Bench", f"{bench_xp:.1f} xP", help="Your bench's projected points (bench strength).")
    m4.metric("Unavailable", unavailable,
              help="Owned players injured / suspended / unavailable (🚑 / 🚫 / ⛔).")
    m5.metric("Doubtful", doubtful, help="Owned players flagged doubtful (❓).")
    # Be explicit that the ×2 is a one-week thing when a longer horizon is selected (owner steer, ADR-083).
    cap_name = by_id[captain_id]["web_name"] if captain_id in by_id else None
    if cap_next and horizon > 1:
        st.caption(f"⚡ Captain **{cap_name}** is doubled for the **next gameweek only** (+{cap_next:.1f} xP); "
                   f"the other {horizon - 1} GW count once — captaincy is re-picked each week.")
    elif captain_benched:
        st.caption("⚡ Your captain is on the **bench** — not doubled in the projected XI (FPL would auto-sub "
                   "to your vice).")

    # Who's flagged (US-240) — name them with their flag (❓ carries the chance%), else all-clear.
    flagged = [(p, availability_flag(p)) for p in owned if availability_flag(p)]
    if flagged:
        st.caption("⚠ Flagged: " + " · ".join(f"{p['web_name']} {flag}" for p, flag in flagged)
                   + " — see the **News** tab for detail.")
    else:
        st.caption("✓ All 15 available.")

    # Price timing (US-286, ADR-092) — flag owned players under buying/selling pressure, to time transfers.
    falling = [p["web_name"] for p in owned if price_prediction(p) == "fall"]
    rising = [p["web_name"] for p in owned if price_prediction(p) == "rise"]
    if falling or rising:
        bits = []
        if falling:
            bits.append("🔻 may **drop** (sell before the change to keep value): " + ", ".join(falling))
        if rising:
            bits.append("🔺 **rising** (hold, or buy now): " + ", ".join(rising))
        st.caption(" · ".join(bits) + " — directional pressure from net transfers, not exact timing.")
    else:
        st.caption("💷 No price moves flagged (net transfers are flat preseason — live from GW1).")

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
    render_pitch(xi, bench, captain_id=captain_id, xp_by_id=xp_by_id, photos=photos, next_opp=next_opp,
                 team_names=team_names, bench_roles=bench_roles)

    # US-344: pick a player → their **full** card (the all-device path; on desktop, hovering a kit shows a
    # compact card). Reuses the card renderer with the squad's data (fixtures from `upcoming`, our xP).
    from src.web_streamlit.player_card import render_player_card
    owned_by_label = {f"{p['web_name']} · {p['team']}": p for p in owned}
    picked = owned_by_label.get(st.selectbox("👤 View your player's card", ["—", *owned_by_label],
                                             help="Or hover a shirt on the pitch (desktop)."))
    if picked:
        short = picked["team"]
        fx = [{"opp": (f["away"] if f["home"] == short else f["home"]),
               "home": f["home"] == short,
               "fdr": f["team_h_difficulty"] if f["home"] == short else f["team_a_difficulty"]}
              for f in upcoming if short in (f["home"], f["away"])][:3]
        render_player_card(picked, team_name=team_names.get(short, short), photo_url=photos.get(picked["id"]),
                           fixtures=fx, projected_xp=xp_by_id.get(picked["id"]))

    # US-352: the card picker **seeds** the substitution — picking a *starter* pre-fills "Bring off" (edge-
    # triggered on `_sub_prefill_for`, so it seeds once per pick and you can still change Bring off freely);
    # picking a *bench* player shows a hint (they're a bring-*on*, not a bring-off).
    picked_id = picked["id"] if picked else None
    if picked_id != st.session_state.get("_sub_prefill_for"):
        st.session_state["_sub_prefill_for"] = picked_id
        if picked_id is not None and picked_id not in bench_ids:      # a starter → seed Bring off
            st.session_state["sub_off"] = f"{picked['position']} {picked['web_name']}"

    # US-351: a direct **substitution** near the pitch — bring a starter OFF (to the bench) and a bench player
    # ON (into the XI). Reuses `substitute` (set_bench + legal_xi_issues); only legal swaps are offered (GK↔GK;
    # a swap that keeps a legal formation). The static pitch card can't hold a working button (S139 — HTML in a
    # markdown block can't call back to Python), so this is the widget equivalent. "Set the bench (pick 4)" (in
    # Edit, below) stays as the bulk path.
    if xi and bench:
        with st.expander("🔁 Substitute — swap a starter with a bench player", expanded=True):
            if picked and picked["id"] in bench_ids:                 # US-352: a benched pick is a bring-*on*
                st.caption(f"👆 **{picked['web_name']}** is on your bench — pick a starter to **bring off**, "
                           f"then choose **{picked['web_name']}** under *Bring on*.")
            off_label = {f"{p['position']} {p['web_name']}": p["id"]
                         for p in sorted(xi, key=lambda x: _ORDER.get(x["position"], 9))}
            off_choice = st.selectbox("Bring off (from your XI)", list(off_label), key="sub_off",
                                      help="The starter to move to the bench (the card picker above pre-fills this).")
            off_id = off_label[off_choice]
            # Only bench players whose swap-in keeps a legal XI (the helper returns no issues).
            legal_ons = [p for p in bench if not substitute(squad, off_id, p["id"], by_id)[1]]
            if legal_ons:
                on_label = {f"{p['position']} {p['web_name']} · {round(xp_by_id.get(p['id'], 0), 1)} xP": p["id"]
                            for p in legal_ons}
                on_choice = st.selectbox("Bring on (from your bench)", list(on_label), key="sub_on",
                                         help="The bench player to bring into your XI — only legal swaps shown.")
                if st.button("Substitute →", key="do_sub"):
                    new, sub_issues = substitute(squad, off_id, on_label[on_choice], by_id)
                    if sub_issues:      # belt-and-braces: the filter already excludes these
                        st.error("Can't substitute — that leaves an illegal XI: " + "; ".join(sub_issues))
                    else:
                        set_active_squad(new)
                        st.success(f"Subbed **{by_id[off_id]['web_name']} → "
                                   f"{by_id[on_label[on_choice]]['web_name']}** — the bench updates too.")
                        st.rerun()
            else:
                why = ("the bench GK only covers your keeper" if by_id[off_id]["position"] == "GK"
                       else "no bench player keeps a legal formation")
                st.caption(f"No legal swap for **{by_id[off_id]['web_name']}** — {why}.")

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
    st.subheader("Edit")

    with st.expander("Rename"):
        new_name = st.text_input("Squad name", value=squad.get("name", "My squad"), max_chars=40,
                                 help="Rename this squad (shown in the download and as the active label).")
        if st.button("Rename"):
            set_active_squad(rename(squad, new_name))
            st.rerun()

    # ☁ Cross-device Save/Load moved to the Squads **sidebar** (US-331) so it's visible on every sub-view — a
    # pointer here for anyone who used to find it under My Squad (only when the store is configured, ADR-094/054).
    if cloud_store.is_configured():
        st.caption("☁ **Save / Load across devices** is now in the **sidebar** (under *Your squad*).")

    with st.expander("Transfer", expanded=True):
        st.caption("🔁 **Substitute** (above) swaps your **lineup** (XI↔bench); a **Transfer** brings in a "
                   "**new** player — it sells one of your 15. Same-position only (the squad is a fixed 2/5/5/3).")
        if owned:
            # Filter which of your players to swap out by position (US-299) — a swap is same-position, so this
            # scopes the whole edit ("change my forwards" → FWD).
            pos_filter = st.segmented_control(
                "Position", ["All", "GK", "DEF", "MID", "FWD"], default="All", key="swap_pos",
                help="Filter which of your players to swap out by position.")
            # Your bank drives affordability (US-300): a swap out → in fits when in.price ≤ out.price + bank.
            bank = round(FPL_BUDGET - sum(p["price"] for p in owned), 1)
            st.caption(f"Bank: £{bank:.1f}m")
            c_aff, c_flag = st.columns(2)
            affordable_only = c_aff.checkbox(
                "Affordable only", value=False, key="swap_affordable",
                help="Hide replacements that would push you over budget (the transfer still checks on apply).")
            # US-353: opt-in — also list flagged (🚑/🚫/⛔) replacements (off by default) so you can plan around
            # or toward a returning player.
            include_flagged = c_flag.checkbox(
                "Include injured/suspended", value=False, key="swap_flagged",
                help="Also list flagged (injured/suspended/unavailable) replacements — off by default.")
            out_pool = [p for p in owned if pos_filter in (None, "All") or p["position"] == pos_filter]
            if not out_pool:
                st.caption(f"No {pos_filter} players in your squad.")
            else:
                out_label = {f"{p['position']} {p['web_name']} (£{p['price']:.1f}m)": p["id"] for p in
                             sorted(out_pool, key=lambda x: (_ORDER.get(x["position"], 9), x["web_name"]))}
                out_choice = st.selectbox("Transfer out", list(out_label), key="swap_out",
                                          help="The player to sell.")
                out_id = out_label[out_choice]
                out = by_id[out_id]
                owned_ids = {p["id"] for p in owned}
                cands = sorted((p for p in players if p["position"] == out["position"]
                                and p["id"] not in owned_ids
                                and (include_flagged or not is_unavailable(p))),
                               key=lambda x: xp_by_id.get(x["id"], 0), reverse=True)
                # US-356: the same-position list is long — let the tester narrow it by team + a max price.
                c_team, c_price = st.columns(2)
                team_filter = c_team.selectbox(
                    "Team", ["All", *sorted({p["team"] for p in cands})], key="swap_team",
                    help="Filter the bring-in list to one club.")
                cand_hi = max([p["price"] for p in cands], default=15.0)
                price_cap = c_price.slider(
                    "Max price (£m)", 0.0, cand_hi, cand_hi, step=0.5, key="swap_maxprice",
                    help="Only show replacements at or below this price.")
                cands = [p for p in cands
                         if (team_filter in (None, "All") or p["team"] == team_filter)
                         and p["price"] <= price_cap]
                budget_in = out["price"] + bank                # the most a replacement can cost and still fit
                affordable = [p for p in cands if p["price"] <= budget_in]
                shown = affordable if affordable_only else cands
                in_label = {f"{p['web_name']} · {p['team']} · £{p['price']:.1f}m · "
                            f"{round(xp_by_id.get(p['id'], 0), 1)} xP": p["id"] for p in shown}
                if in_label:
                    in_choice = st.selectbox("Bring in", list(in_label), key="swap_in",
                                             help="The same-position player to bring in (ranked by xP).")
                    in_id = in_label[in_choice]
                    # US-353: flag the overspend **live** — the projected 15-cost after this transfer, before apply.
                    proj = round(cost - out["price"] + by_id[in_id]["price"], 1)
                    if proj > FPL_BUDGET:
                        st.warning(f"⚠ After this transfer: £{proj:.1f}m — **£{proj - FPL_BUDGET:.1f}m over** the "
                                   f"£{FPL_BUDGET:.0f}m budget (allowed — prices drift — but flagged).")
                    else:
                        st.caption(f"After this transfer: £{proj:.1f}m · bank £{FPL_BUDGET - proj:.1f}m.")
                    if st.button("Transfer →"):
                        ok, swap_issues, warning, new = apply_transfer(squad, out_id, in_id, players)
                        if not ok:
                            st.error("Can't transfer — that would leave an illegal squad: "
                                     + "; ".join(swap_issues))
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

    with st.expander("Set the whole bench at once (pick 4)"):
        st.caption("Bulk edit — re-pick all four bench players. For a single swap, use **🔁 Substitute** "
                   "(above the Edit section).")
        labels = {f"{p['position']} {p['web_name']}": p["id"] for p in
                  sorted(owned, key=lambda x: _ORDER.get(x["position"], 9))}
        default = [lab for lab, i in labels.items() if i in bench_ids]
        picked = st.multiselect("Bench", list(labels), default=default, max_selections=4,
                                help="Pick your 4 bench players; the other 11 are your starting XI.")
        if st.button("Set bench"):
            new = set_bench(squad, [labels[lab] for lab in picked])
            new_xi = [by_id[i] for i in new["player_ids"] if i not in set(new["bench_ids"]) and i in by_id]
            xi_problem = legal_xi_issues(new_xi) if len(new_xi) == 11 else ["the XI isn't 11 players"]
            set_active_squad(new)
            if xi_problem:
                st.warning("Bench set — but the XI isn't legal: " + "; ".join(xi_problem))
            else:
                st.success("Bench set.")
            st.rerun()

    st.divider()
    save = {k: v for k, v in squad.items() if k != "name"}
    save.setdefault("saved_at", datetime.date.today().isoformat())
    payload = json.dumps({squad.get("name", "My squad"): save}, indent=2)
    st.download_button("⬇︎ Download squad.json", payload, file_name="squad.json", mime="application/json")


# ---- Health (analyse the squad over the next 5 GW; ADR-031) ----------------------------------------

def render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges, *, horizon=5):
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
    if count > 1:
        plan = suggest_transfer_plan(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, count=count)
        st.code(render_transfer_plan(
            plan, squad_name, bank=bank, horizon=horizon,
            by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
            gameweeks=ranked[0]["gameweeks"] if ranked else [], show_xmins=True,
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
        st.code(render_transfers(swaps, squad_name, bank=bank, horizon=horizon, show_xmins=True),
                language=None)

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
    st.code(render_ask(result), language=None)


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
    st.code(render_ask(result), language=None)
