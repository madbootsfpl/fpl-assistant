"""Tests for the expected-goals (xG / xA / xGI) view."""

from src.ui.xg import render_xg_table


def _row(name, xg, xa, xgi, xgc, team="ARS", position="FWD"):
    return {"web_name": name, "team": team, "position": position,
            "xg": xg, "xa": xa, "xgi": xgi, "xgc": xgc}


def test_render_xg_shows_columns_and_values():
    rows = [_row("Haaland", 25.5, 2.7, 28.2, 38.6)]
    out = render_xg_table(rows)

    assert "xGI" in out and "xG" in out and "xA" in out and "xGC" in out
    assert "Haaland" in out
    assert "28.2" in out          # xGI value shown

def test_render_xg_shows_an_availability_fit_flag():
    # US-235 (ADR-074) + US-276: the xg table's Fit column — 🚑 injured, ✅ available
    hurt = {**_row("Hurt", 5.0, 1.0, 6.0, 10.0), "status": "i", "chance": 0}
    fit = {**_row("Ready", 6.0, 1.0, 6.0, 10.0), "status": "a"}
    out = render_xg_table([hurt, fit])
    assert "Fit" in out and "🚑" in out and "✅" in out


def test_render_xg_respects_the_limit():
    rows = [_row(f"P{i}", i, 0, i, 0) for i in range(30)]
    out = render_xg_table(rows, limit=5)
    assert "top 5 of 30" in out


def test_render_xg_coerces_none_to_zero():
    rows = [_row("New", None, None, None, None)]
    out = render_xg_table(rows)
    assert "0.0" in out           # None → 0.0, no crash


def test_render_xg_empty_prompts_refresh():
    assert "refresh" in render_xg_table([])
