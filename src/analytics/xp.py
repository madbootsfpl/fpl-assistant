"""Expected Points (xP) — the first *cross-domain* metric.

xP joins two threads: a player's scoring rate (`points_per_game`) and their team's
fixture difficulty. The link is `team_id` — a player belongs to a team, a team has
fixtures, each fixture has a difficulty (reusing the FDR `_view` seam).

Formula (ADR-006): per fixture, xP = points_per_game × (1 + (3 − difficulty) × 0.10),
or 0 if the player isn't available. Over a horizon of the next N gameweeks, we sum the
per-fixture xP (ADR-007) — so a double gameweek (two fixtures in one gameweek) adds up.
"""

from src.analytics.fdr import _view

_K = 0.10   # fixture weighting: ±20% at the extremes (ADR-006)
_BASELINE_SEASONS = 3    # multi-season look-back for the xP baseline (ADR-028)
# A season needs ~10 full games before its points-per-90 is trustworthy — otherwise a
# tiny cameo (e.g. 2 pts in 20 mins → pp90 9.0+) invents an absurd rate. Same minutes
# gate the over/under and DefCon views use (ADR-017/018); the Sprint 016 Meslier lesson.
_MIN_SEASON_MINUTES = 900


def _get(row, key):
    """Read `key` from a sqlite Row or a dict, returning None if it's absent.

    Lets player_xp accept both real rows (which have `code`) and lightweight test
    dicts (which may not) without a KeyError.
    """
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def baseline_rate(
    history, k_seasons: int = _BASELINE_SEASONS, min_minutes: int = _MIN_SEASON_MINUTES
):
    """A multi-season points-per-90 baseline for one player (ADR-028).

    Recency- and minutes-weighted over the last `k_seasons` seasons that clear
    `min_minutes` (a small sample invents an absurd rate — see the gate above), using
    only the fields ADR-027 confirmed reliable across seasons (points + minutes).
    Returns None when no season qualifies (young/fringe player), so the caller can
    fall back to the current single-season rate.
    """
    seasons = [h for h in history if (h["minutes"] or 0) >= min_minutes][-k_seasons:]
    if not seasons:
        return None
    num = den = 0.0
    for rank, h in enumerate(seasons, start=1):   # oldest → 1 … newest → n (recency)
        pp90 = h["total_points"] * 90.0 / h["minutes"]
        weight = rank * h["minutes"]              # newer + higher-minutes seasons weigh more
        num += weight * pp90
        den += weight
    return num / den


def _multiplier(difficulty) -> float:
    """Turn a 1-5 difficulty into a scoring multiplier (neutral at 3, or if unknown)."""
    if difficulty is None:
        return 1.0
    return 1 + (3 - difficulty) * _K


def _horizon_gameweeks(upcoming, gameweeks: int) -> list[int]:
    """The next `gameweeks` gameweek numbers present in `upcoming`, in order."""
    events = sorted({f["event"] for f in upcoming if f["event"] is not None})
    return events[:gameweeks]


def _difficulties_by_team_gw(upcoming, source: str, horizon_events) -> dict:
    """Map team_id → {gameweek → [fixture difficulties]} within the horizon.

    Grouping by gameweek (not a flat list) is what lets xP split per GW (ADR-032): a
    double gameweek gives two entries in one GW, a blank gameweek gives none — the same
    DGW/BGW handling as ADR-007, now visible per week.
    """
    horizon = set(horizon_events)
    by_team_gw: dict = {}
    for f in upcoming:
        if f["event"] not in horizon:
            continue
        for team_id, team_short in ((f["team_h"], f["home"]), (f["team_a"], f["away"])):
            difficulty, _, _ = _view(f, team_short, source)
            by_team_gw.setdefault(team_id, {}).setdefault(f["event"], []).append(difficulty)
    return by_team_gw


def _status_is_active(p) -> bool:
    """Default availability: only a fully-fit player (status 'a') scores (ADR-006)."""
    return p["status"] == "a"


def player_xp(
    players, upcoming, source: str = "fpl", horizon: int = 1, baseline_by_code=None,
    is_available=None,
) -> list[dict]:
    """Compute each player's expected points over the next `horizon` gameweeks.

    `players` are rows from Storage.get_players() (team_id, points_per_game, status,
    ep_next, web_name, position, team, code). `upcoming` is from get_upcoming_fixtures().

    The scoring **rate** is the multi-season historical baseline (ADR-028) when available
    — keyed by the player's `code` in `baseline_by_code` — else the current
    `points_per_game`. xP is the sum of per-fixture rate × fixture-multiplier over the
    horizon; 0 if the player is unavailable or has no rate at all. Sorted by xP, highest first.

    `is_available(player)` decides who scores (others → 0); it defaults to "status is 'a'".
    The captain view (ADR-029) passes a looser predicate so *doubtful* players still get an
    xP (to be suggested with a flag) rather than being zeroed.
    """
    horizon_events = _horizon_gameweeks(upcoming, horizon)
    diff_by_team_gw = _difficulties_by_team_gw(upcoming, source, horizon_events)
    baseline_by_code = baseline_by_code or {}
    is_available = is_available or _status_is_active

    results = []
    for p in players:
        ppg = p["points_per_game"]
        baseline = baseline_by_code.get(_get(p, "code"))
        rate = baseline if baseline is not None else ppg   # ADR-028: baseline, else current
        available = is_available(p)
        gw_map = diff_by_team_gw.get(p["team_id"], {})
        # Fixtures flattened in gameweek order (for `games` and the next-fixture difficulty).
        flat = [d for gw in horizon_events for d in gw_map.get(gw, [])]

        if rate is None or not available:
            by_gameweek = {gw: 0.0 for gw in horizon_events}
            xp = 0.0
        else:
            # Per-GW xP unrounded, so the total is exactly today's number (ADR-032);
            # per-GW cells are rounded only for display.
            unrounded = {
                gw: rate * sum(_multiplier(d) for d in gw_map.get(gw, []))
                for gw in horizon_events
            }
            xp = round(sum(unrounded.values()), 1)
            by_gameweek = {gw: round(v, 1) for gw, v in unrounded.items()}

        results.append({
            "id": p["id"],
            "web_name": p["web_name"],
            "team": p["team"],
            "position": p["position"],
            "xp": xp,
            "games": len(flat),                       # fixtures in the horizon (DGW → >horizon)
            "ep_next": p["ep_next"],
            "difficulty": flat[0] if flat else None,  # next fixture (for N=1 display)
            "rate": round(rate, 2) if rate is not None else None,
            "rate_source": "hist" if baseline is not None else "current",
            "by_gameweek": by_gameweek,               # ADR-032: {gw → xP}, sums to `xp`
            "gameweeks": list(horizon_events),
        })

    results.sort(key=lambda r: r["xp"], reverse=True)
    return results
