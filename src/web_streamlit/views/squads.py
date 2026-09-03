"""Squad views (ADR-069): Build · My Squad · Health · Transfer · Captain, rendered from shared data.

Extracted from the old separate pages — **same behaviour, same engine, same output**. The consolidated
Squads page loads data + the shared squad picker once and calls only the selected view (lazy). All reuse
the CLI analytics/renderers; every edit mutates `st.session_state` only (no server writes).
"""

import datetime
import json

import streamlit as st

from src import ask, llm
from src.analytics import (
    PRICE_DOWN,
    PRICE_UP,
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
    available_squads,
    captain_bonus,
    move_bench_sub,
    rename,
    render_your_team,
    set_active_squad,
    set_bench,
    set_captain,
    set_vice,
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

_NEW_SQUAD = "➕ Build a new squad"

# ADR-178 — how many gameweeks get their own column before the rest fold into the total.
#
# ⚠️ **Capped deliberately.** The Lab offers horizons out to 10, and ten weekly numbers would show a precision
# the model does not have — ADR-173 caught exactly that, where a longer window multiplied a suppressed rate
# instead of correcting it. Five is the point beyond which a per-week figure is a guess wearing a decimal.
_BREAKOUT_MAX = 5
_BREAKOUT_HELP = ("Total expected points over the horizon — the per-gameweek columns are its parts and sum "
                  "to it (ADR-032). An empty gameweek cell means that team has no fixture, not a projected "
                  "zero.")


def _breakout_gameweeks(ranked) -> list:
    """The gameweeks that get their own column — the window's first few (ADR-178)."""
    gws = ranked[0]["gameweeks"] if ranked and ranked[0]["gameweeks"] else []
    return list(gws)[:_BREAKOUT_MAX]


def _gw_columns(pid, by_gameweek_by_id, gws, played):
    """`{"GW3": 5.1, "GW4": None, …}` — the per-gameweek xP breakout (ADR-178).

    ⚠️ **A blank gameweek is `None`, not `0.0`, and that is the whole point of the column.** `decision_xp`
    initialises `by_gameweek` for every gameweek in the window (ADR-032), so a team with no fixture reads
    `0.0` — indistinguishable from a player projected to score nothing. `played` says which gameweeks that
    team actually has a fixture in, so the cell can be **empty**: not projected, rather than projected zero.

    This is the reason the breakout exists at all. A cumulative total reads identically whether it is
    5 · 5 · 5 or 15 · 0 · 0, and blanks and doubles are exactly what multi-week planning is about — the total
    does not merely omit them, it conceals them.
    """
    bg = by_gameweek_by_id.get(pid, {})
    return {f"GW{g}": (bg.get(g, 0.0) if g in played else None) for g in gws}


def _fixture_gameweeks(upcoming, gws) -> dict:
    """`{team short_name: {gameweek, …}}` — which of `gws` each team actually plays in."""
    # ⚠️ Keyed by `home`/`away` — the **short names** — not `team_h`/`team_a`, which are FPL's numeric ids.
    # Reading the ids and looking them up by short name returned an empty set for every team, i.e. "nobody
    # plays", which would have blanked the entire breakout while looking like a real answer.
    out = {}
    for f in upcoming or []:
        event = f["event"]
        if event in gws:
            for side in ("home", "away"):
                out.setdefault(f[side], set()).add(event)
    return out


# ADR-180 — the Lab's optional constraints, and their inert defaults. The expander may only hide a control
# that **cannot change the answer while untouched**; this list is what a guard checks that claim against.
LAB_CONSTRAINTS = {
    "lab_no_xmins": False, "lab_unavailable": False,
    "lab_cheap": 0, "lab_premium": 0, "lab_differential": 0,
    "lab_include": [], "lab_exclude": [], "lab_bench": [],
}


def _constraint_count() -> int:
    """How many optional constraints are actually set — so the expander can say so in its own label.

    Folding controls away is only safe if a *set* one cannot hide. Reads `session_state` rather than the
    return values, because the label has to be written **before** the widgets inside it are created.
    """
    return sum(1 for key, inert in LAB_CONSTRAINTS.items()
               if st.session_state.get(key, inert) not in (inert, None))


def render_plan(squad_name, squad, players, upcoming, history, gw_history, photos, badges, *,
                teams=None, horizon=5):
    """Plan an **existing** squad over the gameweeks ahead — the Lab's second mode (ADR-178).

    Owner: *"it is used for planning your squad for the future — should this be done in the Lab? Then the Lab
    becomes more useful."* The Lab could only ever build from nothing, which is a few-times-a-season job, so
    the page was closed the rest of the time. This is the read that makes it worth opening: your fifteen,
    priced week by week, at the long horizons the Lab has always offered.

    ⚠️ **A read, not an optimise.** Nothing here proposes a transfer. Searching a path from a squad you
    already own is ADR-132, declined on evidence — and the distinction is the whole reason this is cheap:
    the Lab *showing* your squad over ten weeks needs no new model, while the Lab *routing* you through them
    needs one nobody has justified.
    """
    by_id = {p["id"]: p for p in players}
    owned = [by_id[i] for i in squad.get("player_ids", []) if i in by_id]
    if not owned:
        st.info("That squad has no players we can resolve — rebuild it, or pick another.")
        return

    _flag_unavailable(owned)
    ranked = decision_xp(players, upcoming, history, horizon=horizon, gw_history_by_code=gw_history)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    bg = {r["id"]: r["by_gameweek"] for r in ranked}
    gws = _breakout_gameweeks(ranked)
    played = _fixture_gameweeks(upcoming, set(gws))

    bench_ids = set(squad.get("bench_ids") or [])
    xi_ids = ({p["id"] for p in owned} - bench_ids) if bench_ids else best_legal_xi(owned, xp_by_id)
    xi_players = [p for p in owned if p["id"] in xi_ids]
    bench_players = [p for p in owned if p["id"] not in xi_ids]

    cost = round(sum(p["price"] for p in owned), 1)
    st.caption(f"**{squad_name}** · £{cost:.1f}m · projected over "
               + (f"GW{gws[0]}–{gws[-1]}" if len(gws) > 1 else f"GW{gws[0]}" if gws else "the window")
               + ". Planning only — nothing here changes your squad.")

    next_opp = {t: (team_schedule(upcoming, t) or [None])[0] for t in {p["team"] for p in owned}}
    kits = shirt_url_by_id(owned, teams)
    bench_roles = {p["id"]: role for role, p in bench_order(bench_players, xp_by_id)}
    # ADR-179 — the Lab pitch carries the market glyphs and a per-gameweek line. `per_gw_by_id` is the same
    # `by_gameweek` the table below decomposes (ADR-032), trimmed to the breakout window, so the shirt and
    # the table can never disagree about a week.
    render_pitch(xi_players, bench_players, captain_id=squad.get("captain_id"),
                 vice_captain_id=squad.get("vice_captain_id"), xp_by_id=xp_by_id,
                 market=True, per_gw_by_id={p["id"]: {g: (bg.get(p["id"], {}).get(g)
                                                          if g in played.get(p["team"], set()) else None)
                                                      for g in gws} for p in owned},
                 photos=photos, next_opp=next_opp, bench_roles=bench_roles, kits=kits)

    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
        "£m": p["price"],
        **_gw_columns(p["id"], bg, gws, played.get(p["team"], set())),
        "xP": round(xp_by_id.get(p["id"], 0), 1),
        "Role": "XI" if p["id"] in xi_ids else "Bench", "Trends": " ".join(crowd_flags(p)),
        "Set": " ".join(set_piece_flags(p)),
    } for p in sorted(owned, key=lambda x: (x["id"] not in xi_ids, _ORDER.get(x["position"], 9)))],
        help={"Set": SET_PIECE_LEGEND, "xP": _BREAKOUT_HELP})


