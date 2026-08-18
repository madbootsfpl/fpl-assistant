"""Player DNA — percentile-within-position player profiling (Sprint 168, ADR-118).

Pure: given a target player and the full player pool, rank the player against
**same-position** peers across eight facets (a "DNA" fingerprint) — each a
**percentile 0–100** so a defender's attacking threat and a forward's are read on
the same scale. Display-only: it creates no new xP and never touches `decision_xp`
(ADR-041). The renderer (`web_streamlit/dna_card.py`) draws these axes as a radar.

Preseason it ranks on **last-season totals** — the same basis xP falls back to when
there's no in-season history yet — so the fingerprint is meaningful from day one;
the per-gameweek *trends* (a separate panel) light up at GW1.

The eight axes (owner-approved, ADR-118):
    Goal Threat (xG/90) · Creativity (xA/90) · Set Pieces (pen/corner/FK order) ·
    FPL Output (pts/90) · Consistency (minutes) · Value (pts/£m) ·
    Bonus Potential (ICT/90 — a proxy; we hold no raw BPS) · Team Attack (team xG).
"""

from dataclasses import dataclass

MIN_MINUTES = 450   # a peer must have played at least this to enter the ranking pool (denoise fringe players)


def _get(row, key):
    """Row/dict-safe accessor (a `sqlite3.Row` has no `.get()`) — returns None if absent."""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _f(v) -> float:
    """A value coerced to float, or 0.0 (None / blank / non-numeric safe)."""
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _per90(value, minutes) -> float:
    """A per-90 rate; 0.0 when there are effectively no minutes (never divides by zero)."""
    m = _f(minutes)
    return _f(value) / (m / 90.0) if m >= 1 else 0.0


def _value_per_m(row) -> float:
    """Total points per £m (bang-for-buck); 0.0 when price is missing."""
    price = _f(_get(row, "price"))
    return _f(_get(row, "total_points")) / price if price > 0 else 0.0


def _set_piece_score(row) -> float:
    """A single set-piece involvement score — penalties weighted highest, then corners / free kicks.
    An `order` of 1 = first-choice (best); 4+ or missing contributes nothing. Ranked into a percentile,
    so the absolute scale only has to order players (pen taker > corner/FK taker > none)."""
    score = 0.0
    for key, weight in (("penalties_order", 3.0), ("corners_order", 1.0), ("freekicks_order", 1.0)):
        order = _get(row, key)
        if order and order >= 1:
            score += weight * max(0.0, 4.0 - order)   # order 1 → 3·w, 2 → 2·w, 3 → 1·w, 4+ → 0
    return score


def _percentile(value, values) -> int | None:
    """Percentile of `value` within `values` = the share of peers **at or below** it (0–100).
    None when there are no peers to rank against (an empty pool)."""
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return round(100 * sum(1 for v in vals if v <= value) / len(vals))


@dataclass(frozen=True)
class Axis:
    """One facet of a player's DNA: a raw value + its percentile-within-position (None if unranked)."""
    label: str          # e.g. "Goal Threat"
    sublabel: str       # e.g. "xG/90"
    value: float        # the player's raw value on this facet
    percentile: int | None   # 0–100 within position (None if there was no ranking pool)


@dataclass(frozen=True)
class PlayerDNA:
    """A player's eight-axis fingerprint, ranked within their position."""
    player_id: object
    name: str
    position: str
    pool_size: int          # same-position peers past the minutes floor (the ranking base — surface it in the UI)
    low_minutes: bool       # the target itself is below the floor → read the shape with care
    min_minutes: int
    axes: list[Axis]        # in radar order (the eight above)


# (label, sublabel, extractor) for the seven per-player axes; Team Attack is team-based, handled separately.
_AXES = [
    ("Goal Threat", "xG/90",   lambda r: _per90(_get(r, "xg"), _get(r, "minutes"))),
    ("Creativity",  "xA/90",   lambda r: _per90(_get(r, "xa"), _get(r, "minutes"))),
    ("Set Pieces",  "pen/set", _set_piece_score),
    ("FPL Output",  "pts/90",  lambda r: _per90(_get(r, "total_points"), _get(r, "minutes"))),
    ("Consistency", "minutes", lambda r: _f(_get(r, "minutes"))),
    ("Value",       "pts/£m",  _value_per_m),
    ("Bonus Potl",  "ICT/90",  lambda r: _per90(_get(r, "ict_index"), _get(r, "minutes"))),
]


def _team_xg(players) -> dict:
    """Total xG per team (short-name) across the whole pool — a team's attacking output."""
    totals: dict = {}
    for p in players:
        team = _get(p, "team")
        if team is not None:
            totals[team] = totals.get(team, 0.0) + _f(_get(p, "xg"))
    return totals


def player_dna(target, players, *, min_minutes: int = MIN_MINUTES) -> PlayerDNA | None:
    """The target's percentile-within-position fingerprint across the eight DNA axes.

    `target` is a player row (dict or `sqlite3.Row`); `players` is the full pool (all positions — the
    Team-Attack axis needs every team's players). Each axis is the target's raw value + its percentile among
    **same-position peers with ≥ `min_minutes`** (the target is always ranked, even if itself below the floor —
    then `low_minutes` is set so the UI can caption it). Returns None if the target has no position. Never raises
    on zeros / blanks / preseason."""
    pos = _get(target, "position")
    if not pos:
        return None

    peers = [p for p in players
             if _get(p, "position") == pos and _f(_get(p, "minutes")) >= min_minutes]
    low_minutes = _f(_get(target, "minutes")) < min_minutes

    axes: list[Axis] = []
    for label, sublabel, extract in _AXES:
        value = extract(target)
        pool = [extract(p) for p in peers]
        axes.append(Axis(label, sublabel, round(value, 2), _percentile(value, pool)))

    # Team Attack — the target's team total xG, ranked across the distinct team totals (not per-player, so a
    # team with more players in the pool isn't over-counted).
    totals = _team_xg(players)
    team_value = totals.get(_get(target, "team"), 0.0)
    axes.append(Axis("Team Attack", "team xG", round(team_value, 2),
                     _percentile(team_value, list(totals.values()))))

    return PlayerDNA(player_id=_get(target, "id"), name=_get(target, "web_name") or "",
                     position=pos, pool_size=len(peers), low_minutes=low_minutes,
                     min_minutes=min_minutes, axes=axes)
