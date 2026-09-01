"""Tests for the xP historical baseline (ADR-028).

Cover the baseline maths (recency + minutes weighting, reliable fields only, edge
cases) and its use in player_xp: baseline-when-present, fall back to current ppg,
and the rate_source flag. Offline, plain dicts.
"""

import pytest

from src.analytics import baseline_rate, fallback_rate, player_xp
from src.analytics.xp import cold_start_rate


def _season(pts, mins):
    return {"total_points": pts, "minutes": mins}


# ---- baseline_rate ----------------------------------------------------------

def test_single_season_baseline_is_points_per_90():
    # one season: 100 pts over 1800 mins = 20 nineties → 5.0 pp90
    assert baseline_rate([_season(100, 1800)]) == 5.0


def test_empty_history_returns_none():
    assert baseline_rate([]) is None


def test_zero_minute_seasons_are_ignored():
    # a season with 0 minutes carries no rate and must not divide-by-zero
    assert baseline_rate([_season(0, 0), _season(90, 900)]) == 9.0


def test_recent_and_higher_minute_seasons_weigh_more():
    # older weak season (pp90 2.0) vs recent strong season (pp90 6.0), recent has more
    # minutes too → the weighted baseline sits well above the midpoint (4.0).
    b = baseline_rate([_season(40, 1800), _season(120, 1800)])
    assert 4.0 < b <= 6.0


def test_tiny_minute_seasons_are_gated_out():
    # cameo seasons below the 900-min bar invent absurd rates (the smoke-test bug) →
    # they must not produce a baseline; no qualifying season → None (fall back to ppg)
    assert baseline_rate([_season(2, 20)]) is None        # 2 pts in 20 mins → pp90 9.0
    assert baseline_rate([_season(50, 600)]) is None      # 600 mins < 900
    # a real sample still yields a baseline; the cameo alongside it is ignored
    assert baseline_rate([_season(2, 20), _season(120, 1800)]) == 6.0


def test_only_last_k_seasons_are_used():
    # four seasons; with k=3 the oldest (huge pp90) is dropped, so it can't dominate
    hist = [_season(900, 900), _season(20, 1000), _season(20, 1000), _season(20, 1000)]
    b = baseline_rate(hist, k_seasons=3)
    assert b < 3.0            # ~2.0, the oldest 90.0-pp90 season excluded


# ---- fallback_rate: sane low-evidence rate (ADR-040) ------------------------

def test_fallback_shrinks_a_cameo_toward_the_prior():
    # Benitez case: 90 mins, 7 pts → career pp90 7.0, but c = 90/900 = 0.1 →
    # 7.0×0.1 + 2.0×0.9 = 2.5 (a plausible rate, not a 7-pts/GW star).
    assert fallback_rate([_season(7, 90)]) == 2.5


def test_fallback_barely_shrinks_when_minutes_are_ample():
    # ≥900 career minutes → c = 1.0 → the player's own career pp90, no shrink.
    assert fallback_rate([_season(200, 1800)]) == 10.0        # 200×90/1800 = 10.0


def test_fallback_confidence_comes_from_the_biggest_season_not_the_sum():
    # Enes Ünal case: three cameo seasons must NOT compound to confidence. career pp90 = 9.0
    # (90 pts / 900 mins), but the biggest season is only 300 min → c = 300/900 = 1/3 →
    # 9.0×(1/3) + 2.0×(2/3) = 4.33, not the un-shrunk 9.0.
    assert round(fallback_rate([_season(30, 300)] * 3), 2) == 4.33


def test_fallback_is_none_without_any_history():
    assert fallback_rate([]) is None
    assert fallback_rate([_season(0, 0)]) is None             # no minutes → no rate


# ---- player_xp uses the baseline -------------------------------------------

def _player(pid, code, ppg, team_id=1, minutes=900):
    # `minutes` at the 900-min bar → a no-history player's rate is their ppg (ADR-124's full-evidence end).
    return {"id": pid, "code": code, "web_name": f"P{pid}", "team": "ARS",
            "position": "MID", "team_id": team_id, "points_per_game": ppg, "status": "a",
            "ep_next": 1.0, "minutes": minutes}


def _fixture(event=1, home_id=1):
    return {"event": event, "team_h": home_id, "team_a": 2, "home": "ARS", "away": "CHE",
            "team_h_difficulty": 3, "team_a_difficulty": 3}


def test_player_xp_prefers_baseline_over_ppg():
    players = [_player(1, code=999, ppg=2.7)]          # misleading low current ppg
    baselines = {999: 6.5}                             # multi-season says higher
    out = player_xp(players, [_fixture()], baseline_by_code=baselines)
    assert out[0]["rate"] == 6.5 and out[0]["rate_source"] == "hist"
    assert out[0]["xp"] == 6.5                         # neutral difficulty (×1.0)