def render_build(players, upcoming, history, gw_history, photos, badges, *, teams=None, horizon=5):
    by_label = {f"{p['web_name']} · {p['team']} · £{p['price']:.1f}m": p["id"]
                for p in sorted(players, key=lambda p: (p["web_name"] or "").lower())}
    labels = list(by_label)

    def _ids(chosen):
        return [by_label[la] for la in chosen]

    # ADR-178 — the Lab starts from a **squad**, not always from nothing. Owner: *"instead of having just a
    # new squad, use the drop down that currently has 'Squad name' and select your Current Squad or a New
    # Squad (even multiple)."* The field below used only to *label the output*; the picker makes it an input,
    # which is what turns the Lab from a few-times-a-season optimiser into the place you plan from where you
    # actually are.
    #
    # ⚠️ Picking an existing squad **reads** it — it does not optimise over it. Searching a transfer path from
    # your current fifteen is ADR-132, which was declined on evidence: the best sell was the same player in
    # all six gameweeks and the market yielded one beneficial move, a tree with one branch. That line holds.
    _saved = available_squads()
    # ⚠ Labelled **"Start from"**, not "Squad". The page already carries a picker labelled "Squad" (the shared
    # `squad_picker`, ADR-054), and two identically-labelled dropdowns stacked on one tab is ambiguous for a
    # reader and unaddressable for a test. Found by a guard that grabbed the wrong one.
    _choice = st.selectbox(
        "Start from", [_NEW_SQUAD, *_saved], key="lab_squad",
        help="Plan a squad you already own over the gameweeks ahead, or build a new one from scratch.")
    if _choice != _NEW_SQUAD:
        render_plan(_choice, _saved[_choice], players, upcoming, history, gw_history, photos, badges,
                    teams=teams, horizon=horizon)
        return

    c1, c2, c3 = st.columns(3)
    budget = c1.slider("Budget (£m)", 80.0, 100.0, 100.0, step=0.5,
                       help="The most you'll spend across all 15 players.")
    name = c1.text_input("Name this squad", value="My squad", max_chars=40,
                         help="A name for this squad — used in the download and as the active-squad "
                              "label.").strip() or "My squad"
    objective = c2.selectbox("Objective", ["xp", "points", "value", "xgi"],
                             help="xp = expected points (xMins-weighted); the CLI default.")
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

    # ADR-180 — the eight constraints fold away. Owner: *"lot of real estate used in Lab when new build."*
    #
    # ⚠️ **The line is not "advanced-looking", it is checkable: every one of these defaults to NO
    # constraint** (`0`, `[]`, `False`), so on the default path they provably did not affect the squad
    # rendered below them. Eight controls' worth of height above an answer they had no part in.
    #
    # The count in the label is what makes hiding them safe rather than merely tidy: a constraint that is set
    # can never be silently in force, which is the failure mode an expander invites.
    _set = _constraint_count()
    with st.expander(f"⚙ Constraints (optional){f' — {_set} set' if _set else ''}", expanded=bool(_set)):
        x1, x2 = st.columns(2)
        no_xmins = x1.checkbox("Ignore expected minutes (--no-xmins)", value=False, key="lab_no_xmins",
                               disabled=objective != "xp", help="xp objective only.")
        include_unavailable = x2.checkbox("Include injured/suspended", value=False, key="lab_unavailable",
                                          help="Also consider flagged players (off by default).")
        a1, a2, a3 = st.columns(3)
        cheap = a1.number_input("Low-cost (≤£4.5m)", min_value=0, max_value=8, value=0, key="lab_cheap",
                                help="Require at least this many budget (≤£4.5m) players.")
        premium = a2.number_input("Premium (≥£9m)", min_value=0, max_value=5, value=0, key="lab_premium",
                                  help="Require at least this many premium (≥£9m) players.")
        differential = a3.number_input("Differentials (≤5% owned)", min_value=0, max_value=5, value=0,
                                       key="lab_differential",
                                       help="Require at least this many low-owned (≤5%) picks.")
        include = _ids(st.multiselect("Must include", labels, key="lab_include",
                                      help="Force these players into the squad."))
        exclude = _ids(st.multiselect("Must exclude", labels, key="lab_exclude",
                                      help="Never pick these players."))
        declared_bench = _ids(st.multiselect("Declare bench (up to 4)", labels, key="lab_bench",
                                             help="Pins these to the bench; leave empty to auto-derive "
                                                  "the XI."))

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
    _bg = {r["id"]: r["by_gameweek"] for r in ranked}
    _gws = _breakout_gameweeks(ranked)
    _played = _fixture_gameweeks(upcoming, set(_gws))
    render_pitch(xi_players, bench_players, captain_id=None, xp_by_id=display_xp, photos=photos,
                 market=True, per_gw_by_id={p["id"]: {g: (_bg.get(p["id"], {}).get(g)
                                                          if g in _played.get(p["team"], set()) else None)
                                                      for g in _gws} for p in selected},
                 next_opp=next_opp, bench_roles=bench_roles, kits=kits)

    # ADR-178 — a score per gameweek, not one total. The Trends/Set columns keep their **words**: this is the
    # reference surface the pitch's glyphs point at, and it is why the pitch needs no market flags of its own.
    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
        "£m": p["price"],
        **_gw_columns(p["id"], _bg, _gws, _played.get(p["team"], set())),
        "xP": round(p.get("xp", 0), 1),
        "Role": "XI" if p["id"] in xi else "Bench", "Trends": " ".join(crowd_flags(p)),
        "Set": " ".join(set_piece_flags(p)),
    } for p in sorted(selected, key=lambda x: (x["id"] not in xi, _ORDER.get(x["position"], 9)))],
        help={"Set": SET_PIECE_LEGEND, "xP": _BREAKOUT_HELP})
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
            # ADR-178 — the breakout belongs here too. Found by a guard asserting *every* Lab player table
            # carries it: this one had been left cumulative, and one table quietly answering a different
            # question than the two above it is how a reader learns not to trust any of them.
            render_player_table([{
                "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
                "Pos": p["position"], "Player": p["web_name"], "Team": p["team"],
                "£m": p["price"],
                **_gw_columns(p["id"], _bg, _gws, _played.get(p["team"], set())),
                "xP": round(p.get("xp", 0), 1), "Trends": " ".join(crowd_flags(p)),
                "Set": " ".join(set_piece_flags(p)),
            } for p in sorted(xi_result["selected"], key=lambda x: _ORDER.get(x["position"], 9))],
                help={"Set": SET_PIECE_LEGEND, "xP": _BREAKOUT_HELP})
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


