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


def render_squad(result, budget: float = 80.0) -> str:
    if result["status"] != "Optimal":
        return (
            f"No legal XI within £{budget:.1f}m (solver status: {result['status']}). "
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

    lines = [f"Optimal XI — budget £{budget:.1f}m", "", header, divider]
    for p in result["selected"]:
        name = str(p["web_name"])[:_NAME_W]
        price = f"£{p['price']:.1f}m"
        lines.append(
            f"{p['position']:<{_POS_W}} {name:<{_NAME_W}} {str(p['team'] or ''):<{_TEAM_W}} "
            f"{price:>{_PRICE_W}} {p['total_points']:>{_PTS_W}}"
        )

    lines.append("")
    lines.append(f"Total: £{result['total_cost']:.1f}m · {result['total_points']} pts")
    return "\n".join(lines)
