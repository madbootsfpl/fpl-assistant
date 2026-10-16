"""Who actually replaces whom in the lineup (ADR-351).

🔴🔴 **`bring_in` and `drop` are two set differences, not two halves of a swap list.** Every consumer that
zipped them invented the pairing, and the phone did: the owner read *"▲ Leno ▼ Barry"* — a **goalkeeper
for an outfielder**, which FPL does not allow.

⭐ The XI itself was legal; `best_legal_xi` produced it. ⚠️⚠️ *The advice was sound and the sentence
describing it was not* — which is the worse half, because the sentence is what somebody acts on.
"""

from __future__ import annotations

import pytest

from src.analytics.gameweek import lineup_swaps


def _p(name: str, position: str) -> dict:
    return {"id": abs(hash(name)) % 10_000, "web_name": name, "position": position}


def _pairs(swaps):
    return [(s["in"]["web_name"], s["out"]["web_name"]) for s in swaps]


def test_a_keeper_only_ever_replaces_a_keeper():
    """🔴 The reported bug, in the owner's own numbers. The same three changes, paired truthfully."""
    swaps = lineup_swaps(
        [_p("Leno", "GK"), _p("Guéhi", "DEF"), _p("Semenyo", "MID")],
        [_p("Barry", "MID"), _p("Pickford", "GK"), _p("Virgil", "DEF")],
    )
    assert ("Leno", "Pickford") in _pairs(swaps)
    for s in swaps:
        is_gk = s["in"]["position"] == "GK"
        assert (s["out"]["position"] == "GK") == is_gk, (
            f"{s['in']['web_name']} ({s['in']['position']}) cannot replace "
            f"{s['out']['web_name']} ({s['out']['position']})")


def test_every_player_is_accounted_for_exactly_once():
    """⚠️ A pairing that drops or repeats a name is a different plan from the one the engine chose."""
    incoming = [_p("Leno", "GK"), _p("Guéhi", "DEF"), _p("Semenyo", "MID")]
    outgoing = [_p("Barry", "MID"), _p("Pickford", "GK"), _p("Virgil", "DEF")]
    swaps = lineup_swaps(incoming, outgoing)

    assert sorted(s["in"]["web_name"] for s in swaps) == sorted(p["web_name"] for p in incoming)
    assert sorted(s["out"]["web_name"] for s in swaps) == sorted(p["web_name"] for p in outgoing)


def test_positions_are_matched_where_they_can_be():
    """⭐ Not because FPL requires it beyond the keeper, but because *"Guéhi for Virgil"* reads as a
    decision and *"Guéhi for Pickford"* reads as a mistake."""
    swaps = lineup_swaps([_p("Guéhi", "DEF"), _p("Semenyo", "MID")],
                         [_p("Barry", "MID"), _p("Virgil", "DEF")])
    assert set(_pairs(swaps)) == {("Guéhi", "Virgil"), ("Semenyo", "Barry")}


def test_a_formation_change_pairs_across_positions_rather_than_refusing():
    """⚠️ A legal XI can change shape — a defender in for a midfielder. ⭐ *Refusing to pair that would
    hide a real change*, so the keeper rule holds and the rest falls back to one-for-one."""
    swaps = lineup_swaps([_p("Guéhi", "DEF")], [_p("Barry", "MID")])
    assert _pairs(swaps) == [("Guéhi", "Barry")]


def test_an_unbalanced_change_drops_the_half_pair():
    """⚠️⚠️ A pair with a missing half is not a swap. ⭐ *A half-swap read as a whole one is how this
    started* — so it is left out rather than rendered against nothing."""
    assert lineup_swaps([_p("Guéhi", "DEF")], []) == []
    assert lineup_swaps([], [_p("Barry", "MID")]) == []


def test_a_keeper_with_no_keeper_to_replace_makes_no_pair_at_all():
    """⚠️⚠️ **The guard that makes the keeper rule decide something.** Position-matching alone already
    pairs GK with GK whenever both are present — ⭐ *so a mutation removing the keeper rule survived*,
    because the two were indistinguishable on every realistic input.

    They differ here: a keeper coming in with none going out. A legal XI always has exactly one keeper, so
    this should not arise — ⚠️ *and if it ever does, falling back would pair him with an outfielder and
    print the exact sentence this ADR exists to stop.*
    """
    swaps = lineup_swaps([_p("Leno", "GK"), _p("Guéhi", "DEF")], [_p("Virgil", "DEF")])
    assert _pairs(swaps) == [("Guéhi", "Virgil")], "the keeper was paired with somebody"
    assert not any(s["in"]["position"] == "GK" for s in swaps)


def test_a_sqlite_row_works_as_well_as_a_dict():
    """🔴 **Caught by ten Streamlit tests, not by this file.** `sqlite3.Row` has no `.get`, and Streamlit
    passes rows straight from the store rather than through JSON — ⭐ *so the first version raised on the
    one surface that does not serialise*, while every test here passed on dicts.
    """
    import sqlite3

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE p (id int, web_name text, position text)")
    conn.executemany("INSERT INTO p VALUES (?,?,?)",
                     [(1, "Leno", "GK"), (2, "Guéhi", "DEF"), (3, "Pickford", "GK"), (4, "Virgil", "DEF")])
    rows = {r["web_name"]: r for r in conn.execute("SELECT * FROM p")}

    swaps = lineup_swaps([rows["Leno"], rows["Guéhi"]], [rows["Pickford"], rows["Virgil"]])
    assert _pairs(swaps) == [("Leno", "Pickford"), ("Guéhi", "Virgil")]


def test_a_row_without_a_position_column_does_not_raise():
    """⚠️ Row raises `IndexError` for a missing key where a dict returns None. ⭐ *A pairing is a
    convenience; it must never be the thing that takes the screen down.*"""
    swaps = lineup_swaps([{"web_name": "A"}], [{"web_name": "B"}])
    assert _pairs(swaps) == [("A", "B")]


def test_nothing_to_do_is_no_swaps():
    assert lineup_swaps([], []) == []


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_the_count_the_screen_prints_is_the_number_of_swaps(n):
    """⭐ The heading said *"3 changes"* and then printed three lines; both must come from the same list.

    📌 This is the server half — that the list is as long as the change. The screen half, that the heading
    counts *that* list and not `bring_in`, is pinned in `mobile/test/lineup_swaps_render_test.dart`.
    """
    incoming = [_p(f"in{i}", "MID") for i in range(n)]
    outgoing = [_p(f"out{i}", "MID") for i in range(n)]
    assert len(lineup_swaps(incoming, outgoing)) == n