def render_my_squad(squad_name, squad, players, upcoming, history, gw_history, photos, *, teams=None, horizon=5,
                    this_week=None, deadline=None):
    """`this_week` (ADR-171): a zero-arg renderer dropped in **between the team banner and the xP strip** —
    the ① slot of the merged golden page. A callable rather than a flag because the answer needs `ask`, which
    this module's pitch/lineup half has no other reason to touch; passing the *rendering* in keeps the
    dependency at the page, where the composition decision is."""
    # US-423 (density): the "on the pitch — pick a player…" caption dropped (the pitch + ⚙ panel are discoverable)
    # so the pitch sits higher on mobile.
    # US-386: a brand status card so your team stands out + Save/backup is signposted. "Yours" = the shown squad is
    # your session's active squad (not a demo); "synced" = signed-in mode (the account is the store, ADR-113).
    from src.web_streamlit import auth
    _mine = active_squad()
    _is_yours = _mine is not None and (squad is _mine or squad.get("player_ids") == _mine.get("player_ids"))
    by_id = {p["id"]: p for p in players}
    owned = [by_id[i] for i in squad["player_ids"] if i in by_id]

    # ADR-175 rev — **deadline · cost on one line, above everything.** Two facts, each one short clause, were
    # taking two full-width captions with the banner wedged between them. They answer the same question ("can
    # I still act, and with what?") and the preview showed them as one line; the build drifted.
    _issues = squad_15_issues(owned)
    _cost = round(sum(p["price"] for p in owned), 1)
    _over = round(_cost - FPL_BUDGET, 1)
    _legal = (f"£{_cost:.1f}m · ✓ a legal 15" if not _issues and _over <= 0 else
              f"£{_cost:.1f}m · ✓ legal · ⚠ £{_over:.1f}m over" if not _issues else
              "⚠ not a legal 15")
    # ADR-175 rev — the horizon shares this row rather than taking one of its own. The preview overlaid it on
    # the pitch; Streamlit cannot put a live widget on top of an HTML block, and a column beside the facts it
    # qualifies is the same idea at the same cost — **one line for three things**, where the build had three.
    st.caption(f"{deadline + '  ·  ' if deadline else ''}{_legal}")
    # ADR-179 — **this page answers one question: what do I do this week.** The `GW1 | GW1–3` control that
    # ADR-175 introduced (itself a cut from 1/2/3/4/5/10) is gone at the owner's call, and the *Cumulative /
    # GW-only* switch goes with it, since that only rendered above a horizon of 1. Two controls, not one.
    #
    # Measured before agreeing (ADR-178): the GW1–3 view changes the suggested XI in **63.7%** of squads but
    # costs **0.32 xP** in the week you actually play it — an order of magnitude inside ADR-161's sd 3.51. It
    # changed the answer constantly and the outcome essentially never.
    #
    # Nothing is lost that this page still needs: the **player card** under a shirt shows 3 gameweeks anyway
    # (sized per team, so a blank leaves no hole), ADR-173's *"Longer view: +X over the next 5 GWs"* fires
    # whenever the horizon is under 5 — so at a fixed week it now fires **always** — and the multi-week read
    # lives in the Lab, which has offered 1-10 since US-374.
    horizon = 1
    if _issues:
        st.error("Not a legal 15: " + "; ".join(_issues))

    st.markdown(team_banner_html(squad, is_yours=_is_yours, synced=auth.is_configured()), unsafe_allow_html=True)
    render_your_team(squad, is_yours=_is_yours)   # US-385/386: the one Your-team panel — import · back up (ADR-113)
    # the chosen horizon is returned so the answer panels below share the window the pitch is showing
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


    if this_week is not None:      # ① the week's answer, above the pitch it is about (ADR-171)
        this_week()

    # A quick-view team summary (US-239) — reuses the horizon-aware xP + availability; display-only.
    # The projected XI is the declared XI (if a bench is set) else the best legal XI — same as Health.
    xi_ids = ({p["id"] for p in owned} - bench_ids) if bench_ids else best_legal_xi(owned, xp_by_id)

    # US-422 (ADR-121): a per-GW xP toggle — show the cumulative horizon (as today) OR just the horizon's last
    # gameweek, from the already-computed by_gameweek (ADR-032). Display-only: the XI/captain SELECTION above stays
    # cumulative; only the shown numbers + the pitch chips switch. Offered only when the horizon spans >1 GW.
    # US-422 (ADR-121) offered *Cumulative / GW-only* — it existed only to disentangle a multi-gameweek
    # horizon, and with the horizon fixed at one week the two readings are the same number (ADR-179).
    display_xp = xp_by_id
    cap_gw = next_gw
    gw_label = "next GW"

    xi_xp = sum(display_xp.get(i, 0) for i in xi_ids)
    bench_xp = sum(display_xp.get(p["id"], 0) for p in owned if p["id"] not in xi_ids)
    # Captaincy is a next-GW decision → the projected XI adds the captain's double for the shown gameweek,
    # and only when the captain is in the XI (a benched captain isn't doubled). ADR-083.
    cap_next = captain_bonus(captain_id, xi_ids, by_gameweek_by_id, cap_gw)
    projected_xi = xi_xp + cap_next
    captain_benched = captain_id is not None and captain_id not in xi_ids
    # US-449 (ADR-163) — a shared strip that WRAPS instead of slivering. US-404 previously cut this from five
    # metrics to three because it "slivered on mobile"; that shrank the symptom and left the mechanism, which
    # is why the owner hit it again on iPhone the moment two more strips shipped.
    from src.web_streamlit.components import render_stat_strip
    render_stat_strip([
        {"label": "Projected XI", "sub": gw_label, "value": f"{projected_xi:.1f} xP",
         "help": "Your starting XI's projected points over the selected horizon, plus your captain's "
                 "double for the next gameweek (the ×2 is a one-week thing)."},
        {"label": "Captain (2×)", "value": f"{cap_next * 2:.1f} xP" if cap_next else "—",
         "help": "Your captain's next-gameweek points, doubled. Captaincy is re-chosen each week, so the "
                 "bonus counts for the next GW only. Set/change one on the Captain tab."},
        {"label": "Bench", "value": f"{bench_xp:.1f} xP", "tone": "mute",
         "help": "Your bench's projected points (bench strength)."},
    ])
    # Be explicit that the ×2 is a one-week thing when a longer horizon is selected (owner steer, ADR-083).
    # The two "the ×2 is a one-week thing" captions went with the horizon (ADR-179): at a fixed next-gameweek
    # window there is no longer window for the double to be misread against.
    if captain_benched:
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
        pbits.append(f":red[{PRICE_DOWN}] " + ", ".join(falling) + " may drop")
    if rising:
        pbits.append(f":green[{PRICE_UP}] " + ", ".join(rising) + " rising")
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
    # ---- The pitch + player panel, as a FRAGMENT (ADR-165) ------------------------------------------
    # Streamlit reruns the **whole page script** on every interaction, so tapping a shirt re-executed this
    # entire view — the strip, the pitch, the panel, the DNA card — to change one selection. A fragment reruns
    # only itself, which is the one lever that actually shortens a tap. (Measured first: caching `decision_xp`
    # was the obvious fix and was wrong — 7ms of a 56ms render. See `docs/Backlog.md`.)
    #
    # **The boundary is the point.** Everything in here either *reads* the squad or *selects* within it, so a
    # partial rerun is correct. The two things that MUTATE it — Make captain, Substitute — call `st.rerun()`,
    # which defaults to `scope="app"` and so reruns the whole page: the xP strip above this fragment has to
    # change when the captain does, and a fragment cannot repaint it.
    #
    # The closure is deliberate. A fragment rerun does not re-execute the parent, so these locals hold the last
    # full run's values — right for selection (the squad has not changed) and irrelevant for mutation (which
    # forces a full rerun anyway).
    @st.fragment
    def _player_panel():
        from src.web_streamlit.tap import render_tappable_pitch
        _label = lambda p: f"{p['web_name']} · {p['team']}"      # noqa: E731 — matches the picker's option text
        _sel_now = st.session_state.get("pa_pick")
        _sel_id = next((p["id"] for p in owned if _label(p) == _sel_now), None)
        render_tappable_pitch(
            xi, bench, select_key="pa_pick", label_for=_label,
            captain_id=captain_id, vice_captain_id=squad.get("vice_captain_id"),
            xp_by_id=display_xp, photos=photos, next_opp=next_opp,
            team_names=team_names, bench_roles=bench_roles, kits=kits, selected_id=_sel_id,
            fixtures_by_id=fixtures_by_id)                      # ADR-109: per-GW row in the hover popover

        # ⚙ Player actions (ADR-108, US-365/366) — one selection drives the **full card** + **Make captain** +
        # **Substitute**, together, in one panel on the golden page (consolidates the old card picker + Substitute
        # expander + the stranded Captain-tab set control). Native selectbox+button → it works on phone/tablet, and
        # gives mobile the full card the desktop-only hover popover never could. Reuses the card renderer +
        # `set_captain` + `substitute` — no analytics change.
        from src.web_streamlit.player_card import render_player_card, render_player_compare
        # ADR-175 rev — **collapsed until wanted.** The panel is the page's biggest block (a picker, the card,
        # Boot Battle's two controls, captain, vice, substitute) and it sat fully open under every pitch,
        # pushing the answers below it. It is a *response* to picking a player, so it opens when one is
        # picked — tapping a shirt writes `pa_pick`, which is exactly that signal — and stays shut otherwise.
        # The picker inside it survives (ADR-133's rule: never lose the non-tap fallback), one click deeper.
        _picked_already = bool(st.session_state.get("pa_pick")) and st.session_state.get("pa_pick") != "—"
        _panel = st.expander("⚙ Players & lineup — card · compare · captain · substitute",
                             expanded=_picked_already)
        with _panel:
            st.subheader("⚙ Players & lineup")
            # ADR-133: name the tap only when it's actually live. The fallback is invisible by design, so this caption
            # is both the user-facing hint that the gesture exists and the signal that the component loaded.
            from src.web_streamlit.tap import available as _tap_available
            st.caption(("**Tap a shirt** on the pitch, or pick below → " if _tap_available() else "Pick a player → ")
                       + "view their card, ⚔️ Boot Battle (compare), make them captain, or substitute. "
                       + ("**Tap the pitch to close it.** " if _tap_available() else "")
                       + "Works on phone too (the pitch hover is desktop-only).")
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
                    render_player_card(picked, team_name=team_names.get(short, short),
                        photo_url=photos.get(picked["id"]),
                                       fixtures=fixtures_by_id.get(picked["id"]),   # ADR-109 per-GW row (no Total col)
                                       projected_xp=xp_by_id.get(picked["id"]))

                # ⚔️ Boot Battle (US-377/380, ADR-110/111) — compare the selected player with another
                # **same-position** player, side by side (winner-tinted). A **pool** selector (US-380): My team
                # (owned) · All players · By club. Reuses `render_player_compare`; the target's per-GW fixtures
                # build on demand (`xp_by_id` / `card_bg_by_id` cover all).
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
                                                  help="Type to search a same-position player to "
                                                       "compare side by side."))
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
                    render_player_card(picked, team_name=team_names.get(short, short),
                        photo_url=photos.get(picked["id"]),
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
                # The vice is a decision the manager makes and FPL stores, so the app should hold it too. It is
                # **display-only in xP terms** — no ×2 — because FPL promotes him only when the captain does not
                # play, and pricing a substitution that usually does not happen would inflate every projected XI.
                # Both setters call `st.rerun()`: the pitch is a fragment (ADR-165) and a fragment rerun does not
                # re-execute the parent, so without it the badge would not appear until something else redrew.
                if squad.get("vice_captain_id") == picked["id"]:
                    st.caption(f"🅥 **{picked['web_name']}** is your vice-captain — he takes the armband only if "
                               "your captain doesn't play.")
                elif picked["id"] != captain_id and st.button(f"🅥 Make {picked['web_name']} vice-captain",
                                                              key="pa_vice"):
                    set_active_squad(set_vice(squad, picked["id"]))
                    st.success(f"Vice-captain set: **{picked['web_name']} (V)** — he plays only if your captain "
                               "doesn't. No ×2.")
                    st.rerun()

                # 🔁 Substitute (US-366, ADR-108) — the selected player is one side of the swap; pick the other. Only
                # legal swaps are offered (substitute() returns no issues: GK↔GK, a swap that keeps a legal formation).
                # A benched pick brings them ON (choose the starter to drop); a starter takes them OFF (choose the bench
                # player). Reuses substitute(); folds in the old standalone expander + the _sub_prefill_for seed. The
                # static pitch card still can't hold a working button (S139), so this selection-driven
                # panel is the path.
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

                # The picker is unconditional again. ADR-135 hid it at rest (the shirt's 🔁 armed the
                # flow); that menu is
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

            # ADR-175 rev — bench order, the reorder control and ⚙ Manage live INSIDE this panel now.
            # They are lineup management, they were sitting between the pitch and the answers, and the
            # owner's preview had *nothing* in that gap.
            if bench_ordered:
                line = " · ".join(f"**{_SUB_LABEL[i]}** {p['web_name']} ({round(xp_by_id.get(p['id'], 0), 1)} xP)"
                                  for i, p in enumerate(outfield_subs))
                if gk_sub:
                    line += f" · **GK** {gk_sub['web_name']}"
                st.caption(f"🔁 **Bench order** (auto-subs): {line} — FPL brings on the first that keeps a legal XI; "
                           "the bench GK only covers your keeper.")
                # ADR-115's constraint, hit again: expanders cannot nest, so inside the players panel these are
            # flat subsections rather than a second layer of disclosure.
            st.markdown("**🔁 Reorder the bench** (auto-sub priority)")
            if True:
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
            # ADR-175 rev — the "make a transfer on the **Transfer tab above**" pointer is gone. Transfer is an
            # answer **below** this pitch now, so the sentence pointed the wrong way — and a signpost to
            # something three inches down the same screen is chrome, not help.

            # US-406 (ADR-115): the secondary edits fold into one collapsed **⚙ Manage** — flat subsections, because
            # Streamlit expanders can't nest.
            st.markdown("**⚙ Manage** — rename · set the whole bench")
            if True:
                st.markdown("**✏️ Rename**")
                new_name = st.text_input("Squad name", value=squad.get("name", "My squad"), max_chars=40,
                                         key="mng_rename",
                                         help="Rename this squad (shown in the download and as the active label).")
                if st.button("Rename", key="mng_rename_btn"):
                    set_active_squad(rename(squad, new_name))
                    st.rerun()

                st.markdown("**🪑 Set the whole bench (pick 4)**")
                st.caption("Bulk edit — re-pick all four bench players. For a single swap, use "
                           "**🔁 Substitute** above.")
                bench_labels = {f"{p['position']} {p['web_name']}": p["id"] for p in
                                sorted(owned, key=lambda x: _ORDER.get(x["position"], 9))}
                bench_default = [lab for lab, i in bench_labels.items() if i in bench_ids]
                bench_pick = st.multiselect("Bench", list(bench_labels), default=bench_default, max_selections=4,
                                            key="mng_setbench",
                                            help="Pick your 4 bench players; the other 11 are your XI.")
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

    _player_panel()

    return horizon      # ADR-175: the answer panels below share the pitch's window

# ---- Health (analyse the squad over the next 5 GW; ADR-031) ----------------------------------------

def _reported_leavers(owned) -> dict:
    """`{id: event}` for owned players the press says are leaving the league (ADR-153/155).

    Wrapped in a try/except because it is a bonus on top of the snapshot: a database built before the events
    table existed, or without a model to read headlines, must render Health exactly as it did before.
    """
    try:
        from datetime import UTC, datetime

        from src.analytics.crowd import crowd_exodus
        from src.analytics.headlines import leavers
        from src.storage import Storage
        store = Storage()
        try:
            return leavers(owned, store.headline_events_by_id(), crowd_exodus, today=datetime.now(UTC).date())
        finally:
            store.close()
    except Exception:                                    # noqa: BLE001 — never load-bearing
        return {}


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
    # ADR-155 — Health reads the same reported-departure fact as AI Tips and the Risk Monitor. It was the one
    # squad surface that didn't, so it counted a player with an agreed move as fully available.
    leaving = _reported_leavers(owned)
    analysis = analyse_squad(
        owned, xi_ids, xp_by_id, horizon=horizon,
        by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in ranked},
        gameweeks=ranked[0]["gameweeks"] if ranked else [],
        weight_by_id={r["id"]: r["minutes_weight"] for r in ranked},
        reported_out=leaving,
    )
    captain_id = squad.get("captain_id")
    # US-436 (ADR-166) — **the fingerprint leads.** The owner: *"the Squad DNA is powerful, maybe rename Health
    # to DNA. Lead with that and have the health underneath as it's less informative."* Agreed, and the tab is
    # renamed to match: what was on top was a 15-row table and a wall of monospace totals — true, but it is the
    # *working* rather than the *reading*. Nothing here is recomputed; the order changed, not the analysis.
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
    render_risk_monitor(squad_risk_rows(owned, upcoming, gw_history=gw_history, history=history), badges)
    _dna_by_id = {p["id"]: player_dna_this_or_last(p, players, _last, _name)[0] for p in owned}
    _tdna = team_dna_all(players, upcoming, gw_history=gw_history, last_rows=_last)
    render_squad_dna(squad_dna(owned, _dna_by_id, _tdna))
    # ADR-131 — what's coming, led by fixture exposure (which varies) rather than xP (which barely does).
    _ranked = decision_xp(players, upcoming, history, horizon=6, gw_history_by_code=gw_history)
    _bg = {r["id"]: r["by_gameweek"] for r in _ranked}
    render_forward_plan(forward_plan(owned, upcoming, _bg, horizon=6), len(owned))
    # ADR-145 — how much of a gameweek rides on ONE match. Sits under the forward plan because it answers the
    # same "what's coming" question one level down: the plan says which weeks are hard, this says which weeks
    # are *narrow*. Measured on the starting XI, not the 15 — a benched player scores nothing, so counting
    # them would dilute the share with points that were never at risk. Speaks only above the measured 75th
    # percentile, so most squads see nothing here most weeks, which is the point.
    from src.analytics.concentration import concentration_note, match_concentration
    _xi_ids = set(best_legal_xi(owned, {r["id"]: r["xp"] for r in _ranked}))
    _notes = [n for r in match_concentration([p for p in owned if p["id"] in _xi_ids], upcoming, _bg, horizon=6)
              if (n := concentration_note(r))]
    for _n in _notes:
        st.caption(f"🎯 {_n}")
    st.divider()
    st.divider()

    # …and the health check underneath: the 15 as a table, then the totals. Still here, still exact — just no
    # longer the first thing you meet.
    st.markdown("##### 🩺 Squad health — the 15, and the totals")
    render_player_table([{
        "photo": photos.get(p["id"], ""), "badge": badges.get(p["team"], ""),
        "Pos": p["position"], "Player": p["web_name"] + (" (C)" if p["id"] == captain_id else ""),
        "Team": p["team"], "£m": p["price"], "xP": round(xp_by_id.get(p["id"], 0), 1),
        "Role": "XI" if p["id"] in xi_ids else "Bench",
        "Trends": " ".join([*crowd_flags(p), *(["✈️ leaving"] if p["id"] in leaving else [])]),
        "Set": " ".join(set_piece_flags(p)),
    } for p in sorted(owned, key=lambda x: (x["id"] not in xi_ids, _ORDER.get(x["position"], 9)))],
        help={"Set": SET_PIECE_LEGEND,
              "Trends": "Ownership, transfer momentum, price and form — plus **✈️ leaving** when the press "
                        "reports a move out of the league (the analysis below names the outlet)."})
    st.code(render_squad_analysis(analysis, squad_name, show_xmins=True, captain_id=captain_id), language=None)

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
    # ADR-153/156 — one lookup for the whole view: it drives the ⛔ banner, the timing call and the ranking,
    # and three separate lookups is how one page ends up contradicting itself.
    leaving = _reported_leavers(owned)
    dead = replace_dead(owned, players, xp_by_id, upcoming, bench_ids=bench_ids, bank=bank,
                        horizon=horizon, today=datetime.now(UTC).date(), reported_out=leaving)
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
    _plan = suggest_transfer_plan(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, count=2,
                                  reported_out=leaving)
    _next_gw = ranked[0]["gameweeks"][0] if ranked and ranked[0]["gameweeks"] else None
    _bg = {r["id"]: r["by_gameweek"] for r in ranked}
    _delay = None
    if _plan and _next_gw is not None:
        _delay = round(_bg.get(_plan[0]["in"]["id"], {}).get(_next_gw, 0.0)
                       - _bg.get(_plan[0]["out"]["id"], {}).get(_next_gw, 0.0), 2)
    _free = st.number_input("Free transfers you hold", 0, 5, 1,
                            help="FPL gives one a week and rolls unused ones up to five.")
    # ADR-156 — the same `dead` list the ⛔ banner above is built from, so the two cannot say different things.
    _timing = transfer_timing(_plan, free=_free, next_gw_gain=_delay, horizon=horizon, dead=dead)
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
        plan = suggest_transfer_plan(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, count=count,
                                     reported_out=leaving)
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
        swaps = suggest_transfers(owned, players, xp_by_id, bench_ids=bench_ids, bank=bank, limit=5,
                                  reported_out=leaving)
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
    # ADR-179 — this used to end *"the Gameweeks ahead selector doesn't change it"*. There is no such
    # selector on this page any more, so the sentence pointed at a control the reader cannot find. The fact
    # it was making is still true and still worth saying; only the reassurance about a vanished widget went.
    st.caption("Captaincy is always the **next gameweek** — a one-week decision, re-picked every week.")
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

    # ADR-171 — **the setter lives in one place, and it is not here.** While this was its own tab the
    # duplication was invisible: the ⚙ panel had "👑 Make X captain", this tab had a selectbox and a button,
    # and AI Tips recommended a third. Merging all three onto one screen did not create the problem, it
    # revealed it. The ⚙ panel's button wins because that is where the *selection* already lives (ADR-135's
    # surviving shape) — a second control acting on the same state, six inches down the same page, is a bug
    # you can see. What is unique to this section — the ranked 15 and the grounded card — stays.
    current = squad.get("captain_id")
    if current:
        cur = next((p["web_name"] for p in owned if p["id"] == current), "?")
        st.caption(f"Your captain: **{cur} (C)** — change it on the pitch above (tap a shirt → "
                   "**👑 Make … captain**).")
    else:
        top = picks[0] if picks else None
        st.caption((f"No captain set — the pick above is **{top['web_name']}**. " if top else "No captain set. ")
                   + "Set one on the pitch above (tap a shirt → **👑 Make … captain**).")


