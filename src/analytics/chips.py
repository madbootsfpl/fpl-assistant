"""Chip-strategy guidance (ADR-082) — WHEN to play each chip, from a squad's per-GW xP + fixture run.

An **assembler**, not new analytics (the `gameweek_plan` shape, ADR-070): it reduces the per-GW xP the caller
already computed (`by_gameweek`, ADR-032) into one recommendation per chip, so the chip answer can't drift from
the standalone tools. Pure given its inputs (the only I/O is `best_legal_xi`'s in-memory solve); the `ask` layer
humanises + verifies it (ADR-034/037). Fixture-run + xP based — double/blank gameweeks and mini-league position
sharpen it in-season / at GW1 (a caption says so).
"""

from src.analytics.optimizer import best_legal_xi

# The chips, in the order we present them (ceiling first, then the whole-squad and reset chips).
CHIP_NAMES = ("Triple Captain", "Bench Boost", "Free Hit", "Wildcard")

_WILDCARD_WINDOW = 3        # the rolling stretch (GWs) a wildcard resets for; clamped to the horizon


def _points(by_gameweek_by_id, owned, gw) -> dict:
    """Each owned player's xP in gameweek `gw` (id → xP), 0 where absent. Empty-safe."""
    return {p["id"]: (by_gameweek_by_id.get(p["id"], {}) or {}).get(gw, 0.0) for p in owned}


def chip_advisor(owned, by_gameweek_by_id, gameweeks) -> dict | None:
    """Recommend the best gameweek (or window) for each chip, from the squad's per-GW xP.

    `owned` are the squad's 15 player rows; `by_gameweek_by_id` is `{id → {gw → xP}}` (from
    `decision_xp`, ADR-032); `gameweeks` the horizon's GW numbers in order. Returns
    ``{triple_captain, bench_boost, free_hit, wildcard}`` (each a dict), or None if there's nothing to
    reduce (no players / no gameweeks). Each reduction is a decomposition of `by_gameweek` + the best
    legal XI that GW — so it agrees with the lineup/captain tools by construction.
    """
    if not owned or not gameweeks:
        return None

    by_id = {p["id"]: p for p in owned}
    # Per GW: the per-player xP, the best legal XI (ids), that XI's total, and the whole-15 total.
    per_gw = {}
    for gw in gameweeks:
        pts = _points(by_gameweek_by_id, owned, gw)
        xi = best_legal_xi(owned, pts)
        per_gw[gw] = {
            "pts": pts,
            "xi": xi,
            "xi_total": round(sum(pts[i] for i in xi), 1),
            "squad_total": round(sum(pts.values()), 1),
        }

    # Triple Captain — the single starter with the highest ceiling in any GW (a TC only lifts a starter).
    tc_gw, tc_id, tc_val = None, None, -1.0
    for gw in gameweeks:
        g = per_gw[gw]
        for i in g["xi"]:
            if g["pts"][i] > tc_val:
                tc_gw, tc_id, tc_val = gw, i, g["pts"][i]
    tc_player = by_id.get(tc_id)
    triple_captain = {
        "gameweek": tc_gw,
        "player": tc_player,
        "player_xp": round(tc_val, 1),
        "extra_points": round(tc_val, 1),   # TC = ×3 vs a ×2 captain → an extra ×1 of the player's GW xP
    }

    # Bench Boost — the GW where all 15 score most (the bench's points count this week).
    bb_gw = max(gameweeks, key=lambda gw: per_gw[gw]["squad_total"])
    bb = per_gw[bb_gw]
    bench_boost = {
        "gameweek": bb_gw,
        "squad_total": bb["squad_total"],
        "bench_points": round(bb["squad_total"] - bb["xi_total"], 1),
    }

    # Free Hit — the squad's weakest single week (lowest best-XI xP): a one-off to cover a bad GW.
    fh_gw = min(gameweeks, key=lambda gw: per_gw[gw]["xi_total"])
    free_hit = {
        "gameweek": fh_gw,
        "xi_total": per_gw[fh_gw]["xi_total"],
    }

    # Wildcard — the weakest sustained stretch (lowest rolling window of best-XI xP): reset before it.
    window = min(_WILDCARD_WINDOW, len(gameweeks))
    starts = range(len(gameweeks) - window + 1)
    best_start = min(starts, key=lambda s: sum(per_gw[gameweeks[s + k]]["xi_total"] for k in range(window)))
    win_gws = gameweeks[best_start:best_start + window]
    wildcard = {
        "window": (win_gws[0], win_gws[-1]),
        "gameweeks": list(win_gws),
        "avg_xi": round(sum(per_gw[g]["xi_total"] for g in win_gws) / window, 1),
    }

    return {
        "triple_captain": triple_captain,
        "bench_boost": bench_boost,
        "free_hit": free_hit,
        "wildcard": wildcard,
    }
