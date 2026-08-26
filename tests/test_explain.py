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
    explain_worth,
    squad_confidence,
    transfer_confidence,
    worth_confidence,
)


def test_confidence_band_cutoffs():
    assert confidence_band(90) == "High" and confidence_band(75) == "High"
    assert confidence_band(60) == "Medium" and confidence_band(55) == "Medium"
    assert confidence_band(40) == "Low"


def test_explain_worth_grounds_value_reasons_and_risks():
    # US-284: a grounded Why/Risk/Confidence for a value verdict — computed from the value, rank + median.
    good = {"position": "FWD", "price": 15.5, "penalties_order": 1, "corners_order": None,
            "freekicks_order": None, "selected_by": 75.0, "form": 0.0, "status": "a"}
    ex = explain_worth(good, value=1.87, median=0.99, rank=19, n_peers=62, xp=29.0, horizon=5)
    why, risk = " | ".join(ex.reasons), " | ".join(ex.risks)
    assert "Projects 29.0 points over 5 GW" in why
    assert "Above the FWD median value (1.87 vs 0.99 xP/£m)" in why
    assert "Top-third value for a FWD (#19 of 62)" in why and "Penalty taker" in why
    assert "Premium price (£15.5m ties up budget)" in risk    # a value premium still ties up budget
    assert ex.confidence >= 75 and ex.band == confidence_band(ex.confidence)

    poor = {"position": "MID", "price": 8.0, "penalties_order": None, "corners_order": None,
            "freekicks_order": None, "selected_by": 3.0, "form": 0.0, "status": "a"}
    ex2 = explain_worth(poor, value=0.40, median=1.00, rank=50, n_peers=60, xp=8.0, horizon=5)
    risk2 = " | ".join(ex2.risks)
    assert "Below the MID median value (0.40 vs 1.00 xP/£m)" in risk2
    assert "Mid-pack value (#50 of 60 MIDs)" in risk2 and "Differential (3% owned)" in risk2
    assert ex2.confidence < ex.confidence                     # worse value → lower confidence
    assert explain_worth(None, value=0, median=0, rank=None, n_peers=0, xp=0) is None   # empty-safe


def test_explanations_speak_the_ownership_tier_vocabulary():
    # US-290: the "why" uses the same tier words as the badges — essential / template (✓), differential (⚠),
    # popular / absent (neither).
    from src.analytics.explain import _ownership_signal
    assert _ownership_signal({"selected_by": 74.0}) == ("Essential (74% owned)", None)
    assert _ownership_signal({"selected_by": 45.0}) == ("Template pick (45% owned)", None)
    assert _ownership_signal({"selected_by": 3.0}) == (None, "Differential (3% owned)")
    assert _ownership_signal({"selected_by": 12.0}) == (None, None)     # popular → neither
    assert _ownership_signal({}) == (None, None)                        # absent → neither


def test_worth_confidence_is_bounded_and_reflects_value():
    assert 1 <= worth_confidence(0.0, 0.0) <= 99
    assert 1 <= worth_confidence(None, None) <= 99            # empty-safe
    assert worth_confidence(2.0, 1.0, penalty=True) > worth_confidence(0.3, 0.1)   # better value → higher


def test_render_explanation_has_a_clean_confidence_line_and_no_caveat():
    # US-278: the "heuristic, not a probability" caveat moved to the shared MODEL_NOTE, so the block's
    # confidence line is clean and matches the card format ("NN/100 (Band)").
    from src.analytics.explain import Explanation
    from src.ui.explain import render_explanation
    out = render_explanation(Explanation(reasons=["r"], risks=["k"], confidence=69, band="Medium"))
    assert "Confidence: 69/100 (Medium)" in out
    assert "not a probability" not in out and "/ 100 ·" not in out


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
    assert "Highest projected points" in why                   # US-277: no redundant number (it's on the card)
    assert "Penalty taker" in why and "Set-piece involvement" in why
    assert "Expected ~" in why and "Template pick (48% owned)" in why
    assert "Strong fixture vs HUL" in why                       # difficulty 2

    risk = " | ".join(ex.risks)
    assert "Away fixture" in risk
    # ADR-144: the "Only +0.1 ahead of Runner" risk was removed. The margin is now stated on **every** card
    # and characterised against the measured spread, so this bullet was the same fact told a second time, in a
    # second place, with a different threshold (0.5) than the card calibrates on. The gap still feeds
    # `captain_confidence` — a narrow lead should lower the confidence, not add a bullet.
    assert "ahead of Runner" not in risk, "the margin belongs on the card, said once"
    assert ex.band == confidence_band(ex.confidence)


def test_explain_captain_skips_gated_zero_signals_and_is_empty_safe():
    # form 0 preseason → no "in form"; a clear lead → no "narrow lead"; not a template → no template line
    top = _pick(minutes_weight=0.95)
    runner = _pick(id=2, xp=4.0)                                # a 2.0 lead → clear
    rows = {1: {"selected_by": 3.0, "freekicks_order": None, "corners_order": None, "form": 0.0, "status": "a"}}
    ex = explain_captain([top, runner], rows)
    assert not any("in form" in r.lower() for r in ex.reasons)
    assert not any("narrow lead" in r.lower() for r in ex.risks)
    assert any("Differential (3% owned)" in r for r in ex.risks)   # 3% owned → the differential-tier risk (US-290)
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
    assert "Penalty taker" in why and "Template pick (45% owned)" in why

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


