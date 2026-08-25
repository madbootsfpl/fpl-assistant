"""Console rendering for the 'price' intent (Sprint 128, ADR-092).

A directional price-change list — likely risers ▲ / fallers ▼ by transfer pressure (net transfers per 1%
ownership). A display lens, never xP; **0 on flat preseason data → live from GW1**. Built on the shared table
renderer (ADR-025).
"""

from src.analytics.price import PRICE_DOWN, PRICE_UP

from ._table import Col, render_rows

_NAME_W = 17


def _mover_rows(rows):
    """Render the mover table. `rows` are the **display dicts** built by the caller, not player rows.

    Worth stating, because the shape is not obvious: `pressure` is computed by the caller and exists on no
    player record, so a `sqlite3.Row` handed to this raises. `.get()` below is safe precisely because the
    contract is a dict.
    """
    cols = [
        Col("Player", _NAME_W, "<", lambda r: str(r["web_name"])[:_NAME_W]),
        Col("Team", 5, "<", lambda r: str(r["team"] or "")),
        Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
        Col("Own%", 6, ">", lambda r: f"{r.get('selected_by') or 0:.1f}"),
        Col("Pressure", 10, ">", lambda r: f"{r['pressure']:+,.0f}"),
    ]
    return render_rows(rows, cols, rank=True)


def render_price_movers(risers, fallers) -> str:
    """A price-mover block: ▲ likely risers then ▼ likely fallers, each ranked by transfer pressure.

    Same glyph pair as the web (ADR-140), from `analytics.price`, so the two surfaces cannot drift. A terminal
    renders them uncoloured — which is no worse than the two *identically red* emoji they replace, since the
    section headers already carry the direction here.
    """
    lines = ["Price change predictor — directional pressure (a flag, not the exact price or timing)", ""]
    lines.append(f"{PRICE_UP} Likely to rise:")
    lines += _mover_rows(risers) if risers else ["  (none)"]
    lines += ["", f"{PRICE_DOWN} Likely to fall:"]
    lines += _mover_rows(fallers) if fallers else ["  (none)"]
    lines += ["", "Net transfers per 1% ownership — a directional flag, not the exact price/timing; "
              "sharpens in-season (live from GW1)."]
    return "\n".join(lines)
