"""Tests for the explainability framework (Sprint 104, ADR-089).

`explain_captain` / `captain_confidence` are pure: given a pick + its signals they produce grounded ✓ reasons,
⚠ risks, and a transparent confidence — never an LLM guess. The confidence must be deterministic + bounded and
must temper coin-flips / doubts.
"""

from src.analytics import (
    captain_confidence,
    confidence_band,
    explain_captain,
    explain_squad,
    explain_transfer,
    squad_confidence,
    transfer_confidence,
)


def test_confidence_band_cutoffs():
    assert confidence_band(90) == "High" and confidence_band(75) == "High"
    assert confidence_band(60) == "Medium" and confidence_band(55) == "Medium"
    assert confidence_band(40) == "Low"


def test_captain_confidence_is_bounded_and_reflects_the_signals():
    # a nailed-on runaway pick at home → High
    hi = captain_confidence(0.95, 1.2, penalty=True, venue="H", difficulty=2, doubtful=False, chance=None)
    assert hi >= 75
    # the same player away with a coin-flip lead → clearly lower
    lo = captain_confidence(0.95, 0.1, penalty=True, venue="A", difficulty=3, doubtful=False, chance=None)
    assert lo < hi
    # a doubtful pick is capped by the chance of playing
    doubt = captain_confidence(0.9, 1.0, penalty=True, venue="H", difficulty=2, doubtful=True, chance=25)
    assert doubt <= round(25 * 0.8)
    assert 1 <= hi <= 99 and 1 <= lo <= 99                       # always bounded


def _pick(**kw):
    base = {"id": 1, "web_name": "Cap", "xp": 6.0, "opponent": "HUL", "venue": "A", "difficulty": 2,
            "minutes_weight": 0.9, "penalty_taker": True, "doubtful": False, "chance": None}
    base.update(kw)
    return base


def test_explain_captain_lists_grounded_reasons_and_risks():
    top = _pick()
    runner = _pick(id=2, web_name="Runner", xp=5.9)             # +0.1 lead → a "narrow lead" risk
    rows = {1: {"selected_by": 48.0, "freekicks_order": 1, "corners_order": None, "form": 0.0, "status": "a"}}
    ex = explain_captain([top, runner], rows)

    why = " | ".join(ex.reasons)
    assert "Highest projected points (6.0)" in why
    assert "On penalties" in why and "Takes set-pieces" in why
    assert "Expected to start" in why and "Template pick (48% owned)" in why
    assert "Favourable fixture (HUL)" in why                    # difficulty 2

    risk = " | ".join(ex.risks)
    assert "Away fixture (HUL)" in risk
    assert "Narrow lead over Runner (+0.1)" in risk
    assert ex.band == confidence_band(ex.confidence)


def test_explain_captain_skips_gated_zero_signals_and_is_empty_safe():
    # form 0 preseason → no "in form"; a clear lead → no "narrow lead"; not a template → no template line
    top = _pick(minutes_weight=0.95)
    runner = _pick(id=2, xp=4.0)                                # a 2.0 lead → clear
    rows = {1: {"selected_by": 3.0, "freekicks_order": None, "corners_order": None, "form": 0.0, "status": "a"}}
    ex = explain_captain([top, runner], rows)
    assert not any("in form" in r.lower() for r in ex.reasons)
    assert not any("narrow lead" in r.lower() for r in ex.risks)
    assert any("Big differential" in r for r in ex.risks)      # 3% owned
    assert explain_captain([], rows) is None                    # empty-safe


# ── US-270: transfer explainability ───────────────────────────────────────────

def test_transfer_confidence_scales_with_the_gain():
    assert transfer_confidence(0.3) < transfer_confidence(2.5)          # a bigger XI gain → more confident
    assert transfer_confidence(3.0) >= 75                               # a clear upgrade → High
    doubt = transfer_confidence(3.0, doubtful_in=True, chance_in=25)    # capped by the buy's chance
    assert doubt <= round(25 * 0.8)
    assert 1 <= transfer_confidence(0.1) <= 99                          # bounded


def _move(**kw):
    base = {"position": "MID", "gain": 2.4,
            "out": {"id": 1, "web_name": "Old", "team": "AAA", "price": 7.0, "xp": 4.0},
            "in": {"id": 2, "web_name": "New", "team": "BBB", "price": 8.0, "xp": 6.5}}
    base.update(kw)
    return base


def test_explain_transfer_lists_the_gain_price_and_signals():
    in_row = {"penalties_order": 1, "corners_order": None, "freekicks_order": None,
              "selected_by": 45.0, "form": 0.0, "status": "a", "chance": None}
    ex = explain_transfer(_move(), in_row, horizon=5)
    why = " | ".join(ex.reasons)
    assert "+2.4 to your starting XI over 5 GW" in why
    assert "Higher projected points (6.5 vs 4.0)" in why
    assert "On penalties" in why and "Template pick (45% owned)" in why

    risk = " | ".join(ex.risks)
    assert "Costs £1.0m from your bank" in risk                         # buy is £1.0m pricier
    assert "Selling Old (4.0 xP)" in risk
    assert ex.band == confidence_band(ex.confidence)
    assert explain_transfer(None, in_row) is None                      # empty-safe


# ── US-271: squad-build explainability ────────────────────────────────────────

def test_squad_confidence_rewards_reliability_and_budget_use():
    assert squad_confidence(0.95, 1.0) > squad_confidence(0.6, 0.6)   # reliable + fully spent → higher
    assert squad_confidence(0.5, 0.4) < 75                            # rotation-heavy + money left → lower
    assert 1 <= squad_confidence(0.9, 0.99) <= 99                     # bounded


def _sq(**kw):
    # a 15 with an id/web_name/price/position + ownership/status; two players are the XI-bench split
    base = {"selected_by": 20.0, "status": "a"}
    base.update(kw)
    return base


def test_explain_squad_lists_the_build_signals_and_flags_risks():
    selected = [{"id": i, "web_name": f"P{i}", "position": "MID", "price": 6.0, **_sq()} for i in range(1, 16)]
    xp = {i: 5.0 for i in range(1, 16)}
    weight = {i: 0.9 for i in range(1, 16)}
    xi_ids = list(range(1, 12))                          # first 11 start
    weight[11] = 0.4                                     # one rotation-risk starter (in the XI)
    ex = explain_squad(selected, xp, weight, budget=100.0, xi_ids=xi_ids, horizon=5)

    why = " | ".join(ex.reasons)
    assert "Optimised on projected points (xP)" in why
    assert "Starting XI projects 55.0 over 5 GW" in why  # 11 × 5.0
    assert "Spent £90.0m of £100.0m" in why              # 15 × £6.0m
    risk = " | ".join(ex.risks)
    assert "£10.0m unspent" in risk                      # 100 − 90
    assert "rotation-risk starter" in risk               # id 15's 0.4 weight
    assert ex.band == confidence_band(ex.confidence)
    assert explain_squad([], xp, weight, budget=100.0, xi_ids=[]) is None   # empty-safe
