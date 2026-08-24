"""Tests for the Team DNA engine (Sprint 172, US-418, ADR-119)."""

import sqlite3

from src.analytics.team_dna import team_dna, team_dna_all, team_insights


def _p(team, position="MID", *, xg=0.0, xa=0.0, xgc=0.0, total_points=0, minutes=2000,
       penalties_order=None, name=None):
    return {"id": id(name or team) % 100000, "web_name": name or f"{team}-p", "team": team,
            "position": position, "xg": xg, "xa": xa, "xgc": xgc, "ict_index": 0.0,
            "total_points": total_points, "minutes": minutes, "price": 6.0,
            "penalties_order": penalties_order, "corners_order": None, "freekicks_order": None,
            "selected_by": 5.0}


def _fx(home, away, hd, ad, event=1):
    return {"event": event, "home": home, "away": away, "team_h_difficulty": hd, "team_a_difficulty": ad}


def _axis(dna, label):
    return next(a for a in dna.axes if a.label == label)


def _pool_and_fixtures():
    # Three teams: CITY (elite attack), WALL (elite defence), MINN (weak both).
    players = [
        # CITY — huge attacking output, leaky-ish
        _p("CITY", "FWD", xg=25, total_points=200), _p("CITY", "MID", xg=10, xa=12, total_points=180),
        _p("CITY", "GK", xgc=42, total_points=120),
        # WALL — miserly defence, modest attack
        _p("WALL", "FWD", xg=8, total_points=110), _p("WALL", "DEF", xa=2, total_points=140),
        _p("WALL", "GK", xgc=20, total_points=170),
        # MINN — weak everywhere
        _p("MINN", "FWD", xg=3, total_points=60), _p("MINN", "MID", xg=1, xa=2, total_points=55),
        _p("MINN", "GK", xgc=55, total_points=80),
    ]
    fixtures = [                                 # CITY easiest run, MINN hardest
        _fx("CITY", "MINN", 2, 5), _fx("WALL", "CITY", 3, 2), _fx("MINN", "WALL", 5, 3),
    ]
    return players, fixtures


def test_attacking_and_output_top_for_the_elite_team():
    players, fixtures = _pool_and_fixtures()
    city = team_dna("CITY", players, fixtures)
    assert _axis(city, "Attacking Threat").percentile == 100
    assert _axis(city, "FPL Output").percentile == 100
    assert city.grade in ("A+", "A")


def test_defensive_strength_inverts_low_xga_wins():
    players, fixtures = _pool_and_fixtures()
    wall = team_dna("WALL", players, fixtures)   # lowest keeper xGC (20)
    minn = team_dna("MINN", players, fixtures)   # highest keeper xGC (55)
    assert _axis(wall, "Defensive Strength").percentile == 100
    assert _axis(minn, "Defensive Strength").percentile < 100


def test_fixture_axis_rewards_the_easiest_run():
    players, fixtures = _pool_and_fixtures()
    city = team_dna("CITY", players, fixtures)   # difficulty 2 (home to MINN)
    assert _axis(city, "Fixture Strength").percentile == 100


def test_clean_sheet_blends_defence_and_fixtures():
    players, fixtures = _pool_and_fixtures()
    wall = team_dna("WALL", players, fixtures)
    cs = _axis(wall, "Clean-Sheet Potl").percentile
    d = _axis(wall, "Defensive Strength").percentile
    f = _axis(wall, "Fixture Strength").percentile
    assert cs == round((d + f) / 2)              # the documented blend


def test_grade_letters_span_the_teams():
    players, fixtures = _pool_and_fixtures()
    grades = {t: d.grade for t, d in team_dna_all(players, fixtures).items()}
    assert grades["CITY"] in ("A+", "A")
    assert grades["MINN"] in ("C", "D")          # weak everywhere → a low grade


def test_insights_are_grounded_and_flag_the_fixture_swing():
    players, fixtures = _pool_and_fixtures()
    minn = team_dna("MINN", players, fixtures)
    texts = " || ".join(i.text for i in team_insights(minn))
    assert "tough next-5" in texts.lower()       # MINN has the hardest run
    wall = team_dna("WALL", players, fixtures)
    assert any("Miserly defence" in i.text for i in team_insights(wall))


