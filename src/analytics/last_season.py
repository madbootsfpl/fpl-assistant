"""Last season's numbers, in *player* shape — so the stat boards can answer before this season can (ADR-126).

The over/under, clean-sheet and DefCon boards gate at 900 minutes (~10 matches). That gate is the Sprint 016
Meslier lesson (ADR-017/018): a per-90 rate off a cameo is not a weak signal, it is a wrong one. It is also why
all three sit empty until roughly gameweek 10 — ten weeks of blank boards, right when a new user is deciding
whether the tool has anything to say.

Rather than move the gate (which would fill the boards with nonsense), this projects each player's most recent
stored season into the same mapping shape `Storage.get_players()` returns. The three board functions are pure
over that shape, so they run **unchanged** on last season's numbers — no analytics module knows this exists.

What this deliberately does not do: blend seasons. A number that is part last-season and part this-season cannot
be labelled honestly, and a reader cannot tell what they are looking at. The caller shows one season or the
other and says which.
"""


def _get(row, key):
    """One field from a `sqlite3.Row` or a dict, or None if absent (mirrors `xp._get`)."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def last_season_name(history_by_code) -> str | None:
    """The season label to put on screen (e.g. `2025/26`) — the most recent one stored for anyone.

    Taken from the data rather than hardcoded, so the label cannot drift from the numbers beneath it.
    """
    names = {_get(row, "season_name")
             for rows in (history_by_code or {}).values() for row in (rows or [])}
    names.discard(None)
    return max(names) if names else None


def _row_for(seasons, season_name):
    """A player's row for exactly `season_name`, or None if they have none.

    Deliberately *not* "their most recent season". A player who spent last season outside the Premier League
    has an older row — two-plus years stale — and dropping it under a banner that names last season would put a
    wrong label on a real number, which is the one thing this module exists to avoid. No row is the honest
    answer for them, and the caller's 🌱 note already covers players with nothing at all.
    """
    return next((r for r in reversed(seasons or []) if _get(r, "season_name") == season_name), None)


def last_season_rows(players, history_by_code) -> list[dict]:
    """Each player's most recent season, shaped like a `get_players()` row so the stat boards can consume it.

    Only the fields the three boards read are projected — FPL's history fields are verbose and the boards are
    the only caller. `defcon_per90` is derived here because the live player row carries it precomputed while the
    history row carries the season total.

    **Performance comes from last season; identity and market facts come from the current row.** `id`,
    `web_name`, `team` and `position` are what they are *now* — a player shows under the club they play for
    today, which is the club a manager is deciding about — and so is `selected_by`, because ownership is only
    ever a statement about the present (last season's closing ownership would tell a manager nothing about who
    is differential this week, and FPL does not store it anyway).

    The consequence of taking the club from the current row is that a *team* stat carries across a transfer: a
    defender who moved in the summer brings his old side's `xgc` under his new side's badge. That is real and
    the caller must label it; it is not fixable here, because FPL's history records what a player did without
    recording who for.

    Only rows from **the single most recent stored season** are returned, so every row on screen belongs to the
    season the caller names. Players with nothing for that season — new to the league, or away from it last
    year — are omitted rather than represented by an older, silently mislabelled row.
    """
    season_name = last_season_name(history_by_code)
    if season_name is None:
        return []
    out = []
    for p in players:
        season = _row_for((history_by_code or {}).get(_get(p, "code")), season_name)
        if season is None:
            continue
        minutes = _get(season, "minutes") or 0
        defcon = _get(season, "defensive_contribution") or 0
        out.append({
            "id": _get(p, "id"),
            "web_name": _get(p, "web_name"),
            "team": _get(p, "team"),
            "position": _get(p, "position"),
            "minutes": minutes,
            # Attacking (over/under): expected vs actual, both season totals.
            "xg": _get(season, "expected_goals"),
            "xa": _get(season, "expected_assists"),
            "goals_scored": _get(season, "goals_scored"),
            "assists": _get(season, "assists"),
            # Defensive: xGC is a season total (the board divides by minutes); DefCon is a rate we derive.
            "xgc": _get(season, "expected_goals_conceded"),
            "defcon_per90": (defcon * 90.0 / minutes) if minutes else 0.0,
            # Team DNA's key-players table (ADR-126 follow-up) reads these three.
            "total_points": _get(season, "total_points"),
            "xgi": _get(season, "expected_goal_involvements"),
            # Now-facts, taken live rather than from the season — see the note above. Ownership, price and
            # set-piece duty describe the player as he is *today*: you pay today's price, and it is today's
            # penalty taker you want, not whoever took them last April. Player DNA (ADR-118) reads these.
            "selected_by": _get(p, "selected_by"),
            "price": _get(p, "price"),
            "penalties_order": _get(p, "penalties_order"),
            "corners_order": _get(p, "corners_order"),
            "freekicks_order": _get(p, "freekicks_order"),
        })
    return out
