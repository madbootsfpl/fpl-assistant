"""Tests for the Price Change Predictor (Sprint 112, ADR-092).

A directional, ownership-normalised transfer-pressure **lens** — never `decision_xp`. Pure, empty-safe, and
0 on flat preseason data (net transfers = 0 → 'stable').
"""

from src.analytics import decision_xp, price_flag, price_prediction, price_pressure
from src.analytics.price import PRICE_FALL_PRESSURE, PRICE_RISE_PRESSURE
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
    assert price_flag(_p(net_in=int(PRICE_RISE_PRESSURE * 10) + 10, own=10.0)) == "🔺"
    assert price_flag(_p(net_out=int(PRICE_FALL_PRESSURE * 10) + 10, own=10.0)) == "🔻"
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
