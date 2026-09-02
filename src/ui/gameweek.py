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
    lines += _timing_lines(plan, horizon)

    lines.append(f"  Flags:    {_flags_line(plan['flags'])}")
    if explanation:                       # the honest attribution closing an explained plan (US-278)
        lines += ["", MODEL_NOTE]
    return "\n".join(lines)