_DEFAULT_NARRATOR = object()   # "caller said nothing" — distinct from an explicit `narrator=None`


# ---- The eager/button rule (ADR-171) ---------------------------------------------------------------

def narrator_attached() -> bool:
    """Is a language model attached to *this* deployment? Probed once per session, then remembered.

    This is the whole hinge of the merged page. `ask.answer` costs **~120 ms** with no model and **27-86 s**
    with `qwen3:8b` narrating, so "is this cheap enough to render on load?" has no fixed answer — it depends
    on the machine. ADR-166 answered it once, in a constant, from a dev box; the number went stale silently
    and cost the golden page its best section for three days.

    Cached in `session_state` rather than `st.cache_data` on purpose: the answer is a property of the running
    deployment (it cannot change mid-session), and a session-scoped cache is one that tests get a fresh copy
    of, rather than one leaking a dev machine's answer into the next assertion.
    """
    if "llm_attached" not in st.session_state:
        st.session_state["llm_attached"] = llm.reachable()
    return st.session_state["llm_attached"]


def _apply_the_transfer(result, squad, players) -> None:
    """The one action ADR-174 puts on the golden page: apply the transfer the block just recommended.

    **The page already named the move; only the doing was missing.** ADR-171 put the recommendation here and
    a manager still had to cross to another tab to act on it, having read exactly what to do.

    It applies `result.plan`'s transfer — **the object the text above was rendered from** — so the button and
    the sentence cannot disagree. Recomputing the swap here would be a second search that could legitimately
    return a different move.

    ⚠️ **This is one button, not the Transfer tab moved.** ADR-115 removed an in-page transfer expander as
    *"a real redundancy"* and that still holds: the tab owns *finding* a move — filters, the manual picker,
    multi-move plans, the watchlist — and this owns *acting on the one already named*. It is ADR-135's line
    ("the entity owns actions on things you have; the pickers own finding things you don't") applied to a
    recommendation instead of a shirt.
    """
    tr = (getattr(result, "plan", None) or {}).get("transfer")
    if not tr or not players:
        return
    out_n, in_n = tr["out"]["web_name"], tr["in"]["web_name"]
    # Name both players on the button. The block above is a wall of text on a phone, and a bare "Apply" at
    # the end of it is a control whose effect you have to scroll back up to remember.
    _apply = st.container(key="ms_week_apply")   # ADR-175 rev — a CSS hook so the primary action reads primary
    # ADR-180 — `type="primary"` rather than a hard-coded fill in `nav_css`. Streamlit paints a primary
    # button with the theme's accent, so it is purple in **both** themes and follows the one declaration in
    # config.toml; the CSS hook now only makes it full width.
    if _apply.button(f"🔄 Apply: {out_n} → {in_n}", key="ms_week_apply_btn", type="primary",
                 help="Applies this exact swap to your squad. Explore alternatives on the Transfer tab."):
        ok, issues, warning, new = apply_transfer(squad, tr["out"]["id"], tr["in"]["id"], players)
        if not ok:
            st.error("Can't apply — that would leave an illegal squad: " + "; ".join(issues))
        else:
            set_active_squad(new)
            done = f"Applied **{out_n} → {in_n}** — new cost £{new['cost']:.1f}m."
            st.warning(f"{done}  ⚠ {warning}") if warning else st.success(done)
            st.rerun()


