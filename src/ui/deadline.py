"""Render the next-deadline countdown banner (Sprint 101, ADR-086).

A pure string from `(gameweek, deadline, now)` — a human countdown (days/hours) plus the date in UK time
(FPL is UK-based). `now`-injected so it's unit-tested; the web edge passes `datetime.now(timezone.utc)`.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

_UK = ZoneInfo("Europe/London")


def _countdown(delta) -> str:
    """A short 'in 14 days' / 'in 3h 20m' phrase for a positive timedelta."""
    total = int(delta.total_seconds())
    days, rem = divmod(total, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes = rem // 60
    if days >= 1:
        return f"in {days} day{'s' if days != 1 else ''}" + (f", {hours}h" if hours else "")
    if hours >= 1:
        return f"in {hours}h {minutes}m"
    return f"in {minutes}m"


def deadline_banner(gameweek: int, deadline: datetime, now: datetime) -> str:
    """One line, e.g. '⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) — in 14 days'. The date is shown in UK time;
    the countdown is from `now` (both timezone-aware)."""
    local = deadline.astimezone(_UK)
    when = local.strftime("%a %-d %b, %H:%M")
    return f"⏳ GW{gameweek} deadline: {when} (UK) — {_countdown(deadline - now)}"
