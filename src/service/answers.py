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
    team_schedule,
)
from src.analytics.gameweek import gameweek_plan
from src.analytics.optimizer import DEFAULT_BUDGET
from src.analytics.transfer import replacements_for, route_to_player
from src.kits import shirt_url
from src.manager import fetch_manager_team
from src.service.inputs import WIDE, load, opened
from src.service.requests import (
    DEFAULT_HORIZON,
    MAX_HORIZON,
    BuildRequest,
    CaptainRequest,
    ChipsRequest,
    FeedbackRequest,
    GameweekRequest,
    MyTeamRequest,
    PlayersRequest,
    ReplacementsRequest,
    RouteRequest,
    SignalsRequest,
    SquadRequest,
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

        owned = [p for p in players if p["id"] in set(owned_ids)]
        teams = store.get_teams()
        upcoming = store.get_upcoming_fixtures()
        code_by_club = {t["short_name"]: t["code"] for t in teams}
        # ⚠️ Clubs come from the squad being **shown**, so a drafted-in player from a new club still gets a
        # kit and a fixture. Deriving them from the FPL squad would leave the new signing shirtless.
        clubs = {p["team"] for p in owned}
        gameweek, at, label, urgency = deadline_line(upcoming, datetime.now(UTC))
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

    fixtures = {}
    for club in clubs:
        cell = (team_schedule(upcoming, club) or [None])[0]
        fixtures[club] = None if cell is None else {
            "opponent": cell["opponent"], "venue": cell["venue"],
            "difficulty": cell.get("difficulty"),
        }

    xp_by_id = {p["id"]: p["xp"] for p in answer["xi"] + answer["bench"]}
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
        "deadline": {"at": at.isoformat(), "label": label, "urgency": urgency},
        "analysis": answer,
        "kits": kit_by_club,
        "fixtures": fixtures,
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

    return {
        # ⭐ Stated, because it is NOT what the caller asked for and a client showing "next 8 GWs" over a
        # 3-gameweek window would be describing someone else's answer.
        "window": window,
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

    from src.web_streamlit.feedback import relay_result

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
}


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

    from src.analytics.crowd import exodus_detector

    # ⚠️ Bound to the whole board, never the fifteen — ADR-210: a tenth of fifteen flags somebody weekly.
    exodus_for = exodus_detector(data.players)

    found = []
    for player in data.owned:
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

        for event in events.get(player["id"], []):
            row = dict(event)
            found.append({"kind": "headline", "key": f"headline:{player['id']}:{row.get('seen_at')}",
                          "player": summary, "headline": row.get("title") or "",
                          "detail": f"Reported by {row.get('source') or 'an outlet'}.",
                          "at": row.get("seen_at")})

    found.sort(key=lambda s: (_TIERS[s["kind"]], s["player"]["web_name"]))
    return {
        "signals": found,
        # ⭐ So a quiet week reads as *"nothing to report"* rather than as a screen that failed to load.
        "checked": len(data.owned),
    }
