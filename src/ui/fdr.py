"""Console rendering for the Fixture Difficulty (FDR) view.

Pure formatting: it takes the ranked FDR results (from analytics.team_fdr) and
returns a string. It has its own shape (per team, with an average and opponents),
so it's a separate renderer rather than bending the player table.
"""

_RANK_W = 3
_TEAM_W = 5
_GAMES_W = 6
_AVG_W = 8


def render_fdr_table(rows, next_n: int = 5, source: str = "fpl", hardest: bool = False) -> str:
    if not rows:
        return "No upcoming fixtures to rate."

    header = (
        f"{'#':<{_RANK_W}} {'Team':<{_TEAM_W}} {'Games':>{_GAMES_W}} "
        f"{'Avg FDR':>{_AVG_W}}  Next opponents"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _TEAM_W} {'-' * _GAMES_W} "
        f"{'-' * _AVG_W}  {'-' * 14}"
    )

    lines = [header, divider]
    for rank, row in enumerate(rows, start=1):
        avg = row["avg_difficulty"]
        avg_str = f"{avg:.1f}" if avg is not None else "—"
        opponents = ", ".join(row["opponents"])
        lines.append(
            f"{rank:<{_RANK_W}} {row['team']:<{_TEAM_W}} {row['games']:>{_GAMES_W}} "
            f"{avg_str:>{_AVG_W}}  {opponents}"
        )

    run = "hardest" if hardest else "easiest"
    lines.append("")
    lines.append(
        f"Ranked by {run} run over the next {next_n} fixtures (source: {source})."
    )
    return "\n".join(lines)
