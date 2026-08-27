"""Tests for the in-season form blend (ADR-060, US-197) — dormant until GW1.

`form_rate` + `blend_form` are pure; the blend folds into `player_xp` / `decision_xp` behind
`config.FORM_WEIGHT`, which defaults to 0 (dormant) → xP is unchanged. Covers the maths, the
`player_xp` hook, and the `decision_xp` invariance (weight 0 ⇒ identical) + activation
(weight > 0 ⇒ the rate shifts toward recent form).
"""

from src import config
from src.analytics.form import blend_form, form_rate, form_windows
from src.analytics.xp import decision_xp, player_xp


def _gw(rnd, pts, mins):
    return {"round": rnd, "total_points": pts, "minutes": mins}


def _player(code=100, ppg=5.0, minutes=900):
    # `minutes` at the 900-min evidence bar → a no-history player's rate is their ppg (ADR-124's full-evidence end).
    return {"id": 1, "code": code, "team_id": 1, "points_per_game": ppg, "minutes": minutes,
            "status": "a", "ep_next": 4.0, "web_name": "P", "position": "MID", "team": "ARS"}


def _fixture(event=1, h_diff=3):
    # neutral difficulty (3) → ×1.0, so a one-GW horizon gives xp == rate (easy to reason about)
    return {"event": event, "team_h": 1, "team_a": 2, "home": "ARS", "away": "BUR",
            "team_h_difficulty": h_diff, "team_a_difficulty": h_diff,
            "home_team_strength": None, "away_team_strength": None}


# ---- form_rate --------------------------------------------------------------

def test_form_rate_is_recency_and_minutes_weighted():
    # pp90 2 then 8; recency weights the newer GW more → (90·2 + 180·8) / 270 = 6.0
    pp90, conf = form_rate([_gw(1, 2, 90), _gw(2, 8, 90)], min_minutes=180)
    assert round(pp90, 3) == 6.0
    assert conf == 1.0                        # 180 window minutes / 180 = full confidence


def test_form_rate_skips_zero_minute_gameweeks():
    pp90, conf = form_rate([_gw(1, 0, 0), _gw(2, 6, 90)], min_minutes=90)
    assert round(pp90, 2) == 6.0              # only the played GW counts
    assert conf == 1.0


def test_form_rate_is_none_without_minutes():
    assert form_rate([]) == (None, 0.0)
    assert form_rate([_gw(1, 0, 0)]) == (None, 0.0)


def test_form_rate_window_limits_to_last_n():
    # k=2 → only the last two GWs; the ancient 100-point GW is ignored
    pp90, _ = form_rate([_gw(1, 100, 90), _gw(2, 4, 90), _gw(3, 4, 90)], k_gameweeks=2, min_minutes=180)
    assert round(pp90, 2) == 4.0


def test_form_rate_confidence_caps_a_cameo():
    # a single 10-minute cameo: high pp90 but low confidence
    pp90, conf = form_rate([_gw(1, 3, 10)], min_minutes=270)
    assert pp90 == 27.0
    assert round(conf, 4) == round(10 / 270, 4)


# ---- blend_form -------------------------------------------------------------

def test_blend_form_mixes_base_and_form():
    assert blend_form(4.0, 8.0, 1.0, 0.5) == 6.0        # w = 0.5·1 → 0.5·4 + 0.5·8


def test_blend_form_is_inert_when_dormant_or_no_form():
    assert blend_form(4.0, 8.0, 1.0, 0.0) == 4.0        # weight 0 → base unchanged
    assert blend_form(4.0, None, 0.0, 0.5) == 4.0       # no form → base unchanged


# ---- player_xp hook ---------------------------------------------------------

def test_player_xp_blends_form_when_weight_positive():
    # neutral fixture → xp == rate. base ppg 5, form 9, w = 0.5·1 → rate 7.0
    r = player_xp([_player(ppg=5.0)], [_fixture()],
                  form_by_code={100: (9.0, 1.0)}, form_weight=0.5)
    assert r[0]["xp"] == 7.0


def test_player_xp_unchanged_when_form_weight_zero():
    r0 = player_xp([_player(ppg=5.0)], [_fixture()])
    r1 = player_xp([_player(ppg=5.0)], [_fixture()],
                   form_by_code={100: (9.0, 1.0)}, form_weight=0.0)
    assert r0[0]["xp"] == r1[0]["xp"] == 5.0            # dormant ⇒ identical


