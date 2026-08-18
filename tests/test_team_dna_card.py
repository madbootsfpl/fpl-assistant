"""Tests for the Team DNA browse card (Sprint 172, US-419, ADR-119)."""

from src.analytics.team_dna import team_dna
from src.web_streamlit.team_dna_card import (
    fixtures_html,
    head_html,
    key_players_html,
    team_key_players,
)


def _p(team, position="MID", *, xg=0.0, xa=0.0, xgc=0.0, total_points=0, minutes=2000,
       xgi=0.0, selected_by=5.0, name=None):
    return {"id": id(name or team) % 100000, "web_name": name or f"{team}-p", "team": team,
            "position": position, "xg": xg, "xa": xa, "xgc": xgc, "xgi": xgi, "ict_index": 0.0,
            "total_points": total_points, "minutes": minutes, "price": 6.0, "penalties_order": None,
            "corners_order": None, "freekicks_order": None, "selected_by": selected_by}


def _fx(home, away, hd, ad, event=1):
    return {"event": event, "home": home, "away": away, "team_h_difficulty": hd, "team_a_difficulty": ad}


def _dna():
    players = [_p("CITY", "FWD", xg=25, total_points=200, xgi=27, name="Star"),
               _p("CITY", "GK", xgc=25, total_points=120),
               _p("TOWN", "FWD", xg=4, total_points=60), _p("TOWN", "GK", xgc=50, total_points=80)]
    return team_dna("CITY", players, [_fx("CITY", "TOWN", 2, 4)], team_names={"CITY": "Man City"}), players


def test_head_html_has_grade_radar_and_chips():
    dna, _ = _dna()
    html = head_html(dna)
    assert "Man City" in html and "Team DNA" in html
    assert f">{dna.grade}<" in html                    # the grade letter
    assert "<polygon" in html                          # the radar
    assert html.count('class="td-chip"') == 8          # a chip per axis


def test_grade_tone_reflects_the_grade():
    dna, _ = _dna()
    assert dna.grade in ("A+", "A")
    assert "#01fc7a" in head_html(dna)                  # A/A+ → green tone


def test_fixtures_html_tints_by_fdr_and_is_empty_safe():
    html = fixtures_html([(1, "BOU", "H", 2), (2, "ARS", "A", 4)])
    assert "GW1" in html and "BOU" in html and "GW2" in html
    assert fixtures_html([]) == ""


def test_key_players_helper_and_table():
    dna, players = _dna()
    kp = team_key_players(players, "CITY")
    assert kp and kp[0]["name"] == "Star"              # top by points
    assert kp[0]["xgi90"] > 0
    html = key_players_html(kp)
    assert "Star" in html and "xGI/90" in html
    assert key_players_html([]) == ""


def test_key_players_skips_low_minute_players():
    players = [_p("CITY", "FWD", total_points=200, minutes=2000, name="Reg"),
               _p("CITY", "MID", total_points=90, minutes=200, name="Fringe")]
    names = [p["name"] for p in team_key_players(players, "CITY")]
    assert "Reg" in names and "Fringe" not in names    # < 900 mins dropped
