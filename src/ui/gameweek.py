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


def _transfer_line(transfer, horizon: int = 5) -> str:
    if not transfer:
        return "no positive-gain upgrade — hold your transfer"
    out, inc = transfer["out"], transfer["in"]
    window = f"over {horizon} GW" if horizon != 1 else "next GW"
    return (f"{out['web_name']} ({out['team']}) → {inc['web_name']} ({inc['team']})  "
            f"(+{transfer['gain']} XI xP {window})")


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

    lines.append(f"  Transfer: {_transfer_line(plan['transfer'], horizon)}{_conf(tr_ex)}")
    if tr_ex and tr_ex.reasons:
        lines.append("            Edge: " + " · ".join(tr_ex.reasons[:2]))

    lines.append(f"  Flags:    {_flags_line(plan['flags'])}")
    if explanation:                       # the honest attribution closing an explained plan (US-278)
        lines += ["", MODEL_NOTE]
    return "\n".join(lines)
