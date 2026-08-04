"""Console rendering for the team analyser (ADR-031).

Pure formatting: takes the indicators (from analytics.analyse_squad) and lays out a
squad health check — a summary block, the XI and bench tables, and highlights that
cross-link to `captain` and `transfer`. Built on the shared table renderer (ADR-025).
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


_BASE_COLS = [
    Col("Player", _NAME_W, "<", _name),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("£", 6, ">", lambda r: f"{r['price']:.1f}"),
]
_XP_COL = Col("xP", 6, ">", lambda r: f"{r['xp']:.1f}")
_XMINS_COL = Col("xMins", 6, ">", lambda r: str(expected_minutes(r.get("minutes_weight"))))


def _columns(gameweeks, show_xmins=False):
    """Base columns + a per-GW column per gameweek (ADR-032) + the total, when present.

    With `show_xmins` (xMins v0, ADR-038), an expected-minutes column precedes the total.
    """
    cols = list(_BASE_COLS)
    for gw in gameweeks:
        cols.append(
            Col(f"GW{gw}", 5, ">", lambda r, gw=gw: f"{r['by_gameweek'].get(gw, 0):.1f}")
        )
    if show_xmins:
        cols.append(_XMINS_COL)
    cols.append(_XP_COL)
    return cols


def render_squad_analysis(analysis: dict, squad_name: str, show_xmins: bool = False) -> str:
    horizon = analysis["horizon"]
    window = f"{horizon} GW" if horizon != 1 else "next GW"
    cols = _columns(analysis.get("gameweeks") or [], show_xmins=show_xmins)

    lines = [
        f"Squad analysis — '{squad_name}' over the next {window}", "",
        f"  Projected XI xP : {analysis['projected_xp']:>6}   "
        f"(bench {analysis['bench_xp']})",
        f"  Squad value     : £{analysis['value']:.1f}m   "
        f"Availability issues: {len(analysis['issues'])}",
    ]
    if analysis["concentrated_clubs"]:
        clubs = ", ".join(analysis["concentrated_clubs"])
        lines.append(f"  At the 3-per-club cap: {clubs} (less transfer room)")

    lines += ["", "Starting XI:"]
    lines += render_rows(analysis["xi"], cols, rank=True)

    lines += ["", "Bench:"]
    if analysis["bench"]:
        lines += render_rows(analysis["bench"], cols, rank=True)
    else:
        lines.append("  (none — no bench in this squad)")

    lines.append("")
    top = analysis["top_pick"]
    if top:
        lines.append(
            f"Captain lead : {top['web_name']} ({top['xp']} xP) — `captain --squad {squad_name}`."
        )
    weak = ", ".join(f"{w['web_name']} ({w['xp']})" for w in analysis["weakest"])
    lines.append(f"Weakest links: {weak} — `transfer --squad {squad_name}`.")
    if analysis["issues"]:
        names = ", ".join(p["web_name"] for p in analysis["issues"])
        lines.append(f"Availability : {names}.")

    lines.append("")
    xmins_note = (
        "`xMins` = expected minutes next GW (xMins v0); xP is weighted by it (`--no-xmins` for raw). "
        if show_xmins else ""
    )
    plays = "weighted by expected minutes" if show_xmins else "assumes they play"
    lines.append(
        f"GWn = projected xP that gameweek (rounded; the xP total is authoritative). {xmins_note}"
        f"Projected xP is the XI's expected points over the horizon (a mean; {plays}). `--load` shows "
        "the current state; `--sort xp` orders the XI by xP."
    )
    return "\n".join(lines)
