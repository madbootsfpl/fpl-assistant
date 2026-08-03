"""Defensive Contribution reliability (ADR-018).

FPL awards 2 points/match for clearing a threshold of defensive actions. This ranks
players by how comfortably they clear it on average — `defensive_contribution_per_90`
minus the position threshold. A positive margin means a reliable DefCon-point earner;
the larger the margin, the more reliably they clear it game to game. Goalkeepers are not
DefCon-eligible and are excluded.
"""

# Per-match thresholds (FPL rules). DEF count CBIT; MID/FWD count CBIT + recoveries.
# NOTE: these numbers are transcribed from FPL's published scoring rules — the API does
# NOT expose them (see Handbook Ch25). Treat as a hand-maintained assumption: confirm
# against FPL's official rules, and re-check each season (FPL can change them).
THRESHOLD = {"DEF": 10, "MID": 12, "FWD": 12}   # GK: not eligible → excluded
MIN_MINUTES = 900   # ~10 matches — a per-90 rate off a tiny sample is noise


def _num(value) -> float:
    return value or 0.0


def defcon_reliability(players, min_minutes: int = MIN_MINUTES) -> list[dict]:
    """Rank players by (defensive_contribution_per_90 − position threshold), gated.

    `players` are mappings with position, defcon_per90, minutes (as returned by
    Storage.get_players()). Goalkeepers and players below `min_minutes` are skipped.
    Returns rows sorted by `margin` descending (most reliable earners first).
    """
    rows = []
    for p in players:
        threshold = THRESHOLD.get(p["position"])
        if threshold is None:                       # GK (or unknown) → not eligible
            continue
        if _num(p["minutes"]) < min_minutes:
            continue
        per90 = _num(p["defcon_per90"])
        rows.append({
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "minutes": int(_num(p["minutes"])),
            "per90": round(per90, 1),
            "threshold": threshold,
            "margin": round(per90 - threshold, 1),
        })
    rows.sort(key=lambda r: r["margin"], reverse=True)
    return rows
