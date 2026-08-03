"""Tests for the clean-sheet / defensive-solidity lens (xGC/90)."""

from src.analytics.cleansheet import defensive_solidity
from src.ui.cleansheet import render_cleansheet


def player(name, pos, xgc, minutes):
    return {"web_name": name, "team": "ARS", "position": pos,
            "xgc": xgc, "minutes": minutes}


def test_xgc90_maths():
    # xgc 20 over 1800 mins → 20 * 90 / 1800 = 1.0
    rows = defensive_solidity([player("Def", "DEF", xgc=20.0, minutes=1800)])
    assert rows[0]["xgc90"] == 1.0


def test_sorted_ascending_lowest_is_best():
    rows = defensive_solidity([
        player("Leaky", "DEF", xgc=30.0, minutes=1800),   # 1.5
        player("Solid", "DEF", xgc=10.0, minutes=1800),   # 0.5
    ])
    assert [r["web_name"] for r in rows] == ["Solid", "Leaky"]


def test_only_def_and_gk():
    rows = defensive_solidity([
        player("Keeper", "GK", xgc=18.0, minutes=3000),
        player("Back", "DEF", xgc=20.0, minutes=3000),
        player("Mid", "MID", xgc=25.0, minutes=3000),     # excluded
        player("Fwd", "FWD", xgc=30.0, minutes=3000),     # excluded
    ])
    assert {r["web_name"] for r in rows} == {"Keeper", "Back"}


def test_minutes_gate_excludes_small_samples():
    rows = defensive_solidity([
        player("Reg", "DEF", xgc=15.0, minutes=2000),
        player("Cameo", "DEF", xgc=0.5, minutes=100),     # tiny sample, would rank "best"
    ], min_minutes=900)
    assert {r["web_name"] for r in rows} == {"Reg"}


def test_none_xgc_is_skipped_not_coerced_to_best():
    # A missing xGC must NOT compute to 0.0 and top the list.
    rows = defensive_solidity([
        player("Unknown", "DEF", xgc=None, minutes=3000),
        player("Known", "DEF", xgc=20.0, minutes=3000),
    ])
    assert [r["web_name"] for r in rows] == ["Known"]


def test_render_shows_columns_and_team_caveat():
    rows = defensive_solidity([player("Raya", "GK", xgc=27.4, minutes=3330)])
    out = render_cleansheet(rows)

    assert "Raya" in out and "xGC/90" in out
    assert "team" in out.lower()          # the team-level caveat


def test_render_empty_prompts_refresh():
    assert "refresh" in render_cleansheet([])
