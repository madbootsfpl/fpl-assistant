"""Percentile ranking — the one definition both DNA modules share (ADR-127).

Player DNA (ADR-118) and Team DNA (ADR-119) each had their own copy of this, and both carried the same bug:
they counted peers **"at or below"** the value, so a tie ranked at the *top* of its tie group. Nearly every
goalkeeper has 0 xG, so a 0 counted as beating every other 0 and landed in the 90s — the axis read *elite*
precisely because the player had nothing there (A.Becker: Goal Threat 96th percentile on a raw 0.00).

The same line held a second, quieter fault: it counted the player themselves, inflating everyone by `1/n`.
At Team DNA's 20-team scale that is +5 points for the best team and ~+2.5 through the middle.

One function, imported by both — the fix written once. Two copies of a rule is how the last one drifted
(see `fpl_rules.DEADLINE_LEAD`, ADR-123).
"""


def percentile_rank(value, values, *, invert: bool = False) -> int | None:
    """Where `value` sits within `values`, 0–100, with **ties sharing their average rank** (ADR-127).

        rank = below + (equal + 1) / 2          # 1-based average rank across the tie group
        pct  = 100 × (rank − 1) / (n − 1)

    The classic percentile rank: the best of a set scores **100**, the worst **0**, and a set where every value
    is identical scores **50** for all of them — "no different from your peers", which is the honest reading
    when there is nothing to separate them.

    Keeping the 0–100 endpoints matters beyond neatness: the insight copy is written as *"top {100 − pct}%"*, so
    a formula that caps the best at 98 would have the best player in the game reading "top 2%".

    `invert=True` for lower-is-better axes (xGA, FDR) so the best still scores highest. `None` when there is
    nothing to rank against; 50 for a single peer (a lone value is neither above nor below anything).

    `value` need not be a member of `values` — Player DNA ranks a below-the-floor target against a floored
    pool — so the result is clamped into range rather than trusted to land there.
    """
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    if len(vals) == 1:
        return 50
    below = sum(1 for v in vals if (v > value if invert else v < value))
    equal = sum(1 for v in vals if v == value)
    avg_rank = below + (equal + 1) / 2
    return max(0, min(100, round(100 * (avg_rank - 1) / (len(vals) - 1))))
