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
            "id": p["id"],          # US-425: carry the id so the web "My squad only" filter can match
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "minutes": int(minutes),
            "xgc90": round(p["xgc"] * 90 / minutes, 2),
        })
    rows.sort(key=lambda r: r["xgc90"])   # ascending — lowest xGC/90 is best
    return rows


# ADR-188 — a defender's points depend on his own club keeping a clean sheet, and `decision_xp` has never
# priced that: a defender's xP is his own pts/90 × minutes × **opponent** difficulty, with no term for the
# defence he plays behind. Team DNA has shown the number for weeks (Arsenal 75% against Sunderland 25% on the
# day this was written) without the recommendation engine using it.
CLEAN_SHEET_POINTS = 4          # FPL: a DEF/GK clean sheet is worth 4


def clean_sheet_delta(player, team_rate, league_rate) -> float:
    """Points per match a DEF/GK gains (or loses) from his club's clean-sheet rate vs the league's.

    A **delta**, deliberately, and for the same reason ADR-097's DefCon magnifier is one: the player's own
    historical pts/90 already contains the clean sheets he kept at his old rate. Adding an absolute
    clean-sheet term would double-count them. What is *not* in the baseline is whether **this** club, **this**
    season, keeps them more or less often than the average — so only the difference is priced.

    Returns 0.0 for outfield players, and for any club with no played gameweeks yet: `team_clean_sheet_rate`
    returns None there, and **an unknown rate must never read as a bad one** (the ADR-172 failure, where an
    all-empty history was treated as "never plays").
    """
    if player["position"] not in CLEAN_SHEET_POSITIONS:
        return 0.0
    if team_rate is None or league_rate is None:
        return 0.0
    return CLEAN_SHEET_POINTS * (team_rate - league_rate)


def league_clean_sheet_rate(rates) -> float | None:
    """The mean clean-sheet rate across clubs that have one — the baseline a delta is measured against.

    Clubs with no played gameweeks are excluded rather than counted as 0%, so the average is over what is
    known. None when nothing is known at all.
    """
    known = [r for r in (rates or {}).values() if r is not None]
    return sum(known) / len(known) if known else None
