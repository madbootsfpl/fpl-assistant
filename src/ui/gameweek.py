"""Console rendering for the gameweek plan (ADR-070).

A plain-text block — Captain / Lineup / Transfer / Flags — that is the exact plan the analytics
assembled (`gameweek_plan`). It shows with or without the LLM (the prose is a bonus); the same
"the block is the truth" shape the other `ask` details use. Rendered in the CLI and, via
`render_ask`, in the web's Squads → AI Tips view.
"""

from .explain import MODEL_NOTE, render_explanation


def _captain_line(cap) -> str:
    if not cap:
        return "no eligible captain — check availability"
    venue = "home vs" if cap["venue"] == "H" else "away vs"
    extra = "".join([
        " (penalty taker)" if cap.get("penalty_taker") else "",
        " ⚠ doubtful" if cap.get("doubtful") else "",
    ])
    return f"{cap['web_name']} ({cap['team']}) — xP {cap['xp']} next GW, {venue} {cap['opponent']}{extra}"


def _lineup_line(lineup) -> str:
    if not lineup["has_declared_bench"]:
        return "no saved bench — the best legal XI is shown; save a bench to compare"
    if not lineup["bring_in"] and not lineup["drop"]:
        return "already the best legal XI — no change"
    starts = ", ".join(p["web_name"] for p in lineup["bring_in"])
    benched = ", ".join(p["web_name"] for p in lineup["drop"])
    return f"start {starts} — bench {benched}"


def _transfer_line(transfer, horizon: int = 5, *, has_dead: bool = False) -> str:
    if not transfer:
        # ADR-136: "hold" is only honest when there is nothing wrong with the 15. With a dead slot above,
        # saying "hold your transfer" in the next breath is the exact bug this was reported as.
        return ("no further upgrade — but fill the dead slot above first" if has_dead else
                "no positive-gain upgrade — hold your transfer")
    out, inc = transfer["out"], transfer["in"]
    window = f"over {horizon} GW" if horizon != 1 else "next GW"
    return (f"{out['web_name']} ({out['team']}) → {inc['web_name']} ({inc['team']})  "
            f"(+{transfer['gain']} XI xP {window})")


def _replace_lines(replacements, horizon: int = 5) -> list[str]:
    """The dead-slot moves (ADR-136), one line each — or nothing at all when the squad has none.

    Printed **above** Transfer, because a slot that cannot score is a bigger problem than a marginal upgrade,
    and stated as its own thing: the number is what the slot is throwing away, not what the swap adds to the
    XI. When there are no dead slots this renders no line, so the plan is unchanged for the squads it does not
    apply to.
    """
    if not replacements:
        return []
    window = f"over {horizon} GW" if horizon != 1 else "next GW"
    out = []
    for i, r in enumerate(replacements):
        label = "Replace:" if i == 0 else "        "
        # A *reported* departure is not the same claim as FPL saying he is gone, and the wording says so.
        verb = "is reported to be leaving" if r.get("reported") else "can't play"
        out.append(f"  {label}  ⛔ {r['out']['web_name']} ({r['out']['team']}) {verb} — {r['reason']}. "
                   f"→ {r['in']['web_name']} ({r['in']['team']}, £{r['in']['price']}) "
                   f"is worth {r['gain']} xP {window}")
    return out


def _flags_line(flags) -> str:
    if not flags:
        return "none — all your players are available"
    return "; ".join(
        f"{f['web_name']} ({f['reason']}{'' if f['chance'] is None else f', {f['chance']}%'})"
        for f in flags
    )


def _conf(explanation) -> str:
    """' · Confidence 72/100 · Medium' from an `Explanation`, or '' when none (US-273, ADR-089)."""
    return f"  · Confidence {explanation.confidence}/100 · {explanation.band}" if explanation else ""


