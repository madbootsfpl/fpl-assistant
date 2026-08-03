"""Console rendering for Defensive Contribution reliability (ADR-018).

Pure formatting: takes the ranked rows (from analytics.defcon_reliability) and lists the
most reliable DefCon-point earners — per-90 defensive actions vs the position threshold.
A positive margin means they clear the bar on average; the bigger the margin, the safer.
"""

_RANK_W = 3
_NAME_W = 16
_TEAM_W = 5
_POS_W = 4
_MIN_W = 6
_NUM_W = 7


def render_defcon(rows, limit: int = 20, min_minutes: int = 900) -> str:
    if not rows:
        return (
            f"No outfield players with at least {min_minutes} minutes — run `refresh` "
            "first, or lower --min-minutes."
        )

    header = (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} {'Pos':<{_POS_W}} "
        f"{'Mins':>{_MIN_W}} {'DC/90':>{_NUM_W}} {'Thr':>{_NUM_W}} {'Margin':>{_NUM_W}}"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _NAME_W} {'-' * _TEAM_W} {'-' * _POS_W} "
        f"{'-' * _MIN_W} {'-' * _NUM_W} {'-' * _NUM_W} {'-' * _NUM_W}"
    )

    lines = [
        f"Defensive Contribution — per-90 vs threshold, players ≥ {min_minutes} mins",
        "", header, divider,
    ]
    for rank, r in enumerate(rows[:limit], start=1):
        lines.append(
            f"{rank:<{_RANK_W}} {str(r['web_name'])[:_NAME_W]:<{_NAME_W}} "
            f"{str(r['team'] or ''):<{_TEAM_W}} {str(r['position'] or ''):<{_POS_W}} "
            f"{r['minutes']:>{_MIN_W}} {r['per90']:>{_NUM_W}.1f} {r['threshold']:>{_NUM_W}} "
            f"{r['margin']:>+{_NUM_W}.1f}"
        )

    lines.append("")
    lines.append(
        "Margin = DC/90 − threshold (DEF 10, MID/FWD 12; GK n/a). Positive = clears the "
        "bar on average — a reliability guide, not a guaranteed 2 pts every match."
    )
    return "\n".join(lines)
