"""Tests for the pure DefCon-magnifier analytics (ADR-097, US-318)."""

from src.analytics.defcon_xp import (
    DEFCON_MAG_HI,
    DEFCON_MAG_LO,
    defcon_magnifier,
    defcon_points_per_match,
)


def _p(position="DEF", defcon_per90=10.0):
    return {"position": position, "defcon_per90": defcon_per90}


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
