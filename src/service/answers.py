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
    minutes_weight_from_history,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
    team_schedule,
)
from src.analytics.gameweek import gameweek_plan
from src.analytics.optimizer import DEFAULT_BUDGET
from src.analytics.transfer import route_to_player
from src.kits import shirt_url
from src.manager import fetch_manager_team
from src.service.inputs import WIDE, load, opened
from src.service.requests import (
    BuildRequest,
    CaptainRequest,
    GameweekRequest,
    MyTeamRequest,
    RouteRequest,
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
    return {"gameweek": data.ranked[0]["gameweeks"][0] if data.ranked else None, "picks": picks}


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
        "target": {"id": target["id"], "web_name": target["web_name"], "team": target["team"],
                   "position": target["position"], "price": target["price"],
                   "xp": data.xp_by_id.get(target["id"], 0.0)},
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
    for p in result["selected"]:
        p["xp"] = data.xp_by_id.get(p["id"], 0)
    return {
        "horizon": request.horizon,
        "budget": request.budget,
        # ⭐ The solver's own word, surfaced. "Infeasible" is an answer — *nothing fits these constraints* —
        # and swallowing it would leave a client showing an empty squad with no reason.
        "status": result["status"],
        "selected": result["selected"],
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
