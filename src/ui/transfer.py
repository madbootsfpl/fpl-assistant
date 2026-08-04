"""Console rendering for transfer suggestions (ADR-030).

Pure formatting: takes the ranked moves (from analytics.suggest_transfers) and shows each
as OUT → IN with prices, xP, and the gain — a recommendation that explains itself. Built on
the shared table renderer (ui._table, ADR-025).
"""

from ._table import Col, render_rows

_OUT_W = 16
_IN_W = 16


def _out_name(s) -> str:
    name = str(s["out"]["web_name"])
    if s.get("out_on_bench"):
        name = f"{name} (b)"          # the player you'd sell is on your bench
    return name[:_OUT_W]


_COLS = [
    Col("Out", _OUT_W, "<", _out_name),
    Col("£", 5, ">", lambda s: f"{s['out']['price']:.1f}"),
    Col("xP", 6, ">", lambda s: f"{s['out']['xp']:.1f}"),
    Col("→", 1, "<", lambda s: "→"),
    Col("In", _IN_W, "<", lambda s: str(s["in"]["web_name"])[:_IN_W]),
    Col("£", 5, ">", lambda s: f"{s['in']['price']:.1f}"),
    Col("xP", 6, ">", lambda s: f"{s['in']['xp']:.1f}"),
    Col("ΔxP", 6, ">", lambda s: f"+{s['gain']:.1f}"),
]


def _plan_columns(gameweeks, by_gameweek_by_id):
    """Out → In, then a per-GW column of the *incoming* player's xP (ADR-036), then the gain."""
    cols = [
        Col("Out", _OUT_W, "<", _out_name),
        Col("→", 1, "<", lambda s: "→"),
        Col("In", _IN_W, "<", lambda s: str(s["in"]["web_name"])[:_IN_W]),
    ]
    for gw in gameweeks:
        cols.append(Col(
            f"GW{gw}", 5, ">",
            lambda s, gw=gw: f"{by_gameweek_by_id.get(s['in']['id'], {}).get(gw, 0):.1f}",
        ))
    cols.append(Col("ΔxP", 6, ">", lambda s: f"+{s['gain']:.1f}"))
    return cols


def render_transfer_plan(
    plan, squad_name: str, bank: float = 0.0, horizon: int = 5,
    by_gameweek_by_id=None, gameweeks=(), show_xmins: bool = False,
) -> str:
    window = f"{horizon} gameweek{'s' if horizon != 1 else ''}"
    if not plan:
        return (
            f"No positive-gain transfer plan for '{squad_name}' over the next {window} "
            f"(bank £{bank:.1f}m). Try a larger --bank, or the squad may already be strong."
        )

    total = round(sum(m["gain"] for m in plan), 1)
    end_bank = plan[-1]["bank_after"]
    cols = _plan_columns(gameweeks, by_gameweek_by_id or {})
    lines = [
        f"Transfer plan for '{squad_name}' — {len(plan)} move(s) by xP gain over the next "
        f"{window} (start bank £{bank:.1f}m). GWn = the incoming player's projected xP that week.",
        "",
    ]
    lines += render_rows(plan, cols, rank=True)
    xmins_note = (
        " xP is weighted by expected minutes (xMins v0; `--no-xmins` for raw)." if show_xmins else ""
    )
    lines += [
        "",
        f"Total: +{total} xP over {window} · end bank £{end_bank:.1f}m.",
        "A coordinated plan — each move is legal given the last (shared bank, ≤3/club, no repeats; "
        "`(b)` = selling a benched player). Assumes you have that many free transfers — hits (−4) "
        f"aren't modelled — and it's greedy, so not guaranteed optimal.{xmins_note}",
    ]
    return "\n".join(lines)


def render_transfers(
    suggestions, squad_name: str, bank: float = 0.0, horizon: int = 5, show_xmins: bool = False,
) -> str:
    window = f"{horizon} gameweek{'s' if horizon != 1 else ''}"
    if not suggestions:
        return (
            f"No positive-gain transfers for '{squad_name}' over the next {window} "
            f"(bank £{bank:.1f}m). The squad may already be strong — or try a larger --bank."
        )

    lines = [
        f"Transfer suggestions for '{squad_name}' — by xP gain over the next {window} "
        f"(bank £{bank:.1f}m)", "",
    ]
    lines += render_rows(suggestions, _COLS, rank=True)

    starts = (
        "xP is weighted by expected minutes (xMins v0; `--no-xmins` for raw)."
        if show_xmins else "xP is a mean over the horizon and assumes the incoming player starts."
    )
    lines.append("")
    lines.append(
        "Each is a single, legal, affordable swap (same position, ≤3/club, within the sale "
        f"price + bank). `(b)` = the player you'd sell is on your bench (less weekly impact). {starts}"
    )
    return "\n".join(lines)
