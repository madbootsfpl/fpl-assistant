"""Transfers, Rank, Chips and Awards — free riders on a fetch already being made (ADR-287).

⭐⭐ **Four sub-tabs were parked as unbuilt when three of them were already paid for.** `with_captains`
spends one FPL request per manager, and the payload it gets back carries `active_chip` and an
`entry_history` holding the overall rank, the transfer count, the hit and the bench points. ⚠️ *The data
was arriving and being discarded.*
"""

from __future__ import annotations

from src.service.answers import _awards, _manager_rows

ROWS = [
    {"entry": 1, "manager": "Tony", "team": "MadBoots", "rank": 1},
    {"entry": 2, "manager": "Dave", "team": "Dave FC", "rank": 2},
    {"entry": 3, "manager": "Sarah", "team": "Sarah XI", "rank": 3},
]


def picks(**history) -> dict:
    base = {"points": 0, "overall_rank": 0, "event_transfers": 0,
            "event_transfers_cost": 0, "points_on_bench": 0}
    chip = history.pop("active_chip", None)
    return {"active_chip": chip, "entry_history": {**base, **history}}


def test_a_row_carries_everything_the_four_tabs_need() -> None:
    rows = _manager_rows(
        {1: picks(points=77, overall_rank=3842466, event_transfers=2,
                  event_transfers_cost=4, points_on_bench=8, active_chip="bboost")},
        ROWS,
    )

    assert rows == [{
        "entry": 1, "manager": "Tony", "team": "MadBoots",
        "points": 77, "overall_rank": 3842466,
        "transfers": 2, "hit": 4, "bench_points": 8, "chip": "bboost",
    }]


def test_no_chip_is_null_not_empty() -> None:
    # ⚠️ `""` would render as a blank chip rather than as no chip.
    assert _manager_rows({1: picks()}, ROWS)[0]["chip"] is None


def test_a_hit_stays_positive() -> None:
    # ⭐ *A cost stored as a negative number gets added somewhere by accident exactly once.*
    assert _manager_rows({1: picks(event_transfers_cost=8)}, ROWS)[0]["hit"] == 8


def test_only_the_managers_whose_fetch_succeeded() -> None:
    """⚠️ *A partial read must never present itself as the whole league* (ADR-215)."""
    rows = _manager_rows({1: picks(points=50), 3: picks(points=60)}, ROWS)

    assert [r["entry"] for r in rows] == [3, 1]
    assert all(r["manager"] for r in rows)


def test_an_unknown_entry_still_yields_a_row() -> None:
    # ⭐ The standings and the picks come from two calls; a manager in one and not the other is a
    # possibility, and dropping him silently would make the counts disagree with `captains_from`.
    rows = _manager_rows({99: picks(points=10)}, ROWS)

    assert rows[0]["entry"] == 99
    assert rows[0]["manager"] is None


def test_the_gameweek_winner_is_the_highest_scorer() -> None:
    awards = _awards(
        {1: picks(points=50), 2: picks(points=91), 3: picks(points=70)}, ROWS
    )

    assert awards[0] == {
        "kind": "gameweek_winner", "entry": 2, "manager": "Dave",
        "team": "Dave FC", "value": 91,
    }


def test_the_worst_bench_is_the_most_wasted() -> None:
    awards = _awards(
        {1: picks(points_on_bench=3), 2: picks(points_on_bench=19)}, ROWS
    )

    assert [a["kind"] for a in awards] == ["gameweek_winner", "worst_bench"]
    assert awards[1]["value"] == 19
    assert awards[1]["manager"] == "Dave"


def test_no_bench_award_when_nobody_wasted_anything() -> None:
    """⭐ *An award for wasting nothing is not an award*, and "0 pts left on the bench" makes the reader
    work out whether that is good."""
    awards = _awards({1: picks(points=40), 2: picks(points=50)}, ROWS)

    assert [a["kind"] for a in awards] == ["gameweek_winner"]


def test_awards_are_structured_not_worded() -> None:
    """⚠️ The server sends *who* and *how much*; the client supplies the title and the emoji.

    ⭐ The same split as a player card's badges (ADR-286): *a client that has to take a sentence apart to
    lay it out will one day take it apart differently.*
    """
    for award in _awards({1: picks(points=40, points_on_bench=6)}, ROWS):
        assert set(award) == {"kind", "entry", "manager", "team", "value"}
        assert isinstance(award["value"], int)


def test_a_league_nobody_could_be_read_for_has_no_awards() -> None:
    # ⚠️ Empty, never a podium of nulls.
    assert _awards({}, ROWS) == []
    assert _manager_rows({}, ROWS) == []


def test_a_tie_does_not_change_hands_on_a_refresh() -> None:
    """⭐ *An award that changes hands on a refresh is an award nobody believes.*"""
    tied = {1: picks(points=70), 2: picks(points=70), 3: picks(points=70)}

    assert {_awards(tied, ROWS)[0]["entry"] for _ in range(5)} == {1}
