"""The six squad questions, answered.

⭐ **Nothing here computes football.** Every function assembles inputs, calls the engine the CLI calls, and
shapes the answer — ADR-181's rule on a new surface. A number that appears here and nowhere else is a second
implementation, and this layer exists to prevent exactly that.
"""

from datetime import UTC, datetime

from src.analytics import (
    SQUAD_15,
    analyse_squad,
    available_players,
    baseline_rate,
    bench_order,
    best_legal_xi,
    captain_picks,
    is_unavailable,
    minutes_weight_from_history,
    player_summary,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
    team_dna_all,
    team_insights,
    team_schedule,
)
from src.analytics.compare import compare_rows, stat_rows
from src.analytics.gameweek import gameweek_plan
from src.analytics.gw_form import team_form
from src.analytics.last_season import last_season_name, last_season_rows
from src.analytics.optimizer import DEFAULT_BUDGET, legal_xi_issues
from src.analytics.player_dna import player_dna as analytics_player_dna
from src.analytics.player_dna import player_insights
from src.analytics.team_dna import key_players_this_or_last
from src.analytics.transfer import replacements_for, route_to_player
from src.fpl_rules import CHIP_NAMES, chips_available
from src.kits import photo_url, shirt_url
from src.manager import fetch_manager_team
from src.service.inputs import RUN, WIDE, load, opened, reported_leavers
from src.service.requests import (
    DEFAULT_HORIZON,
    MAX_HORIZON,
    BuildRequest,
    CaptainRequest,
    ChipsRequest,
    CompareRequest,
    FeedbackRequest,
    GameweekRequest,
    MyTeamRequest,
    PlayerDnaRequest,
    PlayerRequest,
    PlayersRequest,
    ReplacementsRequest,
    RouteRequest,
    SignalsRequest,
    SquadRequest,
    TeamDnaRequest,
    TransfersRequest,
)
from src.storage import Storage
from src.ui.deadline import deadline_line


def analysis(request: SquadRequest, *, store: Storage | None = None) -> dict:
    """A squad's health over the horizon: projected XI xP, the bench, weak links, club concentration."""
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store)
    finally:
        if ours:
            store.close()

    xi_ids = ([i for i in request.player_ids if i not in set(request.bench_ids)]
              if request.bench_ids else best_legal_xi(data.owned, data.xp_by_id))
    return analyse_squad(
        data.owned, xi_ids, data.xp_by_id, horizon=request.horizon,
        by_gameweek_by_id={r["id"]: r["by_gameweek"] for r in data.ranked},
        gameweeks=data.ranked[0]["gameweeks"] if data.ranked else [],
        weight_by_id={r["id"]: r["minutes_weight"] for r in data.ranked},
        reported_out=data.leaving,
    )


def transfers(request: TransfersRequest, *, store: Storage | None = None) -> dict:
    """The best swaps for a squad — a coordinated plan when `count` > 1, a ranked menu when it is 1.

    ⭐⭐ **`window` and `horizon_xp` are passed, and that is the whole of ADR-209.** `window` tells the
    tie-break how many gameweeks `xp_by_id` covers, so the band is sized for *this* question rather than
    always for five; `horizon_xp` lets the longer view break a near-tie, which is the half that moves
    expected points. ⚠️ Omitting either is silent: the ranking still returns, and simply names a different
    player.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store)
    finally:
        if ours:
            store.close()

    common = {
        "bench_ids": request.bench_ids, "bank": request.bank, "reported_out": data.leaving,
        "window": request.horizon, "horizon_xp": data.horizon_xp,
    }
    moves = (suggest_transfer_plan(data.owned, data.players, data.xp_by_id, count=request.count, **common)
             if request.count > 1
             else suggest_transfers(data.owned, data.players, data.xp_by_id, limit=request.limit, **common))
    return {
        "horizon": request.horizon,
        # ⭐ Echoed rather than assumed. The answer depends on both, and a client that sent the wrong one
        # should be able to see that from the reply instead of from the advice being odd.
        "bank": request.bank,
        "count": request.count,
        "coordinated": request.count > 1,
        "longer_window": WIDE if data.horizon_xp else None,
        "moves": moves,
    }


def captain(request: CaptainRequest, *, store: Storage | None = None) -> dict:
    """Who to captain **this gameweek** — always next-GW, whatever horizon the client sent.

    ⚠️ **Needs the raw history, and cannot use the published board.** `captain_picks` reprices at horizon 1
    through `player_xp`; reading a stored total instead would be a second recipe for the same number, which
    is the drift ADR-041 exists to prevent. ⭐ *The cheaper path is only cheaper if it answers the same
    question.*
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store, need_history=True)
    finally:
        if ours:
            store.close()

    # ⚠️ ADR-173 — `minutes_weight` must come from the per-gameweek history, not last season's share. The web
    # captain tab was the one caller that never passed it, and the owner saw two surfaces disagree about his
    # own squad: *"different recommendations from My Squad 'what should I do this week' and captaincy."*
    picks = captain_picks(
        data.owned, data.upcoming,
        baseline_by_code={c: baseline_rate(r) for c, r in (data.history or {}).items()},
        limit=request.limit,
        minutes_weight=minutes_weight_from_history(data.history, data.gw_history),
        history_by_code=data.history,
    )
    # ⭐⭐ **Summarised, and the xP decomposition dropped** (ADR-227). `captain_picks` returns `player_xp`'s
    # rows, so every pick carried `rate`, `rate_source`, `ep_next`, `defcon_xp`, `clean_sheet_xp`,
    # `by_gameweek_exact` and more — the **model's working**, not the answer.
    #
    # ⚠️ That is the raw-row problem wearing different clothes: internals in the contract mean a change to
    # how xP is computed changes what a phone receives. ⭐ *If a screen ever wants "why this xP", that is an
    # explanation-shaped answer, not fields riding along on every pick.*
    #
    # ⚠️ `doubtful` is dropped too, deliberately: it is `status == "d"` said twice, and two representations
    # of one fact are two things that can disagree.
    by_id = {p["id"]: p for p in data.owned}
    shaped = [
        {**player_summary(by_id[pick["id"]], {pick["id"]: pick.get("xp", 0)},
                          reported_out=data.leaving),
         "opponent": pick.get("opponent"),
         "venue": pick.get("venue"),
         "difficulty": pick.get("difficulty"),
         "penalty_taker": pick.get("penalty_taker", False)}
        for pick in picks if pick["id"] in by_id
    ]
    return {"gameweek": data.ranked[0]["gameweeks"][0] if data.ranked else None, "picks": shaped}


