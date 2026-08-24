"""Tests for the shared percentile rank (ADR-127).

Player DNA and Team DNA each had their own copy of this, both counting peers "at or below" — so a tie ranked
at the *top* of its tie group. Nearly every goalkeeper has 0 xG, so a 0 beat every other 0 and landed in the
90s: the axis read *elite* precisely because the player had nothing there. These pin the replacement.
"""

import pytest

from src.analytics.ranking import percentile_rank as pr

# ---- the bug this exists for ------------------------------------------------------

def test_a_fully_tied_pool_sits_in_the_middle_not_at_the_top():
    """The reported case: every keeper has 0 set-piece involvement, so no keeper is better or worse than any
    other. "No different from your peers" is 50 — it was 100, which read as elite."""
    assert pr(0.0, [0.0] * 20) == 50


def test_a_zero_among_mostly_zeros_is_not_elite():
    """A.Becker's Goal Threat: a 0 in a pool where almost everyone is 0 used to score in the 90s."""
    pool = [0.0] * 27 + [0.4, 0.9, 1.4]
    assert pr(0.0, pool) < 50


def test_a_genuine_leader_is_untouched():
    """The fix must not flatten real signal — the best still reads 100."""
    pool = [0.1, 0.2, 0.3, 0.9]
    assert pr(0.9, pool) == 100


# ---- the range -------------------------------------------------------------------

def test_best_is_100_and_worst_is_0():
    vals = list(range(20))
    assert pr(19, vals) == 100 and pr(0, vals) == 0


def test_the_endpoints_matter_for_the_insight_copy():
    """Insights read "top {100 - pct}%", so the best player must score 100 or the copy says "top 2%"."""
    vals = list(range(20))
    assert max(1, 100 - pr(19, vals)) == 1


def test_ties_share_their_average_rank():
    # Three tied at the bottom of six: they occupy ranks 1-3, averaging 2 → (2-1)/(6-1) = 20.
    assert pr(1, [1, 1, 1, 5, 6, 7]) == 20


def test_inverted_axes_rank_lowest_as_best():
    """xGA and FDR are lower-is-better, so the smallest value must score highest."""
    vals = [0.5, 1.0, 1.5, 2.0]
    assert pr(0.5, vals, invert=True) == 100
    assert pr(2.0, vals, invert=True) == 0


# ---- edges -----------------------------------------------------------------------

def test_no_peers_is_unranked_not_zero():
    assert pr(5, []) is None
    assert pr(5, [None, None]) is None


def test_a_pool_of_one_is_a_tied_pool():
    """You cannot meaningfully be "best of one" — a lone value is neither above nor below anything."""
    assert pr(5, [5]) == 50
    assert pr(99, [5]) == 50


def test_a_value_outside_the_pool_stays_in_range():
    """Player DNA ranks a below-the-floor target against a floored pool, so `value` need not be a member —
    and the arithmetic can otherwise fall below zero on a small pool."""
    assert pr(-5, [1, 2]) == 0
    assert pr(99, [1, 2]) == 100
    assert 0 <= pr(0, [1, 2]) <= 100


@pytest.mark.parametrize("n", [2, 3, 7, 20, 149])
def test_every_result_is_a_percentage(n):
    vals = list(range(n))
    assert all(0 <= pr(v, vals) <= 100 for v in vals)
