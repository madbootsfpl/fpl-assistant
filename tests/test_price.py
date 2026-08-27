"""Tests for the Price Change Predictor (Sprint 112, ADR-092).

A directional, ownership-normalised transfer-pressure **lens** — never `decision_xp`. Pure, empty-safe, and
0 on flat preseason data (net transfers = 0 → 'stable').
"""

from src.analytics import decision_xp, price_flag, price_prediction, price_pressure
from src.analytics.price import (
    PRICE_DOWN,
    PRICE_FALL_PRESSURE,
    PRICE_RISE_PRESSURE,
    PRICE_UP,
    price_move,
    price_series,
)
from src.storage import Storage


def _p(net_in=0, net_out=0, own=10.0):
    return {"transfers_in_event": net_in, "transfers_out_event": net_out, "selected_by": own}


def test_price_pressure_is_net_transfers_per_ownership_point():
    assert price_pressure(_p(net_in=500_000, net_out=100_000, own=10.0)) == 40_000.0   # +400k / 10%
    assert price_pressure(_p(net_in=0, net_out=350_000, own=10.0)) == -35_000.0        # −350k / 10% (signed)
    assert price_pressure(_p(net_in=0, net_out=0, own=50.0)) == 0.0                     # flat → 0 (dormant)


def test_price_pressure_is_none_safe():
    assert price_pressure({}) is None                                  # no fields
    assert price_pressure(_p(net_in=100_000, own=0)) is None           # no ownership → can't normalise
    assert price_pressure({"selected_by": 10.0}) is None               # no transfer fields (net None)


def test_price_prediction_thresholds():
    rise_own, fall_own = 10.0, 10.0
    just_rise = _p(net_in=int(PRICE_RISE_PRESSURE * rise_own) + rise_own, own=rise_own)   # pressure ≥ threshold
    just_fall = _p(net_out=int(PRICE_FALL_PRESSURE * fall_own) + fall_own, own=fall_own)
    assert price_prediction(just_rise) == "rise"
    assert price_prediction(just_fall) == "fall"
    assert price_prediction(_p(net_in=100, own=10.0)) == "stable"       # tiny pressure → stable
    assert price_prediction({}) == "stable"                            # empty-safe → stable


def test_price_flag_maps_direction_to_a_distinct_marker():
    # ADR-140: plain text triangles, NOT 🔺/🔻. U+1F53A is literally "red triangle pointed up", so the old
    # pair was red-up and red-down — direction carried twice while colour carried nothing. Plain glyphs
    # inherit the surrounding colour, which is what lets each surface paint them green-up / red-down.
    assert price_flag(_p(net_in=int(PRICE_RISE_PRESSURE * 10) + 10, own=10.0)) == PRICE_UP == "▲"
    assert price_flag(_p(net_out=int(PRICE_FALL_PRESSURE * 10) + 10, own=10.0)) == PRICE_DOWN == "▼"
    assert PRICE_UP not in "🔺🔻" and PRICE_DOWN not in "🔺🔻", \
        "an emoji brings its own colour, and both of the obvious ones are red — that is the bug"
    assert price_flag(_p(net_in=0, net_out=0, own=10.0)) == ""          # stable → no flag
    # distinct from the retrospective crowd 💰/💸 (this is forward-looking)
    assert price_flag(_p(net_in=999_999_999, own=10.0)) not in ("💰↑", "💸↓")


def test_price_is_a_lens_and_never_changes_decision_xp():
    # ADR-092 invariant: the predictor must not feed the grounded xP.
    store = Storage()
    try:
        players = [dict(p) for p in store.get_players()]
        upcoming = store.get_upcoming_fixtures()
        history = store.get_history_by_code()
    finally:
        store.close()
    if not players:
        return
    base = {r["id"]: r["xp"] for r in decision_xp(players, upcoming, history)}
    for p in players:                                                  # force strong price pressure both ways
        p["transfers_in_event"], p["transfers_out_event"] = 5_000_000, 0
    assert any(price_prediction(p) == "rise" for p in players)         # the lens now fires…
    after = {r["id"]: r["xp"] for r in decision_xp(players, upcoming, history)}
    assert base == after                                              # …but xP is identical