def gameweek(request: GameweekRequest, *, store: Storage | None = None) -> dict:
    """This gameweek's whole plan: captain · lineup · transfers · timing · flags (ADR-070/191)."""
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store, need_history=True, need_events=True)
    finally:
        if ours:
            store.close()

    from src.analytics.crowd import exodus_detector

    plan = gameweek_plan(
        data.owned, data.players, data.upcoming, data.xp_by_id,
        baseline_by_code={c: baseline_rate(r) for c, r in (data.history or {}).items()},
        minutes_weight=minutes_weight_from_history(data.history, data.gw_history),
        history_by_code=data.history,
        bench_ids=request.bench_ids,
        bank=request.bank,
        horizon=request.horizon,
        events_by_id=data.events,
        horizon_xp=data.horizon_xp,
        # ⚠️ ADR-210 — bound to the whole board, never the fifteen the plan is about.
        exodus_for=exodus_detector(data.players),
        free=request.free,
    )
    plan["horizon_gw"] = WIDE
    # ⚠️⚠️ **ADR-227 normalised the captain ENDPOINT and missed the captain INSIDE the plan.** Both come
    # from `captain_picks`, so both carried the xP model's working — `rate`, `ep_next`, `defcon_xp` — and
    # the claim "one shape everywhere" was true of five surfaces out of seven.
    #
    # ⭐ *The sweep only saw what it was pointed at*, and this endpoint was not in its fixture. That is the
    # finding, more than the fields: `tests/test_player_shape.py` now asserts its own completeness.
    by_id = {p["id"]: p for p in data.owned}

    def shaped(pick):
        if not pick or pick.get("id") not in by_id:
            return pick
        return {**player_summary(by_id[pick["id"]], {pick["id"]: pick.get("xp", 0)},
                                 reported_out=data.leaving),
                "opponent": pick.get("opponent"),
                "venue": pick.get("venue"),
                "difficulty": pick.get("difficulty"),
                "penalty_taker": pick.get("penalty_taker", False)}

    plan["captain"] = shaped(plan.get("captain"))
    plan["captain_ranked"] = [shaped(p) for p in (plan.get("captain_ranked") or [])]

    # ⚠️ The lineup hands back the squad's own rows — so `start`, `bench`, `bring_in` and `drop` were four
    # more raw shapes. ⭐ No fixture extras here: a lineup entry is a *player*, not a pick, and adding
    # `opponent` to it would invent a distinction the answer does not make.
    def summarise(p):
        return (player_summary(by_id[p["id"]], data.xp_by_id, reported_out=data.leaving)
                if p.get("id") in by_id else p)

    lineup = plan.get("lineup") or {}
    for key in ("start", "bench", "bring_in", "drop"):
        if isinstance(lineup.get(key), list):
            lineup[key] = [summarise(p) for p in lineup[key]]
    # ⭐⭐ **The explanation ships WITH the plan, not beside it** (ADR-089/224). The owner, on seeing the
    # phone's bare version: *"I was more thinking of capturing this"* — and pasted the web app's full
    # Confidence · Edge · Risk block. ⚠️ A recommendation without its reasoning is a different product:
    # ADR-182's mantra is *"Analytics decide. Logic explains. You make the call"*, and a screen that shows
    # only the first clause has quietly dropped the other two.
    #
    # ⭐ Returned as one key rather than merged into the plan, so a caller that only wants the decision can
    # still ignore it — and so nothing here can be mistaken for a number the engine computed.
    plan["explanation"] = _explained(plan, data, request.horizon)
    return plan


def _explained(plan: dict, data, horizon: int) -> dict | None:
    """`explain_gameweek`'s output, flattened to plain dicts a client can read.

    ⚠️ **Never load-bearing.** The explanation is a reading of a decision already made; if it cannot be
    produced the plan is still the plan, and a screen that failed entirely because a sentence could not be
    built would be letting the commentary take down the match.
    """
    try:
        from dataclasses import asdict

        from src.analytics.explain import explain_gameweek

        xp_by_id = {r["id"]: r["xp"] for r in data.ranked}
        found = explain_gameweek(plan, {p["id"]: p for p in data.players}, xp_by_id, horizon=horizon)
        if not found:
            return None
        return {
            key: (asdict(value) if hasattr(value, "__dataclass_fields__") else value)
            for key, value in found.items()
        }
    except Exception:                                    # noqa: BLE001 — commentary, never the decision
        return None


