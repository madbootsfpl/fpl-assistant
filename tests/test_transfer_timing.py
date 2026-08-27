"""Tests for transfer timing (ADR-132).

The roadmap asked for a multi-gameweek transfer *path search*. A prototype found no path: the best sell was the
same player in all six gameweeks, and the whole market yielded one positive-gain move. So this is the
arithmetic a manager actually faces — use it, bank it, or take the hit — and these pin the sums.
"""

from src.analytics.transfer_timing import (
    bank_or_use,
    free_transfer_run,
    hit_is_worth_it,
    transfer_timing,
)


def _mv(out="A", inn="B", gain=3.0):
    return {"out": {"web_name": out, "id": 1}, "in": {"web_name": inn, "id": 2}, "gain": gain}


# ---- the free-transfer run ---------------------------------------------------------

def test_unused_transfers_roll_over_and_cap_at_five():
    assert free_transfer_run(1, 7) == [1, 2, 3, 4, 5, 5, 5]


def test_spending_one_resets_the_roll():
    assert free_transfer_run(1, 5, made_per_gw=[1]) == [1, 1, 2, 3, 4]


def test_spending_more_than_you_hold_floors_at_zero():
    """Spending beyond your free transfers is exactly what a hit is — the count must not go negative."""
    assert free_transfer_run(1, 3, made_per_gw=[3]) == [1, 1, 2]


# ---- the hit threshold --------------------------------------------------------------

def test_a_hit_needs_to_gain_more_than_it_costs():
    assert hit_is_worth_it(4.1) is True
    assert hit_is_worth_it(4.0) is False        # equal is not worth it
    assert hit_is_worth_it(3.0) is False        # the live case: the best move over six weeks
    assert hit_is_worth_it(None) is False


# ---- bank or use ---------------------------------------------------------------------

def test_no_worthwhile_move_means_bank():
    assert bank_or_use([])["action"] == "bank"
    assert bank_or_use([_mv(gain=0.0)])["action"] == "bank"


def test_holding_two_transfers_removes_the_reason_to_wait():
    assert bank_or_use([_mv(gain=3.0), _mv(gain=6.0)], 1.0, free=2)["action"] == "use"


def test_banking_wins_when_it_saves_more_than_waiting_costs():
    """Banking buys one thing — a second free transfer — so its value is the hit it avoids."""
    d = bank_or_use([_mv(gain=3.0), _mv("C", "D", 6.0)], 1.2)
    assert d["action"] == "bank" and d["value"] == 4.0 and d["cost"] == 1.2


def test_the_saving_is_capped_by_the_second_move_s_own_gain():
    """Avoiding a 4-point hit to make a move worth 1.0 gains you 1.0, not 4.0."""
    d = bank_or_use([_mv(gain=3.0), _mv("C", "D", 1.0)], 0.4)
    assert d["value"] == 1.0


def test_using_wins_when_waiting_costs_more_than_it_saves():
    d = bank_or_use([_mv(gain=3.0), _mv("C", "D", 1.0)], 2.0)
    assert d["action"] == "use"


def test_no_second_move_means_nothing_to_bank_for():
    d = bank_or_use([_mv(gain=3.0)], 1.2)
    assert d["action"] == "use" and d["value"] == 0.0


# ---- the whole picture reads as one plan ---------------------------------------------

def test_banking_never_also_advises_taking_the_hit():
    """A second move that would justify a hit is the *reason* to bank. Saying both reads as two opinions."""
    t = transfer_timing([_mv(gain=3.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=1.2, horizon=6)
    assert "Bank your free transfer" in t["headline"]
    assert "banking makes it free" in t["hit_verdict"]
    assert "more than the" not in t["hit_verdict"]


def test_the_live_case_reads_plainly():
    """One move worth 3.0 over six gameweeks, and a hit costs 4."""
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 3.0)], free=1, next_gw_gain=1.2, horizon=6)
    assert "Use your free transfer" in t["headline"] and "Gibbs-White" in t["headline"]
    assert t["take_hit"] is False
    assert "no hit to consider" in t["hit_verdict"]      # no second move, so hits aren't mentioned twice


def test_nothing_worth_doing_says_hold():
    t = transfer_timing([], free=1, horizon=6)
    assert "hold" in t["headline"] and "Nothing is worth transferring in" in t["hit_verdict"]


def test_a_second_move_worth_the_hit_is_recommended_when_banking_is_not():
    t = transfer_timing([_mv(gain=3.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=9.0, horizon=6)
    assert t["decision"]["action"] == "use" and t["take_hit"] is True
    assert "worth the hit" in t["headline"]


# ---- A dead slot takes the free transfer (ADR-156) ------------------------------------------------
# The page used to say two things at once: a ⛔ banner naming Watkins as unable to score, and — directly
# beneath it — "use your free transfer on Gibbs-White → Cunha". Both were computed correctly; neither knew
# about the other.

def _dead(out="Watkins", inn="Welbeck", gain=15.5, reason="per Romano"):
    return {"out": {"web_name": out, "id": 9}, "in": {"web_name": inn, "id": 8},
            "gain": gain, "reason": reason}


def test_a_dead_slot_takes_the_free_transfer_ahead_of_a_bigger_looking_upgrade():
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 3.3)], free=1, next_gw_gain=1.2, horizon=6,
                        dead=[_dead()])
    assert "Watkins → Welbeck" in t["headline"]
    assert "per Romano" in t["headline"]                 # the reader can check the claim
    assert t["decision"]["action"] == "use"
    assert "Gibbs-White" not in t["headline"], "the upgrade drops to being the hit question"


def test_a_dead_slot_is_never_banked_against():
    """Banking buys a second free transfer next week. A hole in the squad costs the same every week it stays."""
    # next_gw_gain 0.0 + a second move worth 6.0 is the textbook "bank it" case…
    banked = transfer_timing([_mv(gain=1.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=0.0, horizon=6)
    assert banked["decision"]["action"] == "bank"
    # …and it stops being one the moment part of the squad cannot play.
    t = transfer_timing([_mv(gain=1.0), _mv("C", "D", 6.0)], free=1, next_gw_gain=0.0, horizon=6,
                        dead=[_dead()])
    assert t["decision"]["action"] == "use"
    assert "Bank" not in t["headline"]


def test_the_best_ordinary_move_becomes_the_hit_question_behind_a_dead_slot():
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 6.5)], free=1, horizon=6, dead=[_dead()])
    assert t["take_hit"] is True                         # 6.5 > the 4-point hit
    assert "Gibbs-White → Cunha" in t["hit_verdict"]

    quiet = transfer_timing([], free=1, horizon=6, dead=[_dead()])
    assert "only move worth making" in quiet["hit_verdict"]
    assert "Nothing is worth transferring in" not in quiet["hit_verdict"]


def test_the_two_gains_are_never_compared_as_numbers():
    """ADR-136 keeps them apart: `replace_dead`'s gain is 'points recovered from zero', an upgrade's is
    'XI improvement'. The dead slot wins on kind, so a *smaller* number still goes first."""
    t = transfer_timing([_mv("Gibbs-White", "Cunha", 9.9)], free=1, horizon=6,
                        dead=[_dead(gain=1.1)])
    assert "Watkins → Welbeck" in t["headline"]
