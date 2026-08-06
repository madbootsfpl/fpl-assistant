"""Squad views (ADR-069): Build · My Squad · Health · Transfer · Captain, rendered from shared data.

Extracted from the old separate pages — **same behaviour, same engine, same output**. The consolidated
Squads page loads data + the shared squad picker once and calls only the selected view (lazy). All reuse
the CLI analytics/renderers; every edit mutates `st.session_state` only (no server writes).
"""

import datetime
import json

import streamlit as st

from src.analytics import (
    SQUAD_15,
    WEEKLY_BENCH_WEIGHT,
    analyse_squad,
    archetype_bands,
    available_players,
    baseline_rate,
    best_legal_xi,
    captain_picks,
    crowd_flags,
    decision_xp,
    is_unavailable,
    legal_xi_issues,
    minutes_weight_from_history,
    objective_scores,
    select_squad,
    squad_15_issues,
    suggest_transfer_plan,
    suggest_transfers,
    team_schedule,
)
from src.ui.analyse import render_squad_analysis
from src.ui.captain import render_captain_picks
from src.ui.squad import render_squad
from src.ui.transfer import render_transfer_plan, render_transfers
from src.web_streamlit.pitch import render_pitch
from src.web_streamlit.squads import (
    FPL_BUDGET,
    apply_transfer,
    rename,
    set_active_squad,
    set_bench,
    set_captain,
)
from src.web_streamlit.tables import render_player_table

_ORDER = {"GK": 0, "DEF": 1, "MID": 2, "FWD": 3}
_BENCH_MAX = 4
_FORMATIONS = {"3-4-3": (3, 4, 3), "3-5-2": (3, 5, 2), "4-4-2": (4, 4, 2),
               "4-3-3": (4, 3, 3), "4-5-1": (4, 5, 1), "5-4-1": (5, 4, 1), "5-3-2": (5, 3, 2)}


# ---- Build (the full CLI `squad` options → a saveable 15; ADR-062) ---------------------------------

def render_build(players, upcoming, history, gw_history, photos, badges):
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
        ranked = decision_xp(players, upcoming, history, minutes_weighted=not no_xmins,
                             gw_history_by_code=gw_history)
        scores = {r["id"]: r["xp"] for r in ranked}
    else:
        scores = objective_scores(players, objective)
        ranked = decision_xp(players, upcoming, history, gw_history_by_code=gw_history)   # xP for display
    display_xp = {r["id"]: r["xp"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}

    forced = set(include) | set(declared_bench)
    pool = players if include_unavailable else available_players(players, keep_ids=forced)[0]
    bands = archetype_bands(cheap=cheap or None, premium=premium or None)
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

    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
        "£m": p["price"], "xP": round(p.get("xp", 0), 1),
        "Role": "XI" if p["id"] in xi else "Bench", "Trends": " ".join(crowd_flags(p)),
    } for p in sorted(selected, key=lambda x: (x["id"] not in xi, _ORDER.get(x["position"], 9)))])
    st.code(render_squad(result, budget=budget, objective=objective, full=True,
                         xi_ids=xi_ids, bench_boost=bench_boost), language=None)

    squad = {
        "player_ids": [p["id"] for p in selected],
        "player_names": [p["web_name"] for p in selected],
        "bench_ids": [p["id"] for p in selected if p["id"] not in xi],
        "cost": result["total_cost"],
        "saved_at": datetime.date.today().isoformat(),
    }
    payload = json.dumps({name: squad}, indent=2)
    dl, use = st.columns(2)
    dl.download_button("⬇︎ Download squad.json", payload, file_name="squad.json",
                       mime="application/json", use_container_width=True)
    if use.button("Use this squad →", use_container_width=True):
        set_active_squad({**squad, "name": name})
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
            render_player_table([{
                "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
                "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
                "£m": p["price"], "xP": round(p.get("xp", 0), 1), "Trends": " ".join(crowd_flags(p)),
            } for p in sorted(xi_result["selected"], key=lambda x: _ORDER.get(x["position"], 9))])
            st.caption(f"Best **{shape}** XI (display only) — the saveable build above is always a full 15.")


# ---- My Squad (view & edit the active squad; ADR-055) ----------------------------------------------

