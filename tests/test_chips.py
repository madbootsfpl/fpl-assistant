"""Tests for the chip-strategy assembler (ADR-082).

`chip_advisor` is a pure reduction of the per-GW xP (`by_gameweek`) + the best legal XI — no I/O beyond the
in-memory solve. A crafted `by_gameweek` makes each chip's best GW deterministic, so the four heuristics are
pinned exactly. It must never change the analytics — it only *reads* the xP the caller computed.
"""

from src.analytics import chip_advisor
from src.ui.chips import render_chip_advice


def _squad():
    """A legal 15 (2 GK · 5 DEF · 5 MID · 3 FWD), spread over 6 clubs (≤3/club so an XI is selectable),
    cheap enough that any XI fits the budget."""
    pos = ["GK", "GK"] + ["DEF"] * 5 + ["MID"] * 5 + ["FWD"] * 3
    return [{"id": i + 1, "web_name": f"P{i + 1}", "team": f"T{i % 6 + 1}", "position": p,
             "price": 5.0, "total_points": 0}
            for i, p in enumerate(pos)]


def _by_gameweek(owned):
    """Craft per-GW xP so each chip's best GW is unambiguous over GWs [1..4]:
    - GW1: player 8 spikes to 20 (everyone else 2) → the highest single-starter ceiling (Triple Captain).
    - GW2: everyone scores 10 → the biggest all-15 total (Bench Boost).
    - GW3: everyone scores 1 → the weakest single week (Free Hit).
    - GW4: everyone scores 3. Rolling 3-GW XI windows: [1,2,3] vs [2,3,4]; the latter is weaker (Wildcard).
    """
    b = {}
    for p in owned:
        pid = p["id"]
        b[pid] = {1: (20.0 if pid == 8 else 2.0), 2: 10.0, 3: 1.0, 4: 3.0}
    return b


def test_chip_advisor_picks_the_right_gameweek_for_each_chip():
    owned = _squad()
    gameweeks = [1, 2, 3, 4]
    advice = chip_advisor(owned, _by_gameweek(owned), gameweeks)

    tc = advice["triple_captain"]
    assert tc["gameweek"] == 1 and tc["player"]["id"] == 8 and tc["player_xp"] == 20.0

    bb = advice["bench_boost"]
    assert bb["gameweek"] == 2 and bb["squad_total"] == 150.0        # 15 × 10
    assert bb["bench_points"] == 40.0                                # 150 total − 110 best-XI

    fh = advice["free_hit"]
    assert fh["gameweek"] == 3 and fh["xi_total"] == 11.0            # 11 × 1

    wc = advice["wildcard"]
    assert wc["window"] == (2, 4) and wc["gameweeks"] == [2, 3, 4]   # the weaker rolling stretch
    assert wc["avg_xi"] == round((110 + 11 + 33) / 3, 1)


def test_chip_advisor_is_empty_safe():
    assert chip_advisor([], {}, [1, 2]) is None                     # no players
    assert chip_advisor(_squad(), {}, []) is None                   # no gameweeks


def test_wildcard_window_clamps_to_a_short_horizon():
    owned = _squad()
    # Only two GWs → the window can't be 3; it clamps to 2 and spans both.
    b = {p["id"]: {1: 5.0, 2: 1.0} for p in owned}
    wc = chip_advisor(owned, b, [1, 2])["wildcard"]
    assert wc["window"] == (1, 2) and wc["gameweeks"] == [1, 2]


def test_render_chip_advice_shows_every_chip_and_the_caption():
    owned = _squad()
    advice = chip_advisor(owned, _by_gameweek(owned), [1, 2, 3, 4])
    block = render_chip_advice(advice, "TST", horizon=4)
    for label in ("Triple Captain", "Bench Boost", "Free Hit", "Wildcard"):
        assert label in block
    assert "GW1" in block and "GW2" in block                        # the recommended weeks
    assert "in-season" in block                                     # the honest what-sharpens-later note


def test_render_chip_advice_handles_no_advice():
    assert "no data" in render_chip_advice(None, "TST")


def test_render_chip_advice_appends_the_model_note_only_when_explained():
    # US-278: the shared Model note closes an explained answer — here, when per-chip confidences are shown.
    from src.analytics.explain import explain_chips
    owned = _squad()
    advice = chip_advisor(owned, _by_gameweek(owned), [1, 2, 3, 4])
    assert "Model note:" not in render_chip_advice(advice, "TST", horizon=4)          # no confidences
    explained = render_chip_advice(advice, "TST", horizon=4, confidences=explain_chips(advice))
    assert "Model note:" in explained
