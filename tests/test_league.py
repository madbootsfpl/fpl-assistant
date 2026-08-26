"""Tests for the league analytics (ADR-141).

Offline, against fixture-shaped payloads. The numbers here are the ones measured live against the top 20
managers in the world in GW1 — Palmer at 90% EO against 11.9% global ownership — because that gap is the
reason the module exists and a test that encodes it explains itself.
"""

from src.analytics.league import (
    captain_split,
    chip_usage,
    effective_ownership,
    last_completed_gameweek,
    league_name,
    ownership_gaps,
    standings_rows,
)


def _pick(element, position, *, captain=False):
    return {"element": element, "position": position, "is_captain": captain}


def _picks(*elements, captain=None, chip=None):
    """A picks payload: the given elements as the XI, then four bench players."""
    starters = [_pick(e, i + 1, captain=(e == captain)) for i, e in enumerate(elements)]
    bench = [_pick(900 + i, 12 + i) for i in range(4)]
    return {"picks": starters + bench, "active_chip": chip}


# ---- effective ownership -------------------------------------------------------------

def test_a_captain_counts_twice_because_that_is_what_it_costs_you():
    """The definition, and the reason ownership alone is not enough: if a player you don't own is captained
    by half your league, you lose *double* to half your league."""
    picks = {1: _picks(10, 11, captain=10), 2: _picks(10, 11, captain=11)}
    eo = effective_ownership(picks)
    assert eo[10] == 150.0, "owned by 2/2 (100) + captained by 1/2 (50)"
    assert eo[11] == 150.0


def test_owned_and_captained_by_everyone_reads_two_hundred_percent():
    picks = {1: _picks(10, captain=10), 2: _picks(10, captain=10)}
    assert effective_ownership(picks)[10] == 200.0


def test_bench_players_are_excluded_because_a_bench_scores_you_nothing():
    """Counting them would overstate exposure — the whole point of EO is what actually costs you points."""
    picks = {1: _picks(10)}
    eo = effective_ownership(picks)
    assert eo[10] == 100.0
    assert all(pid < 900 for pid in eo), "the four bench players must not appear"


def test_the_divisor_is_what_we_actually_fetched():
    """A partial league still gives a usable EO. An exception would throw away 49 good fetches for one bad id,
    which is why the fetcher drops failures rather than raising."""
    assert effective_ownership({1: _picks(10), 2: _picks(10), 3: _picks(11)})[10] == round(2 / 3 * 100, 1)
    assert effective_ownership({}) == {}


# ---- the gap that justifies the feature ----------------------------------------------

def test_the_gap_separates_a_differential_from_a_template_pick():
    """The measured case, as a test. Palmer read 11.9% global ownership — every other surface in this app
    calls that a differential — while sitting at 90% EO among the top 20 managers in the world. Those are
    opposite decisions, and global ownership cannot tell them apart."""
    players = [{"id": 10, "web_name": "Palmer", "selected_by": 11.9},
               {"id": 11, "web_name": "Szoboszlai", "selected_by": 42.5}]
    gaps = {g["player"]["web_name"]: g for g in ownership_gaps({10: 90.0, 11: 35.0}, players)}
    assert gaps["Palmer"]["gap"] == 78.1, "template among the elite, differential by global ownership"
    assert gaps["Szoboszlai"]["gap"] == -7.5, "the other direction — where a differential actually is"


def test_the_biggest_gap_leads_in_either_direction():
    """Sorted by absolute gap: a player the league is *under*-exposed to is as interesting as one it is
    piled into, and ranking only the positives would hide half the answer."""
    players = [{"id": 1, "web_name": "A", "selected_by": 50.0}, {"id": 2, "web_name": "B", "selected_by": 5.0}]
    order = [g["player"]["web_name"] for g in ownership_gaps({1: 5.0, 2: 20.0}, players)]
    assert order == ["A", "B"], "-45 outranks +15"


def test_a_player_missing_from_the_dataset_is_skipped_not_guessed_at():
    assert ownership_gaps({999: 50.0}, [{"id": 1, "web_name": "A", "selected_by": 5.0}]) == []


# ---- captains, chips, standings ------------------------------------------------------

def test_the_captain_split_keeps_its_shape():
    """A 6/5/4 spread is a completely different week from 18/1/1, and only the shape says so."""
    picks = {i: _picks(10, 11, 12, captain=c) for i, c in enumerate([10, 10, 11, 12])}
    assert captain_split(picks) == [(10, 2), (11, 1), (12, 1)]


def test_chips_come_free_from_the_same_payloads():
    """`active_chip` rides along on every picks response — on the live GW1 data, 18 of the top 20 played
    Bench Boost, which is a consensus worth seeing as one number."""
    picks = {1: _picks(10, chip="bboost"), 2: _picks(10, chip="bboost"), 3: _picks(10)}
    assert chip_usage(picks) == [("bboost", 2), ("none", 1)]


def test_movement_is_positive_when_climbing_and_none_when_there_is_no_history():
    """`last_rank` of 0 means no previous rank — a new entry, or the league's first gameweek. That is not a
    rise of 400 places, so it reads as None and the caller shows "new"."""
    payload = {"standings": {"results": [
        {"entry": 1, "player_name": "A", "entry_name": "TA", "rank": 1, "last_rank": 4,
         "event_total": 70, "total": 200},
        {"entry": 2, "player_name": "B", "entry_name": "TB", "rank": 2, "last_rank": 0,
         "event_total": 60, "total": 190},
        {"entry": 3, "player_name": "C", "entry_name": "TC", "rank": 3, "last_rank": 1,
         "event_total": 50, "total": 180}]}}
    rows = standings_rows(payload)
    assert [r["movement"] for r in rows] == [3, None, -2]
    assert rows[0]["team"] == "TA" and rows[0]["total"] == 200


def test_empty_and_malformed_standings_do_not_explode():
    for payload in ({}, {"standings": {}}, {"standings": {"results": []}}):
        assert standings_rows(payload) == []
    assert league_name({}) == ""


# ---- which gameweek can we trust? ----------------------------------------------------

def test_the_last_completed_gameweek_comes_from_the_deadline_rule():
    """Derived from `get_upcoming_fixtures`, which cuts on the gameweek **deadline** (ADR-123) — so its first
    event is the next one you can act on, and the one before it is done. Reusing that rule rather than
    inventing a second one is what stops the two disagreeing about where "now" is.

    It is also what makes the picks cache safe to keep forever: ask for the in-flight gameweek and the answer
    would still be changing underneath the cache.
    """
    assert last_completed_gameweek([{"event": 2}, {"event": 3}, {"event": 2}]) == 1
    assert last_completed_gameweek([{"event": 7}]) == 6


def test_before_any_gameweek_has_been_played_there_is_nothing_to_read():
    assert last_completed_gameweek([{"event": 1}]) is None      # GW1 still to come
    assert last_completed_gameweek([]) is None
    assert last_completed_gameweek(None) is None
    assert last_completed_gameweek([{"event": None}]) is None
