"""Tests for xMins v0 — the expected-minutes weight (ADR-038).

Pure functions: player availability + a historical minutes share → a weight in [0, 1],
used at the decision edge to scale xP by expected playing time. The design was corrected
at planning: minutes-only (`starts` is unreliable pre-2022/23), no 900-min gate, and
graceful fallbacks (no history / no news → nailed-on).
"""

from src.analytics.minutes import (
    availability_weight,
    chance_factor,
    completed_gameweeks,
    expected_minutes,
    in_season_share,
    minutes_share,
    minutes_weight_from_history,
    yet_to_play,
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


# ---- has he actually played? (ADR-138) -----------------------------------------------

def _mp(code=1):
    return {"code": code, "web_name": "X", "status": "a"}


def _gw(rnd, minutes, *, played=True):
    """A per-gameweek row. `played` controls whether it has a SCORELINE, which is the only honest signal —
    FPL writes the row when the fixture is *scheduled*, so `minutes == 0` alone means nothing."""
    return {"round": rnd, "minutes": minutes,
            "team_h_score": 1 if played else None, "team_a_score": 0 if played else None}


def test_a_player_whose_team_played_without_him_is_flagged():
    """The state the xMins weight is blind to: his team has played, he did not feature. That is evidence — of
    a bench role, a rotation, or a manager's opinion — and the in-season minutes share is deferred until there
    are enough gameweeks to act on it (ADR-125), so a surface has to say it rather than model it."""
    assert yet_to_play(_mp(), {1: [_gw(1, 0)]}) is True


def test_a_player_who_featured_is_not_flagged():
    assert yet_to_play(_mp(), {1: [_gw(1, 90)]}) is False
    assert yet_to_play(_mp(), {1: [_gw(1, 0), _gw(2, 12)]}) is False, "twelve minutes is still featuring"


def test_a_fixture_that_has_not_kicked_off_proves_nothing():
    """The trap this project has hit before (ADR-125/129): FPL writes a 0-minute row for a **scheduled**
    fixture. Reading that as "didn't play" would libel every player at every club whose gameweek is in flight
    — on the live data, Leno shows 0 minutes only because Fulham have not played yet."""
    assert yet_to_play(_mp(), {1: [_gw(1, 0, played=False)]}) is False


def test_no_history_at_all_is_not_an_accusation():
    for history in ({}, {1: []}, None):
        assert yet_to_play(_mp(), history) is False


def test_a_history_of_empty_seasons_means_unknown_not_never_plays():
    """Found 2026-09-01, via ADR-172's amendment.

    A player promoted with his club carries stored seasons for years spent outside the league. Thomas (COV)
    has **four, all with zero minutes**. Averaging those gave a share of 0.0 — "never plays" — for a player
    who has started every game this season, while an *empty* history two lines up returns None and the
    module's stated rule applies: never penalise the unknown. Same ignorance, opposite answers.

    It stayed invisible because a second bug cancelled it: the cold-start shrink prior escaped the minutes
    weight, quietly handing back the points the 0.0 share had removed. Fixing that (ADR-172) exposed this —
    seven players who have played this season, two of them every minute, would have projected exactly 0.
    """
    assert minutes_share([{"minutes": 0}, {"minutes": 0}, {"minutes": 0}]) is None
    assert minutes_share([]) is None, "and it agrees with the empty case it was contradicting"


def test_a_single_real_season_still_counts_among_empty_ones():
    # Only *total* absence is unknown. One real season is evidence, and must not be discarded with the blanks.
    share = minutes_share([{"minutes": 0}, {"minutes": 0}, {"minutes": 1710}])
    assert share is not None and 0 < share < 1


def test_an_all_empty_history_no_longer_zeroes_a_player_who_is_playing():
    # The end-to-end shape: availability_weight must not read blank seasons as a benching.
    player = {"status": "a", "chance": None}
    assert availability_weight(player, [{"minutes": 0}, {"minutes": 0}]) == 1.0


def test_seasons_that_stopped_are_still_evidence_of_a_benching():
    """The counter-case that narrowed the rule above, and the reason it tests the whole history.

    Minutes alone cannot tell a season spent outside the league from a season spent on the bench. So the
    only honest cut is *have we ever seen him play* — a player with a full season behind him and three
    empty ones since has declined, and must keep his 0.0 share. A pre-existing test
    (`test_only_the_last_k_seasons_count`) said exactly this, and a blanket check on the k-season window
    would have quietly rescued him along with Thomas.
    """
    assert minutes_share(_hist(38 * 90, 0, 0, 0), k_seasons=3) == 0.0


# ---- ADR-173: the minutes he has actually played ---------------------------


def test_a_gameweek_counts_only_once_it_has_a_scoreline():
    # ADR-125's trap: FPL writes the row when the fixture is SCHEDULED, so minutes 0 can mean "not kicked
    # off". Only a scoreline proves it finished — the same test `yet_to_play` uses.
    assert completed_gameweeks({1: [_gw(1, 90), _gw(2, 0, played=False)]}) == {1}


def test_the_share_is_the_minutes_he_played_of_those_available():
    gwh = {7: [_gw(1, 90), _gw(2, 45)]}
    p = {"code": 7, "status": "a", "chance": None}
    assert in_season_share(p, gwh) == 0.75          # 135 of 180


def test_sitting_one_gameweek_out_falls_back_to_history_rather_than_cratering_him():
    """The guard, and the reason the whole design is defensible.

    Two gameweeks cannot tell a player rested once from one being phased out (ADR-125's objection, which
    stands). So this refuses the ambiguous case entirely instead of guessing: a 0-minute gameweek returns
    None, the caller keeps the historical share, and one rest can never crater a player.
    """
    gwh = {7: [_gw(1, 90), _gw(2, 0)]}
    p = {"code": 7, "status": "a", "chance": None}
    assert in_season_share(p, gwh) is None


def test_missing_from_a_completed_gameweek_does_not_qualify_either():
    # No row at all for a gameweek his league played — same ignorance, same answer.
    gwh = {7: [_gw(1, 90)], 8: [_gw(1, 90), _gw(2, 90)]}
    assert in_season_share({"code": 7, "status": "a", "chance": None}, gwh) is None
    assert in_season_share({"code": 8, "status": "a", "chance": None}, gwh) == 1.0


def test_no_completed_gameweeks_means_no_opinion():
    # Preseason and mid-first-gameweek: nothing has finished, so nothing is claimed.
    assert in_season_share({"code": 7}, {7: [_gw(1, 0, played=False)]}) is None
    assert in_season_share({"code": 7}, {}) is None


def test_the_weight_prefers_played_minutes_over_last_seasons():
    """End to end: a player with a thin history but a full record this season is no longer held down.

    Calafiori carried 0.43 from an injury-hit season while playing 94% of the minutes available; Kinsky
    carried 0.18 while being first choice. The historical share is not wrong about last season — it is
    answering a question about this one.
    """
    hist = {7: [{"minutes": 900, "total_points": 40}]}        # a half-season → a low historical share
    gwh = {7: [_gw(1, 90), _gw(2, 90)]}                       # …but he has started every game since
    p = {"code": 7, "status": "a", "chance": None}
    assert minutes_weight_from_history(hist)(p) < 0.5         # today, without the per-GW data
    assert minutes_weight_from_history(hist, gwh)(p) == 1.0   # with it


def test_availability_still_gates_the_in_season_share():
    # A flagged player is unavailable no matter how many minutes he has played — chance_factor still applies.
    gwh = {7: [_gw(1, 90), _gw(2, 90)]}
    injured = {"code": 7, "status": "i", "chance": 0}
    assert minutes_weight_from_history({}, gwh)(injured) == 0.0
