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

from src.analytics.crowd import ownership_tier
from src.analytics.optimizer import is_unavailable
from src.analytics.ranking import percentile_rank

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
    """Percentile of `value` within `values` (0–100), ties sharing their average rank — see
    `analytics.ranking.percentile_rank` (ADR-127). Kept as a thin alias because it is used throughout this
    module and named for what it means here."""
    return percentile_rank(value, values)


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


def player_dna(target, players, *, min_minutes: int = MIN_MINUTES, skip_axes=()) -> PlayerDNA | None:
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
        if label in skip_axes:      # no honest source for this axis in this pool (ADR-126 fallback)
            continue
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


# ── AI Insights (Sprint 170, ADR-118) ─────────────────────────────────────────
# ICT index is the one DNA input FPL does not keep in a player's season history, so a last-season pool has no
# honest way to rank Bonus Potential. Dropping the axis is the honest answer — an axis every player scores 0 on
# would rank them all identically and read as real.
_NO_LAST_SEASON_SOURCE = ("Bonus Potl",)


def player_dna_this_or_last(target, players, last_rows=None, season_name=None, **kw):
    """A player's DNA from this season, or from last season's pool if this season cannot rank anyone (ADR-126).

    The peer pool needs `min_minutes` (450 — five matches), so for the first weeks of a season it is empty and
    *every* percentile comes back None. That is not a small degradation: percentiles are the whole point of the
    radar, so the card renders a fingerprint with nothing in it.

    Falls back to ranking the player among last season's pool — the target too, so a full-season value is
    compared against full-season peers rather than one gameweek against thirty-eight. Returns
    `(dna, season_label)`; the label is None when the DNA is this season's, or when the player has no
    last-season row at all (new to the league — then the card should say it cannot rank them, not invent it)."""
    dna = player_dna(target, players, **kw)
    if dna is None or dna.pool_size:
        return dna, None
    tid = _get(target, "id")
    last_target = next((r for r in (last_rows or []) if _get(r, "id") == tid), None)
    if last_target is None:
        return dna, None
    return player_dna(last_target, last_rows, skip_axes=_NO_LAST_SEASON_SOURCE, **kw), season_name


# Plain-English, GROUNDED observations synthesised from the DNA percentiles + the player row + crowd tier — the
# "the AI explains" panel. Every bullet traces to a value (a percentile, a set-piece order, an ownership tier, a
# price); nothing is invented. Display-only; no `decision_xp`.

_POS_WORD = {"GK": "goalkeepers", "DEF": "defenders", "MID": "midfielders", "FWD": "forwards"}
# Skill axes for the "top strengths" lines — Set Pieces is excluded on purpose: it gets its own dedicated ⚡ line
# (penalty taker / on set pieces), so listing it here too would double up.
_SKILL_AXES = ("Goal Threat", "Creativity", "FPL Output", "Value", "Bonus Potl")
_PREMIUM_PRICE = 9.0


@dataclass(frozen=True)
class Insight:
    """One grounded observation: a `kind` (good ✓ · sp ⚡ · info ℹ · warn ⚠) + its text."""
    kind: str
    text: str


def _num(v) -> str:
    v = _f(v)
    if abs(v) >= 100:
        return f"{v:,.0f}"
    return f"{int(v)}" if v == int(v) else f"{v:g}"


def _ord(n) -> str:
    n = int(n)
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def player_insights(player, dna, *, max_items: int = 5) -> list[Insight]:
    """A prioritised list of grounded insights for `player` given its `dna` (from `player_dna`). Availability leads
    when flagged, then top skill strengths, team context, set-piece floor, ownership, then price/minutes cautions.
    Pure, dict + `sqlite3.Row` safe, empty-safe (fewer bullets for a blank player, never raises). Capped at
    `max_items`."""
    if player is None or dna is None:
        return []
    pos = _POS_WORD.get(dna.position, "players")
    by = {a.label: a for a in dna.axes}
    out: list[Insight] = []

    # 1. availability first when flagged
    if is_unavailable(player):
        out.append(Insight("warn", "Unavailable — injured or suspended"))
    elif _get(player, "status") == "d":
        chance = _get(player, "chance")
        out.append(Insight("warn", f"Doubtful — {int(chance)}% chance to play" if chance is not None
                                   else "Doubtful to start"))

    # 2. top 1–2 skill strengths
    skills = sorted((a for a in dna.axes if a.label in _SKILL_AXES and a.percentile is not None),
                    key=lambda a: a.percentile, reverse=True)
    elite = [a for a in skills if a.percentile >= 85][:2]
    if elite:
        for a in elite:
            out.append(Insight("good", f"Elite {a.label.lower()}: top {max(1, 100 - a.percentile)}% of {pos} "
                                       f"({a.sublabel} {_num(a.value)})"))
    elif skills and skills[0].percentile >= 65:
        a = skills[0]
        out.append(Insight("good", f"Strong {a.label.lower()}: {a.sublabel} {_num(a.value)} "
                                   f"({_ord(a.percentile)} percentile)"))

    # 3. team context
    ta = by.get("Team Attack")
    if ta and ta.percentile is not None and ta.percentile >= 80:
        out.append(Insight("info", f"Plays in a top-{max(1, 100 - ta.percentile)}% attack"))

    # 4. set-piece floor
    if _get(player, "penalties_order") == 1:
        out.append(Insight("sp", "First-choice penalty taker — a steady points floor"))
    elif _get(player, "corners_order") == 1 or _get(player, "freekicks_order") == 1:
        out.append(Insight("sp", "On set pieces (corners / free kicks)"))

    # 5. ownership context
    tier = ownership_tier(player)
    own = _get(player, "selected_by")
    if tier and own is not None:
        if "differential" in tier:
            out.append(Insight("info", f"Differential — only {own:.1f}% owned"))
        elif "essential" in tier or "template" in tier:
            out.append(Insight("info", f"Owned by {own:.1f}% — {tier}"))

    # 6. cautions
    val = by.get("Value")
    price = _get(player, "price")
    if (val and val.percentile is not None and val.percentile <= 35
            and price is not None and price >= _PREMIUM_PRICE):
        out.append(Insight("warn", f"Premium at £{_num(price)}m — value only mid-pack "
                                   "(the case is ceiling, not £-efficiency)"))
    con = by.get("Consistency")
    if not is_unavailable(player) and ((con and con.percentile is not None and con.percentile <= 30)
                                       or dna.low_minutes):
        out.append(Insight("warn", "Limited minutes so far — rotation or fitness risk"))

    return out[:max_items]


# ── Per-gameweek trend (Sprint 171, ADR-118) — lights up at GW1 ───────────────

def player_gw_points(gw_history, code, *, last: int = 8) -> list[tuple]:
    """The player's **points-per-gameweek** series `[(round, total_points), …]`, most recent `last` rounds, in
    round order. `gw_history` is `{element_code: [rows by round]}` (Storage.get_gw_history_by_code) — **empty
    preseason**, so this returns `[]` until GW1 results land. Skips rounds with no `total_points`. Row/dict safe."""
    rows = (gw_history or {}).get(code) or []
    series = [(_get(r, "round"), _get(r, "total_points")) for r in rows
              if _get(r, "round") is not None and _get(r, "total_points") is not None]
    series.sort(key=lambda t: t[0])
    return series[-last:]