def route(request: RouteRequest, *, store: Storage | None = None) -> dict:
    """*"What would it take to field X?"* — every legal one-transfer route to owning the target (ADR-207).

    ⭐ **A blocked route is information, not an absence.** *"Short by £0.6m"* answers the question; an empty
    list looks like the question was not understood.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store)
        # ⚠️ Checked here rather than by appending the target to the squad's ids — ⭐ *that reading made an
        # already-owned target look like a sixteenth player*, and `route_to_player`'s "you already own him"
        # answer disappeared. It also priced the departure lookup over sixteen players instead of fifteen.
        if request.target_id not in data.by_id:
            raise ValueError(f"unknown player ids: [{request.target_id}]")
        target = data.by_id[request.target_id]
    finally:
        if ours:
            store.close()

    # ⚠️ `reported_out` is passed here and the CLI never did — it re-ranks the sale candidates, so leaving it
    # out would route a manager *through* a player the rest of the app knows is going (ADR-155's species).
    answer = route_to_player(target, data.owned, data.xp_by_id, bank=request.bank,
                             reported_out=data.leaving)
    return {
        "horizon": request.horizon,
        "target": player_summary(target, data.xp_by_id, reported_out=data.leaving),
        **answer,
    }


def build(request: BuildRequest, *, store: Storage | None = None) -> dict:
    """The best legal fifteen within a budget (ADR-013/043) — the wildcard question."""
    request.validate()
    store, ours = opened(store)
    try:
        # ⭐ No squad to resolve, so nothing is owned — but the include/exclude ids are still real players
        # and get the same "named, not dropped" treatment as a squad's.
        data = load([*request.include_ids, *request.exclude_ids], request.horizon, store)
    finally:
        if ours:
            store.close()

    # ⚠️ Forced-in players stay in the pool even when unavailable — that is the manager's call, not ours.
    pool, excluded = available_players(data.players, keep_ids=request.include_ids)
    result = select_squad(
        pool, budget=request.budget, formation=SQUAD_15, scores=data.xp_by_id,
        include_ids=request.include_ids, exclude_ids=request.exclude_ids,
    )
    # ⭐⭐ **Summarised, not the raw solver output** (ADR-227). `select_squad` returns the database rows it
    # was given, so this endpoint was shipping **45 columns per player** — `cbi`, `cost_change_event`,
    # `scout_news_link` — 12 KB where 3 will do, on the client whose architecture was justified by
    # measuring payload. ⚠️ It also made the database schema part of the API contract: rename a column and
    # the mobile response changes, with nothing in between to notice.
    #
    # ⭐ `bench` and `forced` survive because they are **answers, not raw data**: the solver decided one and
    # the caller asked for the other, and neither exists on a player row.
    selected = [
        {**player_summary(p, data.xp_by_id),
         "bench": bool(p.get("bench")),
         "forced": bool(p.get("forced"))}
        for p in result["selected"]
    ]
    return {
        "horizon": request.horizon,
        "budget": request.budget,
        # ⭐ The solver's own word, surfaced. "Infeasible" is an answer — *nothing fits these constraints* —
        # and swallowing it would leave a client showing an empty squad with no reason.
        "status": result["status"],
        "selected": selected,
        "total_cost": result["total_cost"],
        "projected_xp": round(sum(data.xp_by_id.get(p["id"], 0) for p in result["selected"]), 1),
        "unavailable_excluded": len(excluded),
        "default_budget": DEFAULT_BUDGET,
    }


def _deadline_parts(at, now) -> tuple[str, str]:
    """The deadline as two short facts: when it is, and how long is left.

    ⭐ Reuses the web's own formatters so the phone cannot disagree with the banner about the same moment —
    ⚠️ *two renderings of one timestamp is how a countdown and a date drift by an hour across a DST
    boundary.*
    """
    from src.ui.deadline import _UK, _countdown

    return at.astimezone(_UK).strftime("%a %-d %b, %H:%M"), _countdown(at - now)


def _data_freshness(store) -> dict:
    """How old this data is, and whether a finished gameweek is missing from it (ADR-248).

    ⭐⭐⭐ **The app had no way to say how old its numbers were, so a stale board looked like a wrong
    engine.** The owner checked a player's last five, saw a blank against Coventry and no Arsenal game at
    all, and reasonably asked why the app was not reflecting reality. It was reflecting reality — *a
    reality from the previous afternoon.*

    ⚠️ **`refreshed_at` alone is not the answer.** "Updated 20 hours ago" is fine on a Tuesday and useless
    the evening a gameweek finishes. What matters is whether a **completed gameweek is missing**, which is
    exactly what `backfill_due` already computes — ⭐ *so this asks the pipeline's own question rather than
    inventing a second definition of "behind".*
    """
    from src.pipeline import backfill_due

    # ⚠️ `backfilled_at` is deliberately NOT returned. It was, briefly — and it made the contract sample
    # unstable, because it is a string in a backfilled database and null in the committed test fixture.
    # ⭐ *A field nobody reads is a field that can only cause drift*, and the client answers "is the board
    # behind?" from `behind`, which is computed rather than stamped.
    status = dict(store.data_status() or {})
    try:
        behind, why, rounds = backfill_due(store.get_all_fixtures(), store.get_gw_history_by_code())
    except Exception:  # pragma: no cover - a freshness check must never take a screen down
        behind, why, rounds = False, "could not be checked", set()

    return {
        "refreshed_at": status.get("refreshed_at"),
        # ⭐ The rounds, not just a flag: *"missing GW5"* is a fact someone can act on; *"stale"* is a mood.
        "missing_gameweeks": sorted(rounds),
        "behind": bool(behind),
        "why": why,
    }


def _legal_swaps(owned, bench_ids) -> list[dict]:
    """Who each player can legally change places with (ADR-246).

    ⭐⭐⭐ **The rule stays on this side.** FPL's formation limits — one keeper, 3–5 defenders, 2–5
    midfielders, 1–3 forwards — already live in `XI_FLEX` and are enforced by `legal_xi_issues`. Working
    them out again in Dart would be *a second implementation of a rule the engine already owns*, and this
    project has a whole run of ADRs (151→156) about one fact being re-taught to six surfaces one at a time.

    ⚠️ **Keepers are the case that catches people**: a GK can only ever change places with the other GK, so
    a client that offered "any bench player" would propose squads FPL rejects.

    ⭐ Computed by **trying** each swap rather than by reasoning about it: eleven-ish candidates per player
    and a list-length check is cheap, and a derived rule is the thing that drifts. *Ask the validator; do
    not re-derive what it knows.*
    """
    declared = set(bench_ids or [])
    if not declared:
        return []
    starters = [p for p in owned if p["id"] not in declared]
    bench = [p for p in owned if p["id"] in declared]

    out = []
    for player in owned:
        on_bench = player["id"] in declared
        others = starters if on_bench else bench
        legal = []
        for other in others:
            # ⚠️⚠️ **Whichever of the two is currently STARTING comes out; the other goes in.** The first
            # version removed the wrong one and built a **twelve-man XI** — and `legal_xi_issues` checks
            # position ranges, not the size of the list, so it validated happily. The visible result was a
            # keeper offered a swap with a forward. ⭐ *A validator answers the question it was asked, and
            # "is this eleven legal" was never asked.*
            #
            # ⚠️ A `len(after) == 11` guard was added here after that bug and then **removed**: with the
            # line above correct, one out and one in makes eleven by construction, so the check could not
            # fire — a mutation proved it. ⭐ *An unreachable guard is not defence in depth, it is a
            # comment that looks like code.* The size is asserted in `test_legal_swaps.py`, where it can.
            starting, coming = (other, player) if on_bench else (player, other)
            after = [p for p in starters if p["id"] != starting["id"]] + [coming]
            if not legal_xi_issues(after):
                legal.append(other["id"])
        out.append({"id": player["id"], "benched": on_bench, "with": legal})
    return out


def _suggested_lineup(owned, declared_bench_ids, xp_by_id, leaving) -> dict | None:
    """The best legal XI you could field **from the players you already own** (ADR-244).

    ⭐⭐ **The pitch could already tell you the lineup was wrong and gave you no way to fix it.** This Week
    said *"3 changes"* and named them; acting on it meant reading three lines, remembering them, and
    tapping four shirts on another screen. ⭐ *An app that can compute the answer and makes you transcribe
    it has stopped halfway.*

    ⚠️ **Lineup only — never transfers.** Starting a player you own is free and reversible; a transfer
    costs points and cannot be taken back. One button must not do both, whatever the xP says.

    ⭐ Reuses `best_legal_xi` on the same `lineup_xp` convention as `gameweek_plan`: ADR-154's rule that a
    player reported to be leaving is ranked as if he scores nothing **for selection only**. ⚠️ Deriving a
    second, subtly different optimum here is how two screens start recommending different teams.

    Returns None when there is nothing to do — ⭐ *the absence of a suggestion is the answer "your lineup is
    already the best one", and a strip that said so on every visit would be noise.*
    """
    lineup_xp = dict(xp_by_id)
    for pid in leaving or []:
        lineup_xp[pid] = 0.0

    optimal = best_legal_xi(owned, lineup_xp)
    declared = set(declared_bench_ids or [])
    declared_xi = {p["id"] for p in owned if p["id"] not in declared} if declared else set(optimal)
    if not declared or set(optimal) == declared_xi:
        return None

    by_id = {p["id"]: p for p in owned}
    benched = [by_id[i] for i in by_id if i not in optimal]
    # ⭐ The bench in the order FPL will actually substitute, so applying the plan does not silently
    # reorder it into something the auto-sub would disagree with.
    ordered = [pid for _, pid in
               ((role, p["id"]) for role, p in bench_order(benched, lineup_xp))] if benched else []

    # ⚠️ Scored on the REAL xP, not `lineup_xp`. The zeroing above is a selection device; quoting a gain
    # computed from it would credit the manager with points a fiction created.
    def total(ids):
        return sum(xp_by_id.get(i) or 0 for i in ids)

    return {
        "start": [i for i in optimal],
        "bench": ordered,
        "bring_in": sorted(set(optimal) - declared_xi),
        "drop": sorted(declared_xi - set(optimal)),
        "gain": round(total(optimal) - total(declared_xi), 1),
    }


def _recent_rows(rows, club_by_id) -> list[dict]:
    """The last few appearances — points, minutes, **and who it was against** (ADR-242).

    ⭐⭐ **"Last 5 should maybe indicate who they played"** (tester feedback item 5), and the data was
    already in the row: `player_history` has stored `opponent_team` and `was_home` since ADR-201. A run of
    bare numbers cannot distinguish a quiet week from a hard one — ⚠️ *two blanks against City and Arsenal
    say something completely different from two blanks against the bottom two, and the column that made
    them different was being dropped on the way out.*

    ⚠️ `opponent` is **null, never a guess**, when the club id is unknown — an away trip to "???" is worse
    than an away trip to nothing.
    """
    out = []
    for r in rows:
        row = dict(r)
        out.append({
            "gameweek": row.get("round"),
            "points": row.get("total_points"),
            "minutes": row.get("minutes"),
            "opponent": club_by_id.get(row.get("opponent_team")),
            "home": bool(row.get("was_home")),
        })
    return out


def my_team(request: MyTeamRequest, *, store: Storage | None = None) -> dict:
    """Everything the **My Team** pitch draws, in one call.

    ⭐⭐ **A composition, not a new answer.** It calls `fetch_manager_team`, `analysis`, `team_schedule`,
    `bench_order`, `shirt_url_by_id` and `deadline_line` — every one of them already shipping. Nothing here
    computes football, which is the rule this layer exists to keep.

    ⚠️ **Why it is one endpoint rather than five.** The pitch needs ten things `analysis` does not return —
    the gameweek, the deadline, the armbands, the bank, the kit, the opponent, the venue, the difficulty and
    the bench order. On a phone that is five round trips before anything renders, on the client whose whole
    architecture was justified by measuring payload (spike 017). ⭐ *A screen-shaped endpoint is a real cost
    — it couples the API to a layout — and it is the smaller one here.*

    ⭐ **Every map is keyed by something that is naturally a string**, so JSON changes nothing on the way
    out: kits and fixtures by club short name, bench roles by role. The alternative — keying by player id —
    would repeat `by_gameweek`'s trap, where `"10"` sorts before `"6"` and a client silently misreads it.
    """
    request.validate()
    store, ours = opened(store)
    try:
        players = store.get_players()
        squad, message = fetch_manager_team(request.manager_id, players)
        if squad is None:
            # ⭐ The FPL client's own words, passed through. It distinguishes a bad id from an unreachable
            # API from a team that is not public yet, and a client cannot tell those apart from a 400 alone.
            raise ValueError(message)

        fpl_ids = list(squad["player_ids"])
        # ⭐⭐ **The draft replaces the fifteen and nothing else.** Name, bank, deadline and armbands still
        # come from FPL — a draft that invented its own bank would let a manager plan a move he cannot pay
        # for, and one that invented its own deadline would price the wrong gameweek.
        drafting = bool(request.draft_player_ids)
        owned_ids = list(request.draft_player_ids) if drafting else fpl_ids
        bench_ids = (list(request.draft_bench_ids) if drafting
                     else list(squad.get("bench_ids") or []))
        answer = analysis(SquadRequest(player_ids=owned_ids, bench_ids=bench_ids,
                                       horizon=request.horizon), store=store)

        # ⚠️⚠️ **The run card had three fixtures and one number** (ADR-242). ADR-235's premise is *one
        # fetch, three readings* — and the third reading shipped without its data: `horizon` is 1 because
        # the headline is a **this-week** projection, so `by_gameweek` carried a single gameweek while the
        # card drew three columns. Two of them always read "—".
        #
        # ⭐ Answered with a second pass rather than by raising `horizon`, because raising it changes the
        # headline: the owner's `projected_xp` goes 44.9 → 133.9, which is a three-week total wearing a
        # one-week label. *A fix that corrupts the number beside it is not a fix.*
        #
        # ⭐ Skipped entirely when the caller already asked for a wide enough window — the common case for
        # every other consumer.
        if request.horizon >= RUN:
            run_answer = answer
        else:
            run_answer = analysis(SquadRequest(player_ids=owned_ids, bench_ids=bench_ids,
                                               horizon=RUN), store=store)
        run_xp = [{"id": p["id"], "by_gameweek": p["by_gameweek"]}
                  for p in run_answer["xi"] + run_answer["bench"]]

        owned = [p for p in players if p["id"] in set(owned_ids)]
        teams = store.get_teams()
        upcoming = store.get_upcoming_fixtures()
        code_by_club = {t["short_name"]: t["code"] for t in teams}
        # ⚠️ Clubs come from the squad being **shown**, so a drafted-in player from a new club still gets a
        # kit and a fixture. Deriving them from the FPL squad would leave the new signing shirtless.
        clubs = {p["team"] for p in owned}
        gameweek, at, label, urgency = deadline_line(upcoming, datetime.now(UTC))
        # ⭐⭐ **The parts as well as the sentence** (ADR-253). `label` is a 96-character line built for a
        # desktop banner; on a phone it wrapped to three, which is ~40pt of the screen's most valuable
        # real estate spent on a match count nobody acts on from the pitch.
        #
        # ⚠️ The sentence stays — the web renders it and it is right there. ⭐ *A client too narrow for a
        # prose line needs the facts, not a second prose line written for it* — so the phone composes its
        # own from `when` and `countdown`, and the API does not acquire a `compact=True` flag that would
        # make it responsible for someone else's layout.
        _uk_when, _left = _deadline_parts(at, datetime.now(UTC))
        # ⚠️ Inside the `try`, because it needs the store — and ⚠️ the **whole board**, not the squad:
        # ADR-210's exodus threshold is the worst tenth of the live distribution, and a tenth of fifteen
        # flags somebody every week.
        leaving = reported_leavers(owned, players, store)
        freshness = _data_freshness(store)
        # ⚠️ ~50ms over fifteen players, measured — cheap enough to fold into the screen everyone opens,
        # and it saves the round trip that had this feature parked since ADR-228.
        signal_keys = [s["key"] for s in signals(
            SignalsRequest(player_ids=owned_ids, horizon=1), store=store)["signals"]]
    finally:
        if ours:
            store.close()

    by_id = {p["id"]: p for p in owned}
    # ⚠️ Keyed by club and not by player — eleven entries instead of fifteen, and the client picks the
    # keeper variant by position, which is the same derivation the web pitch already makes.
    kit_by_club = {
        club: {"outfield": shirt_url(code_by_club.get(club)),
               "gk": shirt_url(code_by_club.get(club), "GK")}
        for club in clubs
    }

    # ⭐⭐ **Three fixtures, not one** (ADR-235). The card used to carry the next opponent; a manager
    # deciding whether to hold a player is asking about his **run**, not his Saturday — which is why the
    # Hub shows three and why ours looked thin beside it.
    #
    # ⚠️ Still a list per **club**, so it stays keyed by something JSON leaves alone, and three clubs
    # sharing a fixture do not each carry a copy.
    fixtures = {
        club: [
            {"gameweek": cell.get("event"), "opponent": cell["opponent"],
             "venue": cell["venue"], "difficulty": cell.get("difficulty")}
            for cell in (team_schedule(upcoming, club) or [])[:RUN]
        ]
        for club in clubs
    }

    # ⭐ **Direction only, and the evidence for it.** `price_detector` answers rise/fall/stable against a
    # live percentile (ADR-215). It does **not** answer *when*, and the Hub's "Tonight / >1 Week / 0.6%" is
    # a progress-to-threshold estimate we do not compute — ⚠️ *inventing one would be a number that looks
    # authoritative and is not*. So the card carries the call **and the net transfers behind it**, which is
    # a fact rather than a forecast.
    from src.analytics import price_detector

    predict = price_detector(players)
    prices = {}
    for p in owned:
        row = dict(p)
        prices[p["id"]] = {
            "direction": predict(p),
            "net_transfers": (row.get("transfers_in_event") or 0) - (row.get("transfers_out_event") or 0),
            "changed_this_gameweek": round((row.get("cost_change_event") or 0) / 10, 1),
        }

    xp_by_id = {p["id"]: p["xp"] for p in answer["xi"] + answer["bench"]}
    suggested = _suggested_lineup(owned, bench_ids, xp_by_id, leaving)
    benched = [by_id[i] for i in bench_ids if i in by_id]
    # ⭐ Role → id, so the phone orders the bench the way FPL will actually substitute. Without it a client
    # invents an order, and the first auto-sub proves it wrong.
    roles = {role: p["id"] for role, p in bench_order(benched, xp_by_id)} if benched else {}

    return {
        "manager_id": request.manager_id,
        "squad": {
            "name": squad.get("name"),
            "player_ids": owned_ids,
            "bench_ids": bench_ids,
            "captain_id": squad.get("captain_id"),
            "vice_captain_id": squad.get("vice_captain_id"),
            # ⭐ FPL's own numbers, not ours. `cost` is what the fifteen price at today; `value` is what FPL
            # says the team is worth **including** the bank, which is why the two differ.
            "bank": squad.get("bank"),
            "value": squad.get("value"),
            "cost": squad.get("cost"),
            "active_chip": squad.get("active_chip"),
        },
        # ⭐⭐ **The server says whether this is the real team.** A client can forget to mention it; a field
        # cannot. ⚠️ *An app that shows a plan as your squad is lying about something you can act on* — and
        # `fpl_player_ids` is what lets a client check its saved draft against reality rather than trusting
        # that nothing moved while the app was closed.
        "draft": drafting,
        "fpl_player_ids": fpl_ids,
        # ⚠️ Echoed because FPL does not publish it and the client supplied it — ⭐ *a header that showed a
        # number the manager never set would be the app inventing his position.*
        "free_transfers": request.free_transfers,
        "gameweek": gameweek,
        # ⚠️ The label carries the timezone and the countdown already (ADR-086) — re-deriving "in 18 days"
        # on the client would be a second clock, and the two would disagree by however long the app was open.
"deadline": {"at": at.isoformat(), "label": label, "urgency": urgency,
                     # ⭐ Short enough for one line on a phone: "Sat 10 Oct, 11:00" · "in 17 days, 11h".
                     "when": _uk_when, "countdown": _left},
        "analysis": answer,
        "kits": kit_by_club,
        "fixtures": fixtures,
        # ⚠️ Keyed by player id, which JSON turns into a string — the client parses it back. Unlike kits
        # and fixtures there is no club-level answer here: two Arsenal players move in price separately.
        "prices": prices,
        # ⭐ How many fixtures each club's list holds, so a client sizes its row rather than guessing.
        "run": RUN,
        # ⭐ Null when your XI is already the best one — see `_suggested_lineup`.
        "suggested_lineup": suggested,
        # ⭐ Who each player may change places with, decided by the engine's own formation rules.
        "swaps": _legal_swaps(owned, bench_ids),
        # ⚠️ **On the screen a manager actually opens.** A freshness field on `/health` would be read by
        # monitoring and by nobody else — ⭐ *the place to say "these numbers are from yesterday" is beside
        # the numbers.*
        "data": freshness,
        # ⭐⭐⭐ **The keys, not the signals** (ADR-256). The pitch wants a badge saying *"three things you
        # have not seen"* — and the server cannot know what you have seen, because it has no idea when you
        # last looked. ⚠️ *It can say what EXISTS; only the device knows what is new*, which is ADR-232's
        # split reused rather than a second mechanism invented.
        #
        # ⭐ Keys only: three strings against a full sweep's worth of player summaries. The badge is a
        # count, and a count does not need the things it counted.
        "signal_keys": signal_keys,
        # ⭐ A **list**, not a map keyed by player id. The docstring above explains why ids never become
        # JSON keys here; a list sidesteps the question rather than arguing with it.
        "run_xp": run_xp,
        "bench_roles": roles,
    }


def replacements(request: ReplacementsRequest, *, store: Storage | None = None) -> dict:
    """Every legal replacement for one owned player — **affordable or not** (ADR-226).

    ⚠️ **Over-budget candidates are returned and flagged, never filtered.** The owner's call: *"can select a
    higher priced player, just flag it as over budget."* ⭐ That matches what `apply_transfer` has always
    done — an over-budget squad is a **soft warning, never a block**, because prices drift and a manager
    planning a move he cannot quite afford yet is planning, not erring.

    ⭐ And filtering would be worse than unhelpful: *a candidate silently removed looks like a candidate
    that does not exist*, so the manager would conclude the player is ineligible rather than dear.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store)
    finally:
        if ours:
            store.close()

    out = data.by_id[request.out_id]
    budget = round(out["price"] + request.bank, 1)
    rows = replacements_for(out, data.players, data.owned, xp_by_id=data.xp_by_id,
                            bank=request.bank, reported_out=data.leaving, limit=request.limit)
    return {
        "horizon": request.horizon,
        "out": player_summary(out, data.xp_by_id, reported_out=data.leaving),
        # ⭐ Stated so a screen can show *"£8.5m to spend"* rather than making the reader do the addition
        # of a sale price and a bank they are looking at on another row.
        "budget": budget,
        "bank": request.bank,
        "candidates": rows,
    }


