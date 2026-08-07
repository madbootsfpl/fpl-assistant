"""Tests for the crowd/sentiment lens (Phase 6, ADR-057).

`crowd_flags` is a pure, empty-safe row→flags function; the crucial invariant is that these signals are a
**display lens only** — they must never change the grounded xP (`decision_xp`).
"""

from src.analytics import (
    availability_flag,
    crowd_flags,
    decision_xp,
    net_transfers,
    set_piece_flags,
    trending,
)
from src.analytics.crowd import DIFFERENTIAL_OWN, FORM_MIN, TEMPLATE_OWN, TRENDING_NET
from src.storage import Storage


def _p(**kw):
    return kw          # a player "row" is just a mapping; crowd_flags is empty-safe


def test_set_piece_flags_for_a_first_choice_taker():
    # ADR-081: order == 1 → the flag; any other order (or absent) → nothing. Display-only, empty-safe.
    assert set_piece_flags(_p(penalties_order=1)) == ["⚽ pens"]
    assert set_piece_flags(_p(corners_order=1)) == ["🚩 corners"]
    assert set_piece_flags(_p(freekicks_order=1)) == ["🎯 FK"]
    assert set_piece_flags(_p(penalties_order=1, corners_order=1, freekicks_order=1)) == [
        "⚽ pens", "🚩 corners", "🎯 FK",
    ]


def test_set_piece_flags_ignores_non_first_choice_and_is_empty_safe():
    assert set_piece_flags(_p(penalties_order=2, corners_order=6, freekicks_order=3)) == []
    assert set_piece_flags(_p()) == []                                   # nothing present → no flags
    assert set_piece_flags(_p(penalties_order=None)) == []               # None → no crash, no flag


def test_availability_flag_per_status():
    # ADR-074: a compact flag per FPL status code; available / unknown → no flag; empty-safe
    assert availability_flag(_p(status="i")) == "🚑"     # injured
    assert availability_flag(_p(status="s")) == "🚫"     # suspended
    assert availability_flag(_p(status="u")) == "⛔"     # unavailable
    assert availability_flag(_p(status="n")) == "⛔"     # not available
    assert availability_flag(_p(status="d")) == "❓"     # doubtful, chance unknown → just the flag
    assert availability_flag(_p(status="a")) == ""       # available → no flag
    assert availability_flag(_p()) == ""                 # missing status → no flag (empty-safe)


def test_availability_flag_shows_the_chance_on_a_doubtful_player():
    # US-236: a doubtful player carries the chance of playing (❓ 75%) when known
    assert availability_flag(_p(status="d", chance=75)) == "❓ 75%"
    assert availability_flag(_p(status="d", chance=0)) == "❓ 0%"     # 0% is a real value, still shown
    assert availability_flag(_p(status="i", chance=25)) == "🚑"      # only doubtful appends the chance


def test_availability_flag_is_distinct_from_crowd_and_rating():
    # the availability emojis must not collide with crowd flags or the rating circles (🟢🟡🟠🔴)
    flags = set("🚑🚫⛔❓")
    assert not (flags & set("🟢🟡🟠🔴🟦💎🔥❄️📈"))


def test_template_and_differential_by_ownership():
    assert "🟦 template" in crowd_flags(_p(selected_by=TEMPLATE_OWN))          # ≥ 20%
    assert "💎 differential" in crowd_flags(_p(selected_by=DIFFERENTIAL_OWN))  # ≤ 5%
    mid = crowd_flags(_p(selected_by=10.0))                                    # in between → neither
    assert "template" not in " ".join(mid) and "differential" not in " ".join(mid)


def test_price_flags_on_cost_change_sign():
    assert crowd_flags(_p(cost_change_event=2)) == ["💰↑"]
    assert crowd_flags(_p(cost_change_event=-1)) == ["💸↓"]
    assert crowd_flags(_p(cost_change_event=0)) == []          # no move → no flag


def test_trending_flags_on_net_transfers():
    assert "🔥 in" in crowd_flags(_p(transfers_in_event=TRENDING_NET, transfers_out_event=0))
    assert "❄️ out" in crowd_flags(_p(transfers_in_event=0, transfers_out_event=TRENDING_NET))
    quiet = crowd_flags(_p(transfers_in_event=10, transfers_out_event=5))     # tiny net → no flag
    assert "🔥" not in " ".join(quiet) and "❄️" not in " ".join(quiet)


def test_in_form_flag():
    assert "📈 form" in crowd_flags(_p(form=FORM_MIN))
    assert crowd_flags(_p(form=2.0)) == []


def test_crowd_flags_is_empty_safe():
    assert crowd_flags(_p()) == []                            # nothing present → no flags, no crash
    assert crowd_flags(_p(selected_by=None, form=None, cost_change_event=None)) == []


def test_net_transfers_handles_absence():
    assert net_transfers(_p(transfers_in_event=100, transfers_out_event=30)) == 70
    assert net_transfers(_p(transfers_in_event=100)) == 100   # one side absent → treated as 0
    assert net_transfers(_p()) is None                        # neither present → None


def test_decision_xp_ignores_the_crowd_fields():
    # THE invariant (ADR-057): the crowd lens must not change the grounded xP prediction.
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

    # Mutate every crowd field to wild values — xP must be identical.
    for p in players:
        p["form"], p["ict_index"], p["value_form"] = 99.0, 999.0, 42.0
        p["transfers_in_event"], p["transfers_out_event"] = 10_000_000, 0
        p["cost_change_event"], p["cost_change_start"] = 9, 9
    after = {r["id"]: r["xp"] for r in decision_xp(players, upcoming, history)}

    assert base == after


# --- trending leaderboards (Sprint 067) ----------------------------------------------------------

def test_trending_ranks_by_each_metric():
    players = [
        {"id": 1, "selected_by": 10, "form": 2.0, "transfers_in_event": 5, "transfers_out_event": 1},
        {"id": 2, "selected_by": 50, "form": 8.0, "transfers_in_event": 1, "transfers_out_event": 9},
        {"id": 3, "selected_by": 30, "form": 5.0, "transfers_in_event": 100, "transfers_out_event": 0},
    ]
    assert [r["id"] for r in trending(players, "owned")] == [2, 3, 1]     # 50 > 30 > 10
    assert [r["id"] for r in trending(players, "form")] == [2, 3, 1]      # 8 > 5 > 2
    assert trending(players, "in")[0]["id"] == 3                          # net +100 buys
    assert trending(players, "out")[0]["id"] == 2                         # net −8 (most sold)
    assert trending(players, "owned", limit=1)[0]["trend"] == 50          # the display value


def test_trending_is_empty_safe():
    assert trending([], "owned") == []
    assert trending([{"id": 1}], "owned")[0]["trend"] == 0                # missing metric → 0, no crash
