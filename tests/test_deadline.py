"""Tests for the next-deadline derivation + banner (Sprint 101, ADR-086).

`next_deadline` is pure and `now`-injected: the earliest kickoff of the next unfinished gameweek − 90 min,
rolling forward once a deadline passes. `deadline_banner` formats the countdown + the UK date.
"""

from datetime import datetime, timedelta, timezone

from src.analytics import deadline_urgency, gameweek_context, next_deadline
from src.ui.deadline import deadline_banner, deadline_line


def _fx(event, kickoff):
    return {"event": event, "kickoff_time": kickoff}


def _fixtures():
    # GW1: two matches (earliest 19:00Z on the 21st); GW2 a week later — order shuffled on purpose.
    return [
        _fx(2, "2026-08-28T14:00:00Z"),
        _fx(1, "2026-08-21T19:00:00Z"),
        _fx(1, "2026-08-22T11:30:00Z"),
        _fx(2, "2026-08-29T11:30:00Z"),
    ]


def test_next_deadline_is_the_earliest_kickoff_minus_90_minutes():
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    gw, deadline = next_deadline(_fixtures(), now)
    assert gw == 1
    assert deadline == datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc)   # 19:00Z − 90 min


def test_next_deadline_rolls_forward_once_a_deadline_passes():
    # after GW1's deadline, the next one is GW2's
    just_after = datetime(2026, 8, 21, 18, 0, tzinfo=timezone.utc)
    gw, _deadline = next_deadline(_fixtures(), just_after)
    assert gw == 2


def test_next_deadline_is_empty_safe():
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    assert next_deadline([], now) is None                              # no fixtures
    assert next_deadline([_fx(1, None), _fx(None, "2026-08-21T19:00:00Z")], now) is None   # no usable rows
    past = datetime(2027, 1, 1, tzinfo=timezone.utc)
    assert next_deadline(_fixtures(), past) is None                    # everything is behind us


def test_deadline_banner_shows_the_countdown_and_uk_time():
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc)      # 18:30 UK (BST)
    banner = deadline_banner(1, deadline, now)
    assert "GW1 deadline" in banner
    assert "18:30 (UK)" in banner                                     # UTC 17:30 → BST 18:30
    assert "in 14 days" in banner                                     # 2026-08-07 12:00 → 2026-08-21 17:30


def test_deadline_banner_handles_hours_and_minutes():
    now = datetime(2026, 8, 21, 15, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc)      # 2h 30m away
    assert "in 2h 30m" in deadline_banner(1, deadline, now)


# ── US-267: urgency, context, escalation ──────────────────────────────────────

def test_deadline_urgency_thresholds():
    assert deadline_urgency(timedelta(days=2)) == "calm"              # > 24h
    assert deadline_urgency(timedelta(hours=10)) == "today"           # < 24h
    assert deadline_urgency(timedelta(hours=1, minutes=30)) == "imminent"   # < 2h
    assert deadline_urgency(timedelta(seconds=-5)) == "imminent"      # passed → still imminent


def test_gameweek_context_counts_matches_and_first_kickoff():
    ctx = gameweek_context(_fixtures(), 1)
    assert ctx["matches"] == 2                                        # two GW1 fixtures in the fixture
    assert ctx["first_kickoff"] == datetime(2026, 8, 21, 19, 0, tzinfo=timezone.utc)   # the earliest
    empty = gameweek_context(_fixtures(), 99)
    assert empty == {"matches": 0, "first_kickoff": None}             # empty-safe


def test_deadline_banner_escalates_with_urgency():
    dl = datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc)
    ctx = {"matches": 10, "first_kickoff": datetime(2026, 8, 21, 19, 0, tzinfo=timezone.utc)}
    calm = deadline_banner(1, dl, dl - timedelta(days=5), ctx)
    today = deadline_banner(1, dl, dl - timedelta(hours=6), ctx)
    imminent = deadline_banner(1, dl, dl - timedelta(hours=1), ctx)
    assert calm.startswith("⏳") and "deadline:" in calm
    assert today.startswith("🟠") and "TODAY" in today
    assert imminent.startswith("🔴") and "set your team!" in imminent
    assert "10 matches" in calm and "first kick-off" in calm          # the context clause


def test_deadline_line_returns_gameweek_deadline_text_and_urgency():
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    gameweek, deadline, text, urgency = deadline_line(_fixtures(), now)
    assert gameweek == 1 and deadline == datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc)
    assert "GW1 deadline" in text and urgency == "calm"
    assert deadline_line([], now) is None                            # nothing ahead → None
