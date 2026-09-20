"""GW1-readiness smoke — the GW1-gated features degrade cleanly preseason (Sprint 138, US-341).

A regression guard so a refactor can't quietly break the season-start switch-flip: the price predictor, the
momentum/trending board, and the manager-import all handle preseason/empty input without crashing (they show 0 /
"stable" / a note now, and light up on live data at GW1). The owner verifies them on live data at GW1
(docs/GW1_RUNBOOK.md).
"""

from src.analytics import price
from src.analytics.crowd import trending
from src.manager import picks_to_squad


def test_the_price_predictor_is_safe_on_an_empty_row():
    """⚠️ **Renamed, because the old name recorded a bug as a requirement.**

    It was `test_price_predictor_is_dormant_preseason`, and its comment promised *"thresholds calibrate +
    fire at GW1"*. The thresholds were never calibrated: they stayed at the ±20,000 placeholders, which is
    3.5× anything a real board produces, so the predictor returned `stable` for all 662 players for an entire
    season (ADR-215). **Dormancy stopped being the preseason state and became the permanent one**, and the
    name of this test would have read as confirmation to anyone who checked.

    ⭐ What it actually asserts — and all it ever asserted — is that an empty row does not raise. That is
    worth keeping; the claim about seasons is not.
    """
    cuts = price.PriceCuts(rise=1_000.0, fall=-1_000.0)
    assert price.price_pressure({}) is None
    assert price.price_prediction({}, cuts) == "stable"       # no data → no opinion, no crash
    assert price.price_flag({}, cuts) == ""


def test_trending_board_is_empty_safe():
    assert trending([], by="owned", limit=5) == []            # no players → no board (no crash)


def test_manager_import_degrades_on_an_empty_payload():
    # picks unlock only after the GW1 deadline; a payload with no picks must degrade to None, never raise.
    assert picks_to_squad({"picks": []}, [], name="Test") is None
