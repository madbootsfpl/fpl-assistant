"""Clean-sheet / defensive-solidity lens (ADR-019).

Ranks defenders and goalkeepers by expected goals conceded per 90 minutes — the lower,
the more solid the team's defence while they're on the pitch, and the higher their
clean-sheet probability. xGC/90 is computed from the stored `xgc` + `minutes` (it equals
FPL's own `expected_goals_conceded_per_90`). Note this is a *team* signal shown per player.
"""

CLEAN_SHEET_POSITIONS = ("DEF", "GK")   # earn 4 pts for a clean sheet
MIN_MINUTES = 900   # ~10 matches — a per-90 rate off a tiny sample is noise


def defensive_solidity(players, min_minutes: int = MIN_MINUTES) -> list[dict]:
    """Rank DEF/GK by xGC/90 ascending (lowest = best clean-sheet prospect), gated.

    `players` are mappings with position, xgc, minutes, team (as returned by
    Storage.get_players()). Non-DEF/GK, players below `min_minutes`, and players with no
    `xgc` are skipped — a missing xGC can't be ranked (coercing it to 0 would wrongly
    read as the *best* solidity). Returns rows sorted by `xgc90` ascending.
    """
    rows = []
    for p in players:
        if p["position"] not in CLEAN_SHEET_POSITIONS:
            continue
        minutes = p["minutes"] or 0
        if minutes < min_minutes:
            continue
        if p["xgc"] is None:            # missing → not rankable (don't coerce to 0)
            continue
        rows.append({
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "minutes": int(minutes),
            "xgc90": round(p["xgc"] * 90 / minutes, 2),
        })
    rows.sort(key=lambda r: r["xgc90"])   # ascending — lowest xGC/90 is best
    return rows
