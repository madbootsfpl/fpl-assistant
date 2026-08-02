"""Tests for the Expected Points (xP) analytics — the cross-domain join."""

from src.analytics.xp import player_xp
from src.ui.xp import render_xp_table


def player(team_id=1, ppg=5.0, status="a", ep_next=4.0, web_name="P",
           position="MID", team="ARS"):
    return {
        "team_id": team_id,
        "points_per_game": ppg,
        "status": status,
        "ep_next": ep_next,
        "web_name": web_name,
        "position": position,
        "team": team,
    }


def upcoming(team_h=1, team_a=2, home="ARS", away="BUR", h_diff=2, a_diff=5,
             event=1, home_team_strength=None, away_team_strength=None):
    return {
        "event": event,
        "team_h": team_h,
        "team_a": team_a,
        "home": home,
        "away": away,
        "team_h_difficulty": h_diff,
        "team_a_difficulty": a_diff,
        "home_team_strength": home_team_strength,
        "away_team_strength": away_team_strength,
    }


def test_xp_applies_the_fixture_multiplier():
    # ARS (team 1) home, difficulty 2 → ×1.1; ppg 5.0 → xP 5.5.
    result = player_xp([player(ppg=5.0)], [upcoming(h_diff=2)], source="fpl")
    assert result[0]["xp"] == 5.5


def test_xp_is_zero_when_unavailable():
    result = player_xp([player(status="i")], [upcoming(h_diff=2)])
    assert result[0]["xp"] == 0.0


def test_xp_is_zero_when_ppg_missing():
    result = player_xp([player(ppg=None)], [upcoming(h_diff=2)])
    assert result[0]["xp"] == 0.0


def test_xp_uses_the_next_fixture_only():
    # Team 1 has two upcoming fixtures; the first (diff 2) is used, not diff 5.
    fixtures = [upcoming(h_diff=2, event=1), upcoming(h_diff=5, event=2)]
    result = player_xp([player(ppg=5.0)], fixtures)
    assert result[0]["xp"] == 5.5


def test_xp_neutral_when_team_has_no_fixture():
    # Player's team (99) isn't in any fixture → neutral multiplier → xP = ppg.
    result = player_xp([player(team_id=99, ppg=5.0)], [upcoming()])
    assert result[0]["xp"] == 5.0


def test_xp_sorted_highest_first():
    players = [player(ppg=3.0, web_name="Low"), player(ppg=6.0, web_name="High")]
    result = player_xp(players, [upcoming(h_diff=3)])   # neutral ×1.0
    assert result[0]["web_name"] == "High"


def test_xp_custom_source_uses_strength():
    # ARS home; custom difficulty = BUR's away strength (2) → ×1.1, not FPL's 4.
    fixtures = [upcoming(h_diff=4, a_diff=4, away_team_strength=2, home_team_strength=5)]
    result = player_xp([player(ppg=5.0)], fixtures, source="custom")
    assert result[0]["xp"] == 5.5


def test_render_xp_table_empty():
    assert "run `refresh`" in render_xp_table([])


def test_render_xp_table_shows_xp_and_fpl_ep():
    rows = [{
        "web_name": "B.Fernandes", "team": "MUN", "position": "MID",
        "xp": 7.4, "ep_next": 4.0, "difficulty": 2,
    }]

    out = render_xp_table(rows, source="custom")

    assert "B.Fernandes" in out
    assert "7.4" in out          # our xP
    assert "4.0" in out          # FPL's ep_next
    assert "custom" in out       # source noted in the footer


def test_render_xp_table_handles_missing_ep():
    rows = [{
        "web_name": "X", "team": "ARS", "position": "MID",
        "xp": 3.0, "ep_next": None, "difficulty": None,
    }]
    out = render_xp_table(rows)
    assert "—" in out            # None ep_next / difficulty render as a dash
