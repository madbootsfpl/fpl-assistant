"""Tests for squad triage and the squad grade (ADR-130).

The three design faults these pin were all found in a prototype against the live squad, before the code
existed: unknown reading as maximum risk, an absolute fixture scale that said nothing, and two incomparable
scales being naively compared.
"""

from src.analytics.squad_risk import (
    fixture_risk_by_team,
    minutes_risk,
    squad_dna,
    squad_edges,
    squad_risk_rows,
)


def _p(pid=1, code=1, team="AAA", pos="MID", name="P", chance=None, price=6.0, pens=None):
    return {"id": pid, "code": code, "team": team, "position": pos, "web_name": name,
            "status": "a", "chance": chance, "price": price, "penalties_order": pens}


def _gw(rnd, minutes, *, played=True):
    return {"round": rnd, "minutes": minutes, "total_points": 3,
            "team_h_score": 2 if played else None, "team_a_score": 0 if played else None}


def _season(starts, name="2025/26"):
    return {"season_name": name, "starts": starts, "minutes": starts * 90}


# ---- the minutes figure ------------------------------------------------------------

def test_unknown_is_none_not_maximum_risk():
    """The fault the prototype caught: a player new to the league scored 100% — no data rendered as worst
    case. He is not a certainty to be substituted; we cannot say."""
    risk, basis = minutes_risk(_p(), {}, {})
    assert risk is None and basis is None


def test_last_season_starts_are_the_base_rate_until_a_record_exists():
    risk, basis = minutes_risk(_p(), {}, {1: [_season(38)]})
    assert basis == "last season" and risk == 0.0          # started every game
    risk, _ = minutes_risk(_p(), {}, {1: [_season(19)]})
    assert risk == 0.5                                     # started half


def test_his_own_record_takes_over_once_there_are_enough_gameweeks():
    hist = {1: [_gw(r, 90 if r % 2 else 20) for r in range(1, 5)]}     # reached 60 in 2 of 4
    risk, basis = minutes_risk(_p(), hist, {1: [_season(38)]})
    assert basis == "record" and risk == 0.5


def test_a_short_record_still_defers_to_last_season():
    """One or two gameweeks is not a rate — a single blank would read as a 50% risk."""
    _, basis = minutes_risk(_p(), {1: [_gw(1, 90)]}, {1: [_season(38)]})
    assert basis == "last season"


def test_an_injury_flag_raises_the_risk_on_either_basis():
    healthy, _ = minutes_risk(_p(), {}, {1: [_season(38)]})
    doubtful, _ = minutes_risk(_p(chance=25), {}, {1: [_season(38)]})
    assert doubtful > healthy


def test_an_unplayed_gameweek_never_counts_as_a_miss():
    """A fixture that hasn't kicked off is not a failure to reach 60 (ADR-125/129)."""
    hist = {1: [_gw(r, 90) for r in range(1, 5)] + [_gw(5, 0, played=False)]}
    risk, _ = minutes_risk(_p(), hist, {})
    assert risk == 0.0


# ---- fixture risk is relative ------------------------------------------------------

def _fx(event, home, away, hd, ad):
    ids = {"AAA": 1, "BBB": 2, "CCC": 3}
    return {"event": event, "team_h": ids[home], "team_a": ids[away], "home": home, "away": away,
            "team_h_difficulty": hd, "team_a_difficulty": ad}


def test_fixture_risk_is_a_percentile_across_the_league():
    """An absolute scale returned roughly the same middling number for everyone, so "Fixtures" won as the
    driver while saying nothing. Only a *relative* run is a reason to act."""
    up = [_fx(2, "AAA", "BBB", 5, 1), _fx(3, "AAA", "CCC", 5, 1)]
    risk = fixture_risk_by_team(up, next_n=2)
    assert risk["AAA"] > risk["BBB"]                      # AAA's run is the harder one
    assert 0.0 <= risk["AAA"] <= 1.0


# ---- the attention blend -----------------------------------------------------------

def test_minutes_and_fixtures_are_weighted_not_compared_directly():
    """The third fault: `max(probability, percentile)` let an ordinary 79th-percentile run swamp every
    player-level signal, so eight players tied and the list sorted by club."""
    up = [_fx(2, "AAA", "BBB", 5, 1), _fx(3, "AAA", "CCC", 5, 1)]
    owned = [_p(1, 1, "AAA", name="Nailed"), _p(2, 2, "AAA", name="Rotated")]
    hist = {1: [_season(38)], 2: [_season(10)]}
    rows = squad_risk_rows(owned, up, history=hist)
    assert [r["web_name"] for r in rows] == ["Rotated", "Nailed"]   # same club, sorted by the player signal
    assert rows[0]["driver"] == "Minutes"


def test_an_unassessed_player_is_scored_on_fixtures_alone():
    up = [_fx(2, "AAA", "BBB", 3, 3)]
    rows = squad_risk_rows([_p(1, 1, "AAA")], up, history={})
    assert rows[0]["minutes_risk"] is None and rows[0]["attention"] > 0
    assert rows[0]["driver"] == "Fixtures"


# ---- the squad grade ---------------------------------------------------------------

class _Axis:
    def __init__(self, label, percentile):
        self.label, self.percentile = label, percentile


class _DNA:
    def __init__(self, axes):
        self.axes = axes


def test_squad_bars_average_the_engines_percentiles():
    owned = [_p(1, 1, "AAA"), _p(2, 2, "BBB")]
    dna = {1: _DNA([_Axis("Goal Threat", 80), _Axis("Creativity", 60), _Axis("FPL Output", 90)]),
           2: _DNA([_Axis("Goal Threat", 40), _Axis("Creativity", 20), _Axis("FPL Output", 50)])}
    tdna = {"AAA": _DNA([_Axis("Clean-Sheet Potl", 70), _Axis("Fixture Strength", 30)]),
            "BBB": _DNA([_Axis("Clean-Sheet Potl", 50), _Axis("Fixture Strength", 10)])}
    out = squad_dna(owned, dna, tdna)
    assert out["bars"]["Attack"] == 50            # (80+60+40+20)/4
    assert out["bars"]["Defence"] == 60           # one vote per club: (70+50)/2
    assert out["grade"] in ("A+", "A", "B", "C", "D")


def test_a_club_counts_once_however_many_of_its_players_you_own():
    owned = [_p(1, 1, "AAA"), _p(2, 2, "AAA"), _p(3, 3, "BBB")]
    tdna = {"AAA": _DNA([_Axis("Fixture Strength", 90)]), "BBB": _DNA([_Axis("Fixture Strength", 10)])}
    assert squad_dna(owned, {}, tdna)["bars"]["Fixtures"] == 50     # not 63


def test_an_unmeasurable_bar_is_none_rather_than_zero():
    out = squad_dna([_p()], {}, {})
    assert out["bars"]["Attack"] is None and out["grade"] == "—"


def test_edges_are_grounded_in_counts():
    owned = [_p(i, i, "AAA", pens=1) for i in range(1, 4)]
    edges = squad_edges(owned)
    assert any("3 first-choice penalty takers" in e for e in edges)
    assert any("3 players from AAA" in e for e in edges)
