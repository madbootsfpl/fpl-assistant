"""Console rendering for over/under-performance (ADR-017).

Pure formatting: takes the ranked rows (from analytics.over_under) and shows two ends —
the biggest over-performers (regression risk) and under-performers (bounce-back). Only
attacking returns are compared, so a caveat is printed to stop the number being over-read.
"""

_RANK_W = 3
_NAME_W = 16
_TEAM_W = 5
_POS_W = 4
_MIN_W = 6
_NUM_W = 7


def _header():
    return (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} {'Pos':<{_POS_W}} "
        f"{'Mins':>{_MIN_W}} {'Actual':>{_NUM_W}} {'Exp':>{_NUM_W}} {'Diff':>{_NUM_W}}"
    )


def _row(rank, r):
    return (
        f"{rank:<{_RANK_W}} {str(r['web_name'])[:_NAME_W]:<{_NAME_W}} "
        f"{str(r['team'] or ''):<{_TEAM_W}} {str(r['position'] or ''):<{_POS_W}} "
        f"{r['minutes']:>{_MIN_W}} {r['actual']:>{_NUM_W}.1f} {r['expected']:>{_NUM_W}.1f} "
        f"{r['diff']:>+{_NUM_W}.1f}"
    )


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
        "Over-performing (finishing hot → regression risk):", _header(),
    ]
    for rank, r in enumerate(over, start=1):
        lines.append(_row(rank, r))

    lines.append("")
    lines.append("Under-performing (unlucky → bounce-back):")
    lines.append(_header())
    for rank, r in enumerate(under, start=1):
        lines.append(_row(rank, r))

    lines.append("")
    lines.append(
        "Diff = actual − expected attacking points (goals & assists only — not clean "
        "sheets / appearance / bonus). A tendency, not a certainty."
    )
    return "\n".join(lines)
