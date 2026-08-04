"""Console rendering for the Expected Points (xP) table.

Pure formatting: it takes the ranked xP rows (from analytics.player_xp) and returns
a string. Over a single gameweek it shows FPL's own `ep_next` for comparison; over a
multi-gameweek horizon that comparison isn't valid (ours is a sum, FPL's is one GW),
so the FPL column is hidden and a note explains why (ADR-007).

The `Rate` column is the per-match scoring rate xP used (ADR-028): a `*` marks a
multi-season historical baseline; plain is the current single season (the fallback
for players with no history).
"""

from ._table import Col, render_rows

_RANK_W = 3
_NAME_W = 17
_TEAM_W = 5
_POS_W = 4
_GAMES_W = 5
_RATE_W = 6
_XP_W = 6
_EP_W = 5


def _render_by_gameweek(rows, limit: int, source: str) -> str:
    """Per-gameweek layout (ADR-032): a GW column per horizon gameweek, then the total."""
    total = len(rows)
    gameweeks = rows[0].get("gameweeks") or []
    cols = [
        Col("Player", _NAME_W, "<", lambda r: str(r["web_name"])[:_NAME_W]),
        Col("Team", _TEAM_W, "<", lambda r: str(r["team"] or "")),
        Col("Pos", _POS_W, "<", lambda r: str(r["position"] or "")),
    ]
    for gw in gameweeks:
        cols.append(
            Col(f"GW{gw}", 5, ">", lambda r, gw=gw: f"{r['by_gameweek'].get(gw, 0):.1f}")
        )
    cols.append(Col("xP", _XP_W, ">", lambda r: f"{r['xp']:.1f}"))

    lines = render_rows(rows[:limit], cols, rank=True)
    lines.append("")
    shown = "all" if total <= limit else f"top {limit} of"
    lines.append(
        f"Showing {shown} {total} by xP, split per gameweek (difficulty source: {source}). "
        "GWn is rounded; the xP total is authoritative."
    )
    return "\n".join(lines)


def render_xp_table(
    rows, limit: int = 20, source: str = "fpl", horizon: int = 1, by_gameweek: bool = False
) -> str:
    total = len(rows)
    if total == 0:
        return "No players to rank — run `refresh` first."
    if by_gameweek:
        return _render_by_gameweek(rows, limit, source)

    header = (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
        f"{'Pos':<{_POS_W}} {'Games':>{_GAMES_W}} {'Rate':>{_RATE_W}} "
        f"{'xP':>{_XP_W}} {'FPL':>{_EP_W}}"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _NAME_W} {'-' * _TEAM_W} "
        f"{'-' * _POS_W} {'-' * _GAMES_W} {'-' * _RATE_W} "
        f"{'-' * _XP_W} {'-' * _EP_W}"
    )

    lines = [header, divider]
    used_baseline = False
    for rank, r in enumerate(rows[:limit], start=1):
        name = str(r["web_name"])[:_NAME_W]
        team = str(r["team"] or "")
        pos = str(r["position"] or "")
        games = r["games"]
        # Rate + a * when it's the multi-season historical baseline (ADR-028).
        if r.get("rate") is None:
            rate = "—"
        else:
            star = "*" if r.get("rate_source") == "hist" else ""
            rate = f"{r['rate']:.1f}{star}"
            used_baseline = used_baseline or bool(star)
        xp = f"{r['xp']:.1f}"
        # FPL's ep_next is a single-gameweek number — only comparable at horizon 1.
        if horizon == 1 and r["ep_next"] is not None:
            ep = f"{r['ep_next']:.1f}"
        else:
            ep = "—"
        lines.append(
            f"{rank:<{_RANK_W}} {name:<{_NAME_W}} {team:<{_TEAM_W}} "
            f"{pos:<{_POS_W}} {games:>{_GAMES_W}} {rate:>{_RATE_W}} "
            f"{xp:>{_XP_W}} {ep:>{_EP_W}}"
        )

    lines.append("")
    window = "the next gameweek" if horizon == 1 else f"the next {horizon} gameweeks"
    shown = "all" if total <= limit else f"top {limit} of"
    lines.append(f"Showing {shown} {total} by xP over {window} (difficulty source: {source}).")
    if used_baseline:
        lines.append(
            "Rate: * = multi-season baseline (points/90, recency+minutes weighted, ADR-028); "
            "plain = current season. A 'quality when playing' rate — it doesn't model "
            "rotation / minutes (xMins, a later phase)."
        )
    else:
        lines.append(
            "Rate = current-season points per game. Run `history --backfill` for a "
            "multi-season baseline (ADR-028)."
        )
    if horizon > 1:
        lines.append(
            "FPL column hidden — ep_next is next-gameweek only, not comparable to a multi-GW total."
        )
    return "\n".join(lines)
