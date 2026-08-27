"""Transfer *timing* — use it, bank it, or take the hit (ADR-132).

The roadmap asked for a multi-gameweek transfer **path search**. A prototype against the live squad found no
path to search: the best sell was the *same player in all six gameweeks* (one player's share of a squad's ±3%
weekly swing is tiny — ADR-131), and the whole market yielded exactly **one** positive-gain move over the
horizon. A tree needs branches.

What a manager actually faces is arithmetic, and all of it is exact:

* Is the move worth making at all?
* Use this week's free transfer, or bank it for two next week?
* Is a second move worth the −4 it costs?

No search, no invented decay constant — just FPL's own rules (`fpl_rules`) applied to gains the transfer
engine already produces. Pure; every function takes what it needs and returns plain data.
"""

HIT_COST = 4          # FPL: every transfer beyond your free ones costs 4 points
MAX_SAVED = 5         # free transfers roll over, up to five banked


def free_transfer_run(start: int, gameweeks: int, *, made_per_gw=None, max_saved: int = MAX_SAVED) -> list[int]:
    """How many free transfers you hold at each of the next `gameweeks`, given what you spend.

    One is added each gameweek and unused ones roll over to a cap of `max_saved`. `made_per_gw` is how many
    you spend in each week (defaults to none) — spending more than you hold is allowed, because that is what a
    hit *is*; the count simply floors at zero.
    """
    made = list(made_per_gw or [])
    out, held = [], start
    for i in range(gameweeks):
        held = min(max_saved, held + 1) if i else held
        spend = made[i] if i < len(made) else 0
        out.append(held)
        held = max(0, held - spend)
    return out


def hit_is_worth_it(gain, *, hit_cost: int = HIT_COST) -> bool:
    """Is a move worth taking a points hit for? Strictly: does it gain more than the hit costs.

    Stated as its own function because it is the question most often answered by vibes. A gain of 3.0 against a
    cost of 4 is not close, and the number says so more usefully than a plan that quietly assumes yes.
    """
    return gain is not None and gain > hit_cost


def bank_or_use(moves, next_gw_gain=None, *, free: int = 1, hit_cost: int = HIT_COST) -> dict:
    """Whether to spend this week's free transfer now or bank it, with the arithmetic that decides.

    Banking buys one thing — a second free transfer next week — which is only worth having if there is a
    second move you would actually want. Its value is therefore the **hit it saves you**, capped at that
    second move's own gain (saving a 4-point hit to make a move worth 1.0 gains you 1.0, not 4.0).

    It costs the first move's gain for the week you skip, since the move happens a gameweek later.

        bank when   min(second_gain, hit_cost)  >  first_move_gain_next_gw

    Returns the decision, both sides of the comparison, and a plain-English reason. With no worthwhile move at
    all the answer is to bank — there is nothing to spend on.
    """
    first = moves[0]["gain"] if moves else None
    second = moves[1]["gain"] if len(moves) > 1 else None

    if first is None or first <= 0:
        return {"action": "bank", "value": 0.0, "cost": 0.0, "second_gain": None,
                "reason": "No move improves your squad right now — bank the transfer."}

    if free >= 2:
        return {"action": "use", "value": 0.0, "cost": round(first, 2), "second_gain": second,
                "reason": f"You already hold {free} free transfers — no reason to wait."}

    cost = next_gw_gain if next_gw_gain is not None else 0.0
    value = min(second, hit_cost) if second and second > 0 else 0.0
    if value > cost:
        return {"action": "bank", "value": round(value, 2), "cost": round(cost, 2), "second_gain": second,
                "reason": (f"It saves {value:.1f} (the hit avoided on a second move worth {second:.1f}) "
                           f"and costs {cost:.1f} by waiting a week.")}
    return {"action": "use", "value": round(value, 2), "cost": round(cost, 2), "second_gain": second,
            "reason": (f"Waiting costs {cost:.1f} and saves only {value:.1f}" if value
                       else "There's no second move worth banking for.")}


