"""Render the next-deadline countdown banner (Sprint 101, ADR-086; enriched Sprint 103, US-267).

Pure strings from `(gameweek, deadline, now[, context])` — a human countdown that **escalates** as the
deadline nears (calm → today → imminent), the date in UK time, and what's coming that gameweek (matches +
first kick-off). `now`-injected so it's unit-tested; the web edge passes `datetime.now(timezone.utc)` and
picks the widget colour from `analytics.deadline_urgency`.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from src.analytics import deadline_urgency, gameweek_context, next_deadline

_UK = ZoneInfo("Europe/London")


def _countdown(delta) -> str:
    """A short 'in 14 days' / 'in 3h 20m' / 'in 12m' phrase for a timedelta (non-positive → 'now')."""
    total = int(delta.total_seconds())
    if total <= 0:
        return "now"
    days, rem = divmod(total, 86_400)
    hours, rem = divmod(rem, 3_600)
    minutes = rem // 60
    if days >= 1:
        return f"in {days} day{'s' if days != 1 else ''}" + (f", {hours}h" if hours else "")
    if hours >= 1:
        return f"in {hours}h {minutes}m"
    return f"in {minutes}m"


# Urgency → (lead emoji, a short prefix). `calm` just counts down; `today`/`imminent` shout.
_URGENCY = {
    "calm": ("⏳", ""),
    "today": ("🟠", "deadline TODAY — "),
    "imminent": ("🔴", "deadline "),
}


def _context_clause(context) -> str:
    """' · 10 matches · first kick-off Fri 20:00' from a `gameweek_context` dict, or '' when empty."""
    if not context or not context.get("matches"):
        return ""
    ko = context.get("first_kickoff")
    when = f" · first kick-off {ko.astimezone(_UK).strftime('%a %H:%M')}" if ko else ""
    return f" · {context['matches']} matches{when}"


def deadline_banner(gameweek: int, deadline: datetime, now: datetime, context=None) -> str:
    """One line, escalating with urgency (US-267). Examples:
    calm     → '⏳ GW1 deadline: Fri 21 Aug, 18:30 (UK) — in 14 days · 10 matches · first kick-off Fri 20:00'
    today    → '🟠 GW1 deadline TODAY — in 6h 12m · Fri 21 Aug, 18:30 (UK)'
    imminent → '🔴 GW1 deadline in 1h 40m — set your team! · Fri 21 Aug, 18:30 (UK)'
    The date is UK time; the countdown is from `now` (both timezone-aware)."""
    left = deadline - now
    urgency = deadline_urgency(left)
    emoji, prefix = _URGENCY[urgency]
    when = deadline.astimezone(_UK).strftime("%a %-d %b, %H:%M")
    ctx = _context_clause(context)

    if urgency == "calm":
        return f"{emoji} GW{gameweek} deadline: {when} (UK) — {_countdown(left)}{ctx}"
    tail = " — set your team!" if urgency == "imminent" else ""
    return f"{emoji} GW{gameweek} {prefix}{_countdown(left)}{tail} · {when} (UK){ctx}"


def deadline_line(fixtures, now):
    """Everything the edge needs for the next deadline — `(gameweek, deadline, text, urgency)`, or None when
    nothing's ahead. One place for the compute; the web picks a widget colour from the urgency, shows a nudge,
    and (on Home) feeds the live clock the gameweek + deadline."""
    nd = next_deadline(fixtures, now)
    if not nd:
        return None
    gameweek, deadline = nd
    text = deadline_banner(gameweek, deadline, now, gameweek_context(fixtures, gameweek))
    return gameweek, deadline, text, deadline_urgency(deadline - now)
