"""GW1-readiness smoke — the GW1-gated features degrade cleanly preseason (Sprint 138, US-341).

A regression guard so a refactor can't quietly break the season-start switch-flip: the price predictor, the
momentum/trending board, and the manager-import all handle preseason/empty input without crashing (they show 0 /
"stable" / a note now, and light up on live data at GW1). The owner verifies them on live data at GW1
(docs/GW1_RUNBOOK.md).
"""

from src.analytics import price
from src.analytics.crowd import trending
from src.manager import picks_to_squad


def test_price_predictor_is_dormant_preseason():
    # No transfer/ownership data yet → None-safe, "stable", no flag. Thresholds calibrate + fire at GW1.
    assert price.price_pressure({}) is None
    assert price.price_prediction({}) == "stable"             # → no 🔺/🔻 flag preseason
    assert price.price_flag({}) == ""


def test_trending_board_is_empty_safe():
    assert trending([], by="owned", limit=5) == []            # no players → no board (no crash)


def test_manager_import_degrades_on_an_empty_payload():
    # picks unlock only after the GW1 deadline; a payload with no picks must degrade to None, never raise.
    assert picks_to_squad({"picks": []}, [], name="Test") is None
