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


def render_transfers(suggestions, squad_name: str, bank: float = 0.0, horizon: int = 5) -> str:
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

    lines.append("")
    lines.append(
        "Each is a single, legal, affordable swap (same position, ≤3/club, within the sale "
        "price + bank). `(b)` = the player you'd sell is on your bench (less weekly impact). "
        "xP is a mean over the horizon and assumes the incoming player starts."
    )
    return "\n".join(lines)
