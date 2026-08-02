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


def formation_str(players) -> str:
    """The DEF-MID-FWD shape of a set of players, e.g. "5-4-1" (GK implied)."""
    counts = {"DEF": 0, "MID": 0, "FWD": 0}
    for p in players:
        if p["position"] in counts:
            counts[p["position"]] += 1
    return f"{counts['DEF']}-{counts['MID']}-{counts['FWD']}"


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

    # In XI mode every picked player is a starter, so the squad *is* the formation.
    shape = "" if full else f" ({formation_str(result['selected'])})"

    header = (
        f"{'Pos':<{_POS_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
        f"{'Price':>{_PRICE_W}} {'Pts':>{_PTS_W}}"
    )
    divider = (
        f"{'-' * _POS_W} {'-' * _NAME_W} {'-' * _TEAM_W} "
        f"{'-' * _PRICE_W} {'-' * _PTS_W}"
    )

    lines = [
        f"Optimal {what}{shape} — objective: {objective}, budget £{budget:.1f}m",
        "", header, divider,
    ]
    any_forced = False
    any_bench = False
    bench_started = False
    for p in result["selected"]:
        is_bench = bool(p.get("bench"))
        # A "Bench:" heading before the first bench row (they sort to the end).
        if is_bench and not bench_started:
            lines.append("")
            lines.append("Bench:")
            bench_started = True

        name = str(p["web_name"])[:_NAME_W]
        price = f"£{p['price']:.1f}m"
        if is_bench:
            marker, any_bench = " **", True
        elif p.get("forced"):
            marker, any_forced = " *", True
        else:
            marker = ""
        lines.append(
            f"{p['position']:<{_POS_W}} {name:<{_NAME_W}} {str(p['team'] or ''):<{_TEAM_W}} "
            f"{price:>{_PRICE_W}} {p['total_points']:>{_PTS_W}}{marker}"
        )

    lines.append("")
    lines.append(f"Total: £{result['total_cost']:.1f}m · {result['total_points']} pts")
    if objective == "xgi":
        # ADR-015: xGI is an attacking measure (GK/DEF ≈ 0) — say so, don't oversell it.
        lines.append("Note: xGI is attacking — GK/DEF score ≈ 0, so this leans to attackers.")

    # With a declared bench we know the starters — show their subtotal, the honest number.
    # At a full 4-man bench the 11 starters form a legal XI, so state its shape (ADR-014).
    if any_bench:
        starters = [p for p in result["selected"] if not p.get("bench")]
        starters_pts = sum(p["total_points"] for p in starters)
        shape = f" — {formation_str(starters)}" if len(starters) == 11 else ""
        lines.append(f"Starters ({len(starters)}){shape}: {starters_pts} pts")

    legend = []
    if any_forced:
        legend.append("* = forced in")
    if any_bench:
        legend.append("** = benched")
    if legend:
        lines.append(" · ".join(legend))

    if full:
        if any_bench:
            # ADR-013: the starters' subtotal is a true XI only at a full 4-man bench.
            if len(starters) == 11:
                lines.append("Note: Starters (11) is your XI — the bench won't score.")
            else:
                lines.append(
                    f"Note: Starters ({len(starters)}) excludes your bench; bench 4 for "
                    "a full XI. The bench won't score."
                )
        else:
            # ADR-012: without a declared bench, the 15-total counts non-scorers.
            lines.append(
                "Note: Pts totals a bench that won't score — squad strength, not a weekly "
                "total. Declare your bench with --bench."
            )
    return "\n".join(lines)
