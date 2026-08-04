"""Console rendering for the start/bench lineup recommendation (ADR-039).

Pure formatting: the best legal XI (by xMins-weighted xP) and the bench, plus the change
vs the manager's declared bench (or "already optimal"). Built on the shared table renderer
(ADR-025); shows the xMins column (ADR-038) so a rotation risk on the bench is visible.
"""

from src.analytics.minutes import expected_minutes

from ._table import Col, render_rows

_NAME_W = 18


def _name(r) -> str:
    """Player name with an availability marker when injured/suspended/doubtful."""
    name = str(r["web_name"])
    if r["status"] == "d" and r.get("chance") is not None:
        name = f"{name} (d {r['chance']}%)"
    elif r["status"] in ("i", "s", "u", "n"):
        name = f"{name} ({r['status']})"
    return name[:_NAME_W]


_COLS = [
    Col("Player", _NAME_W, "<", _name),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("xMins", 6, ">", lambda r: str(expected_minutes(r.get("minutes_weight")))),
    Col("xP", 6, ">", lambda r: f"{r['xp']:.1f}"),
]


def render_start_bench(xi, bench, change_line: str, squad_name: str, projected_xp) -> str:
    lines = [
        f"Recommended lineup — '{squad_name}' (best legal XI by xMins-weighted xP)", "",
        f"  Projected XI xP : {projected_xp}", "",
        "Start (XI):",
    ]
    lines += render_rows(xi, _COLS, rank=True)
    lines += ["", "Bench:"]
    lines += render_rows(bench, _COLS, rank=True) if bench else ["  (none)"]
    lines += [
        "", change_line, "",
        "`xMins` = expected minutes next GW (xMins v0); the XI is chosen on xMins-weighted xP over the "
        "horizon (a mean; assumes availability). Use `analyse --squad --no-xmins` for the raw view.",
    ]
    return "\n".join(lines)
