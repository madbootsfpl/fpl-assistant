"""Console rendering for the shortlist intent (ADR-042).

Pure formatting: the top players for a position/price query, ranked by the unified xP
(or xP-per-£m for "value"). Shows price + the xMins column (ADR-038). Built on the shared
table renderer (ADR-025).
"""

from src.analytics.minutes import expected_minutes

from ._table import Col, render_rows

_NAME_W = 17


def _name(r) -> str:
    name = str(r["web_name"])
    if r.get("status") == "d" and r.get("chance") is not None:
        name = f"{name} (d {r['chance']}%)"
    return name[:_NAME_W]


_COLS = [
    Col("Player", _NAME_W, "<", _name),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("£", 6, ">", lambda r: f"{r['price']:.1f}"),
    Col("xMins", 6, ">", lambda r: str(expected_minutes(r.get("minutes_weight")))),
    Col("xP", 6, ">", lambda r: f"{r['xp']:.1f}"),
]

# The differential shortlist (ADR-061) adds an ownership column after price.
_OWN_COL = Col("Own%", 6, ">", lambda r: f"{r['selected_by'] or 0:.1f}")


def render_shortlist(rows, title: str, *, show_own: bool = False) -> str:
    """Render the shortlist (ADR-042). `show_own` adds an Own% column for the differential lens
    (ADR-061); without it the output is byte-identical to before."""
    cols = _COLS if not show_own else [*_COLS[:4], _OWN_COL, *_COLS[4:]]
    lines = [title, ""]
    lines += render_rows(rows, cols, rank=True)
    note = ("`xP` = expected points over the next 5 GW (xMins-weighted); `xMins` = expected minutes next "
            "GW. Injured/suspended players are excluded.")
    if show_own:
        note += " `Own%` = ownership; differentials are ≤5%-owned (this sharpens once the season starts)."
    lines += ["", note]
    return "\n".join(lines)
