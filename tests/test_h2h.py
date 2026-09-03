"""Tests for the head-to-head projection (ADR-161).

The module exists for one structural reason — **the players you both start cancel** — so most of these pin
that the cancellation is done right, especially in the case that decides most real head-to-heads: identical
elevens with different captains. Offline, plain dicts; no network, no Storage.
"""

from src.analytics.h2h import (
    catch_up_note,
    chip_name,
    h2h_gap,
    manager_projection,
    reverts_next_gameweek,
)
from src.analytics.league import _BENCH_FROM

XP = {i: 4.0 for i in range(1, 20)}
XP[9], XP[10], XP[11], XP[12] = 8.0, 6.0, 2.0, 5.0
PLAYERS = [{"id": i, "web_name": f"P{i}", "team": "AAA", "position": "MID"} for i in range(1, 20)]


def _picks(ids, captain=None, bench=(), chip=None, multipliers=None):
    """A picks payload, with **FPL's position numbering**: starters 1-11, the bench from 12.

    That numbering used to be faked — every pick was handed `position = i`, so a "benched" player sat at
    position 4 and was only benched because the fixture also wrote `multiplier = 0`. It modelled less than
    reality, and it hid ADR-177: the payload it produced could not tell a bench from an XI by the field FPL
    actually uses for it.
    """
    starters = [p for p in ids if p not in bench]
    benched = [p for p in ids if p in bench]
    out = []
    for pos, pid in enumerate(starters + benched, start=1):
        pos = pos if pid not in bench else max(pos, _BENCH_FROM)
        if multipliers and pid in multipliers:
            mult = multipliers[pid]
        else:
            mult = 0 if pid in bench else (2 if pid == captain else 1)
        out.append({"element": pid, "position": pos, "is_captain": pid == captain, "multiplier": mult})
    return {"picks": out, "active_chip": chip}


def test_a_projection_doubles_the_captain_and_ignores_the_bench():
    proj = manager_projection(_picks([1, 2, 9, 11], captain=9, bench=[11]), XP)
    assert proj["xp"] == 4.0 + 4.0 + 16.0          # P11 is benched and scores nothing
    assert proj["captain"] == 9


def _fifteen(captain=None, chip=None, boosted=False):
    """A realistic fifteen — eleven starters and a four-man bench — optionally bench-boosted.

    `boosted=True` writes the payload FPL actually returns for a Bench Boost week: **multiplier 1 on all
    fifteen**, positions unchanged. That is the input that broke the head-to-head.
    """
    ids = list(range(1, 16))
    picks = []
    for pos, pid in enumerate(ids, start=1):
        starting = pos < _BENCH_FROM
        mult = (2 if pid == captain else 1) if (starting or boosted) else 0
        picks.append({"element": pid, "position": pos, "is_captain": pid == captain, "multiplier": mult})
    return {"picks": picks, "active_chip": chip}


def test_a_chip_played_last_week_does_not_change_next_weeks_projection():
    """ADR-177, owner-reported: *"you are showing MICKA at 59.9 and TS at 70, he is above me in the league?"*

    He was — by 23 points. The card is a projection of the gameweek **still to come**, and it was pricing his
    bench-boosted squad on **fifteen** players against a rival's eleven. The chip is spent; next week the
    bench is a bench again.

    This replaces a test that asserted the opposite (*"the multiplier is taken at face value so chips are not
    re-derived"*). That test was right about the question ADR-161 asked — reconstructing what a squad
    **scored** — and it defended the bug the moment the same code was used to project forward. A test that
    fails when you fix a bug is defending the error, so it asserts the requirement now instead of the
    mechanism.
    """
    plain = manager_projection(_fifteen(captain=9), XP)
    boosted = manager_projection(_fifteen(captain=9, chip="bboost", boosted=True), XP)
    assert boosted["xp"] == plain["xp"], "the same fifteen, projected the same, chip or no chip"
    assert boosted["chip"] == "bboost", "and the chip is still reported, so a surface can say it happened"


