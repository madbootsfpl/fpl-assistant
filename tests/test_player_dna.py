"""Tests for the Player DNA percentile engine (Sprint 168, ADR-118)."""

import sqlite3

from src.analytics.player_dna import (
    MIN_MINUTES,
    _per90,
    _percentile,
    _set_piece_score,
    player_dna,
    player_dna_this_or_last,
    player_gw_points,
)


def _p(pid, position, *, team="AAA", minutes=2000, xg=0.0, xa=0.0, ict_index=0.0,
       total_points=0, price=6.0, penalties_order=None, corners_order=None, freekicks_order=None,
       web_name=None):
    return {"id": pid, "web_name": web_name or f"p{pid}", "position": position, "team": team,
            "minutes": minutes, "xg": xg, "xa": xa, "ict_index": ict_index,
            "total_points": total_points, "price": price, "penalties_order": penalties_order,
            "corners_order": corners_order, "freekicks_order": freekicks_order}


def _axis(dna, label):
    return next(a for a in dna.axes if a.label == label)


# ---- the small helpers -------------------------------------------------------

def test_percentile_is_share_at_or_below():
    assert _percentile(10, [1, 2, 10]) == 100      # the top value → 100
    assert _percentile(1, [1, 2, 10]) == 33        # 1 of 3 at-or-below
    assert _percentile(5, []) is None              # no peers → unranked


def test_per90_scales_by_minutes_and_is_zero_safe():
    assert _per90(9.0, 900) == 0.9                 # 9 over 10×90 mins
    assert _per90(9.0, 0) == 0.0                   # no minutes → no divide-by-zero
    assert _per90(None, 900) == 0.0


def test_set_piece_score_orders_pen_taker_over_corner_over_none():
    pen = _set_piece_score(_p(1, "MID", penalties_order=1))
    corner = _set_piece_score(_p(2, "MID", corners_order=1))
    none = _set_piece_score(_p(3, "MID"))
    assert pen > corner > none == 0.0


# ---- the engine --------------------------------------------------------------

def test_top_scorer_lands_top_percentile_for_goal_threat():
    pool = [
        _p(1, "FWD", xg=25.0, minutes=2700, web_name="Elite"),   # the target — highest xG/90
        _p(2, "FWD", xg=8.0, minutes=2700),
        _p(3, "FWD", xg=2.0, minutes=2700),
    ]
    dna = player_dna(pool[0], pool)
    assert dna is not None
    assert _axis(dna, "Goal Threat").percentile == 100
    assert dna.pool_size == 3 and dna.low_minutes is False


def test_ranking_is_within_position_only():
    target = _p(1, "DEF", xg=5.0, minutes=2700)          # a high-xG defender
    pool = [
        target,
        _p(2, "DEF", xg=0.5, minutes=2700),              # peers: other defenders
        _p(3, "FWD", xg=30.0, minutes=2700),             # a forward — must NOT dilute the DEF ranking
    ]
    dna = player_dna(target, pool)
    assert dna.pool_size == 2                            # only the two defenders
    assert _axis(dna, "Goal Threat").percentile == 100   # top *among defenders*, ignoring the forward


def test_per90_beats_raw_volume():
    # Same xG, but the target played half the minutes → a higher xG/90 → higher percentile.
    target = _p(1, "MID", xg=6.0, minutes=900)
    other = _p(2, "MID", xg=6.0, minutes=1800)
    dna = player_dna(target, [target, other])
    assert _axis(dna, "Goal Threat").percentile == 100
    assert player_dna(other, [target, other]).axes[0].percentile == 50


def test_team_attack_ranks_across_teams():
    # CITY's forwards sum to more xG than TOWN's → a CITY player's Team Attack outranks a TOWN player's.
    players = [
        _p(1, "FWD", team="CITY", xg=20.0), _p(2, "MID", team="CITY", xg=10.0),
        _p(3, "FWD", team="TOWN", xg=3.0), _p(4, "MID", team="TOWN", xg=1.0),
    ]
    city = _axis(player_dna(players[0], players), "Team Attack")
    town = _axis(player_dna(players[2], players), "Team Attack")
    assert city.value == 30.0 and town.value == 4.0
    assert city.percentile == 100 and town.percentile == 50


def test_low_minute_target_is_flagged_but_still_ranked():
    target = _p(1, "FWD", xg=3.0, minutes=200, web_name="NewSigning")   # below the 450 floor
    peers = [_p(2, "FWD", xg=10.0, minutes=2700), _p(3, "FWD", xg=1.0, minutes=2700)]
    dna = player_dna(target, [target, *peers])
    assert dna.low_minutes is True
    assert dna.pool_size == 2                            # the target itself is not in the ranking pool
    assert _axis(dna, "Goal Threat").percentile is not None   # still gets a standing vs the peers


def test_no_position_returns_none():
    assert player_dna(_p(1, None), [_p(1, None)]) is None


def test_empty_pool_is_safe_and_unranked():
    # Only the target, and it is below the floor → no peers → per-player axes unranked, no crash.
    lonely = _p(1, "GK", minutes=100)
    dna = player_dna(lonely, [lonely])
    assert dna is not None and dna.pool_size == 0
    assert _axis(dna, "Goal Threat").percentile is None
    assert _axis(dna, "Team Attack").percentile == 100   # its own team is the only team → top