def test_player_xp_falls_back_to_ppg_without_history():
    # A full season's worth of minutes backs the ppg, so the cold-start blend is all ppg (ADR-124).
    players = [_player(1, code=999, ppg=4.0, minutes=900)]
    out = player_xp(players, [_fixture()], baseline_by_code={})   # no baseline
    assert out[0]["rate"] == 4.0 and out[0]["rate_source"] == "cold_start"


def test_player_xp_works_when_row_has_no_code_key():
    # lightweight rows without a `code` key must not raise (the _get guard)
    p = {"id": 1, "web_name": "P1", "team": "ARS", "position": "MID", "team_id": 1,
         "points_per_game": 3.0, "status": "a", "ep_next": 1.0, "minutes": 900}
    out = player_xp([p], [_fixture()], baseline_by_code={999: 9.9})
    assert out[0]["rate_source"] == "cold_start" and out[0]["rate"] == 3.0


def test_player_xp_uses_the_shrunk_fallback_when_no_baseline():
    # ADR-040: a cameo (ppg 7.0 from one game) uses the shrunk fallback, not raw ppg.
    players = [_player(1, code=999, ppg=7.0)]
    out = player_xp(players, [_fixture()], baseline_by_code={},
                    history_by_code={999: [_season(7, 90)]})
    assert out[0]["rate"] == 2.5 and out[0]["rate_source"] == "fallback"


def test_player_xp_baseline_still_wins_over_the_fallback():
    # a trusted ≥900-min baseline is used even when history is also supplied.
    players = [_player(1, code=999, ppg=7.0)]
    out = player_xp(players, [_fixture()], baseline_by_code={999: 6.5},
                    history_by_code={999: [_season(7, 90)]})
    assert out[0]["rate"] == 6.5 and out[0]["rate_source"] == "hist"


# ---- the cold-start blend (ADR-124) ----------------------------------------
#
# The safety case for ADR-124 is that it *interpolates between two behaviours that already existed*: at zero
# evidence it is ADR-104's ep_next floor, at full evidence it is the old raw-ppg tier. Those two endpoints are
# what the following tests pin — if either drifts, the change stopped being an interpolation.

def test_cold_start_at_zero_evidence_is_exactly_ep_next():
    # ADR-104 unchanged. FPL derives points-per-game from games played, so 0 minutes means 0 ppg — the old
    # `ep_next` tier *was* this case, which is why the blend can subsume it rather than replace it.
    assert cold_start_rate(points_per_game=0, ep_next=2.5, minutes=0) == 2.5


def test_cold_start_at_full_evidence_is_exactly_the_weighted_ppg():
    # The old `current` tier unchanged: ~10 full games is the bar `baseline_rate` already trusts.
    assert cold_start_rate(points_per_game=6.0, ep_next=2.0, minutes=900, weight=0.5) == 3.0
    assert cold_start_rate(points_per_game=6.0, ep_next=2.0, minutes=5000) == 6.0   # clamped past the bar


def test_cold_start_damps_a_one_game_haul():
    # The bug this ADR exists for: one 14-point game used to project 14 a week and top the whole board.
    assert round(cold_start_rate(points_per_game=14.0, ep_next=2.0, minutes=75), 2) == 3.0


def test_cold_start_converges_on_the_truth_as_minutes_accrue():
    # A genuine 6.0-ppg signing is under-rated at first (honest — there's one game of evidence) and reaches
    # their real rate by the 900-minute bar. Monotonic the whole way, no cliff.
    rates = [cold_start_rate(6.0, 2.0, games * 90) for games in (1, 3, 5, 10)]
    assert rates == sorted(rates)
    assert round(rates[0], 2) == 2.40 and rates[-1] == 6.0


def test_cold_start_keeps_ep_next_as_the_signal_that_separates_equal_scorers():
    # Two players with the same one-game ppg but different ep_next must not collapse to the same rate —
    # shrinking toward a flat prior instead of ep_next would lose exactly this (the rejected alternative).
    high = cold_start_rate(6.0, 2.2, 90)
    low = cold_start_rate(6.0, 1.0, 90)
    assert high > low


def test_cold_start_weight_applies_to_the_ppg_term_only():
    # ep_next already prices minutes (ADR-104), so the xMins weight must not discount it a second time.
    # At zero evidence the rate is ep_next whatever the weight is.
    assert cold_start_rate(10.0, 3.0, 0, weight=0.5) == 3.0
    # Half-evidence: only the ppg half is discounted → 0.5×10×0.5 + 3.0×0.5 = 4.0
    assert cold_start_rate(10.0, 3.0, 450, weight=0.5) == 4.0


def test_cold_start_is_empty_safe():
    assert cold_start_rate(None, None, None) == 0.0
    assert cold_start_rate(None, 2.0, None) == 2.0


