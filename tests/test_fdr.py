"""Tests for the Fixture Difficulty (FDR) analytics."""

from src.analytics.fdr import elo_difficulty_bands, fixture_ticker, team_fdr, team_schedule


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


def test_fixture_ticker_grid_shape_and_ordering():
    # Sprint 062: a teams × gameweeks grid, easiest-first, with per-GW opponent/venue/difficulty cells.
    fixtures = [
        fixture("EASY", "HARD", 1, 5, event=1),   # EASY home GW1 (diff 1); HARD away GW1 (diff 5)
        fixture("MID", "EASY", 3, 2, event=2),    # EASY away GW2 (diff 2); MID home GW2 (diff 3)
    ]
    t = fixture_ticker(fixtures, next_n=2)
    assert t["gameweeks"] == [1, 2]
    assert t["rows"][0]["team"] == "EASY"                     # easiest run first
    easy = t["rows"][0]["cells"]
    # `fixtures` (the full list for the gameweek) was added by ADR-129 so a double shows both matches.
    assert {k: easy[1][k] for k in ("event", "opponent", "venue", "difficulty")} == \
        {"event": 1, "opponent": "HARD", "venue": "H", "difficulty": 1}
    assert easy[2]["opponent"] == "MID" and easy[2]["venue"] == "A"


def test_fixture_ticker_blank_gameweek_is_none():
    # a team with no fixture in a listed gameweek → a None cell (a blank GW), no crash
    t = fixture_ticker([fixture("A", "B", 2, 2, event=1)], next_n=2)
    # only GW1 exists in the data, so next_n=2 yields just [1]; every team has a cell for it
    assert t["gameweeks"] == [1]
    assert all(row["cells"][1] is not None for row in t["rows"])


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


def test_elo_bands_rank_strongest_as_5_and_weakest_as_1():
    from collections import Counter
    teams = [{"short_name": f"T{i}", "elo": 1500 + i * 50} for i in range(20)]  # T19 strongest

    bands = elo_difficulty_bands(teams)

    assert bands["T0"] == 1     # weakest Elo → easiest to face
    assert bands["T19"] == 5    # strongest Elo → hardest to face
    assert all(count == 4 for count in Counter(bands.values()).values())   # 4 per band


def test_elo_bands_omit_teams_without_elo():
    bands = elo_difficulty_bands(
        [{"short_name": "A", "elo": 2000.0}, {"short_name": "B", "elo": None}]
    )
    assert "A" in bands and "B" not in bands


def test_team_fdr_elo_source_uses_the_opponents_band():
    fx = fixture("ARS", "BUR", h_diff=2, a_diff=2, event=1)   # FPL diffs irrelevant here
    bands = {"ARS": 1, "BUR": 5}

    result = {r["team"]: r for r in team_fdr([fx], source="elo", elo_bands=bands)}

    assert result["ARS"]["avg_difficulty"] == 5.0   # ARS faces BUR (band 5)
    assert result["BUR"]["avg_difficulty"] == 1.0   # BUR faces ARS (band 1)


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


# ---- doubles in the ticker (ADR-129 audit) ----------------------------------------

def _tick_fx(event, home, away, hd=3, ad=3, i=0):
    ids = {"AAA": 1, "BBB": 2, "CCC": 3, "DDD": 4}
    return {"event": event, "team_h": ids[home], "team_a": ids[away], "home": home, "away": away,
            "team_h_difficulty": hd, "team_a_difficulty": ad,
            "kickoff_time": f"2026-09-0{event}T12:0{i}:00Z"}


def test_ticker_shows_both_fixtures_of_a_double_gameweek():
    """It used to keep only the first, so the one view built for spotting doubles was the one place a double
    was invisible — a blank showed as an empty cell while a double looked like an ordinary week."""
    up = [_tick_fx(2, "AAA", "BBB"), _tick_fx(3, "AAA", "CCC", i=1), _tick_fx(3, "DDD", "AAA", i=2)]
    row = next(r for r in fixture_ticker(up, next_n=2)["rows"] if r["team"] == "AAA")
    cell = row["cells"][3]
    assert [f["opponent"] for f in cell["fixtures"]] == ["CCC", "DDD"]


def test_a_double_is_shaded_by_its_harder_half():
    """The cell carries one colour, and a double is only as easy as its harder match."""
    up = [_tick_fx(3, "AAA", "CCC", hd=2, i=1), _tick_fx(3, "DDD", "AAA", ad=5, i=2)]
    row = next(r for r in fixture_ticker(up, next_n=1)["rows"] if r["team"] == "AAA")
    assert row["cells"][3]["difficulty"] == 5


def test_a_single_fixture_gameweek_still_reads_as_before():
    up = [_tick_fx(2, "AAA", "BBB", hd=4)]
    cell = next(r for r in fixture_ticker(up, next_n=1)["rows"] if r["team"] == "AAA")["cells"][2]
    assert cell["opponent"] == "BBB" and cell["venue"] == "H" and cell["difficulty"] == 4
    assert len(cell["fixtures"]) == 1


def test_a_blank_gameweek_is_still_none():
    up = [_tick_fx(2, "AAA", "BBB"), _tick_fx(3, "BBB", "CCC")]
    row = next(r for r in fixture_ticker(up, next_n=2)["rows"] if r["team"] == "AAA")
    assert row["cells"][3] is None
