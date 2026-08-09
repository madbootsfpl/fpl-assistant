"""DefCon fixture magnifier (ADR-097) — re-weight the DefCon points already in the baseline by fixture.

Defensive-contribution points (2/match for clearing a position threshold of defensive actions, ADR-018)
depend on the fixture: a player defends **more** vs a strong opponent (a clean sheet unlikely) → more
actions → more likely to clear the threshold; **less** when their team dominates a weak one. The magnifier
scales the DefCon *portion* the baseline already prices — a **delta** `(magnifier − 1)`, **0 at neutral**, so
it never double-counts. Pure; gated by `config.DEFCON_MAGNIFIER_WEIGHT` (default 0) at the `player_xp` edge.
"""

from src.analytics.defcon import THRESHOLD

# The P(clear-threshold) spread + the magnifier band — coarse defaults, calibrated at GW1 (ADR-097).
DEFCON_P_SCALE = 10.0        # the per-90 margin that maps to a full ±0.5 swing in P(clear)
DEFCON_MAG_LO = 0.5          # weak opponent / low difficulty (clean sheet likely) → less DefCon
DEFCON_MAG_HI = 1.5          # strong opponent / high difficulty (clean sheet unlikely) → more DefCon


def _get(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _clamp(x, lo, hi) -> float:
    return lo if x < lo else hi if x > hi else x


def defcon_points_per_match(player) -> float:
    """Estimated DefCon points per match (0–2): `2 · P(clear the position threshold)`.

    `P(clear) = clamp(0.5 + (defcon_per90 − threshold) / DEFCON_P_SCALE, 0, 1)`. 0 for a keeper, an ineligible
    position, or a player with no `defcon_per90`. This is the DefCon *share* the magnifier re-weights (it is
    **not** added to xP — the baseline already prices it, ADR-097)."""
    threshold = THRESHOLD.get(_get(player, "position"))
    per90 = _get(player, "defcon_per90")
    if threshold is None or per90 is None:
        return 0.0
    p_clear = _clamp(0.5 + (per90 - threshold) / DEFCON_P_SCALE, 0.0, 1.0)
    return 2.0 * p_clear


def defcon_magnifier(difficulty) -> float:
    """A fixture multiplier for DefCon from the FDR `difficulty` (a clean-sheet-probability proxy): a **weak**
    opponent (low difficulty, clean sheet likely) → ~`DEFCON_MAG_LO`; a **strong** one (high difficulty) →
    ~`DEFCON_MAG_HI`; **neutral (1.0)** at mid-difficulty or an unknown fixture. Clamped to the band."""
    if difficulty is None:
        return 1.0
    mag = DEFCON_MAG_LO + (difficulty - 1) / 4.0 * (DEFCON_MAG_HI - DEFCON_MAG_LO)
    return _clamp(mag, DEFCON_MAG_LO, DEFCON_MAG_HI)