def _extra_move_lines(plan, horizon: int = 5) -> list:
    """The moves beyond the first, when the manager holds more than one free transfer (ADR-191).

    Owner: *"I have £1.0m in the bank, I have 2 free transfers… is this advice the best or most effective?"*
    It was not. The second transfer is worth roughly as much again as the first, and the week's answer showed
    one move because it asked for a **menu** of alternatives and printed the top of it.

    ⚠️ **Each gain here is a MARGINAL gain, and that is why a total is printed.** `suggest_transfer_plan`
    prices every move against the squad and the bank the previous one leaves, so these numbers genuinely add —
    unlike the shortlist they replaced, whose entries were each priced against the original squad and would
    have summed to a figure nobody could actually get. The total is the claim; showing it makes the claim
    checkable.

    ⚠️ **The free-transfer count is stated, not implied.** It is entered by the manager and defaults to 1, so
    the advice rests on something that can be wrong. A stated assumption gets corrected; a silent one gets
    believed.
    """
    moves = plan.get("transfers") or []
    if not moves:
        return []
    free = plan.get("free", len(moves))
    window = f"over {horizon} GW" if horizon != 1 else "next GW"

    if len(moves) < 2:
        # ⚠️ **The silent default, which is the case that needed saying most.** This returned nothing at one
        # free transfer, on the reasoning that one move renders as it always did. But `free` **defaults to 1**
        # — so the only time the plan said what it assumed was when the manager had already told it, and the
        # one time it stayed quiet was the one time the number was a guess.
        #
        # The owner read a one-move answer while holding two transfers and had no way to see which of those
        # the app believed. ⭐ *An assumption is worth stating in inverse proportion to how sure of it you are.*
        # ⚠️ **Both numbers, because either can be the wrong one.** This named only the transfer count, and
        # when the owner reported the advice not responding there was no way to tell from the output whether
        # `free` or `bank` had failed to arrive. A line stating an assumption should let a reader diagnose it,
        # not just be reassured that one exists.
        if not plan.get("transfer"):
            return []
        if free <= 0:
            return ["            Assumes you hold no free transfer — this move would cost a 4-point hit"]
        return [f"            Assumes {free} free transfer{'s' if free != 1 else ''} and "
                f"£{plan.get('bank', 0.0):.1f}m in the bank — change these above if that is wrong"]

    out = []
    span = plan.get("horizon_gw", 5)
    for n, m in enumerate(moves[1:], start=2):
        o, i = m["out"], m["in"]
        # The longer view travels with the move, because a later move is exactly as likely to be right for
        # next week and wrong for the season — and on this page the gain above it is a single gameweek.
        wide = m.get("horizon_gain")
        tail = "" if wide is None else f", {wide:+.1f} over {span} GWs"
        out.append(f"            then #{n}: {o['web_name']} ({o['team']}) → {i['web_name']} ({i['team']})  "
                   f"(+{m['gain']} XI xP {window}{tail})")
    total = round(sum(m["gain"] for m in moves), 1)
    # ⚠️ **"All" is a claim, and it is often false.** The plan stops when no positive-gain move is left, so a
    # well-built squad regularly has fewer moves worth making than transfers in hand. Reporting
    # `len(moves)` as though it were the manager's holding would quietly redefine "all your transfers" as
    # "the ones we found" — and the unused one is *information*: it says the squad is close to right, and it
    # rolls over. (Found by a mutant that swapped the two and no test noticed, because every fixture had
    # them equal.)
    if len(moves) < free:
        out.append(f"            Using {len(moves)} of your {free} free transfers "
               f"(£{plan.get('bank', 0.0):.1f}m banked): "
                   f"+{total} XI xP {window} — no further move gains anything, so the rest keeps")
    else:
        out.append(f"            Using all {free} free transfers (£{plan.get('bank', 0.0):.1f}m banked): "
                   f"+{total} XI xP {window} — each move priced after the one above it")
    return out


def _timing_lines(plan, horizon) -> list:
    """The two lines ADR-173 added: what the swap is worth further out, and whether to bank instead.

    The owner rejected a transfer that was right for next week and wrong for his season — *"there is value in
    letting your transfers build up"*. Both halves of that are answerable and neither was being said: the
    plan showed one option, priced over one gameweek, with no alternative and no longer view. It never lied
    (the line reads "next GW"), but a single number with nothing beside it reads as a verdict.
    """
    out, transfer = [], plan.get("transfer")
    if not transfer:
        return out

    wide = plan.get("horizon_gain")
    if wide is not None:
        near = transfer.get("gain")
        # Name the disagreement when there is one. A move worth less over the longer run is exactly the case
        # the owner hit, and the one a weekly number hides.
        shape = ("and still ahead over" if near is None or wide >= near
                 else "but worth less over")
        out.append(f"            Longer view: {wide:+.1f} XI xP {shape} the next "
                   f"{plan.get('horizon_gw', 5)} GWs")

    timing = plan.get("timing") or {}
    if timing.get("action") == "bank":
        out.append(f"            Or bank it: {timing.get('reason', '')}".rstrip())

    # ADR-186 — the better move just out of reach. Placed after the immediate advice, never instead of it:
    # the move you can make today stays the headline, and this is the reason you might not want to.
    cliff = plan.get("cliff")
    if cliff:
        move = cliff["move"]
        # The span is named, because the number is over the wider window while the headline transfer above
        # it is priced over the page's horizon — unlabelled, the two would look like the same yardstick.
        span = plan.get("horizon_gw", 5)
        out.append(f"            Worth saving for: £{cliff['extra']:.1f}m more makes this "
                   f"{move['out']['web_name']} → {move['in']['web_name']} "
                   f"({cliff['gain']:+.1f} XI xP over {span} GWs, {cliff['uplift']:+.1f} on the move above)")
    return out


def render_gameweek_plan(plan, squad_name, horizon: int = 5, explanation=None) -> str:
    """The one-gameweek plan as a readable block (ADR-070). `horizon` labels the transfer's window
    (ADR-077); the captain + lineup are inherently about the immediate week. `explanation`
    (`explain_gameweek`, ADR-089) adds a per-recommendation Confidence + a short Edge."""
    ex = explanation or {}
    cap_ex, tr_ex = ex.get("captain"), ex.get("transfer")
    lines = [f"This week — squad '{squad_name}'", ""]

    if ex.get("overall"):   # the plan-level Confidence · Edge · Risk summary (US-274, ADR-089)
        lines += [render_explanation(ex["overall"]), ""]

    lines.append(f"  Captain:  {_captain_line(plan['captain'])}{_conf(cap_ex)}")
    if cap_ex and cap_ex.reasons:
        lines.append("            Edge: " + " · ".join(cap_ex.reasons[:3]))

    lines.append(f"  Lineup:   {_lineup_line(plan['lineup'])}")
    lines += [f"            {r}" for r in (ex.get("lineup") or [])]

    lines += _replace_lines(plan.get("replacements"), horizon)

    lines.append(f"  Transfer: "
                 f"{_transfer_line(plan['transfer'], horizon, has_dead=bool(plan.get('replacements')))}"
                 f"{_conf(tr_ex)}")
    if tr_ex and tr_ex.reasons:
        lines.append("            Edge: " + " · ".join(tr_ex.reasons[:2]))
    lines += _extra_move_lines(plan, horizon)
    lines += _timing_lines(plan, horizon)

    lines.append(f"  Flags:    {_flags_line(plan['flags'])}")
    if explanation:                       # the honest attribution closing an explained plan (US-278)
        lines += ["", MODEL_NOTE]
    return "\n".join(lines)
