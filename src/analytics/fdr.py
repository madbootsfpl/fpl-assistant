"""Fixture analysis from a team's perspective (FDR + schedules).

The shared idea is **perspective**: the same fixture is easy for one side and hard
for the other, so each team reads its own difficulty and opponent. `_view` captures
that once; `team_fdr` aggregates it, `team_schedule` lists it.
"""

from collections import defaultdict


def elo_difficulty_bands(teams) -> dict:
    """Turn team Elo into a 1-5 difficulty band, keyed by short_name (ADR-010).

    Sort the rated teams by Elo and split into 5 equal bands (4 per band for 20
    teams): weakest → 1, strongest → 5. Teams without Elo are omitted (their
    difficulty is undefined).
    """
    rated = sorted((t for t in teams if t["elo"] is not None), key=lambda t: t["elo"])
    n = len(rated)
    bands = {}
    for i, t in enumerate(rated):
        bands[t["short_name"]] = min(5, i * 5 // n + 1) if n else None
    return bands


def _view(fixture, team, source: str = "fpl", elo_bands=None):
    """This fixture seen from `team`'s side: (difficulty, opponent, venue).

    `source` selects which difficulty number:
    - "fpl"    → FPL's published team_h/a_difficulty (ADR-004);
    - "custom" → the opponent's overall strength at the venue they play (ADR-005);
    - "elo"    → the opponent's Elo band (1-5) from `elo_bands` (ADR-010).
    """
    is_home = fixture["home"] == team
    opponent = fixture["away"] if is_home else fixture["home"]
    venue = "H" if is_home else "A"
    if source == "elo":
        difficulty = (elo_bands or {}).get(opponent)
    elif source == "custom":
        difficulty = (
            fixture["away_team_strength"] if is_home else fixture["home_team_strength"]
        )
    else:
        difficulty = (
            fixture["team_h_difficulty"] if is_home else fixture["team_a_difficulty"]
        )
    return difficulty, opponent, venue


def team_fdr(fixtures, next_n: int = 5, source: str = "fpl", elo_bands=None) -> list[dict]:
    """Rank teams by average difficulty over their next `next_n` fixtures.

    `fixtures` is a sequence of upcoming-fixture mappings (from
    Storage.get_upcoming_fixtures()), already ordered by gameweek. `source` picks
    FPL's difficulty, our custom one, or Elo (needs `elo_bands`). Returns a list of
    dicts sorted easiest-run first; a team with no valid difficulty sorts last.
    """
    per_team = defaultdict(list)   # short_name -> list of (difficulty, opponent)
    for f in fixtures:
        for team in (f["home"], f["away"]):
            difficulty, opponent, _ = _view(f, team, source, elo_bands)
            per_team[team].append((difficulty, opponent))

    results = []
    for team, games in per_team.items():
        window = games[:next_n]                       # the team's next N fixtures
        diffs = [d for (d, _) in window if d is not None]
        avg = sum(diffs) / len(diffs) if diffs else None
        results.append({
            "team": team,
            "games": len(window),
            "avg_difficulty": avg,
            "opponents": [opp for (_, opp) in window],
        })

    # Easiest run first; undefined averages sort to the bottom.
    results.sort(key=lambda r: (r["avg_difficulty"] is None, r["avg_difficulty"] or 0.0))
    return results


def team_schedule(fixtures, team, source: str = "fpl") -> list[dict]:
    """One team's upcoming fixtures, each seen from that team's perspective.

    Returns a list of {event, opponent, venue, difficulty}, in the order given
    (the caller passes fixtures already ordered by gameweek). `source` picks FPL's
    difficulty or our custom one, exactly as in team_fdr.
    """
    schedule = []
    for f in fixtures:
        if team in (f["home"], f["away"]):
            difficulty, opponent, venue = _view(f, team, source)
            schedule.append({
                "event": f["event"],
                "opponent": opponent,
                "venue": venue,
                "difficulty": difficulty,
            })
    return schedule


def fixture_ticker(fixtures, next_n: int = 6, source: str = "fpl") -> dict:
    """A teams × gameweeks difficulty grid (Sprint 062) — reuses `team_fdr` + `team_schedule`.

    Returns `{"gameweeks": [event, ...], "rows": [{"team", "avg_difficulty", "cells": {event: cell}}]}`
    where `cell` is `{opponent, venue, difficulty, fixtures}` or None (a **blank** gameweek).

    `fixtures` is the full list for that gameweek, so a **double** shows both matches (ADR-129 audit). It used
    to keep only the first, which hid the second half of a double in the one view built for spotting them —
    a blank gameweek was visible as an empty cell while a double was invisible. `opponent` / `venue` /
    `difficulty` stay as the *first* match so existing readers keep working, and `difficulty` is the run's
    hardest of the two, since the cell is shaded by it and a double is only as easy as its harder half.

    Teams are ordered easiest-run-first over the window; `gameweeks` are the next `next_n` upcoming gameweeks.
    """
    events = sorted({f["event"] for f in fixtures if f["event"]})[:next_n]
    ranked = team_fdr(fixtures, next_n=next_n, source=source)     # already easiest-first
    rows = []
    for r in ranked:
        by_event: dict = {}
        for s in team_schedule(fixtures, r["team"], source=source):
            if s["event"] in events:
                by_event.setdefault(s["event"], []).append(s)
        by_event = {ev: {**fx[0], "fixtures": fx,
                         "difficulty": max((f["difficulty"] for f in fx if f["difficulty"] is not None),
                                           default=fx[0]["difficulty"])}
                    for ev, fx in by_event.items()}
        rows.append({
            "team": r["team"],
            "avg_difficulty": r["avg_difficulty"],
            "cells": {ev: by_event.get(ev) for ev in events},
        })
    return {"gameweeks": events, "rows": rows}
