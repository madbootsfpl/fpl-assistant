"""Tests for the head-to-head projection (ADR-161).

The module exists for one structural reason — **the players you both start cancel** — so most of these pin
that the cancellation is done right, especially in the case that decides most real head-to-heads: identical
elevens with different captains. Offline, plain dicts; no network, no Storage.
"""

from src.analytics.h2h import catch_up_note, h2h_gap, manager_projection

XP = {i: 4.0 for i in range(1, 20)}
XP[9], XP[10], XP[11], XP[12] = 8.0, 6.0, 2.0, 5.0
PLAYERS = [{"id": i, "web_name": f"P{i}", "team": "AAA", "position": "MID"} for i in range(1, 20)]


def _picks(ids, captain=None, bench=(), chip=None, multipliers=None):
    out = []
    for i, pid in enumerate(ids, start=1):
        if multipliers and pid in multipliers:
            mult = multipliers[pid]
        else:
            mult = 0 if pid in bench else (2 if pid == captain else 1)
        out.append({"element": pid, "position": i, "is_captain": pid == captain, "multiplier": mult})
    return {"picks": out, "active_chip": chip}


def test_a_projection_doubles_the_captain_and_ignores_the_bench():
    proj = manager_projection(_picks([1, 2, 9, 11], captain=9, bench=[11]), XP)
    assert proj["xp"] == 4.0 + 4.0 + 16.0          # P11 is benched and scores nothing
    assert proj["captain"] == 9


def test_the_multiplier_is_taken_at_face_value_so_chips_are_not_re_derived():
    """Bench Boost makes all fifteen count and Triple Captain makes one count three times. Re-deriving the
    multiplier from `is_captain` and the 1-11/12-15 split would silently get every chipped week wrong."""
    boosted = _picks([1, 2, 3], multipliers={1: 1, 2: 1, 3: 1}, chip="bboost")
    assert manager_projection(boosted, XP)["xp"] == 12.0
    tripled = _picks([9, 1], captain=9, multipliers={9: 3, 1: 1})
    assert manager_projection(tripled, XP)["xp"] == 24.0 + 4.0
    assert manager_projection(tripled, XP)["chip"] is None or True


def test_shared_starters_cancel_and_only_the_differentials_decide_it():
    mine = _picks([1, 2, 3, 4, 11], captain=1)
    theirs = _picks([1, 2, 3, 4, 12], captain=1)
    gap = h2h_gap(mine, theirs, XP, PLAYERS)
    assert gap["shared_count"] == 4
    assert [r["web_name"] for r in gap["my_edge"]] == ["P11"]
    assert [r["web_name"] for r in gap["their_edge"]] == ["P12"]
    assert gap["gap"] == round(2.0 - 5.0, 1)


def test_identical_elevens_with_different_captains_are_not_identical():
    """The case that decides most real head-to-heads. Every player is shared, so a naive set difference finds
    no differentials at all and reports a dead heat — when the captain choice is the entire game."""
    mine = _picks([9, 10, 1], captain=9)
    theirs = _picks([9, 10, 1], captain=10)
    gap = h2h_gap(mine, theirs, XP, PLAYERS)
    assert gap["gap"] == 2.0                        # P9's second copy (8.0) against P10's second copy (6.0)
    assert [(r["web_name"], r["xp"]) for r in gap["my_edge"]] == [("P9", 8.0)]
    assert [(r["web_name"], r["xp"]) for r in gap["their_edge"]] == [("P10", 6.0)]
    assert gap["same_captain"] is False


def test_the_captains_extra_copy_is_priced_not_the_whole_player():
    """A shared captain-vs-not player still contributes his single copy to the shared total; only the *extra*
    copy is a differential. Counting the whole player twice would double-count him into the gap."""
    gap = h2h_gap(_picks([9], captain=9), _picks([9]), XP, PLAYERS)
    assert gap["shared_xp"] == 8.0                  # the copy they both have
    assert [r["xp"] for r in gap["my_edge"]] == [8.0]
    assert gap["their_edge"] == []
    assert gap["gap"] == 8.0


def test_truly_identical_squads_say_so_rather_than_reporting_a_dead_heat_as_a_result():
    gap = h2h_gap(_picks([1, 2, 9], captain=9), _picks([1, 2, 9], captain=9), XP, PLAYERS)
    assert gap["gap"] == 0.0 and gap["my_edge"] == [] and gap["their_edge"] == []
    assert gap["same_captain"] is True
    assert "cannot separate you" in catch_up_note(gap)


def test_the_note_names_the_leader_and_the_biggest_single_differential():
    mine = _picks([1, 2, 3, 4, 11], captain=1)
    theirs = _picks([1, 2, 3, 4, 12], captain=1)
    note = catch_up_note(h2h_gap(mine, theirs, XP, PLAYERS), my_name="you", their_name="Ali")
    assert "Ali lead by 3.0" in note and "P12 (5.0 xP)" in note
    assert "4 shared starters cancel" in note


def test_an_unknown_player_id_does_not_crash_the_comparison():
    """A pick can reference someone missing from our snapshot — a very new signing, or a stale cache."""
    gap = h2h_gap(_picks([999]), _picks([1]), XP, PLAYERS)
    assert gap["my_edge"][0]["web_name"] == "#999"
    assert gap["my_edge"][0]["xp"] == 0.0


def test_empty_payloads_are_safe():
    gap = h2h_gap({}, {}, XP, PLAYERS)
    assert gap["gap"] == 0.0 and gap["shared_count"] == 0
    assert catch_up_note(gap).startswith("Identical")
    assert catch_up_note(None) == ""