def render_this_week(squad_name, squad, *, horizon=5, players=None):
    """① of the merged golden page — the week's answer, eager when it is cheap (ADR-171).

    **Eager when cheap, a click when a narrator is attached.** On Cloud that is 123 ms and the user simply
    gets the answer; locally it would be half a minute, so it stays a button. One rule, asked of the socket,
    rather than a per-tab guess that can go stale.
    """
    st.markdown("##### 🤖 This week")
    _result = None
    if not narrator_attached():
        # **The decision is binding, not a prediction.** Found by the ADR-171 smoke test: `narrator_attached`
        # picks the *layout*, but on its own it does nothing to stop `ask.answer` reaching for a model — so a
        # probe that guessed wrong would render eagerly AND narrate, producing the exact 49-second landing
        # this design exists to prevent. Passing `narrator=None` closes that gap: having judged the answer
        # cheap, we render the cheap answer, and the two can no longer disagree.
        _apply_the_transfer(render_ai_tips(squad_name, squad, horizon=horizon, narrator=None), squad, players)
        return
    if st.button("Work out my week →", key="ms_week",
                 help="A language model is attached to this instance, so the written answer takes ~30s."):
        st.session_state["ms_week_on"] = True
    if st.session_state.get("ms_week_on"):
        _apply_the_transfer(render_ai_tips(squad_name, squad, horizon=horizon), squad, players)
    else:
        st.caption("A language model is attached to this instance, so narrating the answer takes about "
                   "**half a minute** — which is why it is a click here and automatic on the deployed app, "
                   "where there is no model and the same answer costs a tenth of a second.")