def chips(request: ChipsRequest, *, store: Storage | None = None) -> dict:
    """When to play each chip, and what a wildcard is worth (ADR-082/185/229).

    ⚠️⚠️ **The window is the chip's DEADLINE, not the caller's horizon** (ADR-166). A chip expires at the
    end of each half-season, so *"is this week good?"* is the wrong question — ⭐ *the right one is "is this
    week better than the weeks I have left?"*, and it cannot be asked over a window someone picked for a
    different screen.

    ⭐ The wildcard carries what it is **worth**, not only when to play it (ADR-185). The owner found that
    gap himself, from a two-team A/B: the advisor said *"Wildcard GW5-7, your weakest stretch"* while his
    squad already overlapped an optimal rebuild by 3 of 15 — ⚠️ *a recommendation that measures only WHEN
    presents itself as an answer to WHETHER.*
    """
    request.validate()
    from src.analytics.chips import chip_advisor, rebuild_value
    from src.fpl_rules import chip_deadline

    store, ours = opened(store)
    try:
        # The first upcoming gameweek decides which half-season's expiry applies; the window runs to it.
        peek = load(request.player_ids, 1, store)
        first = peek.ranked[0]["gameweeks"][0] if peek.ranked else None
        window = max(1, (chip_deadline(first) - first + 1)) if first else DEFAULT_HORIZON
        # ⚠️ Clamped to eight, which is what the engine will price — a chip deadline twelve weeks out asks
        # for a horizon no other surface computes, and a silently different one would disagree with them.
        window = min(window, MAX_HORIZON)
        data = load(request.player_ids, window, store)
        pool, _ = available_players(data.players)
        rebuild = rebuild_value(data.owned, pool, data.xp_by_id,
                                budget=round(sum(p["price"] for p in data.owned) + request.bank, 1))
    finally:
        if ours:
            store.close()

    # ⭐⭐ **Which chips are actually left** (ADR-234). Fetched only here, and only when a manager id is
    # given: the landing screen does not need it, and ADR-217/218 spent a day making that screen fast.
    #
    # ⚠️ **Never load-bearing, and never optimistic.** If the fetch fails the advice still stands — but the
    # status reads *unknown*, not *available*, because *"we could not check"* and *"you still have it"* are
    # different facts and only one of them is safe to act on.
    status = _chip_status(request.manager_id, first)

    advice = chip_advisor(
        data.owned,
        {r["id"]: r["by_gameweek"] for r in data.ranked},
        data.ranked[0]["gameweeks"] if data.ranked else [],
        rebuild=rebuild,
    )
    # ⚠️ **The triple-captain pick arrives as a raw database row**, because `chip_advisor` hands back the
    # player it was given. ⭐ ADR-227 normalised five such shapes and this is a sixth — in a corner the
    # sweep could not see, because this endpoint did not exist when the sweep was written.
    # *A guard covers the surfaces it was pointed at, and a new surface is not one of them until someone
    # points it.* `tests/test_player_shape.py` now asserts its own completeness for exactly this reason.
    if advice and isinstance(advice.get("triple_captain"), dict):
        pick = advice["triple_captain"].get("player")
        if pick is not None:
            advice["triple_captain"]["player"] = player_summary(
                pick, data.xp_by_id, reported_out=data.leaving)

    # ⚠️ A spent chip keeps its timing advice — *when it would have been best* is still true, and hiding
    # the card entirely would leave a manager wondering whether the app knew about the chip at all.
    # ⭐ The card is marked, not removed: **the recommendation stops being an instruction.**
    for fpl_name, display in CHIP_NAMES.items():
        key = {"wildcard": "wildcard", "bboost": "bench_boost",
               "3xc": "triple_captain", "freehit": "free_hit"}[fpl_name]
        if advice and isinstance(advice.get(key), dict):
            advice[key].update(status.get(fpl_name, {"available": None, "played_in": None}))
            advice[key]["name"] = display

    return {
        # ⭐ Stated, because it is NOT what the caller asked for and a client showing "next 8 GWs" over a
        # 3-gameweek window would be describing someone else's answer.
        "window": window,
        # ⭐ So a client can say "we could not check" rather than implying every chip is in hand.
        "chips_checked": request.manager_id is not None and any(
            v.get("available") is not None for v in status.values()),
        "gameweeks": data.ranked[0]["gameweeks"] if data.ranked else [],
        "expires_after": chip_deadline(first) if first else None,
        "chips": advice,
    }


