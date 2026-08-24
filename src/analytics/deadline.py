"""The next FPL deadline, derived from fixtures (Sprint 101, ADR-086).

The FPL deadline is 90 minutes before the first match of a gameweek. Rather than ingest an events table, we
derive it from the stored `kickoff_time`s: the earliest kickoff of the next unfinished gameweek, minus 90
minutes. Pure and `now`-injected (so it's unit-tested), timezone-aware, empty-safe.
"""

from datetime import datetime, timedelta

from src.fpl_rules import DEADLINE_LEAD as _LEAD  # a gameweek locks 90 minutes before its first kickoff

# Urgency thresholds for the countdown (US-267) — how close the deadline is.
_IMMINENT = timedelta(hours=2)
_TODAY = timedelta(hours=24)


def _get(row, key):
    """A fixture-row field (sqlite Row or dict), or None if absent."""
    try:
        return row[key]
    except (KeyError, IndexError):
        return None


def _parse(kickoff: str):
    """An ISO kickoff string ('…Z') → a timezone-aware datetime, or None if unparseable/empty."""
    if not kickoff:
        return None
    try:
        return datetime.fromisoformat(kickoff.replace("Z", "+00:00"))
    except ValueError:
        return None


def next_deadline(fixtures, now: datetime):
    """The next `(gameweek, deadline)` still ahead of `now`, or None.

    For each gameweek (by `event`), the deadline is its **earliest** `kickoff_time` minus 90 minutes; the
    first gameweek whose deadline is after `now` is returned — so it **rolls forward** once a deadline passes.
    `now` must be timezone-aware (UTC). Empty-safe: fixtures without an event / kickoff are ignored."""
    earliest = {}
    for f in fixtures:
        gw, ko = _get(f, "event"), _parse(_get(f, "kickoff_time"))
        if gw is None or ko is None:
            continue
        if gw not in earliest or ko < earliest[gw]:
            earliest[gw] = ko
    for gw in sorted(earliest):
        deadline = earliest[gw] - _LEAD
        if deadline > now:
            return gw, deadline
    return None


def deadline_urgency(time_left: timedelta) -> str:
    """How close a deadline is (US-267): `imminent` (< 2h), `today` (< 24h), else `calm`. Used to escalate
    the banner's colour + copy. A non-positive `time_left` still reads as `imminent`."""
    if time_left < _IMMINENT:
        return "imminent"
    if time_left < _TODAY:
        return "today"
    return "calm"


def gameweek_context(fixtures, gameweek) -> dict:
    """What's coming in `gameweek` (US-267): `{matches, first_kickoff}` — the number of fixtures and the
    earliest `kickoff_time` (a datetime), from the fixtures we already read. Empty-safe: `{matches: 0,
    first_kickoff: None}` when the gameweek has none/unparseable."""
    kickoffs = [ko for f in fixtures
                if _get(f, "event") == gameweek and (ko := _parse(_get(f, "kickoff_time"))) is not None]
    return {"matches": len(kickoffs), "first_kickoff": min(kickoffs) if kickoffs else None}
