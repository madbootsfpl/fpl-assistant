"""Console rendering for over/under-performance (ADR-017).

Pure formatting: takes the ranked rows (from analytics.over_under) and shows two ends —
the biggest over-performers (regression risk) and under-performers (bounce-back). Only
attacking returns are compared, so a caveat is printed to stop the number being over-read.

The two tables share the shape from the shared renderer (`ui._table`, ADR-025) — each
section calls `render_rows` with `divider=False`, so its rank column restarts at 1.
"""

from ._table import Col, render_rows

_NAME_W = 16

_COLS = [
    Col("Player", _NAME_W, "<", lambda r: str(r["web_name"])[:_NAME_W]),
    Col("Team", 5, "<", lambda r: str(r["team"] or "")),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("Mins", 6, ">", lambda r: str(r["minutes"])),
    Col("Actual", 7, ">", lambda r: f"{r['actual']:.1f}"),
    Col("Exp", 7, ">", lambda r: f"{r['expected']:.1f}"),
    Col("Diff", 7, ">", lambda r: f"{r['diff']:+.1f}"),
]


def render_overperf(rows, limit: int = 10, min_minutes: int = 900) -> str:
    if not rows:
        return (
            f"No players with at least {min_minutes} minutes — run `refresh` first, "
            "or lower --min-minutes."
        )

    over = rows[:limit]                          # sorted desc by diff → most over first
    seen = {id(r) for r in over}
    under = [r for r in reversed(rows) if id(r) not in seen][:limit]

    lines = [
        f"Over/under-performance — attacking points, players ≥ {min_minutes} mins", "",
        "Over-performing (finishing hot → regression risk):",
    ]
    lines += render_rows(over, _COLS, rank=True, divider=False)

    lines.append("")
    lines.append("Under-performing (unlucky → bounce-back):")
    lines += render_rows(under, _COLS, rank=True, divider=False)

    lines.append("")
    lines.append(
        "Diff = actual − expected attacking points (goals & assists only — not clean "
        "sheets / appearance / bonus). A tendency, not a certainty."
    )
    return "\n".join(lines)
