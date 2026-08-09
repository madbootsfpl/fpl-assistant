"""Tests for the gated set-piece xP term (ADR-096, US-313).

`set_piece_bonus` is pure; the term folds into `player_xp`/`decision_xp` behind `config.SET_PIECE_WEIGHT`
(default 0 → dormant, so xP is unchanged) and applies **only to the fallback/current rate tiers** — never
the trusted historical baseline (which already prices an established taker's pens → double-counting).
"""

from src import config
from src.analytics.setpieces import PENALTY_BONUS, SET_PLAY_BONUS, set_piece_bonus
from src.analytics.xp import decision_xp, player_xp


def _player(code=100, ppg=5.0, **extra):
    p = {"id": 1, "code": code, "team_id": 1, "points_per_game": ppg,
         "status": "a", "ep_next": 4.0, "web_name": "P", "position": "MID", "team": "ARS",
         "penalties_order": None, "corners_order": None, "freekicks_order": None}
    p.update(extra)
    return p


def _fixture(event=1, h_diff=3):
    # neutral difficulty (3) → ×1.0, so a one-GW horizon gives xp == rate (easy to reason about)
    return {"event": event, "team_h": 1, "team_a": 2, "home": "ARS", "away": "BUR",
            "team_h_difficulty": h_diff, "team_a_difficulty": h_diff,
            "home_team_strength": None, "away_team_strength": None}


# ---- set_piece_bonus --------------------------------------------------------

def test_set_piece_bonus_scores_only_the_first_choice_duties():
    assert set_piece_bonus({"penalties_order": 1}) == PENALTY_BONUS               # pens dominate
    assert set_piece_bonus({"penalties_order": 1, "corners_order": 1}) == PENALTY_BONUS + SET_PLAY_BONUS
    assert set_piece_bonus({"penalties_order": 1, "corners_order": 1,
                            "freekicks_order": 1}) == PENALTY_BONUS + 2 * SET_PLAY_BONUS
    assert set_piece_bonus({"penalties_order": 2}) == 0.0                         # only the #1 taker
    assert set_piece_bonus({}) == 0.0                                            # empty-safe


# ---- player_xp hook: dormant vs active, tier-restricted ---------------------

def test_player_xp_unchanged_when_set_piece_weight_zero():
    pen = _player(penalties_order=1)
    assert player_xp([pen], [_fixture()])[0]["xp"] == 5.0                         # no term passed
    assert player_xp([pen], [_fixture()], set_piece_weight=0.0)[0]["xp"] == 5.0   # dormant


def test_player_xp_boosts_a_pen_taker_on_the_current_tier():
    # no baseline → current tier; neutral fixture → xp == rate = 5 + 1.0·PENALTY_BONUS
    r = player_xp([_player(penalties_order=1)], [_fixture()], set_piece_weight=1.0)
    assert r[0]["xp"] == round(5.0 + PENALTY_BONUS, 1)


def test_player_xp_does_not_boost_a_hist_tier_taker():
    # WITH a trusted baseline the pens are already priced in → NO boost (no double-counting)
    pen = _player(penalties_order=1)
    r = player_xp([pen], [_fixture()], baseline_by_code={100: 5.0}, set_piece_weight=1.0)
    assert r[0]["xp"] == 5.0


def test_player_xp_does_not_boost_a_non_taker():
    r = player_xp([_player()], [_fixture()], set_piece_weight=1.0)
    assert r[0]["xp"] == 5.0


# ---- decision_xp: invariance (dormant) + activation -------------------------

def test_decision_xp_invariant_while_set_piece_dormant():
    # config.SET_PIECE_WEIGHT defaults to 0 → a pen taker's xP is unchanged
    pen = _player(penalties_order=1)
    assert decision_xp([pen], [_fixture()], {}, horizon=1)[0]["xp"] == 5.0


def test_decision_xp_activates_set_piece_when_weight_set(monkeypatch):
    monkeypatch.setattr(config, "SET_PIECE_WEIGHT", 1.0)
    # current tier (no history) pen taker → 5 + 1.0·PENALTY_BONUS
    r = decision_xp([_player(penalties_order=1)], [_fixture()], {}, horizon=1)
    assert r[0]["xp"] == round(5.0 + PENALTY_BONUS, 1)


# ---- US-314: the grounded contribution + the weight-aware explanation --------

def test_player_xp_records_the_set_piece_contribution():
    pen = _player(penalties_order=1)
    assert player_xp([pen], [_fixture()])[0]["set_piece_xp"] == 0.0               # dormant → 0
    active = player_xp([pen], [_fixture()], set_piece_weight=1.0)[0]
    assert active["set_piece_xp"] == round(PENALTY_BONUS, 1)                      # the term's share of xp
    hist = player_xp([pen], [_fixture()], baseline_by_code={100: 5.0}, set_piece_weight=1.0)[0]
    assert hist["set_piece_xp"] == 0.0                                           # hist tier → not applied


def test_penalty_reason_is_weight_aware_and_grounded():
    from src.analytics.explain import _penalty_reason
    assert _penalty_reason(0.0) == "Penalty taker"                               # dormant → the lens phrasing
    assert _penalty_reason(0.3) == "Penalty taker (+0.3 xP set-piece edge)"      # active → the grounded edge


def test_explain_captain_shows_the_set_piece_edge_when_active():
    from src.analytics.explain import explain_captain
    picks = [{"id": 1, "xp": 6.3, "penalty_taker": True, "set_piece_xp": 0.3,
              "minutes_weight": 1.0, "venue": "H", "difficulty": 3}]
    exp = explain_captain(picks, {1: {"penalties_order": 1, "form": None}})
    assert any("set-piece edge" in r for r in exp.reasons)                        # grounded reason present
    # dormant (no contribution) → the plain lens reason, unchanged
    picks[0]["set_piece_xp"] = 0.0
    exp0 = explain_captain(picks, {1: {"penalties_order": 1, "form": None}})
    assert "Penalty taker" in exp0.reasons and not any("edge" in r for r in exp0.reasons)