# ---- AI Tips (a grounded gameweek plan; ADR-070, labelled "AI Tips" per US-226) ---------------------
def render_ai_tips(squad_name, squad, *, horizon=5, narrator=_DEFAULT_NARRATOR):
    """A grounded gameweek recommendation for the picked squad — captain · lineup · a transfer · flags.

    Section ① of the merged golden page (ADR-171; was the **AI Tips** tab). Routes through `ask.answer`
    (analytics decide, the LLM narrates, every figure/name checked, ADR-037), reusing the session squad.
    `horizon` (ADR-077) sets the lineup/transfer window; the captain is always next-GW. Degrades without
    Ollama. No server writes.

    `narrator=None` renders the **analytics only**, whatever is installed on the machine — used by
    `render_this_week` when it has decided to render eagerly, so that decision cannot be contradicted by a
    model it did not know about (ADR-171).
    """
    st.caption("Your whole week in one view — who to **captain**, any **lineup** change, one **transfer** "
               "to consider, and any **flagged** players. The analytics decide; the answer is checked "
               "against the data (✓/⚠).")
    _kw = {} if narrator is _DEFAULT_NARRATOR else {"narrator": narrator or (lambda *a, **k: None)}
    result = ask.answer(f"what should I do this week for {squad_name}?", active_squad=squad, horizon=horizon,
                        **_kw)
    st.code(render_ask(result, ollama_hint=False), language=None)   # US-375: no "Start Ollama" hint for web users
    return result                      # ADR-174: the caller acts on the plan this just rendered


