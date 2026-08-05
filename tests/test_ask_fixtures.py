"""Tests for the fixtures / FDR `ask` intent (ADR-048).

Offline: routing + team resolution are pure; the two decision modes are exercised with a fake
store and `team_fdr`/`team_schedule` monkeypatched to canned rows (the underlying analytics are
tested elsewhere — here we test the mode selection, the hardest reversal, and the grounded facts).
"""

import types

from src import ask
from src.ask import _fixture_horizon, _match_team, route

_TEAMS = [
    {"name": "Arsenal", "short_name": "ARS"},
    {"name": "Man City", "short_name": "MCI"},
    {"name": "Newcastle", "short_name": "NEW"},
    {"name": "Liverpool", "short_name": "LIV"},
    {"name": "Spurs", "short_name": "TOT"},
]


# ---- routing ----------------------------------------------------------------

def test_routes_fixtures_questions():
    assert route("who has the best fixtures over the next 5?", known_squads=[])[0] == "fixtures"
    assert route("which teams have the hardest fixtures?", known_squads=[])[0] == "fixtures"
    assert route("when does Arsenal play next?", known_squads=[])[0] == "fixtures"
    assert route("who does Man City play?", known_squads=[])[0] == "fixtures"
    assert route("Liverpool schedule", known_squads=[])[0] == "fixtures"
    assert route("show me the fixture difficulty", known_squads=[])[0] == "fixtures"


def test_fixtures_is_last_so_specific_intents_still_win():
    assert route("who should I captain for TS?", known_squads=["TS"])[0] == "captain"
    assert route("best midfielders under 8m", known_squads=[])[0] == "shortlist"
    assert route("what transfer should I make for TS?", known_squads=["TS"])[0] == "transfer"


# ---- team resolution (never a wrong guess) ----------------------------------

def test_match_team_resolves_name_code_and_alias():
    assert _match_team("when does Arsenal play?", _TEAMS) == "ARS"       # full name
    assert _match_team("who does Man City play?", _TEAMS) == "MCI"       # multi-word name
    assert _match_team("fixtures for LIV", _TEAMS) == "LIV"              # a typed code
    assert _match_team("Tottenham schedule", _TEAMS) == "TOT"            # an alias


def test_match_team_never_guesses():
    assert _match_team("fixtures for the new gameweek", _TEAMS) is None  # 'new' ≠ the code NEW
    assert _match_team("who has the best fixtures?", _TEAMS) is None     # no team → league mode
    assert _match_team("Arsenal or Liverpool fixtures?", _TEAMS) == ["ARS", "LIV"]   # ambiguous


def test_fixture_horizon_parses_next_n_or_defaults():
    assert _fixture_horizon("best fixtures next 3") == 3
    assert _fixture_horizon("fixtures over the next 8 gameweeks") == 8
    assert _fixture_horizon("who has the best fixtures?") == 5           # default
    assert _fixture_horizon("fixtures for the next 99 weeks") == 38      # capped to a season


# ---- the two decision modes -------------------------------------------------

def _store():
    return types.SimpleNamespace(
        get_upcoming_fixtures=lambda: [object()],   # non-empty; the fakes ignore its contents
        get_teams=lambda: _TEAMS,
    )


def test_decide_fixtures_team_schedule_mode(monkeypatch):
    monkeypatch.setattr(ask, "team_schedule", lambda up, team, source="fpl": [
        {"event": 1, "opponent": "COV", "venue": "H", "difficulty": 2},
        {"event": 2, "opponent": "AVL", "venue": "A", "difficulty": 4},
    ])
    d = ask._decide_fixtures(_store(), "when does Arsenal play next?")
    assert d["subjects"] == ["ARS"]
    assert d["facts"]["average_difficulty"] == 3.0                       # (2 + 4) / 2
    assert "home vs COV" in d["facts"]["next_fixtures"][0]               # venue humanised
    assert "ARS" in d["detail"]


def test_decide_fixtures_league_ranking_easiest_then_hardest(monkeypatch):
    rows = [
        {"team": "LIV", "games": 5, "avg_difficulty": 2.6, "opponents": ["NEW", "NFO"]},
        {"team": "BOU", "games": 5, "avg_difficulty": 3.6, "opponents": ["MCI", "EVE"]},
    ]
    monkeypatch.setattr(ask, "team_fdr", lambda up, next_n=5, source="fpl": list(rows))
    easiest = ask._decide_fixtures(_store(), "who has the best fixtures over the next 5?")
    assert easiest["subjects"][0] == "LIV" and "easiest" in easiest["facts"]["ranking"]
    hardest = ask._decide_fixtures(_store(), "which teams have the hardest fixtures?")
    assert hardest["subjects"][0] == "BOU" and "hardest" in hardest["facts"]["ranking"]  # reversed


def test_decide_fixtures_ambiguous_team_asks_to_clarify():
    d = ask._decide_fixtures(_store(), "compare Arsenal and Liverpool fixtures")
    assert "More than one team" in d["message"] and "ARS" in d["message"] and "LIV" in d["message"]


def test_decide_fixtures_no_fixtures_returns_none():
    store = types.SimpleNamespace(get_upcoming_fixtures=lambda: [], get_teams=lambda: _TEAMS)
    assert ask._decide_fixtures(store, "best fixtures?") is None