def test_player_xp_reports_the_weight_that_actually_landed():
    # `minutes_weight` is surfaced (it drives the expected-minutes display), so it has to report the effective
    # discount, not the outer multiplier — which the blend deliberately leaves at 1.0.
    half = {"minutes_weight": lambda p: 0.5}
    at_zero = player_xp([_player(1, code=999, ppg=0.0, minutes=0)], [_fixture()],
                        baseline_by_code={}, **half)
    at_full = player_xp([_player(1, code=999, ppg=4.0, minutes=900)], [_fixture()],
                        baseline_by_code={}, **half)
    assert at_zero[0]["minutes_weight"] == 1.0     # nothing was discounted (ADR-104's end)
    assert at_full[0]["minutes_weight"] == 0.5     # the ppg term took the full weight


# ---- ADR-172: the blend needs two independent inputs ------------------------
#
# ADR-124's blend assumed `ppg` and `ep_next` say different things. Upstream they stopped doing so — FPL
# publishes `ep_next == points_per_game` for 513 of 626 players — and blending a number with itself returns
# it, so the shrink cancelled at *every* value of c and this tier handed back raw ppg. That is the exact
# failure ADR-124 exists to prevent, arriving through the input rather than the formula.
#
# These pin the CANCELLATION, not the symptom. A test that merely asserted "Sangaré is lower now" would pass
# on any change that lowers him, including a wrong one.

def test_a_degenerate_ep_next_does_not_cancel_the_shrink():
    """The bug itself: identical inputs must not return the input.

    ppg 9.0 with 165 minutes is c = 0.18 — 82% of the rate is supposed to come from the conservative side.
    Before ADR-172 this returned exactly 9.0, at any c, because 9·c + 9·(1−c) = 9.
    """
    assert cold_start_rate(points_per_game=9.0, ep_next=9.0, minutes=165) != 9.0
    # and it lands where the existing replacement prior puts it: 9·0.183 + 2·0.817
    assert cold_start_rate(points_per_game=9.0, ep_next=9.0, minutes=165) == pytest.approx(3.28, abs=0.01)


def test_the_cancellation_is_broken_at_every_level_of_evidence():
    """Not just at one c. The old behaviour was flat — the fix must slope."""
    rates = [cold_start_rate(points_per_game=9.0, ep_next=9.0, minutes=m) for m in (0, 90, 300, 600)]
    assert rates == sorted(rates), "more evidence must move the rate toward the player's own ppg"
    assert len(set(rates)) == len(rates), "a flat line across c means the shrink is cancelling again"


def test_an_informative_ep_next_is_still_used():
    # The repair must not fire when FPL is being useful: unequal inputs take the ADR-124 path, unchanged.
    assert cold_start_rate(points_per_game=9.0, ep_next=3.0, minutes=165) == pytest.approx(4.10, abs=0.01)


def test_zero_evidence_still_yields_ep_next_even_when_it_equals_ppg():
    """The `ppg > 0` guard is load-bearing, and this is why.

    Preseason `ppg` is 0 and `ep_next` is often 0 too, so a bare equality check would fire on the
    zero-evidence case and hand a player who has never kicked a ball the replacement prior instead of FPL's
    own number — re-breaking ADR-104, which ADR-172 is restoring.
    """
    assert cold_start_rate(points_per_game=0, ep_next=0, minutes=0) == 0.0
    assert cold_start_rate(points_per_game=0, ep_next=2.5, minutes=0) == 2.5


def test_full_evidence_is_the_players_own_ppg_either_way():
    # At c = 1 the conservative term has zero weight, so which side it came from cannot matter.
    assert cold_start_rate(points_per_game=6.0, ep_next=6.0, minutes=900) == 6.0
    assert cold_start_rate(points_per_game=6.0, ep_next=2.0, minutes=900) == 6.0


def test_two_games_do_not_outrank_a_proven_player():
    """The end-to-end shape of the bug, as the owner met it.

    A cold-start player with a huge two-game ppg and a degenerate `ep_next` was out-projecting established
    players — 8 of the top 20, and the top 3 outright, with Haaland 4th.
    """
    hot = _player(1, code=999, ppg=9.0, minutes=165)        # two games, nothing else known
    hot["ep_next"] = 9.0                                    # FPL's degenerate value
    proven = _player(2, code=888, ppg=6.0, minutes=180)
    out = {r["id"]: r for r in player_xp([hot, proven], [_fixture()],
                                         baseline_by_code={888: 5.7})}   # a real multi-season baseline
    assert out[1]["rate_source"] == "cold_start" and out[2]["rate_source"] == "hist"
    assert out[1]["xp"] < out[2]["xp"], "two games must not out-project a proven baseline"
