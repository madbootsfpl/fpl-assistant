"""The next FPL deadline, derived from fixtures (Sprint 101, ADR-086).

The FPL deadline is 90 minutes before the first match of a gameweek. Rather than ingest an events table, we
derive it from the stored `kickoff_time`s: the earliest kickoff of the next unfinished gameweek, minus 90
minutes. Pure and `now`-injected (so it's unit-tested), timezone-aware, empty-safe.
"""

from datetime import datetime, timedelta

_LEAD = timedelta(minutes=90)   # a gameweek locks 90 minutes before its first kickoff


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
