"""Console rendering for the clean-sheet / defensive-solidity lens (ADR-019).

Pure formatting: takes the ranked rows (from analytics.defensive_solidity) and lists the
DEF/GK with the lowest expected goals conceded per 90 — the best clean-sheet prospects.
"""

_RANK_W = 3
_NAME_W = 16
_TEAM_W = 5
_POS_W = 4
_MIN_W = 6
_NUM_W = 8


def render_cleansheet(rows, limit: int = 20, min_minutes: int = 900) -> str:
    if not rows:
        return (
            f"No DEF/GK with at least {min_minutes} minutes — run `refresh` first, "
            "or lower --min-minutes."
        )

    header = (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} {'Pos':<{_POS_W}} "
        f"{'Mins':>{_MIN_W}} {'xGC/90':>{_NUM_W}}"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _NAME_W} {'-' * _TEAM_W} {'-' * _POS_W} "
        f"{'-' * _MIN_W} {'-' * _NUM_W}"
    )

    lines = [
        f"Clean-sheet prospects — xGC/90 (lowest = best), DEF/GK ≥ {min_minutes} mins",
        "", header, divider,
    ]
    for rank, r in enumerate(rows[:limit], start=1):
        lines.append(
            f"{rank:<{_RANK_W}} {str(r['web_name'])[:_NAME_W]:<{_NAME_W}} "
            f"{str(r['team'] or ''):<{_TEAM_W}} {str(r['position'] or ''):<{_POS_W}} "
            f"{r['minutes']:>{_MIN_W}} {r['xgc90']:>{_NUM_W}.2f}"
        )

    lines.append("")
    lines.append(
        "xGC/90 = expected goals conceded per 90 — a *team* defensive signal shown per "
        "player (teammates cluster). Lower = more likely a clean sheet, not a guarantee."
    )
    return "\n".join(lines)
