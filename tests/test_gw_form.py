"""Tests for per-gameweek form — results and per-stat series (ADR-128).

The GW1 follow-ups tracked by ADR-118 (sparklines, W-D-L dots) and ADR-119 (real clean-sheet rate, team form)
all needed the same thing and none could have it: the season aggregates on `players` are a *running total*, so
they know a player has 3 goals but not which weeks. Sprint 179 widened `player_history` from 8 columns to 27;
this is what reads it.

The trap these guard against: FPL writes a per-GW row when the fixture is **scheduled**, not played (ADR-125),
so row presence proves nothing. "Played" is judged on the scoreline being present.
"""

from src.analytics.gw_form import (
    form_dots,
    match_result,
    stat_series,
    team_clean_sheet_rate,
    team_form,
)


def _gw(rnd=1, home=True, hs=2, as_=0, minutes=90, **extra):
    row = {"round": rnd, "was_home": 1 if home else 0, "team_h_score": hs, "team_a_score": as_,
           "minutes": minutes, "total_points": 5, "clean_sheets": 0, "xg": 0.3, "bps": 20}
    row.update(extra)
    return row


def _unplayed(rnd=2):
    """What FPL writes when a fixture is scheduled but not played: a row of zeros, no scoreline."""
    return {"round": rnd, "was_home": 1, "team_h_score": None, "team_a_score": None,
            "minutes": 0, "total_points": 0, "clean_sheets": 0, "xg": None, "bps": 0}


# ---- the result ------------------------------------------------------------------

def test_result_is_read_from_the_player_s_side_of_the_scoreline():
    assert match_result(_gw(home=True, hs=2, as_=0)) == "W"
    assert match_result(_gw(home=False, hs=2, as_=0)) == "L"
    assert match_result(_gw(home=False, hs=0, as_=2)) == "W"
    assert match_result(_gw(hs=1, as_=1)) == "D"


def test_an_unplayed_fixture_has_no_result():
    """Not a loss, not a draw — no result at all. A match kicking off tonight must not read as a defeat."""
    assert match_result(_unplayed()) is None


# ---- form dots -------------------------------------------------------------------

def test_form_dots_are_oldest_first_and_capped():
    hist = {7: [_gw(rnd=r, hs=(2 if r % 2 else 0), as_=(0 if r % 2 else 1)) for r in range(1, 8)]}
    dots = form_dots(hist, 7, last=3)
    assert [r for r, _ in dots] == [5, 6, 7]


def test_form_dots_skip_an_unplayed_gameweek():
    hist = {7: [_gw(rnd=1), _unplayed(2)]}
    assert form_dots(hist, 7) == [(1, "W")]


def test_form_dots_are_empty_without_history():
    assert form_dots({}, 7) == [] and form_dots(None, 7) == []


# ---- per-stat series -------------------------------------------------------------

def test_stat_series_reads_one_column_across_gameweeks():
    hist = {7: [_gw(rnd=1, bps=20), _gw(rnd=2, bps=35)]}
    assert stat_series(hist, 7, "bps") == [(1, 20), (2, 35)]


def test_stat_series_per90_scales_and_drops_minuteless_weeks():
    """A per-90 off zero minutes is undefined, not zero — those gameweeks leave the series."""
    hist = {7: [_gw(rnd=1, xg=0.5, minutes=45), _gw(rnd=2, xg=0.0, minutes=0)]}
    assert stat_series(hist, 7, "xg", per90=True) == [(1, 1.0)]


def test_stat_series_ignores_an_unplayed_gameweek():
    hist = {7: [_gw(rnd=1, bps=20), _unplayed(2)]}
    assert stat_series(hist, 7, "bps") == [(1, 20)]


# ---- team-level --------------------------------------------------------------------

def _p(code, team, pos="MID"):
    return {"code": code, "team": team, "position": pos}


def test_team_form_uses_the_fullest_record_at_the_club():
    """Every player at a club shares its results, but a January signing has gaps — take the longest run."""
    players = [_p(1, "ARS"), _p(2, "ARS")]
    hist = {1: [_gw(rnd=2)], 2: [_gw(rnd=1), _gw(rnd=2, hs=0, as_=1)]}
    assert team_form(hist, players, "ARS") == [(1, "W"), (2, "L")]


def test_clean_sheet_rate_comes_from_the_keeper():
    """A keeper plays the whole match, so his clean_sheets is the team's. An outfielder on at 80 minutes
    carries a 0 for a match his side won 3-0."""
    players = [_p(1, "ARS", "GK"), _p(2, "ARS", "DEF")]
    hist = {1: [_gw(rnd=1, clean_sheets=1), _gw(rnd=2, clean_sheets=0)],
            2: [_gw(rnd=1, clean_sheets=0), _gw(rnd=2, clean_sheets=0)]}
    assert team_clean_sheet_rate(hist, players, "ARS") == 0.5


def test_clean_sheet_rate_ignores_a_benched_keeper():
    players = [_p(1, "ARS", "GK"), _p(2, "ARS", "GK")]
    hist = {1: [_gw(rnd=1, clean_sheets=1, minutes=90)],
            2: [_gw(rnd=1, clean_sheets=0, minutes=0)]}       # the backup, on the bench
    assert team_clean_sheet_rate(hist, players, "ARS") == 1.0


def test_clean_sheet_rate_is_none_before_a_team_has_played():
    """None, not 0% — a club whose opener hasn't kicked off has kept no clean sheets *and* conceded nothing.
    The caller falls back to the proxy rather than showing a fact it doesn't have."""
    players = [_p(1, "CHE", "GK")]
    assert team_clean_sheet_rate({1: [_unplayed(1)]}, players, "CHE") is None
    assert team_clean_sheet_rate({}, players, "CHE") is None
