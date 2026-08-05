"""Console rendering for the optimal squad (starting XI).

Pure formatting: it takes the optimiser's result (from analytics.select_squad) and
returns a string — the XI grouped by position with totals, or a clear message when no
legal XI fits the budget.
"""

from src.analytics.minutes import expected_minutes
from src.analytics.optimizer import legal_xi_issues

# Availability flags for picked players (ADR-023): 'a' shows nothing; 'd' shows the chance.
_STATUS_FLAG = {"i": "inj", "s": "susp", "u": "out", "n": "n/a"}


def _avail_flag(p) -> str:
    status = p.get("status")
    if status == "d":
        chance = p.get("chance")
        return f" (d {chance}%)" if chance is not None else " (doubtful)"
    if status in _STATUS_FLAG:
        return f" ({_STATUS_FLAG[status]})"
    return ""


_POS_W = 3
_NAME_W = 17
_TEAM_W = 5
_PRICE_W = 6
_PTS_W = 5
_XMINS_W = 6
_XP_W = 6


def formation_str(players) -> str:
    """The DEF-MID-FWD shape of a set of players, e.g. "5-4-1" (GK implied)."""
    counts = {"DEF": 0, "MID": 0, "FWD": 0}
    for p in players:
        if p["position"] in counts:
            counts[p["position"]] += 1
    return f"{counts['DEF']}-{counts['MID']}-{counts['FWD']}"


def render_loaded_squad(name, saved, loaded, now_cost, departed) -> str:
    """Render a reloaded saved squad (ADR-024): the picks re-priced + availability + departed.

    `loaded` are the present players (each a mapping with position/web_name/team/price/
    total_points/status/chance and a `bench` flag), sorted starters-then-bench. `departed`
    are the names of saved players no longer in the game. `saved` is the stored record.
    """
    lines = [f"Squad '{name}' — saved {saved.get('saved_at', '?')}", ""]

    if loaded:
        header = (
            f"{'Pos':<{_POS_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
            f"{'Price':>{_PRICE_W}} {'Pts':>{_PTS_W}}"
        )
        lines += [header, "-" * len(header)]
        bench_started = False
        for p in loaded:
            if p.get("bench") and not bench_started:
                lines += ["", "Bench:"]
                bench_started = True
            marker = " **" if p.get("bench") else ""
            lines.append(
                f"{p['position']:<{_POS_W}} {str(p['web_name'])[:_NAME_W]:<{_NAME_W}} "
                f"{str(p['team'] or ''):<{_TEAM_W}} £{p['price']:.1f}m"
                f"{p['total_points']:>{_PTS_W + 1}}{marker}{_avail_flag(p)}"
            )
        lines.append("")

    # Re-price against current data, comparing to what it cost when saved.
    was = saved.get("cost")
    if was is not None:
        lines.append(f"Cost: was £{was:.1f}m → now £{now_cost:.1f}m ({now_cost - was:+.1f}).")
    else:
        lines.append(f"Cost (re-priced): £{now_cost:.1f}m.")

    # Availability of your picks, and anyone who's left the game.
    flagged = [p for p in loaded if _avail_flag(p)]
    if flagged:
        who = ", ".join(f"{p['web_name']}{_avail_flag(p).strip()}" for p in flagged)
        lines.append(f"⚠ {len(flagged)} of your picks now flagged: {who}.")
    if departed:
        lines.append(f"Departed (no longer in the game): {', '.join(departed)}.")
    return "\n".join(lines)


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

    # Under --objective xp (ADR-041/US-121) show what we optimised: xMins + xP, not last-season Pts.
    show_xp = objective == "xp"
    if show_xp:
        value_head = f"{'xMins':>{_XMINS_W}} {'xP':>{_XP_W}}"
        value_rule = f"{'-' * _XMINS_W} {'-' * _XP_W}"
    else:
        value_head = f"{'Pts':>{_PTS_W}}"
        value_rule = f"{'-' * _PTS_W}"

    header = (
        f"{'Pos':<{_POS_W}} {'Player':<{_NAME_W}} {'Team':<{_TEAM_W}} "
        f"{'Price':>{_PRICE_W}} {value_head}"
    )
    divider = (
        f"{'-' * _POS_W} {'-' * _NAME_W} {'-' * _TEAM_W} "
        f"{'-' * _PRICE_W} {value_rule}"
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
        if show_xp:
            value = f"{expected_minutes(p.get('minutes_weight')):>{_XMINS_W}} {p.get('xp', 0):>{_XP_W}.1f}"
        else:
            value = f"{p['total_points']:>{_PTS_W}}"
        lines.append(
            f"{p['position']:<{_POS_W}} {name:<{_NAME_W}} {str(p['team'] or ''):<{_TEAM_W}} "
            f"{price:>{_PRICE_W}} {value}{marker}{_avail_flag(p)}"
        )

    lines.append("")
    if show_xp:
        projected = round(sum(p.get("xp", 0) for p in result["selected"]), 1)
        lines.append(f"Total: £{result['total_cost']:.1f}m · projected {projected} xP")
    else:
        lines.append(f"Total: £{result['total_cost']:.1f}m · {result['total_points']} pts")
    if objective == "xgi":
        # ADR-015: xGI is an attacking measure (GK/DEF ≈ 0) — say so, don't oversell it.
        lines.append("Note: xGI is attacking — GK/DEF score ≈ 0, so this leans to attackers.")
    elif objective == "xp":
        # ADR-041/US-121: optimised on forward-looking xP, and the table now shows it.
        lines.append(
            "Note: `xP` = expected points over the next 5 GW (xMins-weighted — the metric "
            "`transfer`/`analyse` use); `xMins` = expected minutes next GW. `--objective points` "
            "optimises last season's total instead; `--no-xmins` for the raw xP."
        )

    # With a declared bench we know the starters — show their subtotal, the honest number.
    # At a full 4-man bench the 11 starters form a legal XI, so state its shape (ADR-014).
    if any_bench:
        starters = [p for p in result["selected"] if not p.get("bench")]
        shape = f" — {formation_str(starters)}" if len(starters) == 11 else ""
        if show_xp:
            subtotal = f"projected {round(sum(p.get('xp', 0) for p in starters), 1)} xP"
        else:
            subtotal = f"{sum(p['total_points'] for p in starters)} pts"
        lines.append(f"Starters ({len(starters)}){shape}: {subtotal}")

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
                # ADR-022: check the declared bench actually leaves a legal XI.
                issues = legal_xi_issues(starters)
                if issues:
                    lines.append(
                        "Note: this bench doesn't leave a legal XI — "
                        + "; ".join(issues) + "."
                    )
                else:
                    lines.append("Note: Starters (11) is your XI — the bench won't score.")
            else:
                lines.append(
                    f"Note: Starters ({len(starters)}) excludes your bench; bench 4 for "
                    "a full XI. The bench won't score."
                )
        else:
            # ADR-012: without a declared bench, the 15-total counts non-scorers.
            total_word = "The projected xP" if show_xp else "Pts"
            lines.append(
                f"Note: {total_word} totals a bench that won't score — squad strength, not a "
                "weekly total. Declare your bench with --bench."
            )
    return "\n".join(lines)
