"""A flagged player already on your bench costs the week nothing (ADR-240).

⭐⭐⭐ **Found by a tester looking at his own card**, not by the suite. His screen read:

    51/100 Low
    − 8  M.Sangaré is flagged — already on your bench
    − 8  João Pedro is flagged — bench or replace him
    − 8  Hume is flagged — bench or replace him

⚠️ **The first line charges 8 for a risk he had already mitigated, and then tells him to mitigate it.**
The score could not be improved by the action it was asking for — the player was already there.

⭐⭐ **The information was never missing.** `gameweek.py` has computed `"starting": p["id"] in optimal`
since ADR-208, with a comment saying *"a flagged player already on the bench costs the XI nothing"* — while
`gameweek_confidence` counted the whole squad regardless. ⚠️ *A fact computed and then not used reads, from
the outside, exactly like a fact nobody knew.*

⚠️⚠️ **And the whole suite stayed green through the fix**, which is the part worth remembering: 2,331 tests
and not one distinguished a benched flag from a starting one. ⭐ *Passing tests measure what was asked, not
what is true.*
"""

import pytest

from src.analytics.explain import (
    FLAG_COST,
    confidence_band,
    confidence_levers,
    gameweek_confidence,
    starting_flags,
)
from src.ui.gameweek import _levers_lines


def flag(name, *, starting, cover=("Cover", 2.3)):
    return {
        "web_name": name,
        "team": "ARS",
        "reason": "doubtful",
        "chance": 75,
        "starting": starting,
        "cover": {"name": cover[0], "xp": cover[1]} if starting else None,
    }


# ── the score ────────────────────────────────────────────────────────────────────────────────────

def test_a_benched_flag_does_not_cost_the_week_anything():
    xi_only = [flag("A", starting=True)]
    plus_benched = [flag("A", starting=True), flag("B", starting=False)]
    assert confidence_levers(75, xi_only)["score"] == confidence_levers(75, plus_benched)["score"]


def test_the_owners_own_card_now_reads_59_rather_than_51():
    """⭐ The exact squad from the screenshot: a 75 captain, one benched flag and two starting."""
    flags = [flag("M.Sangaré", starting=False),
             flag("João Pedro", starting=True),
             flag("Hume", starting=True)]
    out = confidence_levers(75, flags)
    assert out["score"] == 59, "75 minus two starting flags, not three squad flags"
    # ⚠️ The band moved with it, which is the half the reader actually sees.
    assert confidence_band(out["score"]) == "Medium"


def test_a_starting_flag_still_costs_the_full_amount():
    """⚠️ The fix must not quietly stop charging for flags that DO matter."""
    assert confidence_levers(80, [flag("A", starting=True)])["score"] == 80 - FLAG_COST


@pytest.mark.parametrize("n", [0, 1, 2, 3])
def test_only_the_starting_ones_are_counted(n):
    flags = [flag(f"S{i}", starting=True) for i in range(n)]
    flags += [flag(f"B{i}", starting=False) for i in range(3)]
    assert gameweek_confidence(90, len(starting_flags(flags))) == 90 - FLAG_COST * n


def test_a_flag_that_cannot_say_is_charged_for():
    """⚠️ An older payload with no `starting` key must be charged, not excused.

    ⭐ Undercounting silently inflates the score, and an inflated confidence is the worse failure — it
    reads as a healthy week rather than as missing data.
    """
    assert starting_flags([{"web_name": "A"}]) == [{"web_name": "A"}]


# ── what the reader sees ─────────────────────────────────────────────────────────────────────────

def test_the_benched_line_is_still_shown_and_is_worth_zero():
    """⭐ It stays on the card. It is a real thing about your squad — it just is not costing you."""
    levers = confidence_levers(75, [flag("M.Sangaré", starting=False), flag("Hume", starting=True)])
    by_name = {lv["what"].split(" is flagged")[0]: lv for lv in levers["levers"]}
    assert by_name["M.Sangaré"]["worth"] == 0
    assert by_name["M.Sangaré"]["kind"] == "noted"
    assert by_name["Hume"]["worth"] == FLAG_COST
    assert by_name["Hume"]["kind"] == "action"


def test_the_sentence_agrees_with_the_arithmetic():
    """⚠️⚠️ **The bug was visible in the prose too.** *"minus 24 for 3 flagged players"* against a score
    that had only been docked 16 is a card arguing with itself — ⭐ *and a reader trusts the sentence,
    because it is the part written in words.*
    """
    levers = confidence_levers(75, [flag("M.Sangaré", starting=False),
                                    flag("João Pedro", starting=True),
                                    flag("Hume", starting=True)])
    lines = _levers_lines(levers)
    head = lines[0]
    assert "minus 16" in head, head
    assert "2 flagged players" in head, head
    # ⭐ And the benched one is still named, so nothing is hidden — just not charged.
    assert any("No cost" in line and "M.Sangaré" in line for line in lines), lines
