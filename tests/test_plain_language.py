"""The two sentences the owner could not read (ADR-314).

⭐⭐ *"Could you explain what it means at a more basic level so people will understand?"* — about the
Confidence ceiling, and *"the TIMING statement is also a little unclear"*. Both were **accurate and
unreadable**, which is the failure mode of copy written by the person who already knows the answer.

⚠️ These pin the **properties** that made them unreadable, not the words that replaced them — ⭐ *a test
that asserts a sentence verbatim turns every future improvement into a failing test.*
"""

from __future__ import annotations

import pytest

from src.analytics.explain import confidence_levers
from src.analytics.transfer_timing import bank_or_use

#: Every shape `bank_or_use` can return, with a label for the failure message.
CASES = {
    "nothing worth buying": ([], None, 1),
    "already holding two": ([{"gain": 2.0}], 1.0, 2),
    "banking wins": ([{"gain": 0.4}, {"gain": 3.0}], 0.4, 1),
    "spending wins": ([{"gain": 3.0}, {"gain": 0.5}], 2.8, 1),
    "no second move": ([{"gain": 3.0}], 2.8, 1),
}


@pytest.mark.parametrize("label", sorted(CASES))
def test_the_timing_reason_never_repeats_the_verdict(label: str) -> None:
    """⚠️⚠️ **Every caller states the decision itself** — the app prints `BANK` / `USE` as the headline, the
    CLI prefixes *"Or bank it:"* — so a reason opening *"bank the transfer"* said it twice. ⭐ *The headline
    is the decision; the reason is the arithmetic that makes it checkable.*"""
    moves, nxt, free = CASES[label]
    reason = bank_or_use(moves, nxt, free=free)["reason"]

    lowered = reason.lower()
    for instruction in ("bank the transfer", "use it now", "make the move", "spend it"):
        assert instruction not in lowered, f"{label}: the reason gives the order the headline already gave"


@pytest.mark.parametrize("label", sorted(CASES))
def test_every_number_in_a_timing_reason_says_what_it_is(label: str) -> None:
    """⚠️ The old wording was *"It saves 1.9 (the hit avoided on a second move worth 2.4) and costs 2.8"* —
    ⭐ *three numbers, no units, and a parenthetical carrying the only clause that explained the first one.*
    """
    moves, nxt, free = CASES[label]
    reason = bank_or_use(moves, nxt, free=free)["reason"]

    if any(ch.isdigit() for ch in reason):
        assert "pts" in reason or "free transfer" in reason, (
            f"{label}: a number with nothing saying what it counts — {reason!r}"
        )


def test_the_ceiling_explains_why_the_two_numbers_are_the_same() -> None:
    """⚠️⚠️⚠️ **The old sentence assumed the thing it was explaining.** *"your captain's own number
    (64/100); lifting it means a different captain, not a different week"* is true, and only lands for a
    reader who already knows the ceiling **is** the captain's score.

    ⭐ *A sentence that only makes sense to someone who already knows the thing it explains is not an
    explanation* — so the clause now carries the **because**.
    """
    levers = confidence_levers(64, [{"web_name": "Flagged", "starting": True}])

    fixed = levers["fixed"]
    assert "captain" in fixed, "the ceiling no longer says whose number it is"
    assert "because" in fixed, "…nor why the week's number cannot exceed it"
    assert "64" in fixed, "…nor what the number actually is"


def test_the_ceiling_separates_closing_the_gap_from_raising_the_bar() -> None:
    """⭐ The reader's question is *"how do I get to 80?"*, and the honest answer has two halves: the flags
    close the gap, and **nothing except the captain moves the number they are closing on.** ⚠️ Collapsing
    them is what made the old line read as a riddle."""
    from src.ui.gameweek import _levers_lines

    lines = "\n".join(_levers_lines(confidence_levers(64, [
        {"web_name": "Flagged", "starting": True},
    ])))

    assert "closes the gap" in lines
    assert "different captain" in lines
    assert "64" in lines


def test_a_week_at_its_ceiling_says_so_without_the_advice() -> None:
    """⭐ With nothing holding it down there is no gap to close, so the lever sentence would be advice about
    a problem the reader does not have — ⚠️ *and a suggestion offered when nothing is wrong teaches people
    to stop reading the suggestions.*"""
    from src.ui.gameweek import _levers_lines

    lines = "\n".join(_levers_lines(confidence_levers(64, [])))

    assert "Nothing is holding it down" in lines
    assert "closes the gap" not in lines
