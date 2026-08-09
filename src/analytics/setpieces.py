"""Set-piece xP term (ADR-096) — a per-90 rate bonus for the players nominated on dead balls.

Penalties carry the most value (a penalty is a high-xG shot a specific player takes); corners and
free-kicks add a smaller indirect goal/assist chance. `set_piece_bonus` maps a player's **#1** duties
to a small rate bonus; `decision_xp`/`player_xp` add `SET_PIECE_WEIGHT · bonus` to the rate — but only
on the fallback/current tiers (the trusted historical baseline already prices an established taker's
pens, ADR-096). Pure/empty-safe — the weight (`config.SET_PIECE_WEIGHT`, default 0) gates the effect.
"""

# Per-90 rate contributions of holding the #1 duty (pre-weight). Penalties dominate; set plays are a
# smaller shared bump. Coarse by design (no per-team penalty rate) — calibrated at GW1 via the weight.
PENALTY_BONUS = 0.30
SET_PLAY_BONUS = 0.10       # corners or free-kicks (#1)


def _get(player, key):
    try:
        return player[key]
    except (KeyError, IndexError, TypeError):
        return None


def set_piece_bonus(player) -> float:
    """A player's per-90 set-piece rate bonus (pre-weight): `PENALTY_BONUS` if the **#1** penalty taker,
    plus `SET_PLAY_BONUS` if the #1 corner and/or free-kick taker. 0 for a non-taker. Empty-safe."""
    bonus = 0.0
    if _get(player, "penalties_order") == 1:
        bonus += PENALTY_BONUS
    if _get(player, "corners_order") == 1:
        bonus += SET_PLAY_BONUS
    if _get(player, "freekicks_order") == 1:
        bonus += SET_PLAY_BONUS
    return bonus
