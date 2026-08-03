"""Console rendering for the clean-sheet / defensive-solidity lens (ADR-019).

Pure formatting: takes the ranked rows (from analytics.defensive_solidity) and lists the
DEF/GK with the lowest expected goals conceded per 90 — the best clean-sheet prospects.

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
    Col("xGC/90", 8, ">", lambda r: f"{r['xgc90']:.2f}"),
]


def render_cleansheet(rows, limit: int = 20, min_minutes: int = 900) -> str:
    if not rows:
        return (
            f"No DEF/GK with at least {min_minutes} minutes — run `refresh` first, "
            "or lower --min-minutes."
        )

    lines = [
        f"Clean-sheet prospects — xGC/90 (lowest = best), DEF/GK ≥ {min_minutes} mins",
        "",
    ]
    lines += render_rows(rows[:limit], _COLS, rank=True)

    lines.append("")
    lines.append(
        "xGC/90 = expected goals conceded per 90 — a *team* defensive signal shown per "
        "player (teammates cluster). Lower = more likely a clean sheet, not a guarantee."
    )
    return "\n".join(lines)
