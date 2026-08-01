"""Console rendering for the player table.

`render_player_table` takes rows (as returned by Storage.get_players()) and
returns an aligned table as a string. It does no sorting and no I/O — pass rows
already in the order you want, and print the result at the app edge.
"""

# Fixed column widths, so everything lines up regardless of the data.
_RANK_W = 3
_NAME_W = 17
_TEAM_W = 5
_POS_W = 4
_PRICE_W = 6
_PTS_W = 5


def _truncate(text: str, width: int) -> str:
    """Trim text to `width`, marking the cut with a trailing … when too long."""
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def render_player_table(rows, limit: int = 20) -> str:
    """Render players as an aligned console table.

    `rows` is a sequence of mappings with keys: web_name, team, position,
    price, total_points. Returns a friendly message if there are no rows.
    """
    total = len(rows)
    if total == 0:
        return "No players to display."

    header = (
        f"{'#':<{_RANK_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
        f"{'Pos':<{_POS_W}} {'Price':>{_PRICE_W}} {'Pts':>{_PTS_W}}"
    )
    divider = (
        f"{'-' * _RANK_W} {'-' * _NAME_W} {'-' * _TEAM_W} "
        f"{'-' * _POS_W} {'-' * _PRICE_W} {'-' * _PTS_W}"
    )

    lines = [header, divider]
    for rank, row in enumerate(rows[:limit], start=1):
        name = _truncate(str(row["web_name"]), _NAME_W)
        team = _truncate(str(row["team"] or ""), _TEAM_W)
        pos = str(row["position"] or "")
        price = f"£{row['price']:.1f}m"
        pts = row["total_points"]
        lines.append(
            f"{rank:<{_RANK_W}} {name:<{_NAME_W}} {team:<{_TEAM_W}} "
            f"{pos:<{_POS_W}} {price:>{_PRICE_W}} {pts:>{_PTS_W}}"
        )

    lines.append("")
    if total > limit:
        lines.append(f"Showing top {limit} of {total} players.")
    else:
        lines.append(f"Showing all {total} players.")

    return "\n".join(lines)
