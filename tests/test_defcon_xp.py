"""Tests for the DefCon-magnifier analytics (ADR-097, US-318) + its wiring into xp (US-319)."""

from src import config
from src.analytics.defcon_xp import (
    DEFCON_MAG_HI,
    DEFCON_MAG_LO,
    defcon_magnifier,
    defcon_points_per_match,
)
from src.analytics.xp import decision_xp, player_xp


def _p(position="DEF", defcon_per90=10.0):
    return {"position": position, "defcon_per90": defcon_per90}


def _xp_player(pos="DEF", per90=15.0):
    return {"id": 1, "code": 100, "team_id": 1, "points_per_game": 5.0, "status": "a", "ep_next": 4.0,
            "web_name": "D", "position": pos, "team": "ARS", "penalties_order": None, "corners_order": None,
            "freekicks_order": None, "defcon_per90": per90}


def _fixture(h_diff=3):
    return {"event": 1, "team_h": 1, "team_a": 2, "home": "ARS", "away": "BUR",
            "team_h_difficulty": h_diff, "team_a_difficulty": h_diff,
            "home_team_strength": None, "away_team_strength": None}


# ---- defcon_points_per_match (0–2 = 2 · P(clear)) ---------------------------

def test_points_per_match_from_the_margin_over_the_threshold():
    # DEF threshold 10: margin 0 → P 0.5 → 1.0; margin +5 → P 1.0 → 2.0; margin −5 → P 0 → 0.0
    assert defcon_points_per_match(_p("DEF", 10)) == 1.0
    assert defcon_points_per_match(_p("DEF", 15)) == 2.0
    assert defcon_points_per_match(_p("DEF", 5)) == 0.0


def test_points_per_match_uses_the_position_threshold():
    # MID/FWD threshold 12 → per90 12 is the midpoint (1.0), not per90 10
    assert defcon_points_per_match(_p("MID", 12)) == 1.0
    assert defcon_points_per_match(_p("FWD", 12)) == 1.0


def test_points_per_match_zero_for_keeper_or_missing_data():
    assert defcon_points_per_match(_p("GK", 20)) == 0.0          # GK not eligible
    assert defcon_points_per_match(_p("DEF", None)) == 0.0       # no rate → 0
    assert defcon_points_per_match({}) == 0.0                    # empty-safe


# ---- defcon_magnifier (band, neutral, clamp) -------------------------------

def test_magnifier_maps_difficulty_to_the_band():
    assert defcon_magnifier(1) == DEFCON_MAG_LO                  # weak opponent → less DefCon
    assert defcon_magnifier(3) == 1.0                            # mid difficulty → neutral
    assert defcon_magnifier(5) == DEFCON_MAG_HI                  # strong opponent → more DefCon
    assert defcon_magnifier(2) == 0.75 and defcon_magnifier(4) == 1.25


def test_magnifier_is_neutral_on_unknown_and_clamped_out_of_range():
    assert defcon_magnifier(None) == 1.0                        # no fixture → no change
    assert defcon_magnifier(6) == DEFCON_MAG_HI                 # clamped to the band
    assert defcon_magnifier(0) == DEFCON_MAG_LO


# ---- US-319: the delta wired into player_xp (dormant, active, auditable) ----

def test_player_xp_unchanged_when_defcon_weight_zero():
    # weight 0 → no delta → xp identical (the ADR-041/097 invariant)
    r0 = player_xp([_xp_player()], [_fixture(5)])
    r1 = player_xp([_xp_player()], [_fixture(5)], defcon_weight=0.0)
    assert r0[0]["xp"] == r1[0]["xp"] and r0[0]["defcon_xp"] == 0.0


def test_player_xp_delta_lifts_a_hard_fixture_and_trims_an_easy_one():
    # defcon_pm = 2·P(clear) = 2.0 for a per90-15 DEF (margin +5). delta = 2.0·(magnifier−1).
    hard = player_xp([_xp_player(per90=15.0)], [_fixture(5)], defcon_weight=1.0)[0]   # mag 1.5 → +1.0
    easy = player_xp([_xp_player(per90=15.0)], [_fixture(1)], defcon_weight=1.0)[0]   # mag 0.5 → −1.0
    assert hard["defcon_xp"] == 1.0 and easy["defcon_xp"] == -1.0
    assert round(sum(hard["by_gameweek"].values()), 1) == hard["xp"]                  # ADR-032 still holds


def test_player_xp_no_defcon_delta_for_a_keeper():
    r = player_xp([_xp_player(pos="GK", per90=20.0)], [_fixture(5)], defcon_weight=1.0)[0]
    assert r["defcon_xp"] == 0.0


def test_decision_xp_invariant_while_defcon_dormant():
    # config.DEFCON_MAGNIFIER_WEIGHT defaults to 0 → a DefCon-heavy DEF's xp is unchanged
    assert decision_xp([_xp_player()], [_fixture(5)], {}, horizon=1)[0]["defcon_xp"] == 0.0


def test_decision_xp_activates_the_defcon_delta_when_weight_set(monkeypatch):
    monkeypatch.setattr(config, "DEFCON_MAGNIFIER_WEIGHT", 1.0)
    r = decision_xp([_xp_player(per90=15.0)], [_fixture(5)], {}, horizon=1)[0]
    assert r["defcon_xp"] == 1.0                                                      # +1.0 vs a strong opponent


def test_defcon_reason_is_grounded_and_positive_only():
    from src.analytics.explain import _defcon_reason
    assert _defcon_reason(1.2) == "🛡 DefCon fixture edge (+1.2 xP)"                   # active + a lift
    assert _defcon_reason(0.0) is None                                               # dormant → nothing
    assert _defcon_reason(-0.8) is None                                              # a drag isn't a ✓ reason
