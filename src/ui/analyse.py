"""Console rendering for the team analyser (ADR-031).

Pure formatting: takes the indicators (from analytics.analyse_squad) and lays out a
squad health check — a summary block, the XI and bench tables, and highlights that
cross-link to `captain` and `transfer`. Built on the shared table renderer (ADR-025).
"""

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
    Col("£", 6, ">", lambda r: f"{r['price']:.1f}"),
    Col("xP", 6, ">", lambda r: f"{r['xp']:.1f}"),
]


def render_squad_analysis(analysis: dict, squad_name: str) -> str:
    horizon = analysis["horizon"]
    window = f"{horizon} GW" if horizon != 1 else "next GW"

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
    lines += render_rows(analysis["xi"], _COLS, rank=True)

    lines += ["", "Bench:"]
    if analysis["bench"]:
        lines += render_rows(analysis["bench"], _COLS, rank=True)
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
    lines.append(
        "Projected xP is the starting XI's expected points over the horizon (a mean; "
        "it assumes they play). `--load` shows the current state instead."
    )
    return "\n".join(lines)