def players(request: PlayersRequest, *, store: Storage | None = None) -> dict:
    """Every available player, ranked by xP over the horizon (ADR-230).

    ⚠️ **§4.1 prefers a client that reads the published board straight from Supabase**, which is what
    ADR-213 publishes it for — and spike 018 proved it (667 players, 162 KB, 511 ms). This endpoint exists
    because **that path is not testable today**: staging predates the board, and production credentials are
    not something to hand a browse screen in order to try it. ⭐ *Shipping a path nobody has run is how
    this session's bugs were made.* Revisit when the app carries Supabase config for a real device.

    ⭐ **Unavailable players are excluded, not flagged.** A browse list is for finding someone to buy; a
    player who cannot play is not a candidate, and leaving him in makes the reader do the filtering the
    app exists to do. ⚠️ *Doubtful* players stay — a doubt is a probability, not a verdict (ADR-206).
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load([], request.horizon, store)
    finally:
        if ours:
            store.close()

    by_id = {p["id"]: p for p in data.players}
    rows = [
        player_summary(by_id[r["id"]], data.xp_by_id,
                       {r["id"]: r["by_gameweek"] for r in data.ranked},
                       {r["id"]: r["minutes_weight"] for r in data.ranked})
        for r in data.ranked
        if r["id"] in by_id and not is_unavailable(by_id[r["id"]])
    ]
    return {
        "horizon": request.horizon,
        "gameweeks": data.ranked[0]["gameweeks"] if data.ranked else [],
        # ⭐ Stated so a client can say "667 of 720" rather than implying the list is everyone.
        "total": len(rows),
        "players": rows[:request.limit],
    }


def feedback(request: FeedbackRequest) -> dict:
    """Relay a tester's note to the owner's own sink (ADR-231).

    ⭐⭐ **This exists because the secret cannot live in the client.** The web form POSTs straight to
    `FPL_FEEDBACK_WEBHOOK`; a phone holding that would ship it to every tester. So the server holds it and
    the phone holds nothing — which is the same reasoning that keeps the `service_role` key out of a mobile
    binary (ADR-211).

    ⚠️⚠️ **It never reports a blind "sent".** `relay_result` exists because that was a real bug: the form
    said *sent* while a relay silently refused, because the target address had never been activated. ⭐ *A
    success message that cannot fail is not a success message* — so the relay's own verdict comes back, and
    an unconfigured sink is reported as unconfigured rather than as success.

    ⚠️ **No rate limit, and that is a real gap while the API is unreachable and not after.** On localhost
    the only caller is the owner. The day this is hosted it becomes an open relay to his inbox, and a limit
    has to arrive with the hosting — noted in the ADR rather than left to be discovered.
    """
    request.validate()
    import os
    from datetime import UTC, datetime

    import requests

    from src.relay import relay_result

    webhook = os.environ.get("FPL_FEEDBACK_WEBHOOK")
    inbox = os.environ.get("FPL_FEEDBACK_EMAIL", "hello@madboots.com")
    if not webhook:
        # ⭐ An honest failure with a way through, not a shrug: the client can offer an email instead.
        return {"sent": False, "reason": "no feedback sink is configured on the server", "email": inbox}

    payload = {
        "message": request.message.strip(),
        "email": request.contact.strip(),
        "source": "madboots-mobile",
        "page": request.screen or "(not sure)",
        "version": request.version,
        "ts": datetime.now(UTC).isoformat(timespec="seconds"),
        "_subject": f"MADBOOTS mobile feedback — {request.screen or 'general'}",
    }
    if key := os.environ.get("FPL_FEEDBACK_KEY"):
        payload["access_key"] = key
    origin = os.environ.get("FPL_FEEDBACK_ORIGIN", "https://madboots.streamlit.app")

    try:
        response = requests.post(webhook, json=payload,
                                 headers={"Origin": origin, "Referer": origin}, timeout=6)
    except requests.RequestException as exc:
        return {"sent": False, "reason": f"could not reach the feedback service ({exc.__class__.__name__})",
                "email": inbox}

    ok, note = relay_result(response)
    return {"sent": ok, "reason": note, "email": inbox}


#: ⭐⭐ **The ordering IS the design** (ADR-150). These sources are not equally reliable, and putting them in
#: one list without saying so would present a Reddit rumour beside an injury FPL confirmed. So they descend
#: by **evidentiary strength**, and each says what it is.
_TIERS = {
    "official": 1,     # FPL's own `news`. A fact — it drives `status`, and therefore every xP in the app.
    "departure": 2,    # the press and the crowd agreeing a player is leaving the league (ADR-153/155).
    "exodus": 3,       # our own inference: a sell-off our fields cannot explain (ADR-146).
    "headline": 4,     # reported by a named outlet (ADR-093).
    # ⚠️ Last, and deliberately: what the crowd is **buying** is the weakest evidence here. It is a fact
    # about other managers, not about the player — ⭐ *"lots of people did this" is the reason a template
    # forms, and it is not on its own a reason to join one.*
    "trending": 5,
}

#: ⭐⭐ **The share of the board that anyone actually considers**, read from the live distribution rather
#: than typed (ADR-210/215). Measured on 2026-09-22: ownership has a **median of 0.2%**, so a plain sweep
#: of the market surfaced **194 news items**, nearly all of them about players almost nobody holds.
#:
#: ⚠️ At the 75th percentile (**1.2% owned**) the same sweep gives **22 signals** — a list a person reads.
#: The number is not a judgement about 1.2%; it is *"the quarter of the board most managers consider"*, and
#: it moves when the league does.
GLOBAL_OWNERSHIP_PERCENTILE = 75

#: ⭐ Six fixtures on the DNA page, where the pitch card shows three (`RUN`). A club's *run* is a longer
#: question than a player's next card — ⚠️ *and they are separate constants because they answer separate
#: questions, not because one of them was forgotten.*
DNA_RUN = 6


def signals(request: SignalsRequest, *, store: Storage | None = None) -> dict:
    """What a manager should know about his own fifteen, strongest evidence first (ADR-232).

    ⭐ **Squad-scoped, which is the whole difference from the web page.** That browses the market; this
    answers *"what should I know?"* about the players you actually hold — the question a manager opens a
    phone to ask before a deadline.

    ⚠️ **Each signal says what kind of thing it is**, because they are not equally reliable. An FPL `news`
    string is a fact; an unexplained exodus is *"the crowd knows something and we do not"*; a headline is
    one outlet's reporting. ⭐ *Presenting them as one undifferentiated list would be the page ADR-150 was
    written to replace.*

    ⭐ **Every signal carries a stable `key`**, so a client can remember which it has already shown. The
    app cannot ask the server *what changed since I last looked* — the server has no idea when that was —
    but it can be told what each thing **is**, and work the rest out itself.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store, need_events=True)
        events = data.events or {}
    finally:
        if ours:
            store.close()

    from src.analytics.crowd import exodus_detector, trending

    # ⚠️ Bound to the whole board, never the fifteen — ADR-210: a tenth of fifteen flags somebody weekly.
    exodus_for = exodus_detector(data.players)

    owned_ids = {p["id"] for p in data.owned}
    if request.scope == "global":
        subjects, cut = _market_subjects(data.players)
    else:
        subjects, cut = list(data.owned), None

    # ⭐ Only in global, and only for players the reader does not already hold: *"lots of managers are
    # buying him"* is news about the market. About your own player it is not news at all.
    buying = {}
    if request.scope == "global":
        for row in trending(subjects, by="in", limit=8):
            if row["id"] not in owned_ids:
                buying[row["id"]] = row["trend"]

    found = []
    for player in subjects:
        summary = player_summary(player, data.xp_by_id, reported_out=data.leaving)
        news = (player["news"] or "").strip() if "news" in player.keys() else ""

        if news:
            found.append({"kind": "official", "key": f"official:{player['id']}:{hash(news) & 0xffff}",
                          "player": summary, "headline": news,
                          "detail": "FPL's own news. It drives his status, and therefore his projection."})

        if leaving := data.leaving.get(player["id"]):
            found.append({"kind": "departure", "key": f"departure:{player['id']}",
                          "player": summary,
                          "headline": leaving.get("title") or "Reported to be leaving the league",
                          "detail": f"Reported by {leaving.get('source') or 'the press'}. "
                                    f"FPL still lists him as available."})

        if exodus := exodus_for(player):
            found.append({"kind": "exodus", "key": f"exodus:{player['id']}",
                          "player": summary,
                          # ⚠️ `net` is negative by construction — it is transfers *out* minus in. "-2,762 managers
                          # sold him" reads as nonsense, and the sign is already carried by the
                          # word "sold".
                          "headline": f"{abs(exodus['net']):,} managers sold him this week",
                          # ⭐ Deliberately says nothing about *what* the news is. It reports that the crowd
                          # knows something and we do not — true, checkable, and the most the data supports.
                          "detail": "Nothing in his status or news explains it."})

        if (net_in := buying.get(player["id"])) is not None:
            found.append({"kind": "trending", "key": f"trending:{player['id']}",
                          "player": summary,
                          "headline": f"{abs(int(net_in)):,} managers bought him this week",
                          # ⭐ Says what it is and stops. The app does not know *why* they bought him, and
                          # a confident guess would be the thing ADR-150 was written to remove.
                          "detail": "A crowd movement, not a projection. He may already be priced in."})

        for event in events.get(player["id"], []):
            row = dict(event)
            found.append({"kind": "headline", "key": f"headline:{player['id']}:{row.get('seen_at')}",
                          "player": summary, "headline": row.get("title") or "",
                          "detail": f"Reported by {row.get('source') or 'an outlet'}.",
                          "at": row.get("seen_at")})

    found.sort(key=lambda s: (_TIERS[s["kind"]], s["player"]["web_name"]))
    for signal in found:
        # ⭐ So a global list can say *"you own him"* without the client holding a second copy of the squad.
        signal["owned"] = signal["player"]["id"] in owned_ids
    return {
        "signals": found,
        "scope": request.scope,
        # ⭐ So a quiet week reads as *"nothing to report"* rather than as a screen that failed to load.
        "checked": len(subjects),
        # ⚠️ **What "global" actually means, stated.** A market view that silently drops four fifths of the
        # board is a view that lies by omission — ⭐ *a filter the reader cannot see is a filter he will
        # eventually be surprised by* (ADR-215).
        "ownership_floor": cut,
    }


