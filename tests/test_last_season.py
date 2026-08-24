"""Tests for the last-season fallback behind the gated stat boards (ADR-126).

The three boards (over/under · clean sheets · DefCon) gate at 900 minutes, so they cannot answer until about
gameweek 10. Rather than move that gate — it is the Sprint 016 Meslier lesson, and moving it would fill the
boards with nonsense — last season's numbers are projected into *player* shape and fed to the same functions.
These pin that the projection is faithful, that every row belongs to the season the caller names, and that the
boards run on it unchanged.
"""

from src.analytics import last_season_name, last_season_rows
from src.analytics.cleansheet import defensive_solidity
from src.analytics.defcon import defcon_reliability
from src.analytics.overperf import over_under


def _player(pid=1, code=100, position="DEF", web_name="P", team="ARS"):
    return {"id": pid, "code": code, "web_name": web_name, "team": team, "position": position}


def _season(name="2025/26", minutes=2700, xg=1.0, xa=2.0, goals=3, assists=1, xgc=30.0, defcon=300):
    return {"season_name": name, "minutes": minutes, "expected_goals": xg, "expected_assists": xa,
            "goals_scored": goals, "assists": assists, "expected_goals_conceded": xgc,
            "defensive_contribution": defcon}


# ---- the season label --------------------------------------------------------------

def test_season_name_is_the_most_recent_stored():
    hist = {100: [_season("2023/24"), _season("2024/25")], 200: [_season("2025/26")]}
    assert last_season_name(hist) == "2025/26"


def test_season_name_is_none_without_history():
    assert last_season_name({}) is None and last_season_name(None) is None


# ---- the projection ----------------------------------------------------------------

def test_projection_maps_the_fields_the_boards_read():
    rows = last_season_rows([_player()], {100: [_season(minutes=1800, defcon=200)]})
    assert len(rows) == 1
    r = rows[0]
    assert (r["xg"], r["xa"], r["goals_scored"], r["assists"]) == (1.0, 2.0, 3, 1)
    assert r["xgc"] == 30.0 and r["minutes"] == 1800
    assert r["defcon_per90"] == 200 * 90 / 1800          # a season total becomes the rate the board wants


def test_projection_takes_identity_from_the_current_row_not_the_history():
    """A player shows under the club they play for now — that's the club being decided about. The consequence
    is that a *team* stat crosses a transfer, which is why the clean-sheet board carries a caveat."""
    rows = last_season_rows([_player(pid=7, web_name="Mover", team="BUR", position="DEF")],
                            {100: [_season()]})
    assert (rows[0]["id"], rows[0]["web_name"], rows[0]["team"]) == (7, "Mover", "BUR")


def test_projection_skips_a_player_whose_last_season_was_not_last_season():
    """The banner names one season, so every row must be from it. A player away from the league last year has an
    older row — using it would put a true number under a false label."""
    players = [_player(pid=1, code=100), _player(pid=2, code=200)]
    hist = {100: [_season("2025/26")], 200: [_season("2023/24"), _season("2024/25")]}
    rows = last_season_rows(players, hist)
    assert [r["id"] for r in rows] == [1]


def test_projection_skips_a_player_with_no_history_at_all():
    assert last_season_rows([_player()], {}) == []
    assert last_season_rows([_player()], None) == []


def test_projection_survives_zero_minutes_without_dividing_by_zero():
    rows = last_season_rows([_player()], {100: [_season(minutes=0, defcon=5)]})
    assert rows[0]["defcon_per90"] == 0.0


# ---- the boards run on it unchanged ------------------------------------------------

def test_the_three_boards_consume_the_projection_unchanged():
    """The whole design rests on this: the projection is the same mapping shape `get_players()` returns, so no
    board function needed a line changed to read last season."""
    players = [_player(pid=1, code=100, position="DEF"), _player(pid=2, code=200, position="MID")]
    hist = {100: [_season(minutes=2700, xgc=27.0, defcon=360)],
            200: [_season(minutes=2700, xgc=40.0, defcon=390)]}
    rows = last_season_rows(players, hist)

    assert [r["id"] for r in over_under(rows)]           # attacking board populated
    assert [r["xgc90"] for r in defensive_solidity(rows)] == [0.9]      # DEF only; 27 × 90 / 2700
    # DEF: 360×90/2700 = 12.0/90 vs a threshold of 10 → margin 2.0
    # MID: 390×90/2700 = 13.0/90 vs a threshold of 12 → margin 1.0
    assert [r["id"] for r in defcon_reliability(rows)] == [1, 2]


def test_the_minutes_gate_still_applies_to_last_season():
    """The fallback changes *which season* the board reads, never the 900-minute bar it reads it through — a
    cameo last season is as unreadable as a cameo this season (ADR-017/018)."""
    rows = last_season_rows([_player()], {100: [_season(minutes=200)]})
    assert rows and over_under(rows) == [] and defensive_solidity(rows) == []