def test_empty_pool_is_safe():
    assert team_dna_all([], []) == {}
    assert team_dna("X", [], []) is None
    assert team_insights(None) == []


def test_team_names_map_is_used():
    players, fixtures = _pool_and_fixtures()
    city = team_dna("CITY", players, fixtures, team_names={"CITY": "Manchester City"})
    assert city.name == "Manchester City"
    assert team_dna("WALL", players, fixtures).name == "WALL"   # falls back to the short code


def test_accepts_sqlite3_rows():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cols = ("id", "web_name", "team", "position", "xg", "xa", "xgc", "ict_index", "total_points",
            "minutes", "price", "penalties_order", "corners_order", "freekicks_order", "selected_by")
    con.execute(f"create table pl ({', '.join(cols)})")
    for vals in [(1, "a", "CITY", "FWD", 25, 0, 0, 0, 200, 2700, 8.0, 1, None, None, 30.0),
                 (2, "g", "CITY", "GK", 0, 0, 30, 0, 120, 2700, 5.0, None, None, None, 10.0),
                 (3, "b", "TOWN", "FWD", 4, 0, 0, 0, 70, 2700, 6.0, None, None, None, 4.0),
                 (4, "h", "TOWN", "GK", 0, 0, 50, 0, 80, 2700, 4.5, None, None, None, 3.0)]:
        con.execute(f"insert into pl values ({', '.join('?' for _ in cols)})", vals)
    rows = con.execute("select * from pl").fetchall()
    con.close()
    dna = team_dna("CITY", rows, [_fx("CITY", "TOWN", 2, 4)])    # Row has no .get() — must not raise
    assert dna is not None and _axis(dna, "Attacking Threat").percentile == 100


# ---- the real clean-sheet rate + team form (ADR-128; ADR-119's tracked GW1 follow-up) ----

def _gk(code, team):
    return {"code": code, "team": team, "position": "GK", "web_name": f"gk{code}", "minutes": 2700,
            "xg": 0.0, "xa": 0.0, "xgc": 30.0, "total_points": 100, "selected_by": 5.0,
            "penalties_order": None, "corners_order": None, "freekicks_order": None}


def _played(rnd, cs, *, home=True, hs=2, as_=0):
    return {"round": rnd, "was_home": 1 if home else 0, "team_h_score": hs, "team_a_score": as_,
            "minutes": 90, "clean_sheets": cs, "total_points": 5}


def test_clean_sheet_axis_switches_from_the_proxy_to_what_actually_happened():
    players = [_gk(1, "AAA"), _gk(2, "BBB")]
    fixtures = [{"event": 2, "home": "AAA", "away": "BBB", "team_h_difficulty": 3, "team_a_difficulty": 3}]
    gw = {1: [_played(1, 1)], 2: [_played(1, 0, home=False)]}

    proxy = team_dna_all(players, fixtures)["AAA"]
    real = team_dna_all(players, fixtures, gw_history=gw)["AAA"]

    assert next(a for a in proxy.axes if a.label == "Clean-Sheet Potl").sublabel == "def + fix"
    axis = next(a for a in real.axes if a.label == "Clean-Sheet Potl")
    assert axis.sublabel == "actual" and axis.value == 100      # kept its one clean sheet


def test_a_team_that_has_not_played_keeps_the_proxy():
    """A club whose opener hasn't kicked off must not read 0% — it has conceded nothing and kept nothing."""
    players = [_gk(1, "AAA"), _gk(2, "BBB")]
    fixtures = [{"event": 2, "home": "AAA", "away": "BBB", "team_h_difficulty": 3, "team_a_difficulty": 3}]
    gw = {1: [_played(1, 1)]}                                    # only AAA has played

    dna = team_dna_all(players, fixtures, gw_history=gw)
    assert next(a for a in dna["BBB"].axes if a.label == "Clean-Sheet Potl").sublabel == "def + fix"


def test_no_gw_history_leaves_every_team_on_the_proxy():
    players = [_gk(1, "AAA"), _gk(2, "BBB")]
    fixtures = [{"event": 2, "home": "AAA", "away": "BBB", "team_h_difficulty": 3, "team_a_difficulty": 3}]
    dna = team_dna_all(players, fixtures, gw_history={})
    assert all(next(a for a in d.axes if a.label == "Clean-Sheet Potl").sublabel == "def + fix"
               for d in dna.values())
