"""Console rendering for the player table.

`render_player_table` takes rows (as returned by Storage.get_players()) and
returns an aligned table as a string. It does no sorting and no I/O — pass rows
already in the order you want, and print the result at the app edge.

The table shape (header / divider / aligned rows) comes from the shared renderer
(`ui._table`, ADR-025); this module supplies the columns, title, and footer.
"""

from src.analytics import availability_flag

from ._table import Col, render_rows

# Fixed column widths, so everything lines up regardless of the data.
_NAME_W = 17
_TEAM_W = 5


def _truncate(text: str, width: int) -> str:
    """Trim text to `width`, marking the cut with a trailing … when too long."""
    if len(text) <= width:
        return text
    return text[: width - 1] + "…"


def _value_str(row) -> str:
    # Value is undefined (None) when price is 0/missing — show a dash.
    value = row.get("value")
    return f"{value:.1f}" if value is not None else "—"


_COLS = [
    Col("Player", _NAME_W, "<", lambda r: _truncate(str(r["web_name"]), _NAME_W)),
    Col("Team", _TEAM_W, "<", lambda r: _truncate(str(r["team"] or ""), _TEAM_W)),
    Col("Pos", 4, "<", lambda r: str(r["position"] or "")),
    Col("Price", 6, ">", lambda r: f"£{r['price']:.1f}m"),
    Col("Pts", 5, ">", lambda r: str(r["total_points"])),
    Col("Val/£m", 7, ">", _value_str),
    # Availability last (ADR-074): 🚑/🚫/⛔/❓, blank = available. Kept last so an emoji's terminal width
    # can't push the aligned columns before it out of line.
    Col("Fit", 4, "<", availability_flag),
]


def render_player_table(rows, limit: int = 20) -> str:
    """Render players as an aligned console table.

    `rows` is a sequence of mappings with keys: web_name, team, position,
    price, total_points. Returns a friendly message if there are no rows.
    """
    total = len(rows)
    if total == 0:
        return "No players to display."

    lines = render_rows(rows[:limit], _COLS, rank=True)

    lines.append("")
    if total > limit:
        lines.append(f"Showing top {limit} of {total} players.")
    else:
        lines.append(f"Showing all {total} players.")
    return "\n".join(lines)
