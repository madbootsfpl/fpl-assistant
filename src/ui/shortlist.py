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


def render_shortlist(rows, title: str) -> str:
    lines = [title, ""]
    lines += render_rows(rows, _COLS, rank=True)
    lines += [
        "",
        "`xP` = expected points over the next 5 GW (xMins-weighted); `xMins` = expected minutes next "
        "GW. Injured/suspended players are excluded.",
    ]
    return "\n".join(lines)
