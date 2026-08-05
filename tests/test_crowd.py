"""Tests for the crowd/sentiment lens (Phase 6, ADR-057).

`crowd_flags` is a pure, empty-safe row→flags function; the crucial invariant is that these signals are a
**display lens only** — they must never change the grounded xP (`decision_xp`).
"""

from src.analytics import crowd_flags, decision_xp, net_transfers
from src.analytics.crowd import DIFFERENTIAL_OWN, FORM_MIN, TEMPLATE_OWN, TRENDING_NET
from src.storage import Storage


def _p(**kw):
    return kw          # a player "row" is just a mapping; crowd_flags is empty-safe


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