def transfer_timing(moves, *, free: int = 1, next_gw_gain=None, hit_cost: int = HIT_COST,
                    horizon: int = 1, dead=()) -> dict:
    """The whole timing picture: what to do this week, whether to take a hit, and why.

    `moves` is the ordered plan from `suggest_transfer_plan` (best first). `next_gw_gain` is what the top move
    is worth in the *next* gameweek alone — the cost of delaying it — and comes from `by_gameweek`.

    `dead` is `replace_dead`'s output (ADR-136/156). A slot that cannot score **takes the free transfer**,
    ahead of any upgrade: it is a permanent zero with no auto-sub cover, and banking against it is banking
    against a hole. The two gains are deliberately *not* compared — ADR-136 keeps them apart because they
    measure different things — so the dead slot wins on **kind**, not on number, and the ordinary plan simply
    becomes the hit question behind it.
    """
    if dead:
        return _dead_first(dead, moves, free=free, hit_cost=hit_cost, horizon=horizon)
    decision = bank_or_use(moves, next_gw_gain, free=free, hit_cost=hit_cost)
    second = moves[1] if len(moves) > 1 else None
    take_hit = bool(second) and free < 2 and hit_is_worth_it(second["gain"], hit_cost=hit_cost)
    return {
        "moves": list(moves), "free": free, "horizon": horizon,
        "decision": decision, "take_hit": take_hit,
        "hit_verdict": _hit_verdict(second, take_hit, free, hit_cost,
                                    banking=decision["action"] == "bank", moves=moves),
        "headline": _headline(moves, decision, take_hit, horizon, has_second=second is not None),
    }


def _dead_first(dead, moves, *, free, hit_cost, horizon) -> dict:
    """The timing answer when part of the squad cannot play at all.

    Fixing it is never "bank": a dead slot costs the same every week you leave it, and costs everything the
    week a starter is knocked. The best ordinary upgrade drops down to being the hit question.
    """
    d = dead[0]
    span = f"over {horizon} gameweeks" if horizon > 1 else "next gameweek"
    nxt = moves[0] if moves else None
    take_hit = bool(nxt) and free < 2 and hit_is_worth_it(nxt["gain"], hit_cost=hit_cost)
    reason = f"{d['out']['web_name']} can't play ({d['reason']})"
    return {
        "moves": list(moves), "free": free, "horizon": horizon, "dead": list(dead),
        "decision": {"action": "use", "value": 0.0, "cost": 0.0, "second_gain": nxt["gain"] if nxt else None,
                     "reason": f"{reason}. A slot scoring nothing outranks any upgrade."},
        "take_hit": take_hit,
        "hit_verdict": (_hit_verdict(nxt, take_hit, free, hit_cost, banking=False, moves=moves) if nxt else
                        "Filling the dead slot is the only move worth making, so there's no hit to consider."),
        "headline": (f"**Use your free transfer on {d['out']['web_name']} → {d['in']['web_name']}** — "
                     f"{reason}, so that slot recovers **{d['gain']:.1f} xP** {span}. "
                     f"A dead slot comes before any upgrade."),
    }


def _hit_verdict(second, take_hit, free, hit_cost, banking=False, moves=()) -> str:
    """The hit question, answered so it never contradicts the timing advice.

    When the answer is to bank, a second move that *would* justify a hit is exactly the reason to bank —
    saying "take the hit" alongside "bank the transfer" reads as two opinions rather than one plan.
    """
    if not moves:
        return "Nothing is worth transferring in, so there's no hit to consider."
    if second is None:
        return "Only one move is worth making, so there's no hit to consider."
    if free >= 2:
        return f"A second move is free — you hold {free} transfers."
    if banking:
        return (f"A second move ({second['out']['web_name']} → {second['in']['web_name']}) gains "
                f"{second['gain']:.1f} — banking makes it free instead of a {hit_cost}-point hit.")
    if take_hit:
        return (f"A second move ({second['out']['web_name']} → {second['in']['web_name']}) gains "
                f"{second['gain']:.1f}, more than the {hit_cost}-point hit it costs.")
    return (f"Don't take a hit: the next-best move gains {second['gain']:.1f}, less than the {hit_cost} "
            "points it costs.")


def _headline(moves, decision, take_hit, horizon, has_second=False) -> str:
    if not moves or moves[0]["gain"] <= 0:
        return f"No transfer improves your squad over the next {horizon} gameweek(s) — hold."
    top = moves[0]
    span = f"over {horizon} gameweeks" if horizon > 1 else "next gameweek"
    move = f"**{top['out']['web_name']} → {top['in']['web_name']}** (+{top['gain']:.1f} {span})"
    if decision["action"] == "bank":
        return f"**Bank your free transfer.** {decision['reason']}"
    if take_hit:
        return f"Use your free transfer on {move}, and a second move is worth the hit."
    if has_second:
        return f"Use your free transfer on {move}. Don't take a hit for a second."
    return f"Use your free transfer on {move}."
