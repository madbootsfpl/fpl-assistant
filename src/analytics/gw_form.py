"""Per-gameweek form — results and per-stat series from the backfilled `player_history` (ADR-128).

Both DNA follow-ups needed the same thing and neither could have it: the season aggregates on `players` are a
**running total**, so they can say a player has 3 goals but never *which weeks*. A trend line and a W-D-L dot
need the week itself, which is why Sprint 179 widened the per-GW table (8 columns → 27).

Pure and Row/dict safe, like the rest of `analytics`. Everything here returns an empty result rather than
raising when the data isn't there yet — a gameweek that hasn't been played carries a row with zeros (FPL
creates it at fixture-scheduling time, ADR-125), so "played" is judged on **minutes**, never on row presence.
"""

_WIN, _DRAW, _LOSS = "W", "D", "L"


def _get(row, key):
    """A field from a `sqlite3.Row` or a dict, or None if absent."""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _played(row) -> bool:
    """Did this gameweek actually happen for this player's team?

    A scoreline is the tell: FPL writes the per-GW row when the fixture is *scheduled*, with zeros throughout,
    so `round` and even `minutes` being present prove nothing (ADR-125). A `team_h_score` only exists once the
    match has a result.
    """
    return _get(row, "team_h_score") is not None and _get(row, "team_a_score") is not None


def match_result(row) -> str | None:
    """`W` / `D` / `L` from the player's team's perspective, or None if the match hasn't been played.

    FPL gives the scoreline and a `was_home` flag but never a result, so it is derived here once rather than
    at each call site.
    """
    if not _played(row):
        return None
    h, a = _get(row, "team_h_score"), _get(row, "team_a_score")
    ours, theirs = (h, a) if _get(row, "was_home") else (a, h)
    if ours > theirs:
        return _WIN
    return _DRAW if ours == theirs else _LOSS


def form_dots(gw_history, code, *, last: int = 5) -> list[tuple]:
    """A player's team's recent results as `[(round, "W"|"D"|"L"), …]`, oldest first, most recent `last`.

    Keyed by the player because that is what the card has to hand; the result is a *team* fact, so two players
    from the same club give the same dots. Unplayed gameweeks are skipped, not shown as a loss.
    """
    rows = (gw_history or {}).get(code) or []
    out = [(_get(r, "round"), match_result(r)) for r in rows if _played(r)]
    out = [(rnd, res) for rnd, res in out if rnd is not None and res is not None]
    out.sort(key=lambda t: t[0])
    return out[-last:]


def stat_series(gw_history, code, stat, *, last: int = 8, per90: bool = False,
                agg: str = "sum") -> list[tuple]:
    """One stat's per-gameweek series as `[(round, value), …]`, oldest first, most recent `last` rounds.

    `stat` is a `player_history` column (`xg`, `bps`, `ict_index`, `goals_scored`, …). With `per90=True` the
    value is scaled to a 90-minute rate, and gameweeks with no minutes are dropped — a per-90 off zero minutes
    is not a small number, it is undefined.

    **A row is a fixture, not a gameweek** (ADR-129), so a double gameweek contributes two rows to one round.
    They are combined here rather than plotted as two points at the same x. `agg` says how:

    * `"sum"` (default) — for **counting** stats: points, goals, bps, minutes, xG. A double gameweek's return
      *is* the sum of its two matches, and a per-90 divides by the summed minutes.
    * `"last"` — for **snapshot** stats, `value` (price) being the one that matters. Adding a player's price to
      itself because he played twice would read as a £10m rise.

    Only gameweeks that have actually been played are included, so a scheduled-but-unplayed row cannot enter a
    trend as a zero.
    """
    rows = (gw_history or {}).get(code) or []
    by_round: dict = {}
    for r in rows:
        if not _played(r):
            continue
        rnd, value = _get(r, "round"), _get(r, stat)
        if rnd is None or value is None:
            continue
        total, mins = by_round.get(rnd, (0, 0))
        total = value if agg == "last" else total + value
        by_round[rnd] = (total, mins + (_get(r, "minutes") or 0))

    out = []
    for rnd in sorted(by_round):
        total, mins = by_round[rnd]
        if per90:
            if mins <= 0:
                continue
            total = total * 90.0 / mins
        out.append((rnd, total))
    return out[-last:]


def team_form(gw_history, players, team, *, last: int = 5) -> list[tuple]:
    """A **team's** recent results as `[(round, "W"|"D"|"L"), …]`, oldest first (ADR-119 follow-up).

    Read off whichever of the club's players has the fullest record — every player at a club shares its
    results, but an individual may have joined late or have gaps, so the longest run is the safest source.
    """
    codes = [_get(p, "code") for p in players if _get(p, "team") == team]
    best: list[tuple] = []
    for code in codes:
        dots = form_dots(gw_history, code, last=last)
        if len(dots) > len(best):
            best = dots
    return best


def team_clean_sheet_rate(gw_history, players, team) -> float | None:
    """The share of played gameweeks in which `team` kept a clean sheet, 0.0-1.0 (ADR-119 follow-up).

    Replaces the labelled xGA *proxy* with what actually happened. Taken from the club's **goalkeepers** — a
    keeper is on the pitch for the whole match, so his `clean_sheets` is the team's, while an outfield player
    who came on at 80 minutes carries a 0 for a match his team won 3-0 to nil.

    None when the team has no played gameweeks yet, so the caller can fall back rather than read 0% as a fact.
    """
    gks = [p for p in players if _get(p, "team") == team and _get(p, "position") == "GK"]
    by_round: dict = {}
    for gk in gks:
        for r in (gw_history or {}).get(_get(gk, "code")) or []:
            if not _played(r) or (_get(r, "minutes") or 0) <= 0:
                continue          # a benched keeper's row says nothing about the team
            rnd = _get(r, "round")
            if rnd is not None:
                by_round[rnd] = max(by_round.get(rnd, 0), _get(r, "clean_sheets") or 0)
    if not by_round:
        return None
    return sum(1 for v in by_round.values() if v) / len(by_round)
