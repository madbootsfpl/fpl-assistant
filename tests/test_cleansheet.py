"""Tests for the clean-sheet / defensive-solidity lens (xGC/90)."""

from src.analytics.cleansheet import defensive_solidity
from src.ui.cleansheet import render_cleansheet


def player(name, pos, xgc, minutes):
    return {"id": abs(hash(name)) % 100000, "web_name": name, "team": "ARS", "position": pos,
            "xgc": xgc, "minutes": minutes}


def test_xgc90_maths():
    # xgc 20 over 1800 mins → 20 * 90 / 1800 = 1.0
    rows = defensive_solidity([player("Def", "DEF", xgc=20.0, minutes=1800)])
    assert rows[0]["xgc90"] == 1.0


def test_sorted_ascending_lowest_is_best():
    rows = defensive_solidity([
        player("Leaky", "DEF", xgc=30.0, minutes=1800),   # 1.5
        player("Solid", "DEF", xgc=10.0, minutes=1800),   # 0.5
    ])
    assert [r["web_name"] for r in rows] == ["Solid", "Leaky"]


def test_only_def_and_gk():
    rows = defensive_solidity([
        player("Keeper", "GK", xgc=18.0, minutes=3000),
        player("Back", "DEF", xgc=20.0, minutes=3000),
        player("Mid", "MID", xgc=25.0, minutes=3000),     # excluded
        player("Fwd", "FWD", xgc=30.0, minutes=3000),     # excluded
    ])
    assert {r["web_name"] for r in rows} == {"Keeper", "Back"}


def test_minutes_gate_excludes_small_samples():
    rows = defensive_solidity([
        player("Reg", "DEF", xgc=15.0, minutes=2000),
        player("Cameo", "DEF", xgc=0.5, minutes=100),     # tiny sample, would rank "best"
    ], min_minutes=900)
    assert {r["web_name"] for r in rows} == {"Reg"}


def test_none_xgc_is_skipped_not_coerced_to_best():
    # A missing xGC must NOT compute to 0.0 and top the list.
    rows = defensive_solidity([
        player("Unknown", "DEF", xgc=None, minutes=3000),
        player("Known", "DEF", xgc=20.0, minutes=3000),
    ])
    assert [r["web_name"] for r in rows] == ["Known"]


def test_render_shows_columns_and_team_caveat():
    rows = defensive_solidity([player("Raya", "GK", xgc=27.4, minutes=3330)])
    out = render_cleansheet(rows)

    assert "Raya" in out and "xGC/90" in out
    assert "team" in out.lower()          # the team-level caveat


def test_render_empty_prompts_refresh():
    assert "refresh" in render_cleansheet([])


# ---- ADR-375/376: the defence he played behind -----------------------------

from src.analytics.cleansheet import (  # noqa: E402
    historical_cs_edge,
    league_cs_by_season,
    team_cs_from_fixtures,
    unpriced_defence,
    unpriced_defence_by_id,
)


def _season(name, clean_sheets, starts):
    return {"season_name": name, "clean_sheets": clean_sheets, "starts": starts}


def _fx(h, a, hs, as_):
    return {"team_h": h, "team_a": a, "team_h_score": hs, "team_a_score": as_}


def test_the_league_baseline_is_start_weighted_per_season():
    hist = {1: [_season("2024/25", 10, 40)], 2: [_season("2024/25", 2, 10)]}
    pos = {1: "DEF", 2: "DEF"}
    assert league_cs_by_season(hist, pos)["2024/25"] == 12 / 50     # not the mean of 0.25 and 0.20


def test_the_league_baseline_is_position_matched():
    """⭐ It is subtracted from DEF/GK figures, so it is computed over DEF/GK.

    Taken over every position it left a +0.04 pts/match residual that looked like signal and was a
    population mismatch — ⚠️ *a baseline measured on a different population than it is applied to is a bias
    with a plausible explanation attached.*
    """
    hist = {1: [_season("2024/25", 10, 40)], 2: [_season("2024/25", 0, 40)]}
    pos = {1: "DEF", 2: "FWD"}
    assert league_cs_by_season(hist, pos)["2024/25"] == 0.25        # the forward is not in the baseline


def test_a_season_he_did_not_start_carries_no_denominator():
    hist = {1: [_season("2024/25", 10, 40), _season("2023/24", 0, 0)]}
    assert set(league_cs_by_season(hist, {1: "DEF"})) == {"2024/25"}


