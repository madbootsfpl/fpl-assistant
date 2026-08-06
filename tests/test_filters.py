"""Tests for the shared player filter's pure `apply` (ADR-064).

`filter_controls` (the Streamlit render) is covered by the AppTest suite; `apply` is the pure predicate
— AND across non-empty dimensions, tolerant of dict and sqlite3.Row rows.
"""

import sqlite3

from src.web_streamlit.filters import apply


def _p(name, team, pos, price=5.0):
    return {"web_name": name, "team": team, "position": pos, "price": price}


_ROWS = [_p("Haaland", "MCI", "FWD", 15.0), _p("Saka", "ARS", "MID", 10.0),
         _p("Gabriel", "ARS", "DEF", 6.0), _p("Isak", "NEW", "FWD", 10.5)]


def _sel(teams=(), positions=(), players=(), max_price=None):
    return {"teams": set(teams), "positions": set(positions),
            "players": set(players), "max_price": max_price}


def test_apply_empty_selection_keeps_all():
    assert apply(_ROWS, _sel()) == _ROWS


def test_apply_single_dimension():
    assert [r["web_name"] for r in apply(_ROWS, _sel(teams=["ARS"]))] == ["Saka", "Gabriel"]
    assert [r["web_name"] for r in apply(_ROWS, _sel(positions=["FWD"]))] == ["Haaland", "Isak"]


def test_apply_combines_with_and():
    # ARS ∧ FWD → nobody (Saka is MID, Gabriel is DEF)
    assert apply(_ROWS, _sel(teams=["ARS"], positions=["FWD"])) == []
    # ARS ∧ MID → Saka
    assert [r["web_name"] for r in apply(_ROWS, _sel(teams=["ARS"], positions=["MID"]))] == ["Saka"]


def test_apply_player_dimension_and_price():
    assert [r["web_name"] for r in apply(_ROWS, _sel(players=["Isak", "Haaland"]))] == ["Haaland", "Isak"]
    # max-price 11 drops Haaland (15.0); price absent → unaffected
    assert [r["web_name"] for r in apply(_ROWS, _sel(max_price=11.0))] == ["Saka", "Gabriel", "Isak"]


def test_apply_tolerates_sqlite_rows():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE p (web_name TEXT, team TEXT, position TEXT)")
    conn.executemany("INSERT INTO p VALUES (?,?,?)", [("Saka", "ARS", "MID"), ("Isak", "NEW", "FWD")])
    rows = conn.execute("SELECT * FROM p").fetchall()      # sqlite3.Row, no `price` column
    assert [r["web_name"] for r in apply(rows, _sel(teams=["ARS"]))] == ["Saka"]
    assert apply(rows, _sel(max_price=8.0)) == list(rows)  # no price column → price filter is a no-op
