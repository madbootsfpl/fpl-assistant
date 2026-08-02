"""Console rendering for the optimal squad (starting XI).

Pure formatting: it takes the optimiser's result (from analytics.select_squad) and
returns a string — the XI grouped by position with totals, or a clear message when no
legal XI fits the budget.
"""

_POS_W = 3
_NAME_W = 17
_TEAM_W = 5
_PRICE_W = 6
_PTS_W = 5


def render_squad(
    result, budget: float = 80.0, objective: str = "points", full: bool = False
) -> str:
    # `full` picks the 15-man squad; otherwise a starting XI. Only the wording and the
    # trailing caveat differ — the table is the same.
    what = "15-man squad" if full else "XI"

    if result["status"] != "Optimal":
        return (
            f"No legal {what} within £{budget:.1f}m (solver status: {result['status']}). "
            "Try a higher budget — or run `refresh` if you haven't loaded data yet."
        )

    header = (
        f"{'Pos':<{_POS_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
        f"{'Price':>{_PRICE_W}} {'Pts':>{_PTS_W}}"
    )
    divider = (
        f"{'-' * _POS_W} {'-' * _NAME_W} {'-' * _TEAM_W} "
        f"{'-' * _PRICE_W} {'-' * _PTS_W}"
    )

    lines = [
        f"Optimal {what} — objective: {objective}, budget £{budget:.1f}m", "", header, divider
    ]
    any_forced = False
    for p in result["selected"]:
        name = str(p["web_name"])[:_NAME_W]
        price = f"£{p['price']:.1f}m"
        marker = " *" if p.get("forced") else ""
        any_forced = any_forced or bool(p.get("forced"))
        lines.append(
            f"{p['position']:<{_POS_W}} {name:<{_NAME_W}} {str(p['team'] or ''):<{_TEAM_W}} "
            f"{price:>{_PRICE_W}} {p['total_points']:>{_PTS_W}}{marker}"
        )

    lines.append("")
    lines.append(f"Total: £{result['total_cost']:.1f}m · {result['total_points']} pts")
    if any_forced:
        lines.append("* = forced in")
    if full:
        # ADR-012: for the 15, the total counts bench players who won't score — so it's a
        # squad-strength guide, not a weekly return. Say so, and point at the workflow.
        lines.append(
            "Note: Pts totals a bench that won't score — squad strength, not a weekly "
            "total. Pick your bench with --include."
        )
    return "\n".join(lines)
