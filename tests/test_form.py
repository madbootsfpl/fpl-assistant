"""Tests for the in-season form blend (ADR-060, US-197) — dormant until GW1.

`form_rate` + `blend_form` are pure; the blend folds into `player_xp` / `decision_xp` behind
`config.FORM_WEIGHT`, which defaults to 0 (dormant) → xP is unchanged. Covers the maths, the
`player_xp` hook, and the `decision_xp` invariance (weight 0 ⇒ identical) + activation
(weight > 0 ⇒ the rate shifts toward recent form).
"""

from src import config
from src.analytics.form import blend_form, form_rate
from src.analytics.xp import decision_xp, player_xp


def _gw(rnd, pts, mins):
    return {"round": rnd, "total_points": pts, "minutes": mins}


def _player(code=100, ppg=5.0):
    return {"id": 1, "code": code, "team_id": 1, "points_per_game": ppg,
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
