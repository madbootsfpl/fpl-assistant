"""Tests for fixture concentration (ADR-145) — the honest version of "player clashes".

The Roadmap asked to flag *"your own players meeting = point cannibalisation"*. Two measurements on live data
killed that framing, and these tests carry both, because the reasoning is the feature:

* **Clashes are universal.** 300 random legal squads over five gameweeks: **100%** had one, averaging 26
  clashing pairs; narrowed to the XI *and* to defensive-vs-attacker it was still 7.4 per squad. A warning that
  fires for everyone every week is wallpaper.
* **A clash costs no expected points.** `decision_xp` already prices each player's own fixture, so summing
  them does not double-count. A clash changes the **joint** distribution, not either marginal.

So this measures concentration instead — how much of one gameweek depends on one match — which is actionable
and *subsumes* clashes.
"""

from src.analytics.concentration import (
    CONCENTRATED,
    HEAVY,
    concentration_note,
    match_concentration,
)


def _p(pid, name, team, xp_by_gw):
    return {"id": pid, "web_name": name, "team": team, "position": "MID"}, {pid: xp_by_gw}


def _squad(*specs):
    owned, bg = [], {}
    for pid, name, team, gws in specs:
        p, b = _p(pid, name, team, gws)
        owned.append(p)
        bg.update(b)
    return owned, bg


FIXTURES = [{"event": 2, "home": "LIV", "away": "MCI"},
            {"event": 2, "home": "ARS", "away": "TOT"},
            {"event": 3, "home": "LIV", "away": "ARS"},
            {"event": 3, "home": "MCI", "away": "TOT"}]


def test_it_finds_the_match_carrying_most_of_the_gameweek():
    owned, bg = _squad((1, "A", "LIV", {2: 6.0}), (2, "B", "MCI", {2: 4.0}), (3, "C", "ARS", {2: 2.0}))
    row = next(r for r in match_concentration(owned, FIXTURES, bg) if r["event"] == 2)
    assert (row["home"], row["away"]) == ("LIV", "MCI")
    assert row["xp"] == 10.0 and row["total"] == 12.0
    assert round(row["share"], 3) == round(10 / 12, 3)
    assert sorted(row["players"]) == ["A", "B"]


def test_players_on_both_sides_are_flagged_as_opposed():
    """This is the Roadmap's "clash" — kept as a **qualifier**, not a warning. Their returns partly cancel, so
    the week is even less spread than the share alone says. It is not a loss of expected points."""
    owned, bg = _squad((1, "A", "LIV", {2: 6.0}), (2, "B", "MCI", {2: 4.0}))
    assert match_concentration(owned, FIXTURES, bg)[0]["opposed"] is True


def test_players_in_the_same_match_on_the_SAME_side_are_not_opposed():
    """Two Liverpool players are concentrated but not conflicted — they can both return. Calling that a clash
    is the error the naive framing makes."""
    owned, bg = _squad((1, "A", "LIV", {2: 6.0}), (2, "B", "LIV", {2: 4.0}))
    assert match_concentration(owned, FIXTURES, bg)[0]["opposed"] is False


def test_a_note_appears_only_above_the_measured_seventy_fifth_percentile():
    """The whole discipline. Live data puts concentration at **median 29%, p75 34%, p90 40%, max 64%**, so
    `CONCENTRATED` is p75-ish and `HEAVY` sits above p90. The naive feature fired for every squad every week;
    this speaks about a quarter of the time, which is what makes it worth reading."""
    assert (CONCENTRATED, HEAVY) == (0.35, 0.45)
    ordinary = {"event": 2, "share": 0.29, "xp": 5.0, "total": 17.0, "home": "LIV", "away": "MCI",
                "players": ["A"], "opposed": False}
    assert concentration_note(ordinary) is None, "a median week must say nothing at all"
    assert concentration_note({**ordinary, "share": 0.40}) is not None


def test_a_heavy_week_reads_more_strongly_than_a_merely_concentrated_one():
    base = {"event": 6, "xp": 9.0, "total": 20.0, "home": "LIV", "away": "MCI",
            "players": ["A", "B"], "opposed": False}
    assert not concentration_note({**base, "share": 0.36}).startswith("Over")
    assert concentration_note({**base, "share": 0.50}).startswith("Over")


def test_the_note_names_the_players_because_a_share_alone_is_not_actionable():
    row = {"event": 6, "share": 0.43, "xp": 9.0, "total": 21.0, "home": "LIV", "away": "MCI",
           "players": ["Virgil", "Szoboszlai", "Haaland"], "opposed": True}
    note = concentration_note(row)
    assert "43%" in note and "GW6" in note and "LIV v MCI" in note
    assert "Virgil" in note and "3 players" in note
    assert "both" in note and "partly cancel" in note


def test_a_gameweek_projecting_nothing_is_skipped_not_divided_by():
    """An undefined share is not a share of zero — a blank gameweek must drop out rather than read as 0%."""
    owned, bg = _squad((1, "A", "LIV", {2: 0.0}), (2, "B", "MCI", {2: 0.0}))
    assert match_concentration(owned, FIXTURES, bg) == []


def test_empty_inputs_are_safe():
    assert match_concentration([], FIXTURES, {}) == []
    assert match_concentration([{"id": 1, "web_name": "A", "team": "LIV"}], [], {}) == []
    assert concentration_note(None) is None
