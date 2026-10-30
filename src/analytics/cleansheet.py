"""Clean-sheet / defensive-solidity lens (ADR-019).

Ranks defenders and goalkeepers by expected goals conceded per 90 minutes — the lower,
the more solid the team's defence while they're on the pitch, and the higher their
clean-sheet probability. xGC/90 is computed from the stored `xgc` + `minutes` (it equals
FPL's own `expected_goals_conceded_per_90`). Note this is a *team* signal shown per player.
"""

import math

CLEAN_SHEET_POSITIONS = ("DEF", "GK")   # earn 4 pts for a clean sheet
MIN_MINUTES = 900   # ~10 matches — a per-90 rate off a tiny sample is noise
_EDGE_SEASONS = 3   # seasons of his own history to read the defence he played behind (mirrors the rate's window)


def _field(row, key):
    """Read `key` from a sqlite Row or a dict, None if absent (mirrors `form._field`).

    Needed because the history rows these read come straight from storage as `sqlite3.Row`, which has no
    `.get` — and the ADR-355 pin means the same code meets dicts in tests.
    """
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


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


def clean_sheet_prob(xgc90) -> float | None:
    """A club's xGC/90 as a clean-sheet **probability** — `P(0 conceded) = e^-xGC` (ADR-195).

    ⚠️ **This step is not in ADR-195, and without it the proposal has a units bug.** That ADR says *"swap
    clean-sheet rate for xGC/90 delta, a change to one function's argument"* — but `clean_sheet_delta`
    multiplies by `CLEAN_SHEET_POINTS`, which only means *points* when the delta is a **probability**. Handing
    it a difference in goals-per-90 would produce "4 x goals", a number in no unit at all, and it would have
    looked plausible because the sign and rough magnitude survive.

    ⭐ **A swapped input has to arrive in the units the consumer already assumes**, and the assumption lived in
    the `x 4`, three lines away from the change.

    The Poisson form is the standard one for goals in football: goals conceded ~ Poisson(xGC), so a clean
    sheet is `P(k=0) = e^-xGC`. It also **fixes the sign for free** — lower xGC gives higher probability, so
    the existing `team - league` convention still reads "better than average is positive", with no flip to
    remember. ⚠️ Poisson assumes independent chances, which shot quality violates; it is an approximation, and
    a good one at the accuracy this term is gated at.

    None in, None out — an unknown club stays *no opinion* all the way through (ADR-172).
    """
    if xgc90 is None:
        return None
    return math.exp(-max(0.0, xgc90))


def league_clean_sheet_rate(rates) -> float | None:
    """The mean clean-sheet rate across clubs that have one — the baseline a delta is measured against.

    Clubs with no played gameweeks are excluded rather than counted as 0%, so the average is over what is
    known. None when nothing is known at all.
    """
    known = [r for r in (rates or {}).values() if r is not None]
    return sum(known) / len(known) if known else None


# ─────────────────────────────────────────────────────────────────────────────────────────────────────
# The defence he played behind (ADR-375/376)
#
# ⭐⭐ `clean_sheet_delta` above subtracts the **league** rate so as not to double-count the clean sheets
# already inside a player's historical pts/90. That removes the *average* player's clean sheets, not **his** —
# so every Arsenal defender is credited the identical amount, and a player who moved from a weak defence is
# under-credited by exactly the margin that made him move worth noticing. These read **his own** baseline.
#
# ⚠️ Era-relative on purpose, and the first draft was not. An absolute personal baseline shifts one
# position's whole population in one direction (+0.23 pts/match across 187 DEF/GK), because a clean-sheet
# rate from three seasons ago is not on the same scale as this season's. Each side is therefore measured
# against its own era's league average. ⭐ *A level shift wearing a bias correction's clothes is the easiest
# thing in the world to ship and the hardest to see afterwards.*


def league_cs_by_season(history_by_code, position_by_code, positions=CLEAN_SHEET_POSITIONS) -> dict:
    """`{season_name: clean-sheet rate}` for the league, start-weighted, from stored history.

    **Position-matched by default**, because it is subtracted from DEF/GK figures: computing it over every
    position leaves a +0.04 pts/match residual that looks like signal and is a population mismatch.

    Only rows with `starts > 0` count — `clean_sheets / starts` is the honest per-start rate, and a row with
    no starts carries no denominator.
    """
    acc: dict = {}
    for code, rows in (history_by_code or {}).items():
        if positions and (position_by_code or {}).get(code) not in positions:
            continue
        for r in rows or []:
            starts = _field(r, "starts") or 0
            season = _field(r, "season_name")
            if starts <= 0 or season is None:
                continue
            cs, st = acc.get(season, (0, 0))
            acc[season] = (cs + (_field(r, "clean_sheets") or 0), st + starts)
    return {season: cs / st for season, (cs, st) in acc.items() if st}


