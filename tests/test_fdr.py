"""Tests for the Fixture Difficulty (FDR) analytics."""

from src.analytics.fdr import team_fdr, team_schedule


def fixture(home, away, h_diff, a_diff, event=1,
            home_team_strength=None, away_team_strength=None):
    return {
        "event": event,
        "home": home,
        "away": away,
        "team_h_difficulty": h_diff,
        "team_a_difficulty": a_diff,
        "home_team_strength": home_team_strength,
        "away_team_strength": away_team_strength,
    }


def test_each_team_reads_its_own_difficulty_side():
    # One fixture, easy for the home team (2), hard for the away team (5).
    result = {r["team"]: r for r in team_fdr([fixture("ARS", "BUR", 2, 5)])}

    assert result["ARS"]["avg_difficulty"] == 2.0
    assert result["BUR"]["avg_difficulty"] == 5.0
    assert result["ARS"]["opponents"] == ["BUR"]
    assert result["BUR"]["opponents"] == ["ARS"]


def test_average_over_next_n_uses_correct_side_each_game():
    fixtures = [
        fixture("ARS", "X", 2, 3),   # ARS home → 2
        fixture("Y", "ARS", 3, 4),   # ARS away → 4
    ]
    ars = next(r for r in team_fdr(fixtures, next_n=2) if r["team"] == "ARS")

    assert ars["avg_difficulty"] == 3.0   # (2 + 4) / 2
    assert ars["games"] == 2


def test_ranked_easiest_first():
    ranked = team_fdr([fixture("EASY", "HARD", 1, 5)])

    assert ranked[0]["team"] == "EASY"
    assert ranked[-1]["team"] == "HARD"


def test_next_n_limits_the_window():
    fixtures = [
        fixture("ARS", "A", 1, 3),
        fixture("ARS", "B", 5, 3),
    ]
    ars = next(r for r in team_fdr(fixtures, next_n=1) if r["team"] == "ARS")

    assert ars["games"] == 1
    assert ars["avg_difficulty"] == 1.0   # only the first fixture counts


def test_undefined_when_no_valid_difficulty():
    ars = next(r for r in team_fdr([fixture("ARS", "X", None, 2)]) if r["team"] == "ARS")
    assert ars["avg_difficulty"] is None


def test_custom_fdr_uses_opponent_strength_at_their_venue():
    # ARS home (home strength 5) vs BUR away (away strength 2).
    fx = fixture(
        "ARS", "BUR", h_diff=2, a_diff=5,
        home_team_strength=5, away_team_strength=2,
    )

    result = {r["team"]: r for r in team_fdr([fx], source="custom")}

    # ARS faces BUR playing away → difficulty = BUR's away strength = 2.
    assert result["ARS"]["avg_difficulty"] == 2.0
    # BUR faces ARS playing home → difficulty = ARS's home strength = 5.
    assert result["BUR"]["avg_difficulty"] == 5.0


def test_fpl_is_the_default_source():
    # With FPL difficulties (2 home / 5 away) and different strengths, the default
    # source must use the FPL numbers, not the strengths.
    fx = fixture(
        "ARS", "BUR", h_diff=2, a_diff=5,
        home_team_strength=99, away_team_strength=99,
    )
    result = {r["team"]: r for r in team_fdr([fx])}
    assert result["ARS"]["avg_difficulty"] == 2.0   # team_h_difficulty
    assert result["BUR"]["avg_difficulty"] == 5.0   # team_a_difficulty


def test_team_schedule_reads_each_fixture_from_the_team_view():
    fixtures = [
        fixture("ARS", "BUR", 2, 5, event=1),   # ARS at home
        fixture("MCI", "ARS", 4, 3, event=2),   # ARS away
    ]

    sched = team_schedule(fixtures, "ARS")

    assert sched[0] == {"event": 1, "opponent": "BUR", "venue": "H", "difficulty": 2}
    assert sched[1] == {"event": 2, "opponent": "MCI", "venue": "A", "difficulty": 3}


def test_team_schedule_custom_source_uses_strength():
    # ARS home (home strength 5) vs BUR away (away strength 2).
    fx = fixture(
        "ARS", "BUR", h_diff=2, a_diff=5,
        home_team_strength=5, away_team_strength=2,
    )

    sched = team_schedule([fx], "ARS", source="custom")

    # ARS faces BUR playing away → custom difficulty = BUR's away strength = 2.
    assert sched[0]["difficulty"] == 2
    assert sched[0]["opponent"] == "BUR"
