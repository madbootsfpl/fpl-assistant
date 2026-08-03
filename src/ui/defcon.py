"""Console rendering for Defensive Contribution reliability (ADR-018).

Pure formatting: takes the ranked rows (from analytics.defcon_reliability) and lists the
most reliable DefCon-point earners — per-90 defensive actions vs the position threshold.
A positive margin means they clear the bar on average; the bigger the margin, the safer.

The table shape comes from the shared renderer (`ui._table`, ADR-025); this module
supplies the columns, title, and footer.
"""

from ._table import Col, render_rows

_NAME_W = 16

_COLS = [
    Col("Player", _NAME_W, "<", lambda r: str(r["web_name"])[:_NAME_W]),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("Mins", 6, ">", lambda r: str(r["minutes"])),
    Col("DC/90", 7, ">", lambda r: f"{r['per90']:.1f}"),
    Col("Thr", 7, ">", lambda r: str(r["threshold"])),
    Col("Margin", 7, ">", lambda r: f"{r['margin']:+.1f}"),
]


def render_defcon(rows, limit: int = 20, min_minutes: int = 900) -> str:
    if not rows:
        return (
            f"No outfield players with at least {min_minutes} minutes — run `refresh` "
            "first, or lower --min-minutes."
        )

    lines = [
        f"Defensive Contribution — per-90 vs threshold, players ≥ {min_minutes} mins",
        "",
    ]
    lines += render_rows(rows[:limit], _COLS, rank=True)

    lines.append("")
    lines.append(
        "Margin = DC/90 − threshold (DEF 10, MID/FWD 12; GK n/a). Positive = clears the "
        "bar on average — a reliability guide, not a guaranteed 2 pts every match."
    )
    return "\n".join(lines)
