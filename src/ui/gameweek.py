"""Console rendering for the gameweek plan (ADR-070).

A plain-text block — Captain / Lineup / Transfer / Flags — that is the exact plan the analytics
assembled (`gameweek_plan`). It shows with or without the LLM (the prose is a bonus); the same
"the block is the truth" shape the other `ask` details use. Rendered in the CLI and, via
`render_ask`, in the web's Squads → AI Tips view.
"""


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


def render_gameweek_plan(plan, squad_name, horizon: int = 5) -> str:
    """The one-gameweek plan as a readable block (ADR-070). `horizon` labels the transfer's window
    (ADR-077); the captain + lineup are inherently about the immediate week."""
    return "\n".join([
        f"This week — squad '{squad_name}'",
        "",
        f"  Captain:  {_captain_line(plan['captain'])}",
        f"  Lineup:   {_lineup_line(plan['lineup'])}",
        f"  Transfer: {_transfer_line(plan['transfer'], horizon)}",
        f"  Flags:    {_flags_line(plan['flags'])}",
    ])
