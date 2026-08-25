"""Tests for the Team DNA browse card (Sprint 172, US-419, ADR-119)."""

from src.analytics.team_dna import team_dna, team_dna_all
from src.web_streamlit.team_dna_card import (
    fixtures_html,
    head_html,
    key_players_html,
    key_players_this_or_last,
    league_rows,
    team_key_players,
    your_teams_rows,
    your_teams_strip_html,
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
    # empty (early season — nobody has ~900 mins yet) → the heading + a "fills in" note, not a blank (2026-08-22)
    empty = key_players_html([])
    assert "Key players to target" in empty and "Fills in as the season plays" in empty


def test_key_players_skips_low_minute_players():
    players = [_p("CITY", "FWD", total_points=200, minutes=2000, name="Reg"),
               _p("CITY", "MID", total_points=90, minutes=200, name="Fringe")]
    names = [p["name"] for p in team_key_players(players, "CITY")]
    assert "Reg" in names and "Fringe" not in names    # < 900 mins dropped


# ---- the "Your teams" strip (US-420) -----------------------------------------

def _squad_pool():
    players = [
        _p("CITY", "FWD", xg=25, total_points=200, name="Haaland"), _p("CITY", "GK", xgc=25, total_points=120),
        _p("TOWN", "FWD", xg=3, total_points=60, name="Weak"), _p("TOWN", "GK", xgc=55, total_points=80),
    ]
    fixtures = [_fx("CITY", "TOWN", 2, 5)]
    return players, fixtures


def test_your_teams_rows_best_grade_first_with_your_players():
    players, fixtures = _squad_pool()
    all_dna = team_dna_all(players, fixtures)
    owned = [players[0], players[2]]                    # Haaland (CITY) + Weak (TOWN)
    rows = your_teams_rows(owned, all_dna)
    assert [r["team"] for r in rows] == ["CITY", "TOWN"]   # CITY grades higher → first
    assert rows[0]["players"] == "Haaland"
    assert rows[0]["grade"] in ("A+", "A") and rows[0]["att"] == 100


def test_your_teams_strip_html_has_a_row_per_club_with_dots():
    players, fixtures = _squad_pool()
    rows = your_teams_rows([players[0], players[2]], team_dna_all(players, fixtures))
    html = your_teams_strip_html(rows)
    assert "Your teams" in html
    assert html.count('class="yt-row"') == 2
    assert html.count('class="yt-dot"') == 6           # ATT/DEF/FIX × 2 clubs
    assert your_teams_strip_html([]) == ""


# ---- last-season fallback on the key-players table (ADR-126) -----------------------
#
# Ranking here needs ~900 minutes, so the table sat empty until about gameweek 10 — the same gate, and the same
# fix, as the three stat boards. `team_key_players` runs unchanged on the projection.

def _lp(name, team, pos="MID", pts=150, mins=2700, xgi=9.0, own=12.5):
    """A last-season row in `last_season_rows` shape."""
    return {"id": abs(hash(name)) % 9999, "web_name": name, "team": team, "position": pos,
            "minutes": mins, "total_points": pts, "xgi": xgi, "selected_by": own}


def test_key_players_falls_back_to_last_season_and_names_it():
    rows, season = key_players_this_or_last([], "ARS", [_lp("Saka", "ARS")], "2025/26")
    assert [r["name"] for r in rows] == ["Saka"]
    assert season == "2025/26"


def test_key_players_prefers_this_season_and_announces_nothing():
    this = [{"web_name": "Ødegaard", "team": "ARS", "position": "MID", "minutes": 1000,
             "total_points": 60, "xgi": 4.0, "selected_by": 8.0}]
    rows, season = key_players_this_or_last(this, "ARS", [_lp("Saka", "ARS")], "2025/26")
    assert [r["name"] for r in rows] == ["Ødegaard"] and season is None


def test_key_players_announces_nothing_when_there_is_no_last_season_either():
    """A promoted side whose players are new to the league — the 🌱 "fills in" note stands, and there is no
    season to name, so the caller must not print an empty label."""
    rows, season = key_players_this_or_last([], "SUN", [], "2025/26")
    assert rows == [] and season is None


def test_key_players_ranks_a_summer_signing_with_his_current_club():
    """The projection carries the *current* club, so a player who moved is ranked for the side he plays for
    now — which is the side a manager is deciding about."""
    rows, _ = key_players_this_or_last([], "BUR", [_lp("Mover", "BUR"), _lp("Stayer", "ARS")], "2025/26")
    assert [r["name"] for r in rows] == ["Mover"]


def test_key_players_html_shows_the_season_note_only_when_falling_back():
    with_note = key_players_html([{"name": "Saka", "pos": "MID", "xgi90": 0.6, "pts90": 6.4,
                                   "minpct": 65, "own": 10.1}], season="2025/26")
    without = key_players_html([{"name": "Saka", "pos": "MID", "xgi90": 0.6, "pts90": 6.4,
                                 "minpct": 65, "own": 10.1}])
    assert "2025/26" in with_note and "Ownership is current" in with_note
    assert "2025/26" not in without and "Ownership is current" not in without
    assert "Saka" in with_note and "Saka" in without


def test_key_players_html_keeps_the_empty_note_when_neither_season_has_rows():
    html = key_players_html([], season="2025/26")
    assert "Fills in as the season plays" in html and "<table" not in html


# ---- the league scan's fixture chips (ADR-134) --------------------------------------

class _Ax:
    def __init__(self, label, pct):
        self.label, self.percentile = label, pct


class _D:
    def __init__(self, team, grade="B", score=60, fix=50):
        self.team, self.name, self.grade, self.grade_score = team, team, grade, score
        self.axes = [_Ax("Attacking Threat", 70), _Ax("Defensive Strength", 60), _Ax("Fixture Strength", fix)]


def _cell(opp, venue="H", difficulty=3):
    return {"opponent": opp, "venue": venue, "difficulty": difficulty}


def test_the_scan_shows_the_next_three_fixtures_not_just_the_next_one():
    """One opponent says who's next; three say whether the run the FIX percentile claims looks like one."""
    rows = league_rows({"AAA": _D("AAA")}, {"AAA": [_cell("BBB"), _cell("CCC", "A"), _cell("DDD")]})
    html = your_teams_strip_html(rows)
    assert html.count('class="yt-fx"') == 3
    assert ">BBB<" in html and ">CCC<" in html and ">DDD<" in html


def test_the_chips_carry_venue_and_are_tinted_by_difficulty():
    """Tinting says more than the plain `CHE (A)` it replaced, and takes less width — which is what let three
    fixtures fit the column one text pair filled."""
    html = your_teams_strip_html(league_rows({"AAA": _D("AAA")},
                                             {"AAA": [_cell("BBB", "H", 2), _cell("CCC", "A", 5)]}))
    assert "<i>h</i>" in html and "<i>a</i>" in html
    assert html.count("background:") >= 2                  # each chip carries its own FDR colour


def test_a_single_fixture_cell_still_works():
    """Callers may pass one cell rather than a slice — the squad strip does."""
    rows = league_rows({"AAA": _D("AAA")}, {"AAA": _cell("BBB")})
    assert your_teams_strip_html(rows).count('class="yt-fx"') == 1


def test_a_club_with_no_fixtures_reads_as_a_dash():
    assert "—" in your_teams_strip_html(league_rows({"AAA": _D("AAA")}, {}))


def test_the_squad_strip_still_escapes_its_plain_text_column():
    """The league scan's trailing column is pre-rendered HTML; the squad strip's is player names, and a name
    with an ampersand must not be able to inject markup."""
    html = your_teams_strip_html([{"team": "AAA", "grade": "A", "att": 50, "dfc": 50, "fix": 50,
                                   "players": "A & <b>B</b>"}])
    assert "&amp;" in html and "<b>B</b>" not in html


def test_sorting_by_fixtures_puts_the_easiest_run_first():
    dna = {"AAA": _D("AAA", fix=20), "BBB": _D("BBB", fix=90)}
    assert [r["team"] for r in league_rows(dna, {}, sort_by="fixtures")] == ["BBB", "AAA"]
    assert [r["team"] for r in league_rows(dna, {}, sort_by="grade")][0] in ("AAA", "BBB")
