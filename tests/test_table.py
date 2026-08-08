"""Tests for the console player-table renderer."""

from src.ui.table import render_player_table


def sample_rows(n: int = 3) -> list[dict]:
    return [
        {
            "web_name": f"Player{i}",
            "team": "ARS",
            "position": "MID",
            "price": 7.5,
            "total_points": 100 - i,
            "value": (100 - i) / 7.5,
        }
        for i in range(n)
    ]


def test_empty_rows_returns_message():
    assert render_player_table([]) == "No players to display."


def test_table_has_header_and_rows():
    out = render_player_table(sample_rows(3))

    assert "Player" in out and "Team" in out and "Pts" in out
    assert "Val/£m" in out
    assert "Player0" in out
    assert "£7.5m" in out
    assert "Showing all 3 players." in out


def test_table_shows_an_availability_fit_flag():
    # US-235 (ADR-074) + US-276: the CLI table's Fit column — 🚑 injured, ✅ available
    rows = [
        {"web_name": "Hurt", "team": "ARS", "position": "DEF", "price": 5.0,
         "total_points": 50, "value": 10.0, "status": "i", "chance": 0},
        {"web_name": "Ready", "team": "ARS", "position": "MID", "price": 6.0,
         "total_points": 60, "value": 10.0, "status": "a", "chance": None},
    ]
    out = render_player_table(rows)
    assert "Fit" in out and "🚑" in out               # the header + the injured flag
    assert "✅" in out                                # US-276: the fit player reads ✅, not blank


def test_undefined_value_renders_as_dash():
    rows = [
        {
            "web_name": "NoPrice",
            "team": "ARS",
            "position": "MID",
            "price": 0.0,
            "total_points": 0,
            "value": None,
        }
    ]
    out = render_player_table(rows)
    assert "—" in out


def test_limit_is_respected():
    out = render_player_table(sample_rows(30), limit=20)

    assert "Player19" in out       # the 20th row is shown
    assert "Player20" not in out   # the 21st row is not
    assert "Showing top 20 of 30 players." in out