# ---- Chips (a grounded chip-strategy advisor; ADR-082) ----------------------------------------------
def render_chips(squad_name, squad, *, upcoming=None, horizon=None):
    """A grounded chip-strategy recommendation for the picked squad — when to play each chip.

    Section ③ of the merged golden page (ADR-171; was the **Chips** half of the AI Tips tab, and a tab of its
    own before ADR-166). Routes through `ask.answer` (analytics decide, the LLM narrates, every
    figure/name checked, ADR-037), reusing the session squad. `horizon` (ADR-077) sets the window it looks
    over. Fixture-run + xP based — double/blank gameweeks and mini-league position sharpen it in-season.
    Degrades without Ollama. No server writes.
    """
    # ADR-166 — the window is **the chip's deadline**, not the tab's horizon. Chips expire at the end of each
    # half-season, so "which week should I play this?" only means something across the weeks that remain; the
    # tab defaults to 1 GW, which asked whether *this* week is good and could never answer *which* week is.
    from src.fpl_rules import chip_deadline
    gws = sorted({f["event"] for f in (upcoming or []) if f["event"] is not None})
    if horizon is None:
        horizon = max(1, chip_deadline(gws[0]) - gws[0] + 1) if gws else 5
        horizon = min(horizon, len(gws)) if gws else horizon
    _last = gws[0] + horizon - 1 if gws else None
    st.caption("When to play each chip — **Triple Captain · Bench Boost · Free Hit · Wildcard**. Looked at "
               + (f"over **GW{gws[0]}–GW{_last}**, to this set's chip deadline — a chip expires at the end of "
                  "the half-season, so the question is which of your remaining weeks is best, not whether "
                  "this one is good. " if gws else "")
               + "The analytics decide; the answer is checked against the data (✓/⚠).")
    result = ask.answer(f"which chip should I use for {squad_name}?", active_squad=squad, horizon=horizon)
    st.code(render_ask(result, ollama_hint=False), language=None)   # US-375: no "Start Ollama" hint for web users
