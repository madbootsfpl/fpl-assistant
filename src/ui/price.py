"""Console rendering for the 'price' intent (Sprint 128, ADR-092).

A directional price-change list — likely risers 🔺 / fallers 🔻 by transfer pressure (net transfers per 1%
ownership). A display lens, never xP; **0 on flat preseason data → live from GW1**. Built on the shared table
renderer (ADR-025).
"""

from ._table import Col, render_rows

_NAME_W = 17


def _mover_rows(rows):
    cols = [
        Col("Player", _NAME_W, "<", lambda r: str(r["web_name"])[:_NAME_W]),
        Col("Team", 5, "<", lambda r: str(r["team"] or "")),
        Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
        Col("Own%", 6, ">", lambda r: f"{r.get('selected_by') or 0:.1f}"),
        Col("Pressure", 10, ">", lambda r: f"{r['pressure']:+,.0f}"),
    ]
    return render_rows(rows, cols, rank=True)


def render_price_movers(risers, fallers) -> str:
    """A price-mover block: 🔺 likely risers then 🔻 likely fallers, each ranked by transfer pressure."""
    lines = ["Price change predictor — directional pressure (a flag, not the exact price or timing)", ""]
    lines.append("🔺 Likely to rise:")
    lines += _mover_rows(risers) if risers else ["  (none)"]
    lines += ["", "🔻 Likely to fall:"]
    lines += _mover_rows(fallers) if fallers else ["  (none)"]
    lines += ["", "Net transfers per 1% ownership — a directional flag, not the exact price/timing; "
              "sharpens in-season (live from GW1)."]
    return "\n".join(lines)
