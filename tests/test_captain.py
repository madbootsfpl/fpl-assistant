"""Tests for captain suggestions (ADR-029).

Cover the decision-support rules: rank by xP, exclude goalkeepers, exclude the
hard-unavailable but keep doubtful (flagged), and annotate opponent/venue/penalty.
Offline, plain dicts.
"""

from src.analytics import captain_picks


def _player(pid, pos, ppg, team_id=1, status="a", pens=None, chance=None, code=None):
    return {"id": pid, "code": code, "web_name": f"P{pid}", "team": "ARS",
            "position": pos, "team_id": team_id, "points_per_game": ppg, "status": status,
            "ep_next": 1.0, "penalties_order": pens, "chance": chance}


def _fixture(event=1, home_id=1, away_id=2, home="ARS", away="CHE"):
    return {"event": event, "team_h": home_id, "team_a": away_id, "home": home, "away": away,
            "team_h_difficulty": 3, "team_a_difficulty": 3}


FIXTURES = [_fixture()]


def test_ranks_by_xp_and_annotates():
    players = [_player(1, "MID", 6.0, pens=1), _player(2, "FWD", 4.0)]
    picks = captain_picks(players, FIXTURES)
    assert [p["web_name"] for p in picks] == ["P1", "P2"]   # higher xP first
    top = picks[0]
    assert top["penalty_taker"] is True
    assert top["opponent"] == "CHE" and top["venue"] == "H"   # team 1 is home vs CHE


def test_goalkeepers_are_excluded():
    players = [_player(1, "GK", 9.0), _player(2, "MID", 5.0)]
    picks = captain_picks(players, FIXTURES)
    assert [p["web_name"] for p in picks] == ["P2"]   # the GK (higher xP) is dropped


def test_injured_excluded_but_doubtful_kept_and_flagged():
    players = [
        _player(1, "MID", 6.0, status="i"),              # injured → excluded
        _player(2, "FWD", 5.0, status="d", chance=75),   # doubtful → kept, flagged
    ]
    picks = captain_picks(players, FIXTURES)
    names = [p["web_name"] for p in picks]
    assert names == ["P2"]
    assert picks[0]["doubtful"] is True and picks[0]["chance"] == 75
    assert picks[0]["xp"] > 0        # doubtful still scores (not zeroed like `xp`)


def test_away_venue_and_opponent():
    # player on team 2 (the away side) → opponent is the home team, venue A
    players = [_player(1, "MID", 6.0, team_id=2)]
    picks = captain_picks(players, FIXTURES)
    assert picks[0]["opponent"] == "ARS" and picks[0]["venue"] == "A"


def test_limit_is_respected():
    players = [_player(i, "MID", 10 - i) for i in range(1, 6)]
    picks = captain_picks(players, FIXTURES, limit=3)
    assert len(picks) == 3