def _market_subjects(players):
    """The slice of the board worth sweeping, and the cut that produced it (ADR-245).

    ⭐⭐ **Read from the live distribution, never typed.** Measured on the real board: ownership has a
    **median of 0.2%**, so an unbounded market sweep returned **194 news items**, nearly all about players
    almost nobody holds — ⚠️ *a list that long is not more information, it is a screen a person stops
    reading.* At the 75th percentile the same sweep gives about **22**.
    """
    rows = [dict(p) for p in players]
    shares = sorted((p.get("selected_by") or 0) for p in rows)
    if not shares:
        return [], None
    cut = shares[min(len(shares) - 1, int(len(shares) * GLOBAL_OWNERSHIP_PERCENTILE / 100))]
    return [p for p in rows if (p.get("selected_by") or 0) >= cut], round(cut, 1)


def player_dna(request: PlayerDnaRequest, *, store: Storage | None = None) -> dict:
    """One player's fingerprint, ranked **within his position** (ADR-250).

    ⭐⭐ **Within position, not across the league.** A defender's attacking threat and a forward's are not
    the same question — ranked together, every defender would look poor at a thing defenders are not asked
    to do. ⚠️ *A single scale across incomparable roles is a ranking that flatters and punishes by
    position.*

    ⭐ **`pool_size` and `low_minutes` travel with it**, and the client shows both. A percentile is only as
    meaningful as the field it was measured in: *"84th of 31 midfielders"* is a fact, *"84th"* alone is an
    invitation to over-read it — and a player below the minutes floor is ranked anyway, with a caption,
    rather than silently excluded (ADR-118).
    """
    request.validate()
    store, ours = opened(store)
    try:
        players = store.get_players()
        target = next((p for p in players if p["id"] == request.player_id), None)
        if target is None:
            raise ValueError(f"no player with id {request.player_id}")
        dna = analytics_player_dna(target, players)
        insights = player_insights(target, dna) if dna else []
        data = load([request.player_id], request.horizon, store, need_history=True)
        summary = player_summary(target, data.xp_by_id,
                                 {r["id"]: r["by_gameweek"] for r in data.ranked},
                                 reported_out=data.leaving)
        club_by_id = {t["id"]: t["short_name"] for t in store.get_teams()}
        recent = list((data.gw_history or {}).get(target["code"]) or [])[-RECENT:]
    finally:
        if ours:
            store.close()

    if dna is None:
        # ⚠️ A player with no position cannot be ranked. ⭐ Saying so beats an empty radar, which reads as
        # "this player is bad at everything".
        return {"player": summary, "photo": photo_url(target["code"]), "axes": [], "insights": [],
                "pool_size": 0,
                "low_minutes": True, "min_minutes": 0, "recent": _recent_rows(recent, club_by_id),
                "unranked": "no position on record"}

    return {
        "player": summary,
        # ⭐ Same rule as the card: a face belongs where a name already is.
        "photo": photo_url(target["code"]),
        "axes": [{"label": a.label, "sublabel": a.sublabel, "value": a.value,
                  "percentile": a.percentile} for a in dna.axes],
        "insights": [{"kind": i.kind, "text": i.text} for i in insights],
        # ⭐ The field he was ranked in, not just his place in it.
        "pool_size": dna.pool_size,
        "low_minutes": dna.low_minutes,
        "min_minutes": dna.min_minutes,
        "recent": _recent_rows(recent, club_by_id),
        "unranked": None,
    }