def render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos):
    st.caption("Tweak your squad here — rename · swap · bench · download. 🔧 To **build a fresh one** with "
               "the full option set, switch to **Build**.")
    by_id = {p["id"]: p for p in players}
    owned = [by_id[i] for i in squad["player_ids"] if i in by_id]
    xp_by_id = {r["id"]: r["xp"]
                for r in decision_xp(players, upcoming, history, gw_history_by_code=gw_history)}
    bench_ids = set(squad.get("bench_ids") or [])
    captain_id = squad.get("captain_id")

    issues = squad_15_issues(owned)
    cost = round(sum(p["price"] for p in owned), 1)
    if issues:
        st.error("Not a legal 15: " + "; ".join(issues))
    else:
        over = round(cost - FPL_BUDGET, 1)
        st.success(f"£{cost:.1f}m — ✓ a legal 15" if over <= 0
                   else f"£{cost:.1f}m — ✓ legal, ⚠ £{over:.1f}m over the £{FPL_BUDGET:.0f}m budget")

    next_opp = {t: (team_schedule(upcoming, t) or [None])[0] for t in {p["team"] for p in owned}}
    xi = [p for p in owned if p["id"] not in bench_ids]
    bench = [p for p in owned if p["id"] in bench_ids]
    render_pitch(xi, bench, captain_id=captain_id, xp_by_id=xp_by_id, photos=photos, next_opp=next_opp)

    st.divider()
    st.subheader("Edit")

    with st.expander("Rename"):
        new_name = st.text_input("Squad name", value=squad.get("name", "My squad"), max_chars=40,
                                 help="Rename this squad (shown in the download and as the active label).")
        if st.button("Rename"):
            set_active_squad(rename(squad, new_name))
            st.rerun()

    with st.expander("Swap a player", expanded=True):
        if owned:
            out_label = {f"{p['position']} {p['web_name']} (£{p['price']:.1f}m)": p["id"] for p in
                         sorted(owned, key=lambda x: _ORDER.get(x["position"], 9))}
            out_choice = st.selectbox("Replace", list(out_label), key="swap_out",
                                      help="The player to transfer out.")
            out_id = out_label[out_choice]
            out = by_id[out_id]
            owned_ids = {p["id"] for p in owned}
            cands = sorted((p for p in players if p["position"] == out["position"]
                            and p["id"] not in owned_ids and not is_unavailable(p)),
                           key=lambda x: xp_by_id.get(x["id"], 0), reverse=True)
            in_label = {f"{p['web_name']} · {p['team']} · £{p['price']:.1f}m · "
                        f"{round(xp_by_id.get(p['id'], 0), 1)} xP": p["id"] for p in cands}
            if in_label:
                in_choice = st.selectbox("With", list(in_label), key="swap_in",
                                         help="The same-position player to bring in (ranked by xP).")
                if st.button("Swap →"):
                    ok, swap_issues, warning, new = apply_transfer(squad, out_id, in_label[in_choice],
                                                                   players)
                    if not ok:
                        st.error("Can't swap — that would leave an illegal squad: " + "; ".join(swap_issues))
                    else:
                        set_active_squad(new)
                        msg = f"Swapped **{out['web_name']} → {by_id[in_label[in_choice]]['web_name']}**."
                        st.warning(f"{msg}  ⚠ {warning}") if warning else st.success(msg)
                        st.rerun()
            else:
                st.caption("No available replacements in that position.")

    with st.expander("Set the bench (pick 4)"):
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

def render_health(squad_name, squad, players, upcoming, history, gw_history, photos, badges):
    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    if not owned:
        st.info(f"Squad '{squad_name}' has no current players to analyse.")
        return
    ranked = decision_xp(players, upcoming, history, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    bench_ids = set(squad.get("bench_ids") or [])
    xi_ids = ({p["id"] for p in owned if p["id"] not in bench_ids} if bench_ids
              else best_legal_xi(owned, xp_by_id))
    analysis = analyse_squad(
        owned, xi_ids, xp_by_id,
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
    } for p in sorted(owned, key=lambda x: (x["id"] not in xi_ids, _ORDER.get(x["position"], 9)))])
    st.code(render_squad_analysis(analysis, squad_name, show_xmins=True, captain_id=captain_id), language=None)


# ---- Transfer (best XI-aware swaps; ADR-046) -------------------------------------------------------

def render_transfer(squad_name, squad, players, upcoming, history, gw_history, photos):
    col1, col2 = st.columns(2)
    bank = col1.slider("Bank (£m)", 0.0, 10.0, 0.0, step=0.5,
                       help="Spare money you can add on top of selling a player.")
    count = col2.slider("Transfers (a coordinated plan)", 1, 3, 1,
                        help="How many swaps to plan together (they share the bank).")

    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    if not owned:
        st.info(f"Squad '{squad_name}' has no current players to improve.")
        return
    ranked = decision_xp(players, upcoming, history, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    bench_ids = squad.get("bench_ids", [])
    if count > 1:
        plan = suggest_transfer_plan(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, count=count)
        st.code(render_transfer_plan(
            plan, squad_name, bank=bank,
            by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
            gameweeks=ranked[0]["gameweeks"] if ranked else [], show_xmins=True,
        ), language=None)
    else:
        swaps = suggest_transfers(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, limit=5)
        by_id = {p["id"]: p for p in players}
        render_player_table([{
            "out": photos.get(s["out"]["id"], ""), "Out": s["out"]["web_name"],
            "in": photos.get(s["in"]["id"], ""), "In": s["in"]["web_name"],
            "Pos": s["position"], "+xP": s["gain"],
            "In trends": " ".join(crowd_flags(by_id.get(s["in"]["id"], {}))),
        } for s in swaps])
        st.code(render_transfers(swaps, squad_name, bank=bank, show_xmins=True), language=None)

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

def render_captain(squad_name, squad, players, upcoming, history, photos, badges):
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
    } for pk in picks])
    st.caption("Captaincy risk: a **🟦 template** captain is safe (most managers own them); a "
               "**💎 differential** captain is a bigger rank swing — upside and downside.")
    st.code(render_captain_picks(picks, squad_name=squad_name, show_xmins=True), language=None)

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