# ── US-272: chip explainability ───────────────────────────────────────────────

def test_chip_confidence_low_when_flat_high_when_clear():
    from src.analytics import chip_confidence
    assert chip_confidence(0.2, 60.0) < 55            # a tiny margin vs a big value → Low (preseason-flat)
    assert chip_confidence(12.0, 60.0) >= 75          # a 20% separation → High (a clear window)
    assert 1 <= chip_confidence(0.0, 0.0) <= 99       # empty-safe + bounded


def test_explain_chips_gives_a_confidence_per_chip():
    from src.analytics import confidence_band, explain_chips
    advice = {
        "triple_captain": {"player_xp": 8.0, "margin": 3.0},   # a clear standout GW
        "bench_boost": {"squad_total": 60.0, "margin": 0.4},   # near-flat
        "free_hit": {"xi_total": 45.0, "margin": 0.3},
        "wildcard": {"avg_xi": 46.0, "margin": 0.4},
    }
    out = explain_chips(advice)
    assert set(out) == {"triple_captain", "bench_boost", "free_hit", "wildcard"}
    assert out["triple_captain"]["confidence"] > out["bench_boost"]["confidence"]   # clear beats flat
    assert out["bench_boost"]["band"] == confidence_band(out["bench_boost"]["confidence"])
    assert explain_chips(None) is None                # empty-safe


def test_chip_advisor_exposes_a_margin_per_chip():
    from src.analytics import chip_advisor
    owned = [{"id": i + 1, "web_name": f"P{i+1}", "team": f"T{i%6+1}",
              "position": (["GK", "GK"] + ["DEF"]*5 + ["MID"]*5 + ["FWD"]*3)[i],
              "price": 5.0, "total_points": 0} for i in range(15)]
    # GW1 spikes player 8 → a clear Triple-Captain margin; GW2/3 flatter
    by_gw = {p["id"]: {1: (20.0 if p["id"] == 8 else 2.0), 2: 3.0, 3: 3.0} for p in owned}
    advice = chip_advisor(owned, by_gw, [1, 2, 3])
    assert advice["triple_captain"]["margin"] > 0     # GW1 ceiling clearly beats the others
    assert all("margin" in advice[c] for c in ("triple_captain", "bench_boost", "free_hit", "wildcard"))


# ── US-273/274: gameweek-plan explainability ──────────────────────────────────

def test_gameweek_confidence_is_captain_driven_and_dropped_by_flags():
    from src.analytics import gameweek_confidence
    assert gameweek_confidence(80, 0) == 80
    assert gameweek_confidence(80, 2) == 64                 # −8 per flagged player
    assert 1 <= gameweek_confidence(10, 5) <= 99            # bounded


def test_explain_gameweek_reuses_captain_transfer_and_adds_lineup():
    from src.analytics import explain_gameweek, gameweek_confidence
    captain = {"id": 1, "web_name": "Cap", "xp": 6.0, "opponent": "HUL", "venue": "A", "difficulty": 2,
               "minutes_weight": 0.9, "penalty_taker": True, "doubtful": False, "chance": None}
    runner = {**captain, "id": 2, "web_name": "Runner", "xp": 5.9}
    move = {"position": "MID", "gain": 2.4,
            "out": {"id": 9, "web_name": "Old", "team": "AAA", "price": 7.0, "xp": 4.0},
            "in": {"id": 8, "web_name": "New", "team": "BBB", "price": 8.0, "xp": 6.5}}
    plan = {
        "captain": captain, "captain_ranked": [captain, runner], "transfer": move,
        "lineup": {"bring_in": [{"id": 5, "web_name": "Xin"}], "drop": [{"id": 6, "web_name": "Yout"}],
                   "has_declared_bench": True},
        "flags": [{"web_name": "Sick", "reason": "doubtful", "chance": 75}],
    }
    players_by_id = {1: {"selected_by": 48.0, "freekicks_order": 1, "form": 0.0, "status": "a"},
                    8: {"selected_by": 45.0, "status": "a"}}
    ex = explain_gameweek(plan, players_by_id, {5: 5.5, 6: 4.0}, horizon=5)

    assert ex["captain"] is not None                       # reused explain_captain
    assert ex["transfer"] is not None and ex["transfer"].reasons   # reused explain_transfer
    assert any("Start Xin over Yout" in r for r in ex["lineup"])   # grounded lineup rationale
    assert "Sick" in " ".join(ex["overall"].risks)          # the flagged player is the week's risk
    assert ex["overall"].confidence == gameweek_confidence(ex["captain"].confidence, 1)
    assert explain_gameweek(None, {}, {}) is None            # empty-safe
