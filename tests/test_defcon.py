"""Tests for Defensive Contribution reliability (per-90 vs position threshold)."""

from src.analytics.defcon import defcon_reliability
from src.ui.defcon import render_defcon


def player(name, pos, per90, minutes):
    return {"web_name": name, "team": "ARS", "position": pos,
            "defcon_per90": per90, "minutes": minutes}


def test_margin_uses_the_position_threshold():
    # DEF threshold 10; MID/FWD threshold 12.
    rows = defcon_reliability([
        player("Def", "DEF", per90=11.5, minutes=3000),   # margin +1.5
        player("Mid", "MID", per90=13.9, minutes=3000),   # margin +1.9
    ])
    by_name = {r["web_name"]: r for r in rows}
    assert by_name["Def"]["threshold"] == 10 and by_name["Def"]["margin"] == 1.5
    assert by_name["Mid"]["threshold"] == 12 and by_name["Mid"]["margin"] == 1.9


def test_goalkeepers_are_excluded():
    rows = defcon_reliability([
        player("Keeper", "GK", per90=20.0, minutes=3000),   # not DefCon-eligible
        player("Back", "DEF", per90=11.0, minutes=3000),
    ])
    assert {r["web_name"] for r in rows} == {"Back"}


def test_minutes_gate_excludes_small_samples():
    rows = defcon_reliability([
        player("Reg", "MID", per90=13.0, minutes=2500),
        player("Cameo", "MID", per90=30.0, minutes=200),   # huge rate, tiny sample
    ], min_minutes=900)
    assert {r["web_name"] for r in rows} == {"Reg"}


def test_sorted_by_margin_descending():
    rows = defcon_reliability([
        player("Low", "DEF", per90=10.5, minutes=3000),    # +0.5
        player("High", "DEF", per90=13.0, minutes=3000),   # +3.0
    ])
    assert [r["web_name"] for r in rows] == ["High", "Low"]


def test_none_per90_coerced_and_no_crash():
    rows = defcon_reliability([player("New", "DEF", per90=None, minutes=3000)])
    assert rows[0]["margin"] == -10.0     # 0 − 10


def test_render_shows_columns_and_caveat():
    rows = defcon_reliability([player("Anderson", "MID", per90=13.9, minutes=3000)])
    out = render_defcon(rows)

    assert "Anderson" in out
    assert "Margin" in out and "DC/90" in out
    assert "not a guaranteed" in out       # the reliability caveat


def test_render_empty_prompts_refresh():
    assert "refresh" in render_defcon([])