def team_dna(request: TeamDnaRequest, *, store: Storage | None = None) -> dict:
    """Every club's fingerprint, ranked across the league (ADR-247).

    ⭐⭐ **Team DNA, not player DNA, and that is the choice.** A player's fingerprint answers *what kind of
    player is he?* — a question the app already answers twice, on the expanding card (ADR-237) and in Boot
    Battle (ADR-236). A club's answers *is this attack actually any good?*, which is what you need when
    choosing between two players from different sides, and the app could not answer it at all.

    ⭐ **Eight axes as percentiles**, so "74" means the same thing on Attacking Threat as on Squad Depth.
    The web draws them as a radar; ⚠️ *a radar needs width a phone does not have*, so the client draws bars
    — the same numbers, a shape that survives the screen.

    ⭐ `player_ids` marks which clubs you hold players from. ⚠️ It **filters nothing**: a league table you
    can see yourself in is a different object from a league table of the clubs you already own.
    """
    request.validate()
    store, ours = opened(store)
    try:
        players = store.get_players()
        teams = store.get_teams()
        upcoming = store.get_upcoming_fixtures()
        names = {t["short_name"]: t["name"] for t in teams}
        all_dna = team_dna_all(players, upcoming, team_names=names)
        mine = {p["team"] for p in players if p["id"] in set(request.player_ids)}
        gw_history = store.get_gw_history_by_code()
        past = store.get_history_by_code()
        # ⚠️⚠️ **Last season, when this one cannot rank anybody yet** (ADR-126). The ranking needs ~900
        # minutes and it is September — ⭐ *an empty table reads as "this club has no good players", which
        # is a claim nobody made*, so the fallback answers and the label says which season it answered for.
        last_rows = last_season_rows(players, past)
        last_name = last_season_name(past)
        schedule = {club: [{"gameweek": c.get("event"), "opponent": c["opponent"],
                            "venue": c["venue"], "difficulty": c.get("difficulty")}
                           for c in (team_schedule(upcoming, club) or [])[:DNA_RUN]]
                    for club in all_dna}
        form = {club: [{"gameweek": gw, "result": result}
                       for gw, result in (team_form(gw_history, players, club) or [])]
                for club in all_dna}
        key_players = {}
        for club in all_dna:
            rows_, season = key_players_this_or_last(players, club, last_rows=last_rows,
                                                    season_name=last_name)
            key_players[club] = {"season": season, "players": rows_}
    finally:
        if ours:
            store.close()

    rows = []
    for dna in all_dna.values():
        rows.append({
            "team": dna.team,
            "name": dna.name,
            "grade": dna.grade,
            "score": dna.grade_score,
            "yours": dna.team in mine,
            "axes": [{"label": a.label, "sublabel": a.sublabel, "value": a.value,
                      "percentile": a.percentile} for a in dna.axes],
            "insights": [{"kind": i.kind, "text": i.text} for i in team_insights(dna)],
            # ⭐ The three things the web page carries beside the fingerprint, and the reason a manager
            # opens it: where the club is going, how it has been going, and who to buy.
            "fixtures": schedule.get(dna.team, []),
            "form": form.get(dna.team, []),
            "key_players": key_players.get(dna.team, {"season": None, "players": []}),
        })
    # ⭐ Best first. ⚠️ Ties broken by name rather than left to dict order, so two runs of the same data
    # cannot disagree about the table — *an unstable sort is a diff that appears from nowhere.*
    rows.sort(key=lambda r: (-r["score"], r["name"]))
    return {"teams": rows, "yours": sorted(mine)}


