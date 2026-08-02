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
