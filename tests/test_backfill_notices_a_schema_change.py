"""A migration is not a backfill, and nothing noticed the difference (ADR-298 follow-up).

⚠️⚠️⚠️ **This is the shape of the bug, written down so it cannot happen quietly again.** ADR-298 added
`yellow_cards` and `red_cards` to `player_history`. The migration ran. The columns appeared. Every test
passed — locally, because the test fixture is **rebuilt** from scratch and therefore always has every
column populated.

Production was not rebuilt. Its rows were written before the columns existed, so every booking in every
gameweek read **zero**, and the backfill gate said *"history held for every completed gameweek"* — which
was true, and useless. ⭐ *A row that exists is not a row that is current, and "do we have this gameweek?"
cannot tell the two apart.*

It surfaced as a tester saying *"don't see red or yellow cards"* on a screen whose entire job was to show
them, two builds after it shipped.
"""

import pytest

from src.pipeline import HISTORY_SCHEMA, backfill_due, rewalk_due

# One finished fixture in GW1, and a stored row carrying a scoreline for it.
FIXTURES = [{"event": 1, "finished": True, "team_h_score": 2, "team_a_score": 1}]
HELD = {100: [{"round": 1, "minutes": 90, "total_points": 6, "team_h_score": 2, "team_a_score": 1}]}


def test_a_database_written_before_the_columns_existed_is_due() -> None:
    """⭐ The case production was in, and the one nothing could see."""
    due, why, rounds = rewalk_due(1, HELD)

    assert due is True, "a database one schema behind reported nothing to do"
    assert rounds == {1}, "the gameweeks needing values were not named"
    assert "schema v1" in why and f"v{HISTORY_SCHEMA}" in why, why


def test_a_database_that_never_recorded_a_schema_is_due() -> None:
    """⚠️ Every database that existed before this mechanism, including the live one. ⭐ *A new check whose
    default is "assume fine" fixes nothing the day it ships*, which is the only day that matters here."""
    assert rewalk_due(None, HELD)[0] is True
    assert rewalk_due(0, HELD)[0] is True


def test_a_current_database_is_left_alone() -> None:
    """⚠️ The counterpart, and the expensive one to get wrong: this walk is ~659 throttled requests. ⭐ *A
    gate that always opens is not a gate*, and it would run every hour forever."""
    due, why, rounds = rewalk_due(HISTORY_SCHEMA, HELD)

    assert due is False, why
    assert rounds == set()


def test_a_missing_gameweek_still_wins_regardless_of_schema() -> None:
    """⭐ The original reason for this gate is unchanged and is checked **first** — a gameweek with no rows
    at all is a bigger hole than a gameweek with stale ones, and its message is the more useful one.

    ⚠️ And `backfill_due` is the **reader's** question, unchanged: it drives the app's stale-data banner,
    so it must never fire for a schema lag — *every number on that screen is correct.*"""
    due, why, rounds = backfill_due(
        FIXTURES + [{"event": 2, "finished": True, "team_h_score": 0, "team_a_score": 0}],
        HELD,
    )
    assert due is True
    assert "no stored history" in why, why
    assert rounds == {2}


def test_the_rewalk_covers_the_old_rounds_not_just_the_newest() -> None:
    """⚠️⚠️ **The missing values are in the OLD rows.** A fix that refreshed only the latest gameweek would
    leave GW1-4 blank and look like it had worked — ⭐ *the set a freshness check would skip is exactly the
    set that needs rewriting.*"""
    fixtures = [{"event": n, "finished": True, "team_h_score": 1, "team_a_score": 0} for n in (1, 2, 3)]
    held = {100: [{"round": n, "minutes": 90, "total_points": 2, "team_h_score": 1, "team_a_score": 0}
                  for n in (1, 2, 3)]}

    _due, _why, rounds = rewalk_due(1, held)

    assert rounds == {1, 2, 3}, f"only {sorted(rounds)} would be rewritten"


@pytest.mark.parametrize("column", ["yellow_cards", "red_cards"])
def test_the_columns_that_caused_this_are_in_the_schema_the_version_describes(column: str) -> None:
    """⭐ Ties the number to the thing it is counting. ⚠️ *A version constant nobody can check against the
    schema is a number that stops being bumped* — the failure that produced this file."""
    from src.storage import CREATE_HISTORY

    assert column in CREATE_HISTORY, f"{column} left player_history but HISTORY_SCHEMA still claims it"


def test_an_empty_database_is_not_asked_to_rewalk_nothing() -> None:
    """⚠️⚠️ **Caught by an existing test, not by me.** Without this an empty database asks for ~659
    throttled requests to refresh rows that do not exist. ⭐ *This check is about rows that arrived before
    the question changed; where there are no rows, there is no such thing.*"""
    due, why, rounds = rewalk_due(None, {})

    assert due is False, why
    assert rounds == set()


def test_a_schema_lag_never_tells_a_READER_their_data_is_behind() -> None:
    """⚠️⚠️⚠️ **The worse bug hiding inside the fix, caught by the contract sample.**

    `backfill_due` also answers the app's *"is the board behind?"*, which drives a banner meaning *"the
    numbers on this screen are from yesterday."* Folding the schema check into it put `behind: true` and
    `missing_gameweeks: [1, 2, 3, 4, 5]` into every `my-team` response — ⭐ *nine testers told their data
    was broken when every number was correct and one secondary column was empty.*

    Two questions, two functions.
    """
    behind, why, rounds = backfill_due(FIXTURES, HELD)

    assert behind is False, f"a schema lag reached the reader as staleness: {why}"
    assert rounds == set()
    # ⭐ While the pipeline, asking its own question of the same database, still knows there is work.
    assert rewalk_due(0, HELD)[0] is True
