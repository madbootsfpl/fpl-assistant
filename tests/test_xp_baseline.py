"""Tests for the xP historical baseline (ADR-028).

Cover the baseline maths (recency + minutes weighting, reliable fields only, edge
cases) and its use in player_xp: baseline-when-present, fall back to current ppg,
and the rate_source flag. Offline, plain dicts.
"""

from src.analytics import baseline_rate, fallback_rate, player_xp


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

def _player(pid, code, ppg, team_id=1):
    return {"id": pid, "code": code, "web_name": f"P{pid}", "team": "ARS",
            "position": "MID", "team_id": team_id, "points_per_game": ppg, "status": "a",
            "ep_next": 1.0}


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
    players = [_player(1, code=999, ppg=4.0)]
    out = player_xp(players, [_fixture()], baseline_by_code={})   # no baseline
    assert out[0]["rate"] == 4.0 and out[0]["rate_source"] == "current"


def test_player_xp_works_when_row_has_no_code_key():
    # lightweight rows without a `code` key must not raise (the _get guard)
    p = {"id": 1, "web_name": "P1", "team": "ARS", "position": "MID", "team_id": 1,
         "points_per_game": 3.0, "status": "a", "ep_next": 1.0}
    out = player_xp([p], [_fixture()], baseline_by_code={999: 9.9})
    assert out[0]["rate_source"] == "current" and out[0]["rate"] == 3.0


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