def test_two_identical_squads_are_a_dead_heat_even_when_one_of_them_chipped():
    """The reproduction, end to end. Before the fix these two projected 16 points apart on a flat xP map —
    a lead made entirely of four bench players, on a surface whose only claim is the gap between two totals.
    """
    gap = h2h_gap(_fifteen(captain=9, chip="bboost", boosted=True), _fifteen(captain=9), XP, PLAYERS)
    assert gap["gap"] == 0.0
    assert gap["my_edge"] == [] and gap["their_edge"] == []


def test_an_unchipped_squad_projects_exactly_as_it_did_before():
    """The no-op claim, pinned — and it is what makes the fix safe to apply unconditionally rather than
    behind a chip check. For a normal week, `position` + `is_captain` reproduce FPL's own multipliers, so
    every unchipped head-to-head in the league is byte-identical to what shipped before ADR-177."""
    payload = _fifteen(captain=9)
    from_multipliers = {pk["element"]: pk["multiplier"] for pk in payload["picks"] if pk["multiplier"]}
    assert dict(manager_projection(payload, XP)["starters"]) == from_multipliers


def test_a_triple_captain_projects_as_a_captain():
    """Same fault, smaller: the third copy is spent too. Reading multiplier 3 forward would have handed the
    captain an extra 8.0 he cannot score next week."""
    tripled = _fifteen(captain=9)
    for pk in tripled["picks"]:
        if pk["is_captain"]:
            pk["multiplier"] = 3
    tripled["active_chip"] = "3xc"
    assert manager_projection(tripled, XP)["xp"] == manager_projection(_fifteen(captain=9), XP)["xp"]


def test_a_payload_without_positions_falls_back_to_the_multiplier():
    """The degradation, and it is deliberate: a slightly wrong comparison beats no comparison, and this is
    exactly the behaviour that shipped before ADR-177 — strictly no worse than what it replaces."""
    payload = {"picks": [{"element": 1, "multiplier": 1, "is_captain": False},
                         {"element": 9, "multiplier": 2, "is_captain": True},
                         {"element": 11, "multiplier": 0, "is_captain": False}]}
    assert manager_projection(payload, XP)["xp"] == 4.0 + 16.0


def test_only_free_hit_says_the_squad_will_not_exist_next_week():
    """The one chip a different count cannot repair. Bench Boost and Triple Captain change how the *same*
    fifteen are scored; a Free Hit squad is discarded wholesale at the deadline and the previous one returns.
    Projecting it forward would price a team nobody will own."""
    assert reverts_next_gameweek(_fifteen(chip="freehit")) is True
    for still_yours in (None, "bboost", "3xc", "wildcard"):
        assert reverts_next_gameweek(_fifteen(chip=still_yours)) is False, still_yours
    assert reverts_next_gameweek({}) is False


def test_a_chip_is_named_for_a_reader_not_shown_as_a_code():
    assert chip_name("bboost") == "Bench Boost"
    assert chip_name("3xc") == "Triple Captain"
    assert chip_name(None) == ""
    assert chip_name("some_new_chip") == "some_new_chip", "an unknown code is odd, not invisible"


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


def test_the_note_uses_neutral_pronouns_for_a_rival():
    """US-431, owner: *"'What you have that he doesn't' should be 'What you have that they don't'."*

    A manager id says nothing about who is holding it, and the default is they/them. Pinned as a test because
    copy is the kind of thing that gets rewritten later by someone who does not know it was a correction.
    """
    mine = _picks([1, 2, 3, 4, 11], captain=1)
    theirs = _picks([1, 2, 3, 4, 12], captain=1)
    note = catch_up_note(h2h_gap(mine, theirs, XP, PLAYERS), my_name="you", their_name="they")
    lowered = note.lower()
    for gendered in (" he ", " him ", " his ", " she ", " her "):
        assert gendered not in f" {lowered} "
