"""Tests for xMins v0 — the expected-minutes weight (ADR-038).

Pure functions: player availability + a historical minutes share → a weight in [0, 1],
used at the decision edge to scale xP by expected playing time. The design was corrected
at planning: minutes-only (`starts` is unreliable pre-2022/23), no 900-min gate, and
graceful fallbacks (no history / no news → nailed-on).
"""

from src.analytics.minutes import (
    availability_weight,
    chance_factor,
    expected_minutes,
    minutes_share,
    minutes_weight_from_history,
)


def _hist(*minutes):
    """History rows, oldest → newest, as the store hands them (only `minutes` is used)."""
    return [{"minutes": m} for m in minutes]


# ---- chance_factor: availability next round --------------------------------

def test_chance_none_means_assume_available():
    assert chance_factor({"status": "a", "chance": None}) == 1.0


def test_chance_percentage_scales_to_a_fraction():
    assert chance_factor({"status": "d", "chance": 75}) == 0.75
    assert chance_factor({"status": "d", "chance": 25}) == 0.25


def test_injured_is_zero():
    assert chance_factor({"status": "i", "chance": 0}) == 0.0


def test_suspended_is_zero_even_though_chance_is_none():
    # The planning finding: suspended players show chance = None, so status is the gate.
    assert chance_factor({"status": "s", "chance": None}) == 0.0


def test_unavailable_is_zero():
    assert chance_factor({"status": "u", "chance": None}) == 0.0


# ---- minutes_share: historical share of a full season ----------------------

def test_no_history_returns_none_so_caller_assumes_nailed_on():
    assert minutes_share([]) is None


def test_a_full_season_is_a_share_of_one():
    assert minutes_share(_hist(38 * 90)) == 1.0


def test_partial_minutes_are_a_partial_share():
    # Half a season of minutes → a 0.5 share.
    assert minutes_share(_hist(19 * 90)) == 0.5


def test_over_a_full_season_is_capped_at_one():
    # A double-gameweek-heavy season could exceed 38×90; the share caps at 1.0.
    assert minutes_share(_hist(50 * 90)) == 1.0


def test_recent_seasons_weigh_more():
    # Oldest 0.0 share, newest 1.0 share → recency-weighted mean pulls above the flat 0.5.
    share = minutes_share(_hist(0, 38 * 90))       # ranks 1 and 2
    assert share == (1 * 0.0 + 2 * 1.0) / (1 + 2)  # = 0.667, not 0.5


def test_only_the_last_k_seasons_count():
    # A distant full season is dropped once three nearer seasons exist.
    assert minutes_share(_hist(38 * 90, 0, 0, 0), k_seasons=3) == 0.0


def test_no_900_minute_gate_a_tiny_sample_still_lowers_the_share():
    # Unlike the xP rate baseline, a cameo season is kept — low minutes SHOULD lower the weight.
    assert 0.0 < minutes_share(_hist(200)) < 0.1


# ---- availability_weight: the product -------------------------------------

def test_weight_is_chance_times_minutes_share():
    p = {"status": "d", "chance": 50}
    assert availability_weight(p, _hist(19 * 90)) == 0.25   # 0.50 × 0.50


def test_no_history_weight_is_just_the_chance_factor():
    # Missing history → nailed-on (share 1.0), so the weight is the chance factor alone.
    assert availability_weight({"status": "a", "chance": None}, []) == 1.0
    assert availability_weight({"status": "d", "chance": 75}, []) == 0.75


def test_injured_is_zero_regardless_of_minutes():
    assert availability_weight({"status": "i", "chance": 0}, _hist(38 * 90)) == 0.0


def test_a_nailed_on_starter_keeps_near_full_weight():
    p = {"status": "a", "chance": None}
    assert availability_weight(p, _hist(37 * 90, 38 * 90)) > 0.95


def test_an_available_but_fringe_player_is_demoted():
    # Status 'a', no news — but only ~a quarter of the minutes → a heavy demotion.
    p = {"status": "a", "chance": None}
    assert availability_weight(p, _hist(10 * 90, 9 * 90)) < 0.3


# ---- expected_minutes: the display form -----------------------------------

def test_expected_minutes_is_the_weight_in_minutes():
    assert expected_minutes(1.0) == 90
    assert expected_minutes(0.62) == 56       # 0.62 × 90 = 55.8 → 56
    assert expected_minutes(0.0) == 0


def test_expected_minutes_treats_missing_weight_as_zero():
    assert expected_minutes(None) == 0


# ---- minutes_weight_from_history: the decision-layer closure ---------------

def test_closure_looks_up_history_by_player_code():
    history_by_code = {223094: _hist(38 * 90, 38 * 90)}   # a full-time regular
    weight = minutes_weight_from_history(history_by_code)
    nailed_on = {"code": 223094, "status": "a", "chance": None}
    assert weight(nailed_on) == 1.0


def test_closure_falls_back_to_nailed_on_when_the_player_has_no_history():
    weight = minutes_weight_from_history({})              # nobody backfilled
    p = {"code": 999, "status": "a", "chance": None}
    assert weight(p) == 1.0                               # no history → weight = chance factor
