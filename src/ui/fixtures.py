"""Console rendering for a single team's upcoming fixtures.

Pure formatting: it takes a team's schedule (from analytics.team_schedule) and
returns a string. Its own shape (per fixture, from one team's view), so a small
dedicated renderer.
"""


def render_team_fixtures(schedule, team: str, source: str = "fpl") -> str:
    if not schedule:
        return f"No upcoming fixtures for {team}."

    header = f"{'GW':<3} {'Venue':<5} {'Opponent':<9} {'Diff':>4}"
    divider = f"{'-' * 3} {'-' * 5} {'-' * 9} {'-' * 4}"

    lines = [f"{team} — next fixtures (difficulty: {source})", "", header, divider]
    for f in schedule:
        gw = f["event"] if f["event"] is not None else "?"
        venue = "Home" if f["venue"] == "H" else "Away"
        diff = f["difficulty"] if f["difficulty"] is not None else "—"
        lines.append(
            f"{str(gw):<3} {venue:<5} {f['opponent']:<9} {str(diff):>4}"
        )
    return "\n".join(lines)


_PLAYER_W = 16


def render_squad_fixtures(rows, squad: str, next_n: int = 5, source: str = "fpl",
                          hardest: bool = False) -> str:
    """A saved squad's players ranked by their team's fixture run (ADR-049).

    One row per player — Player / Team / Avg FDR / next opponents — its own shape (per player,
    from the squad's view), so a small dedicated renderer rather than the league FDR table.
    """
    if not rows:
        return f"No fixtures to rate for '{squad}'."

    header = f"{'#':<3} {'Player':<{_PLAYER_W}} {'Team':<5} {'Avg FDR':>7}  Next opponents"
    divider = f"{'-' * 3} {'-' * _PLAYER_W} {'-' * 5} {'-' * 7}  {'-' * 14}"

    lines = [f"{squad} — players by their team's fixture run (difficulty: {source})", "", header, divider]
    for rank, r in enumerate(rows, start=1):
        avg = r["avg_difficulty"]
        avg_str = f"{avg:.1f}" if avg is not None else "—"
        opponents = ", ".join(r["opponents"])
        lines.append(
            f"{rank:<3} {str(r['web_name'])[:_PLAYER_W]:<{_PLAYER_W}} {r['team']:<5} "
            f"{avg_str:>7}  {opponents}"
        )

    run = "hardest" if hardest else "easiest"
    lines.append("")
    lines.append(
        f"Ranked by each player's team's {run} run over the next {next_n} fixtures (source: {source})."
    )
    return "\n".join(lines)