def test_a_league_average_club_gives_an_edge_of_zero():
    """⭐⭐ The self-nulling property, and the whole reason the correction is era-relative.

    A player whose old club kept clean sheets at exactly its era's rate has nothing extra baked into his
    historical points — so the correction must collapse to today's behaviour for him. Without this the term
    is a level shift applied to one position (+0.23 pts/match across 187 DEF/GK, ADR-375).
    """
    league = {"2024/25": 0.25}
    assert historical_cs_edge([_season("2024/25", 10, 40)], league) == 0.0


def test_a_better_old_defence_is_a_positive_edge_and_a_worse_one_negative():
    league = {"2024/25": 0.25}
    assert historical_cs_edge([_season("2024/25", 20, 40)], league) == 0.25     # 0.50 against 0.25
    assert historical_cs_edge([_season("2024/25", 0, 40)], league) == -0.25


def test_no_comparable_season_is_none_rather_than_zero():
    # ⚠️ ADR-172 — an unknown must never read as a neutral one. None makes the caller fall back.
    assert historical_cs_edge([_season("2019/20", 5, 38)], {"2024/25": 0.25}) is None
    assert historical_cs_edge([], {"2024/25": 0.25}) is None


def test_clean_sheets_come_out_of_the_scorelines():
    # 2-0: home kept one, away did not. 1-1: neither.
    rates = team_cs_from_fixtures([_fx(1, 2, 2, 0), _fx(2, 1, 1, 1)])
    assert rates[1] == 0.5 and rates[2] == 0.0


def test_an_unplayed_fixture_is_silent_rather_than_a_clean_sheet():
    # ⚠️ ADR-125/129 — FPL carries the row before kick-off; a None score is not a 0-0.
    assert team_cs_from_fixtures([_fx(1, 2, None, None)]) == {}


def _defender(pid=7, team_id=1):
    return {"id": pid, "code": pid, "position": "DEF", "team_id": team_id, "web_name": "D"}


def test_the_doubt_is_what_a_mover_gains_net_of_what_he_already_carried():
    league = {"2024/25": 0.25}
    rows = [_season("2024/25", 10, 40)]                 # his old club was exactly league-average
    # now behind a 0.60 defence in a 0.30 league → 4 * (0.30 - 0.0) = 1.20
    assert unpriced_defence(_defender(), rows, 0.60, 0.30, league) == 1.2


def test_a_player_already_behind_a_good_defence_is_credited_far_less():
    league = {"2024/25": 0.25}
    rows = [_season("2024/25", 20, 40)]                 # he already kept 0.50, +0.25 on his era
    assert unpriced_defence(_defender(), rows, 0.60, 0.30, league) == 4 * (0.30 - 0.25)


def test_the_doubt_is_one_sided_and_never_argues_a_player_up():
    """⭐⭐ It exists to decline advising a sale, never to talk anyone into a purchase.

    An ungated correction is safe to act on only where being wrong costs nothing, and withholding advice
    is that place — so a negative figure clamps to zero rather than becoming a penalty.
    """
    league = {"2024/25": 0.25}
    rows = [_season("2024/25", 20, 40)]
    assert unpriced_defence(_defender(), rows, 0.10, 0.30, league) == 0.0


def test_outfield_players_and_unknown_baselines_carry_no_doubt():
    league = {"2024/25": 0.25}
    rows = [_season("2024/25", 10, 40)]
    fwd = {**_defender(), "position": "FWD"}
    assert unpriced_defence(fwd, rows, 0.60, 0.30, league) == 0.0
    assert unpriced_defence(_defender(), rows, None, 0.30, league) == 0.0        # club has not played
    assert unpriced_defence(_defender(), [], 0.60, 0.30, league) == 0.0          # no personal baseline


def test_the_builder_only_lists_players_with_a_positive_doubt():
    hist = {7: [_season("2024/25", 10, 40)], 8: [_season("2024/25", 30, 40)]}
    players = [_defender(7, team_id=1), _defender(8, team_id=1)]
    fixtures = [_fx(1, 2, 1, 0), _fx(1, 2, 2, 0), _fx(2, 1, 0, 0), _fx(2, 1, 3, 1)]
    out = unpriced_defence_by_id(players, hist, fixtures)
    assert 7 in out and 8 not in out      # 8's old defence was better than the one he is behind now
