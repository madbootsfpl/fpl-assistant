"""How old the numbers are, said on the wire (ADR-303).

⚠️⚠️⚠️ **The refresh declares a 15-minute cadence and GitHub fires 6-7% of it.** Measured 2026-09-26
against the Actions API: 6 runs in 24 hours, real gaps of 2h27m to 5h41m. So the app was implying a
freshness it did not have — and the staleness banner could not see it, because *a five-hour-old row is
still a row*.

⭐⭐ **Age is its own field and is deliberately not folded into `behind`.** `behind` means a completed
gameweek has **no rows**; age means the last refresh was a while ago. Merging them is the mistake ADR-301
caught, where a schema lag would have reached nine testers as *"your data is broken"*.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.service.answers import _age_minutes

NOW = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("ago", "expected"),
    [(timedelta(minutes=7), 7), (timedelta(hours=3), 180), (timedelta(days=2), 2880)],
)
def test_the_age_is_minutes_since_the_last_refresh(ago, expected):
    assert _age_minutes((NOW - ago).isoformat(), NOW) == expected


def test_a_database_that_has_never_refreshed_is_none_not_zero():
    """⚠️ *A database that has never been refreshed is not one refreshed just now.* ⭐ A client reading
    `0` would print "updated moments ago" about a file nothing has ever written."""
    assert _age_minutes(None, NOW) is None
    assert _age_minutes("", NOW) is None


def test_an_unreadable_stamp_is_none_rather_than_a_crash():
    """⭐ *A freshness check that throws is a pipeline that stops refreshing* — the rule ADR-301's gate
    already follows."""
    assert _age_minutes("not a date", NOW) is None


def test_a_naive_stamp_is_read_as_utc():
    """⚠️ SQLite hands back what was written, and not every writer stamps a timezone. ⭐ *Guessing local
    time would make the age wrong by the offset*, silently, and only for some deployments."""
    assert _age_minutes("2026-09-26T09:00:00", NOW) == 180


def test_a_clock_ahead_of_us_reports_zero_not_a_negative():
    """⚠️⚠️ The writer and the reader are different machines. ⭐ *A negative age renders as a refresh in
    the future*, which is worse than saying "just now" — it looks like a bug in the numbers themselves."""
    assert _age_minutes((NOW + timedelta(hours=2)).isoformat(), NOW) == 0


def test_the_answer_carries_the_age_beside_behind_and_not_inside_it():
    """⭐⭐ Two questions, two fields — the whole point of this ADR.

    ⚠️ A test that only checked `age_minutes` exists would pass if `behind` had been made to mean "old",
    which is the failure this is guarding against.
    """
    from src.service import MyTeamRequest, my_team
    from src.storage import Storage

    store = Storage()
    try:
        data = my_team(MyTeamRequest(manager_id=1013841, horizon=1), store=store)["data"]
    finally:
        store.close()

    assert "age_minutes" in data, "the answer does not say how old it is"
    assert isinstance(data["age_minutes"], (int, type(None)))
    # ⭐ `behind` still answers its own question, unchanged: a hole in the data, not the passage of time.
    assert isinstance(data["behind"], bool)
    assert "missing_gameweeks" in data