def _chip_status(manager_id, gameweek) -> dict:
    """Which chips are still in hand for this half-season (ADR-234).

    ⚠️ **`available: None` means *we do not know*.** No manager id, or a failed fetch, must not read as
    *"you still have it"* — ⭐ *"we could not check" and "you have it" are different facts, and only one of
    them is safe to act on.*
    """
    unknown = {name: {"available": None, "played_in": None} for name in CHIP_NAMES}
    if not manager_id or gameweek is None:
        return unknown
    try:
        from src.api.client import FplClient

        history = FplClient().get_entry_history(manager_id)
        return chips_available(history.get("chips"), gameweek)
    except Exception:                                    # noqa: BLE001 — advice survives a failed lookup
        return unknown


#: How many recent gameweeks a comparison shows. ⭐ Five, because that is the window a manager means by
#: "form" and the one FPL's own `form` field averages over.
RECENT = 5


def compare(request: CompareRequest, *, store: Storage | None = None) -> dict:
    """Two players, side by side — **Boot Battle** (ADR-110/236).

    ⭐⭐ **Offered here so the comparison can sit where the decision is.** The web app has had this since
    ADR-110, on the Players page, as a destination you navigate to. A transfer screen that suggests
    `Groß → Belloumi` and cannot show you the two of them side by side is sending you to another room to
    answer the question it just raised.

    Three things, because the Hub's version showed two we lacked:

    * **the stat grid** — ours already, with the better value marked per row
    * **recent form** — the last five gameweeks, points and minutes
    * **the projected run** — per-gameweek xP for both, so the lines can be drawn against each other

    ⚠️ Same-position only. `compare_rows` orders the stats by what matters for a position, so comparing a
    keeper with a midfielder would produce rows that are individually true and jointly meaningless.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load([request.a_id, request.b_id], request.horizon, store, need_history=True)
        gw_history = data.gw_history or {}
        club_by_id = {t["id"]: t["short_name"] for t in store.get_teams()}
    finally:
        if ours:
            store.close()

    a, b = data.by_id[request.a_id], data.by_id[request.b_id]
    if a["position"] != b["position"]:
        raise ValueError(f"{a['web_name']} is a {a['position']} and {b['web_name']} is a {b['position']} — "
                         f"a comparison across positions ranks them on stats that do not mean the same thing")

    by_gameweek = {r["id"]: r["by_gameweek"] for r in data.ranked}

    def side(player):
        # ⭐ Keyed by the player's **code**, not id: `code` is stable across seasons, which is why the
        # history is stored under it (FPL restarts element ids each August).
        rows = list(gw_history.get(player["code"]) or [])[-RECENT:]
        return {
            **player_summary(player, data.xp_by_id, by_gameweek, reported_out=data.leaving),
            # ⭐ The face, as the web's compare header has had since ADR-110 — a named card, which is where
            # ADR-255 says a mugshot belongs.
            "photo": photo_url(player["code"]),
            "recent": _recent_rows(rows, club_by_id),
        }

    return {
        "horizon": request.horizon,
        "gameweeks": data.ranked[0]["gameweeks"] if data.ranked else [],
        "a": side(a),
        "b": side(b),
        # ⭐ `(label, a, b, winner)` — the winner decided by `_BETTER`, which knows that a lower expected
        # goals-conceded is the better number. ⚠️ A naive `max()` would crown the worse defence.
        "rows": [
            {"label": label, "a": fa, "b": fb, "winner": winner}
            for label, fa, fb, winner in compare_rows(a, b)
        ],
    }


def player(request: PlayerRequest, *, store: Storage | None = None) -> dict:
    """One player in full — the card behind a row (ADR-109/237).

    ⭐ **The stats are ordered by POSITION, not by a fixed list.** A defender leads with expected goals
    conceded and DefCon; a forward with goals and xG involvement. ⚠️ *The same twelve numbers in the same
    order for everyone is a table, not a card* — and it buries the one a reader opened the row for.

    Three blocks, matching what a comparison shows for two: the season stats, the last five gameweeks with
    minutes, and the projected run with its fixtures.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load([request.player_id], request.horizon, store, need_history=True)
        gw_history = data.gw_history or {}
        upcoming = data.upcoming
        # ⭐ Read inside the `try`, because it needs the store — see `_recent_rows`.
        club_by_id = {t["id"]: t["short_name"] for t in store.get_teams()}
    finally:
        if ours:
            store.close()

    row = data.by_id[request.player_id]
    by_gameweek = {r["id"]: r["by_gameweek"] for r in data.ranked}
    recent = list(gw_history.get(row["code"]) or [])[-RECENT:]

    return {
        "horizon": request.horizon,
        "player": player_summary(row, data.xp_by_id, by_gameweek, reported_out=data.leaving),
        # ⭐⭐ **On a named card, never on the pitch** (ADR-255). ADR-084 chose the club kit there on
        # purpose: FPL's photo CDN lags a transfer by weeks while the kit graphic updates instantly, so a
        # just-transferred player would sit on the pitch wearing his old club's face. ⚠️ *On a card his
        # name is beside him and the staleness is a curiosity; on the pitch it is the app being visibly
        # wrong about your team.*
        "photo": photo_url(row["code"]),
        "stats": [{"label": label, "value": value} for label, value in stat_rows(row)],
        "recent": _recent_rows(recent, club_by_id),
        # ⭐ The run **with difficulty**, so a reader can see whether a high projection is a good player or
        # an easy month — which is the question a card is opened to answer.
        "fixtures": [
            {"gameweek": cell.get("event"), "opponent": cell["opponent"],
             "venue": cell["venue"], "difficulty": cell.get("difficulty")}
            for cell in (team_schedule(upcoming, row["team"]) or [])[:request.horizon]
        ],
    }
