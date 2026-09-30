"""The squad questions — the six the CLI has always answered, plus the pitch.

`analysis` · `transfers` · `captain` · `gameweek` · `route` · `build` · `my_team` · `replacements` · `chips`.
The freshness helpers live here because only `my_team` reads them.
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
    player_summary,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
    team_schedule,
)
from src.analytics.gameweek import gameweek_plan
from src.analytics.optimizer import DEFAULT_BUDGET, legal_xi_issues
from src.analytics.transfer import replacements_for, route_to_player
from src.fpl_rules import (
    CHIP_NAMES,
    free_transfers_from_history,
)
from src.kits import shirt_url
from src.manager import fetch_manager_team

# ⭐⭐ **Imported as a module, not as names** (ADR-324). `common`'s helpers are shared by more than one
# answer family, and a test that fakes one — `_chip_status` is faked in three suites — must be able to
# reach every consumer from one place. ⚠️ *Binding a shared function into each module's globals gives it
# as many patch points as there are importers*, which is how a fake silently applies to one caller and
# not the next.
from src.service.answers import common

# ⚠️ **`my_team` reads the signals** — one cross-family call, and the only one in this package (ADR-324).
# The pitch shows a badge per player, and ADR-228 had that parked until it could be done without a second
# round trip: ~50ms over fifteen players, in-process. ⭐ *Recorded here because an import from a sibling
# answer module is the thing this split is meant to make visible, not hide.*
from src.service.answers.market import signals
from src.service.inputs import RUN, SWIPE, WIDE, load, opened, reported_leavers
from src.service.requests import (
    DEFAULT_HORIZON,
    MAX_HORIZON,
    BuildRequest,
    CaptainRequest,
    ChipsRequest,
    GameweekRequest,
    MyTeamRequest,
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
        def flat(value):
            """⚠️ **Recursive now** (ADR-327): `transfers` is a dict of one `Explanation` per move, and a
            flattener that only looked at the top level would hand the client dataclass objects it cannot
            serialise. ⭐ *The shape grew a level and the converter did not, which fails at the wire rather
            than here.*"""
            if hasattr(value, "__dataclass_fields__"):
                return asdict(value)
            if isinstance(value, dict):
                return {k: flat(v) for k, v in value.items()}
            if isinstance(value, list):
                return [flat(v) for v in value]
            return value

        return {key: flat(value) for key, value in found.items()}
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
        # ⚠️ Passed through, and the caller decides. ⭐ *A wildcard squad that ignores the bench spends
        # real money on players who never score* — but changing the default here would change an answer
        # somebody may already rely on, so the choice stays with the request (ADR-268).
        bench_weight=request.bench_weight,
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
        # ⚠️ All fifteen. Kept because it always meant that — ⭐ *changing what a field means is worse
        # than adding one*, and a caller reading it today would silently start getting a smaller number.
        "projected_xp": round(sum(data.xp_by_id.get(p["id"], 0) for p in result["selected"]), 1),
        # ⭐⭐ **What the manager actually scores.** Only the eleven count, so a bench-aware build looks
        # *worse* on `projected_xp` while fielding a *better* side — ⚠️ *a headline that falls when the
        # answer improves is a headline that will be optimised against.* `None` when no bench was
        # designated, because then there is no eleven to name (ADR-268).
        "xi_xp": (round(sum(data.xp_by_id.get(p["id"], 0)
                            for p in result["selected"] if not p.get("bench")), 1)
                  if request.bench_weight is not None else None),
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


def _age_minutes(refreshed_at, now=None) -> int | None:
    """Minutes since the last successful refresh — `None` when nothing has ever refreshed.

    ⚠️ **None, never zero.** *A database that has never been refreshed is not one refreshed just now*, and
    a client reading `0` would print "updated moments ago" about a file nothing has ever written.
    """
    if not refreshed_at:
        return None
    try:
        at = datetime.fromisoformat(str(refreshed_at))
    except ValueError:
        return None
    if at.tzinfo is None:
        at = at.replace(tzinfo=UTC)
    # ⚠️ Clamped at zero: clock skew between the writer and the reader must not report a negative age,
    # which a client would render as a refresh in the future.
    return max(0, int(((now or datetime.now(UTC)) - at).total_seconds() // 60))


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
        # ⭐⭐⭐ **How old the numbers are** (ADR-303), and ⚠️⚠️ **deliberately NOT folded into `behind`.**
        # `behind` means *a completed gameweek has no rows* — a hole. Age means *the last refresh was a
        # while ago* — the data is whole and possibly out of date. ⭐ *Two questions, two fields*: merging
        # them is the mistake ADR-301 caught, where a schema lag reached the reader as "your data is
        # broken" and would have alarmed nine testers about nothing.
        #
        # ⚠️ Why it exists: the refresh declares a 15-minute cadence and GitHub fires **6-7%** of it, so
        # the app was implying a freshness it did not have — and the staleness banner could not see it,
        # because a five-hour-old row is still a row.
        "age_minutes": _age_minutes(status.get("refreshed_at")),
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
        # ⚠️⚠️ **Widened from `RUN` to `SWIPE` by ADR-298.** The second pass existed to fill a
        # three-fixture card; the swipe forward needs a projection for each of five gameweeks, and it
        # reads the same `by_gameweek` map. ⭐ Still a second pass rather than a raised `horizon`, for
        # exactly the reason above — *the headline must stay a one-week number.*
        if request.horizon >= SWIPE:
            run_answer = answer
        else:
            run_answer = analysis(SquadRequest(player_ids=owned_ids, bench_ids=bench_ids,
                                               horizon=SWIPE), store=store)
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
            # ⚠️⚠️ **As far as the caller asked, not a fixed three** (ADR-298). Swiping forward to GW+5
            # needs an opponent for every week it can reach — ⭐ *a projection with no fixture beside it
            # is a number the reader cannot check.* The run card still shows three; that is its own
            # decision and it takes what it needs.
            #
            # ⭐ `SWIPE`, which is `WIDE + 1` — *a window includes the week you are standing on*, so
            # five forward pages need six weeks of fixtures. ⚠️ Shipping `WIDE` here left the fifth
            # page with no opponent on any card.
            for cell in (team_schedule(upcoming, club) or [])[:max(SWIPE, request.horizon)]
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

    # ⭐⭐ **One line for the squad, because fifteen arrows is a reading exercise and a number is a
    # decision** (ADR-335). It leans on falls deliberately: the rule catches **72%** of them against 24%
    # of rises (ADR-334), so *"three of yours are about to drop"* is the claim it can actually support.
    #
    # ⚠️ `at_risk_value` is what those players are worth, not what they would lose — a price change is
    # £0.1m each. ⭐ *The number that makes you look is the exposure; the number that matters is small,
    # and saying the small one first is how a feature gets ignored.*
    falling = [p for p in owned if prices[p["id"]]["direction"] == "fall"]
    rising = [p for p in owned if prices[p["id"]]["direction"] == "rise"]
    squad_price = {
        "changed_this_gameweek": round(sum(v["changed_this_gameweek"] for v in prices.values()), 1),
        "falling": len(falling),
        "rising": len(rising),
        "at_risk_value": round(sum((p["price"] or 0) for p in falling), 1),
    }

    xp_by_id = {p["id"]: p["xp"] for p in answer["xi"] + answer["bench"]}
    suggested = _suggested_lineup(owned, bench_ids, xp_by_id, leaving)
    benched = [by_id[i] for i in bench_ids if i in by_id]
    # ⭐ Role → id, so the phone orders the bench the way FPL will actually substitute. Without it a client
    # invents an order, and the first auto-sub proves it wrong.
    roles = {role: p["id"] for role, p in bench_order(benched, xp_by_id)} if benched else {}

    # ⚠️ Fetched once and named, because the response reads it three times and ⭐ *a network call inside a
    # dict literal is a call nobody can see.*
    _history = common._entry_history(request.manager_id)
    _implied = (free_transfers_from_history(_history.get("current"), _history.get("chips"))
                if _history else None)
    # ⭐ The manager's word, then his history, then the oldest guess in the app. Each step is a fact the
    # step below it does not have.
    _free = request.free_transfers if request.free_transfers is not None else (_implied or 1)

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
        # ⭐⭐⭐ **One number, and the server says where it came from** (ADR-321). Three surfaces were
        # showing three different things — the pitch echoed whatever the client last sent, Settings
        # printed the derived number in a caption it did not use, and the week's plan was computed from
        # the echo. ⚠️ *Two numbers on one screen is a question, not an answer*, and the manager asked it:
        # *"is that 1/3 used?"*
        #
        # ⭐ The precedence is the honest one, unchanged from ADR-318's reasoning: **what the manager said
        # beats what history implies**, because transfers made during the current window are invisible
        # until the deadline passes, so he may know something this does not. What changed is only the
        # case ADR-318 could not express — **nobody has said anything** — which used to be answered with a
        # hard-coded 1 and is now answered from his own history.
        "free_transfers": _free, "free_transfers_implied": _implied,
        # ⭐ Named so a surface can explain itself rather than assert. ⚠️ *A number whose provenance is
        # invisible is one the reader has to take on trust, and this is the number he already distrusted.*
        "free_transfers_source": ("you" if request.free_transfers is not None
                                  else "history" if _implied is not None else "default"),
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
        "squad_price": squad_price,
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
    status = common._chip_status(request.manager_id, first)

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
