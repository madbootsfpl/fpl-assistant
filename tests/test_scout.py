"""Tests for the scout shortlist (ADR-167).

The module's whole risk is overclaiming: two of the signals it reads are ones `decision_xp` deliberately does
not price yet, so these mostly pin what it must *never* say — a score, an ordering that competes with xP, or a
last-season fact without its vintage.
"""

from src.analytics.scout import scout_note, set_piece_reason, worth_a_look


def _p(pid, name, **extra):
    return {"id": pid, "web_name": name, "team": "AAA", "position": "DEF", "price": 5.0,
            "selected_by": 1.0, "minutes": 0, **extra}


def _rate_row(pid, name, minutes=1800, **extra):
    """A row as the rate boards actually read it — `defcon_per90` / `xgc` / `xg`,`xa`,`goals_scored`,
    `assists`, not the raw columns they are derived from. They need ~900 minutes to report anything at all."""
    row = {"id": pid, "web_name": name, "team": "AAA", "position": "DEF", "minutes": minutes,
           "defcon_per90": 0.0, "xgc": None, "xg": 0.0, "xa": 0.0, "goals_scored": 0, "assists": 0}
    row.update(extra)
    return row


def test_one_signal_is_not_a_reason():
    """A single board is a leaderboard; two boards agreeing is the only new thing this can say."""
    players = [_p(1, "Solo", penalties_order=1)]
    assert worth_a_look(players, rows=[]) == []


def test_two_signals_make_the_shortlist_and_carry_their_evidence():
    players = [_p(1, "Both", penalties_order=1)]
    rows = [_rate_row(1, "Both", defcon_per90=12.0)]        # well over the DEF threshold
    found = worth_a_look(players, rows=rows, season="2025/26")
    assert len(found) == 1
    assert found[0]["web_name"] == "Both"
    assert any("penalties" in r for r in found[0]["reasons"])
    assert len(found[0]["reasons"]) >= 2


def test_every_last_season_reason_carries_its_vintage():
    """A last-season fact stated as a present one is the most misleading kind of true statement — and three of
    the four boards read last season until about GW10."""
    players = [_p(1, "Both", penalties_order=1)]
    rows = [_rate_row(1, "Both", defcon_per90=12.0)]
    found = worth_a_look(players, rows=rows, season="2025/26")
    dated = [r for r in found[0]["reasons"] if "2025/26" in r]
    assert dated, "a reason drawn from last season must say so"
    assert not any("2025/26" in r for r in found[0]["reasons"] if "penalties" in r), \
        "…and the set-piece signal is CURRENT, so it must not be dated"


def test_an_over_performer_is_never_a_reason_to_look():
    """Points ahead of the underlying numbers regress. Counting that as a positive would invert the signal —
    the board calls it a **warning**, and the shortlist must not quietly re-read it as a recommendation."""
    players = [_p(1, "Hot", penalties_order=1)]
    hot = [_rate_row(1, "Hot", goals_scored=20, xg=1.0)]   # 20 goals off 1.0 xG — miles ahead of expected
    found = worth_a_look(players, rows=hot)
    reasons = found[0]["reasons"] if found else []
    assert not any("due a bounce" in r for r in reasons)


def test_the_shortlist_is_ordered_by_agreement_not_by_any_stat():
    """The underlying numbers are on different scales measuring different things, so sorting by one would
    smuggle in a ranking this module has no basis for."""
    players = [_p(1, "Two", penalties_order=1), _p(2, "Three", penalties_order=1)]
    rows = [_rate_row(1, "Two", defcon_per90=12.0),
            _rate_row(2, "Three", defcon_per90=12.0, xgc=10.0, goals_scored=0, xg=5.0)]
    found = worth_a_look(players, rows=rows)
    assert [f["web_name"] for f in found][0] == "Three"     # three signals lead two
    assert all(len(f["reasons"]) >= 2 for f in found)
    assert not any("score" in f or "rank" in f for f in found[0])   # no score, no rank — by construction


def test_set_piece_reason_reads_the_duty_not_a_rate():
    """The one current signal: a duty needs no minutes, which is why it survives an empty early season."""
    assert set_piece_reason(_p(1, "A", penalties_order=1)) == "first-choice penalties"
    assert set_piece_reason(_p(1, "A", corners_order=1)) == "first-choice corners"
    assert "order 2" in set_piece_reason(_p(1, "A", penalties_order=2))
    assert set_piece_reason(_p(1, "A")) is None
    assert set_piece_reason(_p(1, "A", penalties_order=5)) is None   # a fifth-choice taker is not a signal


def test_the_note_says_worth_a_look_and_never_worth_points():
    found = [{"web_name": "X", "reasons": ["a", "b"]}]
    note = scout_note(found, season="2025/26")
    assert "not a points projection" in note
    assert "2025/26" in note                                  # the vintage is in the framing too
    for forbidden in ("buy", "transfer in", "captain"):
        assert forbidden not in note.lower()


def test_an_empty_shortlist_is_an_answer_not_a_gap():
    note = scout_note([])
    assert "honest answer" in note and "not a gap" in note


def test_it_is_safe_on_an_empty_or_missing_pool():
    assert worth_a_look([], rows=[]) == []
    assert worth_a_look(None, rows=None) == []
