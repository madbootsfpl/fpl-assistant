"""Tests for over/under-performance (expected vs actual attacking points)."""

from src.analytics.overperf import over_under
from src.ui.overperf import render_overperf


def player(name, pos, xg, xa, goals, assists, minutes):
    return {"id": abs(hash(name)) % 100000, "web_name": name, "team": "ARS", "position": pos,
            "xg": xg, "xa": xa, "goals_scored": goals, "assists": assists,
            "minutes": minutes}


def test_over_under_maths_for_a_midfielder():
    # MID: goal = 5 pts, assist = 3. expected = 10*5 + 5*3 = 65; actual = 12*5 + 6*3 = 78.
    rows = over_under([player("Mid", "MID", xg=10, xa=5, goals=12, assists=6, minutes=3000)])

    assert len(rows) == 1
    r = rows[0]
    assert r["expected"] == 65.0
    assert r["actual"] == 78.0
    assert r["diff"] == 13.0


def test_minutes_gate_excludes_small_samples_and_glitches():
    # A Meslier-style glitch: goals but ~no minutes → excluded by the gate.
    players = [
        player("Regular", "FWD", xg=8, xa=2, goals=10, assists=1, minutes=2500),
        player("Glitch", "GK", xg=0, xa=0, goals=11, assists=0, minutes=0),
    ]
    rows = over_under(players, min_minutes=900)

    names = {r["web_name"] for r in rows}
    assert names == {"Regular"}        # the 0-minute glitch is gone


def test_over_under_sorted_by_diff_descending():
    players = [
        player("Under", "MID", xg=10, xa=0, goals=2, assists=0, minutes=3000),   # -40
        player("Over", "MID", xg=2, xa=0, goals=10, assists=0, minutes=3000),    # +40
    ]
    rows = over_under(players)
    assert [r["web_name"] for r in rows] == ["Over", "Under"]


def test_none_fields_coerced_and_gated():
    # Un-refreshed row: minutes None → excluded (None < gate), no crash.
    rows = over_under([player("New", "FWD", xg=None, xa=None,
                              goals=None, assists=None, minutes=None)])
    assert rows == []


def test_render_shows_both_ends_and_caveat():
    rows = over_under([
        player("Hot", "MID", xg=2, xa=0, goals=12, assists=0, minutes=3000),
        player("Cold", "MID", xg=12, xa=0, goals=2, assists=0, minutes=3000),
    ])
    out = render_overperf(rows, limit=5)

    assert "Over-performing" in out and "Under-performing" in out
    assert "Hot" in out and "Cold" in out
    assert "not clean sheets" in out          # the attacking-only caveat


def test_render_empty_prompts_refresh():
    assert "refresh" in render_overperf([])
