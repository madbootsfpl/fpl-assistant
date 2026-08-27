"""The transfer-window gate (ADR-154).

A club can only sell a player while a window is open, so a "he is leaving" report outside one changes nothing
about this gameweek — he plays on until January. The owner raised it before it could bite: *"we could get a
reported to be leaving outside the window and we should not react in that case."*
"""

from datetime import date

from src.analytics.headlines import reported_leaving
from src.fpl_rules import transfer_window_open

MOVE = [{"kind": "transfer", "source": "Romano", "title": "…agreed a deal to sign Ollie Watkins"}]
EXODUS = {"net": -167_825, "pressure": -17_000}


def test_the_windows_are_the_english_ones():
    assert transfer_window_open(date(2026, 8, 27))       # summer, days before it shuts
    assert transfer_window_open(date(2027, 1, 20))       # winter
    assert not transfer_window_open(date(2026, 9, 2))    # just after the summer window
    assert not transfer_window_open(date(2026, 10, 15))  # mid-season
    assert not transfer_window_open(date(2027, 3, 1))    # after the winter window


def test_a_leaving_report_outside_a_window_changes_nothing():
    """The point of the gate. Both signals can agree in October and he is *still* playing on Saturday —
    acting on it would cost a real transfer for a move that cannot happen yet."""
    assert reported_leaving(MOVE, EXODUS, today=date(2026, 8, 27)) is not None
    assert reported_leaving(MOVE, EXODUS, today=date(2026, 10, 15)) is None


def test_omitting_the_date_skips_the_check():
    """For callers that have already decided the question — the gate belongs in one place, not three."""
    assert reported_leaving(MOVE, EXODUS) is not None


def test_the_gate_is_conservative_at_the_edges_on_purpose():
    """A day early costs silence about a true story; a day late costs a transfer nobody can make. The known
    incompleteness is written down rather than discovered: **other countries' windows do not match England's**
    — the Saudi league has repeatedly stayed open for weeks after the Premier League shut, which is precisely
    the Watkins → Al-Hilal case this was built for. So the gate can suppress a *true* signal in early
    September, and that is the right direction to be wrong in.
    """
    from src.fpl_rules import TRANSFER_WINDOWS

    assert len(TRANSFER_WINDOWS) == 2, "a list of ranges, so a non-English window can be added as a row"
    assert not transfer_window_open(date(2026, 9, 5)), "documented false negative: a Saudi window may be open"