def historical_cs_edge(rows, league_by_season, k: int = _EDGE_SEASONS):
    """How much better than its own era his old defence was, per start — or None if we cannot say.

    This is **the part already inside his historical rate**, and therefore the part to remove before pricing
    the defence he plays behind now. ~0 for a player whose club was league-average, which is what makes the
    correction collapse to today's behaviour for everybody who did not move.

    None when no recent season has both starts and a league rate to compare against — promoted clubs and
    young players, mostly. ⭐ The caller must then fall back, never read None as 0: an unknown edge is not a
    neutral one, and ADR-172 is the record of what treating absence as a value costs.
    """
    use = [r for r in list(rows or [])[-k:]
           if (_field(r, "starts") or 0) > 0 and _field(r, "season_name") in (league_by_season or {})]
    if not use:
        return None
    starts = sum(_field(r, "starts") for r in use)
    above = sum((_field(r, "clean_sheets") or 0) - league_by_season[_field(r, "season_name")] * _field(r, "starts")
                for r in use)
    return above / starts


def unpriced_defence(player, rows, team_rate, league_now, league_by_season) -> float:
    """Points per match this player's xP is **understating** him by, through his defence alone.

    🔴 **`CLEAN_SHEET_WEIGHT` is 0, so `decision_xp` prices no clean-sheet term at all** (ADR-188 built it,
    ADR-370 declined the weight). So the whole era-relative delta is missing from his xP, not just the
    difference between two baselines — that is why this returns the full figure.

    ⭐⭐ **One-sided by construction: it returns 0.0 unless the number is positive.** It exists to stop the
    engine advising a sale on a number it knows is biased *downward* (ADR-376) — never to talk anyone into a
    purchase. An ungated correction is safe to act on only where being wrong about it costs nothing, and
    declining to give advice is that place.
    """
    if _field(player, "position") not in CLEAN_SHEET_POSITIONS:
        return 0.0
    if team_rate is None or league_now is None:
        return 0.0
    edge = historical_cs_edge(rows, league_by_season)
    if edge is None:
        return 0.0                      # no personal baseline — today's behaviour, not a guess
    return max(0.0, CLEAN_SHEET_POINTS * ((team_rate - league_now) - edge))


def team_cs_from_fixtures(fixtures) -> dict:
    """`{team_id: clean-sheet rate}` from played scorelines — a side kept one if it conceded 0.

    ⭐⭐ **Exactly equal to `gw_form.team_clean_sheet_rate`'s goalkeeper proxy** (checked club by club at
    GW8: ARS 0.625/0.625, CHE 0.125/0.125, …) and **much cheaper**: 380 fixture rows that do not grow,
    against a per-gameweek history that adds ~45 KB a week and reaches ~1.7 MB by May. ⭐ *When two
    derivations of the same number agree, keep the one whose cost is flat.*

    Only matches with both scores count — an unplayed fixture is silent, never a 0 (ADR-125/129).
    """
    acc: dict = {}
    for f in fixtures or []:
        home, away = _field(f, "team_h_score"), _field(f, "team_a_score")
        if home is None or away is None:
            continue
        for side, conceded in ((_field(f, "team_h"), away), (_field(f, "team_a"), home)):
            if side is None:
                continue
            kept, played = acc.get(side, (0, 0))
            acc[side] = (kept + (1 if conceded == 0 else 0), played + 1)
    return {side: kept / played for side, (kept, played) in acc.items() if played}


def unpriced_defence_by_id(players, history_by_code, fixtures) -> dict:
    """`{player_id: pts/match his xP understates him by}`, for the DEF/GK it can be read for.

    One call so a caller needs two lines rather than five. Entries are added only when the figure is
    **positive**, so an empty dict is the honest "no doubt anywhere" and `.get(id, 0.0)` is safe everywhere.
    """
    rows = list(players or [])
    league_by_season = league_cs_by_season(history_by_code,
                                           {_field(p, "code"): _field(p, "position") for p in rows})
    team_rate = team_cs_from_fixtures(fixtures)
    if not team_rate:
        return {}                                  # preseason — nothing has been played, nothing comparable
    league_now = sum(team_rate.values()) / len(team_rate)
    out = {}
    for p in rows:
        doubt = unpriced_defence(p, (history_by_code or {}).get(_field(p, "code")) or [],
                                 team_rate.get(_field(p, "team_id")), league_now, league_by_season)
        if doubt > 0:
            out[_field(p, "id")] = doubt
    return out