def test_the_arrows_are_plain_text_so_a_surface_can_colour_them():
    """ADR-140 — the whole reason the glyphs changed.

    An emoji brings its own colour, and both of the obvious triangles are red (U+1F53A is *"red triangle
    pointed up"*), so the old pair spent the fastest channel a reader has on nothing. Plain text triangles
    inherit the surrounding colour, which is what lets the web tables paint them green-up / red-down.

    If someone swaps these back to emoji, the colouring silently stops working — the Styler matches on the
    exact glyph — so this asserts the property rather than the characters.
    """
    assert PRICE_UP.isprintable() and PRICE_DOWN.isprintable()
    assert all(ord(c) < 0x1F000 for c in PRICE_UP + PRICE_DOWN), \
        "an emoji-plane glyph carries its own colour and cannot be recoloured by CSS"
    assert PRICE_UP != PRICE_DOWN


def test_both_legends_say_the_same_thing_in_two_dialects():
    """One rule written twice always drifts, so they are pinned to agree. The Streamlit legend carries colour
    markdown; the plain one is for anywhere that renders literally."""
    from src.analytics.price import PRICE_LEGEND, PRICE_LEGEND_PLAIN

    assert f":green[{PRICE_UP}]" in PRICE_LEGEND and f":red[{PRICE_DOWN}]" in PRICE_LEGEND
    assert ":green[" not in PRICE_LEGEND_PLAIN and ":red[" not in PRICE_LEGEND_PLAIN
    strip = PRICE_LEGEND.replace(f":green[{PRICE_UP}]", PRICE_UP).replace(f":red[{PRICE_DOWN}]", PRICE_DOWN)
    assert strip == PRICE_LEGEND_PLAIN, "the two legends have drifted apart"


# ---- The price journey (ADR-160) ------------------------------------------------------------------
# Retrospective, unlike everything above it in this file: `price_flag` predicts where a price is going,
# these say where it has been.

def _hist(pairs):
    """`{code: [rows]}` for `[(round, value_in_tenths), …]`. A scoreline marks the gameweek as played."""
    return {9: [{"round": r, "value": v, "minutes": 90, "total_points": 2,
                 "team_h_score": 1, "team_a_score": 0, "was_home": True} for r, v in pairs]}


def _pl(price, change=0):
    return {"id": 1, "code": 9, "web_name": "P", "price": price, "cost_change_start": change}


def test_the_move_since_the_season_started_is_read_straight_off_fpl():
    assert price_move(_pl(4.6, 1)) == 0.1
    assert price_move(_pl(7.9, -3)) == -0.3
    assert price_move(_pl(15.5, 0)) == 0.0
    assert price_move({"price": 5.0}) is None


def test_todays_price_is_the_last_point_so_the_chart_cannot_contradict_the_page():
    """`value` is only written when a gameweek is played, but prices move nightly. Watkins really does read
    £8.0m at GW1 and £7.9m everywhere else in the app; a chart ending on the stale number would be a chart
    disagreeing with the number printed beside it."""
    assert price_series(_hist([(1, 80)]), 9, _pl(7.9, -1)) == [("GW1", 8.0), ("now", 7.9)]


def test_a_price_that_has_not_moved_yields_one_point_not_a_flat_pair():
    """Appending an identical 'now' would draw a dead-level line implying two observations of the same thing."""
    assert price_series(_hist([(1, 45)]), 9, _pl(4.5, 0)) == [("GW1", 4.5)]


def test_a_double_gameweek_does_not_add_a_price_to_itself():
    """ADR-129's rule, and `value` is the column it was written for — summing two fixtures in one round would
    read as a £4.5m rise."""
    rows = _hist([(1, 45), (1, 45)])
    assert price_series(rows, 9, _pl(4.5, 0)) == [("GW1", 4.5)]


def test_a_player_with_no_gameweek_rows_still_reports_his_price():
    assert price_series({}, 9, _pl(6.1, 0)) == [("now", 6.1)]
    assert price_series(None, 9, {"web_name": "P"}) == []
