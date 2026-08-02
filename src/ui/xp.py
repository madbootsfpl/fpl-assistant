"""Console rendering for the Expected Points (xP) table.

Pure formatting: it takes the ranked xP rows (from analytics.player_xp) and returns
a string. Over a single gameweek it shows FPL's own `ep_next` for comparison; over a
multi-gameweek horizon that comparison isn't valid (ours is a sum, FPL's is one GW),
so the FPL column is hidden and a note explains why (ADR-007).
"""

_RANK_W = 3
_NAME_W = 17
_TEAM_W = 5
_POS_W = 4
_GAMES_W = 5
_XP_W = 6
_EP_W = 5


def render_xp_table(rows, limit: int = 20, source: str = "fpl", horizon: int = 1) -> str:
    total = len(rows)
    if total == 0:
        return "No players to rank — run `refresh` first."

    header = (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
        f"{'Pos':<{_POS_W}} {'Games':>{_GAMES_W}} {'xP':>{_XP_W}} {'FPL':>{_EP_W}}"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _NAME_W} {'-' * _TEAM_W} "
        f"{'-' * _POS_W} {'-' * _GAMES_W} {'-' * _XP_W} {'-' * _EP_W}"
    )

    lines = [header, divider]
    for rank, r in enumerate(rows[:limit], start=1):
        name = str(r["web_name"])[:_NAME_W]
        team = str(r["team"] or "")
        pos = str(r["position"] or "")
        games = r["games"]
        xp = f"{r['xp']:.1f}"
        # FPL's ep_next is a single-gameweek number — only comparable at horizon 1.
        if horizon == 1 and r["ep_next"] is not None:
            ep = f"{r['ep_next']:.1f}"
        else:
            ep = "—"
        lines.append(
            f"{rank:<{_RANK_W}} {name:<{_NAME_W}} {team:<{_TEAM_W}} "
            f"{pos:<{_POS_W}} {games:>{_GAMES_W}} {xp:>{_XP_W}} {ep:>{_EP_W}}"
        )

    lines.append("")
    window = "the next gameweek" if horizon == 1 else f"the next {horizon} gameweeks"
    shown = "all" if total <= limit else f"top {limit} of"
    lines.append(f"Showing {shown} {total} by xP over {window} (difficulty source: {source}).")
    if horizon > 1:
        lines.append(
            "FPL column hidden — ep_next is next-gameweek only, not comparable to a multi-GW total."
        )
    return "\n".join(lines)
