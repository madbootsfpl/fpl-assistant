"""Console rendering for the expected-goals (xG / xA / xGI) table.

Pure formatting: it takes player rows (from storage, already sorted by xGI) and returns
a string. xGI = xG + xA is the headline attacking involvement; xGC (goals conceded) is a
defensive counterpoint. Values may be None on a database refreshed before Sprint 014, so
they're coerced to 0.0 for display.
"""

_RANK_W = 3
_NAME_W = 17
_TEAM_W = 5
_POS_W = 4
_NUM_W = 6


def _n(value) -> float:
    return value or 0.0


def render_xg_table(rows, limit: int = 20, pos: str | None = None) -> str:
    total = len(rows)
    if total == 0:
        return "No players to rank — run `refresh` first."

    header = (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} {'Pos':<{_POS_W}} "
        f"{'xG':>{_NUM_W}} {'xA':>{_NUM_W}} {'xGI':>{_NUM_W}} {'xGC':>{_NUM_W}}"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _NAME_W} {'-' * _TEAM_W} {'-' * _POS_W} "
        f"{'-' * _NUM_W} {'-' * _NUM_W} {'-' * _NUM_W} {'-' * _NUM_W}"
    )

    lines = [header, divider]
    for rank, r in enumerate(rows[:limit], start=1):
        name = str(r["web_name"])[:_NAME_W]
        team = str(r["team"] or "")
        position = str(r["position"] or "")
        lines.append(
            f"{rank:<{_RANK_W}} {name:<{_NAME_W}} {team:<{_TEAM_W}} {position:<{_POS_W}} "
            f"{_n(r['xg']):>{_NUM_W}.1f} {_n(r['xa']):>{_NUM_W}.1f} "
            f"{_n(r['xgi']):>{_NUM_W}.1f} {_n(r['xgc']):>{_NUM_W}.1f}"
        )

    lines.append("")
    scope = f" ({pos.upper()})" if pos else ""
    shown = "all" if total <= limit else f"top {limit} of"
    lines.append(f"Showing {shown} {total} players{scope} by xGI (last-season expected goals).")
    return "\n".join(lines)
