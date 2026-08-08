"""Tests for the player-history view (Sprint 117, US-295, ADR-027/060).

`player_history` assembles stored rows into a display shape (pure, empty-safe); `render_player_history`
formats it. A read-view lens — never `decision_xp`.
"""

from src.analytics import align_seasons, player_history
from src.ui.history import render_player_history
from src.web_streamlit.views.players import _delta_cell

_PLAYER = {"web_name": "Haaland", "team": "MCI", "position": "FWD", "code": 1}
_SEASONS = [
    {"season_name": "2023/24", "total_points": 217, "minutes": 2553, "starts": 29,
     "expected_goal_involvements": 31.8, "expected_goals_conceded": 25.6,
     "start_cost": 14.0, "end_cost": 14.3},
    {"season_name": "2024/25", "total_points": 181, "minutes": 2736, "starts": 31,
     "expected_goal_involvements": 23.9, "expected_goals_conceded": 41.3,
     "start_cost": 15.0, "end_cost": 14.9},
]
_GWS = [{"round": 1, "total_points": 13, "minutes": 90},
        {"round": 2, "total_points": 2, "minutes": 78}]


def test_player_history_assembles_seasons_and_gameweeks_with_pp90():
    h = player_history(_PLAYER, _SEASONS, _GWS)
    assert h["player"]["web_name"] == "Haaland"
    assert [s["season"] for s in h["seasons"]] == ["2023/24", "2024/25"]
    assert h["seasons"][0]["pp90"] == round(217 / (2553 / 90), 1)      # points per 90 minutes
    assert [g["round"] for g in h["gameweeks"]] == [1, 2]


def test_player_history_carries_price_and_change():
    # US-297: the price columns (already £m) + the season's ± change.
    s = player_history(_PLAYER, _SEASONS, [])["seasons"]
    assert s[0]["start_cost"] == 14.0 and s[0]["end_cost"] == 14.3 and s[0]["change"] == 0.3
    assert s[1]["change"] == round(14.9 - 15.0, 1)                     # a fall → negative
    # empty-safe: a missing cost → change None (no crash), and the renderer shows "—"
    missing = player_history(_PLAYER, [{"season_name": "2020/21", "total_points": 5, "minutes": 90}], [])
    assert missing["seasons"][0]["change"] is None
    assert "—" in render_player_history(missing)


def test_delta_cell_colours_the_price_move():
    # US-311: the web Δ£ cell gains an up/down cue — 🟢 rise, 🔴 fall, plain for flat/unknown.
    assert _delta_cell(0.3) == "+0.3 🟢"
    assert _delta_cell(-0.4) == "−0.4 🔴"        # a real minus sign
    assert _delta_cell(0.0) == "0.0"
    assert _delta_cell(None) == "—"


def test_align_seasons_outer_joins_on_the_season_label():
    # US-312: two players' seasons align on the label; a season only one played → None for the other.
    a = {"seasons": [{"season": "2022/23", "points": 200}, {"season": "2023/24", "points": 226}]}
    b = {"seasons": [{"season": "2023/24", "points": 180}, {"season": "2024/25", "points": 150}]}
    assert align_seasons(a, b, key="points") == [
        {"season": "2022/23", "a": 200, "b": None},          # only A played
        {"season": "2023/24", "a": 226, "b": 180},           # both
        {"season": "2024/25", "a": None, "b": 150},          # only B played
    ]


def test_align_seasons_is_empty_safe():
    assert align_seasons({"seasons": []}, {"seasons": []}) == []
    assert align_seasons({}, {}) == []


def test_player_history_is_empty_safe():
    h = player_history(_PLAYER, [], [])
    assert h["seasons"] == [] and h["gameweeks"] == []
    assert player_history(_PLAYER, None, None)["seasons"] == []        # None → empty, no crash
    assert player_history(_PLAYER, [{"minutes": 0}], [])["seasons"][0]["pp90"] == 0.0   # no minutes → 0, no /0


def test_render_shows_season_table_and_a_gw1_note_when_no_gameweeks():
    out = render_player_history(player_history(_PLAYER, _SEASONS, []))
    assert "History — Haaland (MCI, FWD)" in out and "Past seasons" in out
    assert "2023/24" in out and "217" in out and "Pts/90" in out       # the season table + its columns
    assert "£14.0→14.3" in out                                         # US-297: the price column
    assert "fills once the season starts (GW1)" in out                 # per-GW dormant note


def test_render_shows_the_per_gw_trend_when_present():
    out = render_player_history(player_history(_PLAYER, _SEASONS, _GWS))
    assert "per gameweek (2 played)" in out and "GW" in out            # the trend block
    assert "fills once the season starts" not in out


def test_render_degrades_for_no_player_or_no_history():
    assert "Name a player" in render_player_history({"player": None, "seasons": [], "gameweeks": []})
    empty = render_player_history(player_history(_PLAYER, [], []))
    assert "No history stored for Haaland" in empty and "history --backfill" in empty
