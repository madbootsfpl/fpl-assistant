"""Console rendering for the Expected Points (xP) table.

Pure formatting: it takes the ranked xP rows (from analytics.player_xp) and returns
a string, showing our xP next to FPL's own `ep_next` for comparison.
"""

_RANK_W = 3
_NAME_W = 17
_TEAM_W = 5
_POS_W = 4
_XP_W = 5
_EP_W = 5
_DIFF_W = 4


def render_xp_table(rows, limit: int = 20, source: str = "fpl") -> str:
    total = len(rows)
    if total == 0:
        return "No players to rank — run `refresh` first."

    header = (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
        f"{'Pos':<{_POS_W}} {'xP':>{_XP_W}} {'FPL':>{_EP_W}} {'Diff':>{_DIFF_W}}"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _NAME_W} {'-' * _TEAM_W} "
        f"{'-' * _POS_W} {'-' * _XP_W} {'-' * _EP_W} {'-' * _DIFF_W}"
    )

    lines = [header, divider]
    for rank, r in enumerate(rows[:limit], start=1):
        name = str(r["web_name"])[:_NAME_W]
        team = str(r["team"] or "")
        pos = str(r["position"] or "")
        xp = f"{r['xp']:.1f}"
        ep = f"{r['ep_next']:.1f}" if r["ep_next"] is not None else "—"
        diff = str(r["difficulty"]) if r["difficulty"] is not None else "—"
        lines.append(
            f"{rank:<{_RANK_W}} {name:<{_NAME_W}} {team:<{_TEAM_W}} "
            f"{pos:<{_POS_W}} {xp:>{_XP_W}} {ep:>{_EP_W}} {diff:>{_DIFF_W}}"
        )

    lines.append("")
    shown = "all" if total <= limit else f"top {limit} of"
    lines.append(f"Showing {shown} {total} by xP (difficulty source: {source}).")
    return "\n".join(lines)