# ---- decision_xp: invariance (dormant) + activation (GW1) --------------------

def test_decision_xp_invariant_while_dormant():
    # config.FORM_WEIGHT defaults to 0 → passing per-GW history changes nothing
    players, fixtures = [_player(ppg=5.0)], [_fixture()]
    without = decision_xp(players, fixtures, {}, horizon=1)
    with_gw = decision_xp(players, fixtures, {}, horizon=1,
                          gw_history_by_code={100: [_gw(1, 9, 90), _gw(2, 9, 90), _gw(3, 9, 90)]})
    assert without[0]["xp"] == with_gw[0]["xp"] == 5.0


def test_decision_xp_activates_form_when_weight_set(monkeypatch):
    monkeypatch.setattr(config, "FORM_WEIGHT", 0.5)
    # 3 full GWs at pp90 9 → window 270 min → confidence 1.0; base ppg 5 (no history → current).
    # w = 0.5·1 → rate = 0.5·5 + 0.5·9 = 7.0
    ranked = decision_xp([_player(ppg=5.0)], [_fixture()], {}, horizon=1,
                         gw_history_by_code={100: [_gw(1, 9, 90), _gw(2, 9, 90), _gw(3, 9, 90)]})
    assert ranked[0]["xp"] == 7.0


# ---- Two windows, and the refusal to invent a direction (ADR-159) ----------------------------------
# One number says how a player is scoring; two say which way he is going. The hard part is not the second
# rate — it is knowing when the two windows are the *same rows* and there is no direction to report.

def _wk(minutes, points):
    return {"minutes": minutes, "total_points": points}


def test_a_rising_player_reads_sharper_over_the_short_window():
    rows = [_wk(90, 2), _wk(90, 2), _wk(90, 3), _wk(90, 9), _wk(90, 8), _wk(90, 10)]
    w = form_windows(rows)
    assert w["direction"] == "up" and w["delta"] > 0
    assert w["short"]["pp90"] > w["long"]["pp90"]
    assert (w["short"]["gws"], w["long"]["gws"]) == (3, 6)


def test_a_fading_player_reads_cooler():
    rows = [_wk(90, 10), _wk(90, 8), _wk(90, 9), _wk(90, 3), _wk(90, 2), _wk(90, 2)]
    w = form_windows(rows)
    assert w["direction"] == "down" and w["delta"] < 0


def test_one_gameweek_refuses_a_direction_rather_than_reporting_a_flat_one():
    """Today's real state: one gameweek played, so a 3-GW and a 6-GW window are the same single row. Their
    difference is exactly 0.0 — which drawn as "level" would read as *steady form* rather than *no evidence*.
    """
    w = form_windows([_wk(90, 6)])
    assert w["short"]["pp90"] == w["long"]["pp90"] == 6.0
    assert w["direction"] is None and w["delta"] is None


def test_windows_covering_the_same_matches_refuse_a_direction_even_late_in_a_season():
    """Six gameweeks on the books but only the last three played — an injury return. The long window holds no
    match the short one doesn't, so there is still nothing to compare."""
    rows = [_wk(0, 0), _wk(0, 0), _wk(0, 0), _wk(90, 5), _wk(90, 6), _wk(90, 7)]
    w = form_windows(rows)
    assert (w["short"]["gws"], w["long"]["gws"]) == (3, 3)
    assert w["direction"] is None


def test_a_player_with_no_minutes_has_no_windows_at_all():
    w = form_windows([_wk(0, 0), _wk(0, 0)])
    assert w["short"]["pp90"] is None and w["long"]["pp90"] is None and w["direction"] is None
    assert form_windows([])["direction"] is None


def test_both_windows_use_the_same_rate_so_they_stay_comparable():
    """They are one function called twice on purpose. A second rate written alongside `form_rate` would drift
    from it — different recency weighting on the two halves of a comparison is a subtracted apples and pears."""
    rows = [_wk(90, 4), _wk(60, 8), _wk(90, 2), _wk(30, 9), _wk(90, 6), _wk(90, 1)]
    w = form_windows(rows, short=6, long=6)
    assert w["short"] == w["long"]                    # identical windows → identical numbers, exactly
    assert w["direction"] is None                     # …and no direction, since neither covers more than the other


def test_the_window_sizes_are_arguments_not_hard_coded():
    rows = [_wk(90, 1)] * 4 + [_wk(90, 9)] * 4
    assert form_windows(rows, short=4, long=8)["direction"] == "up"