def test_accepts_sqlite3_row_not_just_dict():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cols = ("id", "web_name", "position", "team", "minutes", "xg", "xa", "ict_index",
            "total_points", "price", "penalties_order", "corners_order", "freekicks_order")
    con.execute(f"create table pl ({', '.join(cols)})")
    con.execute(
        f"insert into pl values ({', '.join('?' for _ in cols)})",
        (1, "Row", "FWD", "AAA", 2700, 20.0, 3.0, 250.0, 200, 10.0, 1, None, None))
    con.execute(
        f"insert into pl values ({', '.join('?' for _ in cols)})",
        (2, "Row2", "FWD", "AAA", 2700, 4.0, 1.0, 90.0, 80, 6.0, None, None, None))
    rows = con.execute("select * from pl").fetchall()
    con.close()

    dna = player_dna(rows[0], rows)                     # sqlite3.Row has no .get() — must not raise
    assert dna is not None and dna.name == "Row"
    assert _axis(dna, "Goal Threat").percentile == 100
    assert _axis(dna, "Set Pieces").value > 0           # the penalty taker


def test_min_minutes_default_is_the_documented_floor():
    assert MIN_MINUTES == 450


# ---- player_gw_points (the trend series, Sprint 171) -------------------------

def test_gw_points_is_empty_preseason():
    assert player_gw_points({}, 100) == []
    assert player_gw_points(None, 100) == []


def test_gw_points_orders_by_round_skips_nulls_and_limits():
    hist = {7: [{"round": 3, "total_points": 5}, {"round": 1, "total_points": 2},
                {"round": 2, "total_points": None}, {"round": 4, "total_points": 9}]}
    assert player_gw_points(hist, 7) == [(1, 2), (3, 5), (4, 9)]     # sorted, null round skipped
    assert player_gw_points(hist, 7, last=2) == [(3, 5), (4, 9)]     # most-recent N
    assert player_gw_points(hist, 999) == []                        # unknown code


# ---- last-season fallback for the peer pool (ADR-126, reported live 2026-08-24) ----
#
# The peer pool gates at 450 minutes, so for the first weeks of a season it is EMPTY — every per-player
# percentile came back None while Team Attack (ranked across team xG totals, no minutes gate) kept its own.
# The radar plotted `(percentile or 0)`, i.e. the centre, so seven vertices collapsed and the fingerprint
# became a single spike through Team Attack. That is what a user saw on the live app.

def _lp(pid, name, team="ARS", pos="MID", mins=2700, xg=8.0, xa=6.0, pts=180, price=9.0, ict=300.0):
    return {"id": pid, "web_name": name, "team": team, "position": pos, "minutes": mins,
            "xg": xg, "xa": xa, "total_points": pts, "price": price, "ict_index": ict,
            "penalties_order": None, "corners_order": None, "freekicks_order": None}


def test_this_season_cannot_rank_anyone_after_one_gameweek():
    """The precondition for the bug: one gameweek of minutes leaves the pool empty and every axis unranked."""
    pool = [_lp(i, f"P{i}", mins=90) for i in range(1, 12)]
    dna = player_dna(pool[0], pool)
    assert dna.pool_size == 0
    assert all(a.percentile is None for a in dna.axes if a.label != "Team Attack")


def test_falls_back_to_ranking_against_last_season():
    this = [_lp(i, f"P{i}", mins=90) for i in range(1, 12)]
    last = [_lp(i, f"P{i}", mins=2700, xg=float(i)) for i in range(1, 12)]
    dna, season = player_dna_this_or_last(this[9], this, last, "2025/26")
    assert season == "2025/26"
    assert dna.pool_size == 11
    assert all(a.percentile is not None for a in dna.axes)


def test_fallback_drops_the_axis_with_no_last_season_source():
    """FPL does not keep ICT in a player's season history, so Bonus Potential cannot be ranked from it. An axis
    every player scores 0 on would rank them all identically and read as real — dropping it is the honest move."""
    this = [_lp(i, f"P{i}", mins=90) for i in range(1, 12)]
    last = [{**_lp(i, f"P{i}", mins=2700), "ict_index": None} for i in range(1, 12)]
    dna, _ = player_dna_this_or_last(this[0], this, last, "2025/26")
    assert "Bonus Potl" not in [a.label for a in dna.axes]
    assert "Goal Threat" in [a.label for a in dna.axes]


def test_this_season_wins_once_it_can_rank():
    """The fallback retires itself — no flag to remember to turn off."""
    this = [_lp(i, f"P{i}", mins=900) for i in range(1, 12)]
    last = [_lp(i, f"P{i}", mins=2700) for i in range(1, 12)]
    dna, season = player_dna_this_or_last(this[0], this, last, "2025/26")
    assert season is None and dna.pool_size == 11


def test_no_last_season_row_leaves_the_player_honestly_unranked():
    """A player new to the league has nothing to fall back on. The card must say it cannot rank him, not
    invent a fingerprint — so no season is announced and the percentiles stay None."""
    this = [_lp(i, f"P{i}", mins=90) for i in range(1, 12)]
    dna, season = player_dna_this_or_last(this[0], this, [_lp(99, "Someone else")], "2025/26")
    assert season is None
    assert all(a.percentile is None for a in dna.axes if a.label != "Team Attack")
