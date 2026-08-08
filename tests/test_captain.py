"""Tests for captain suggestions (ADR-029).

Cover the decision-support rules: rank by xP, exclude goalkeepers, exclude the
hard-unavailable but keep doubtful (flagged), and annotate opponent/venue/penalty.
Offline, plain dicts.
"""

from src.analytics import captain_picks
from src.analytics.explain import Explanation
from src.ui.captain import render_captain_pick, render_captain_picks


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


def test_minutes_weight_demotes_a_rotation_risk_below_a_nailed_on_starter():
    # xMins v0 (ADR-038): P1 has the higher raw rate but is a rotation risk (weight 0.3);
    # P2 is nailed-on (1.0). Weighted, the nailed-on starter tops the list.
    players = [_player(1, "MID", 6.0), _player(2, "FWD", 5.0)]
    raw = captain_picks(players, FIXTURES)
    assert [p["web_name"] for p in raw] == ["P1", "P2"]        # unweighted: P1 first

    weight = lambda p: 0.3 if p["id"] == 1 else 1.0            # noqa: E731
    weighted = captain_picks(players, FIXTURES, minutes_weight=weight)
    assert [p["web_name"] for p in weighted] == ["P2", "P1"]   # weighted: nailed-on P2 first
    assert weighted[0]["minutes_weight"] == 1.0                # the weight is carried on the pick


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


def test_render_captain_pick_is_the_structured_card():
    # US-277 (ADR-089): the tester's "Captain Pick" mockup — medal · Team·Pos · Projected · Confidence ·
    # Why · Risks · Alternatives 🥈🥉 · Model note. The friendly team name comes from the short-code map.
    ranked = [
        {"web_name": "B.Fernandes", "team": "MUN", "position": "MID", "xp": 5.9},
        {"web_name": "Haaland", "team": "MCI", "position": "FWD", "xp": 5.7},
        {"web_name": "Rice", "team": "ARS", "position": "MID", "xp": 4.5},
    ]
    ex = Explanation(reasons=["Highest projected points", "Penalty taker"],
                     risks=["Away fixture", "Only +0.2 pts ahead of Haaland"], confidence=69, band="Medium")
    out = render_captain_pick(ranked, ex, scope="all players", team_names={"MUN": "Man Utd"})
    assert out.startswith("Captain Pick")
    assert "🥇 B.Fernandes" in out and "Man Utd · MID" in out and "Projected: 5.9 pts" in out
    assert "Confidence: 69/100 (Medium)" in out                 # clean line; the caveat is in the Model note
    assert "Why\n✓ Highest projected points" in out and "Risks\n⚠ Away fixture" in out
    assert "Alternatives\n🥈 Haaland 5.7 pts\n🥉 Rice 4.5 pts" in out
    assert "Model note:" in out and out.count("🥇") == 1


def test_render_captain_pick_is_empty_safe():
    ex = Explanation(reasons=["Highest projected points"], risks=[], confidence=80, band="High")
    solo = render_captain_pick([{"web_name": "Solo", "team": "ARS", "position": "FWD", "xp": 6.0}], ex)
    assert "Alternatives" not in solo                           # no runner-ups → no Alternatives section
    assert render_captain_pick([], None).startswith("No captain candidates")


def test_render_captain_picks_delegates_to_the_card_with_friendly_teams():
    # US-278: the CLI/web captain surface is now the same structured card, with a friendly team name and a
    # scope line; a squad name scopes it, and the runner-ups become the Alternatives.
    picks = [
        {"web_name": "B.Fernandes", "team": "MUN", "position": "MID", "xp": 5.9},
        {"web_name": "Haaland", "team": "MCI", "position": "FWD", "xp": 5.7},
    ]
    ex = Explanation(reasons=["Highest projected points"], risks=[], confidence=70, band="Medium")
    out = render_captain_picks(picks, squad_name="RoboTS", explanation=ex, team_names={"MUN": "Man Utd"})
    assert out.startswith("Captain Pick") and "from squad 'RoboTS'" in out
    assert "🥇 B.Fernandes" in out and "Man Utd · MID" in out
    assert "Alternatives\n🥈 Haaland 5.7 pts" in out and "Model note:" in out
    assert render_captain_picks([], squad_name="RoboTS").startswith("No captain candidates in squad")
