"""Tests for the walk-forward calibration harness (ADR-101, US-340).

All synthetic — real returns don't exist until the season runs (GW4–6+). These pin the *mechanics*: the metrics,
the no-leakage walk-forward, and the sweep's best-value selection (incl. the smaller-weight-on-a-flat-curve guard).
"""

import sqlite3

import pytest

from src.analytics import backtest

# --- metrics ------------------------------------------------------------------------

def test_rank_handles_ties():
    assert backtest._rank([10, 20, 20, 30]) == [1.0, 2.5, 2.5, 4.0]


def test_spearman_perfect_and_reversed():
    assert backtest.spearman([1, 2, 3, 4], [1, 2, 3, 4]) == pytest.approx(1.0)
    assert backtest.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_spearman_is_rank_based_not_value_based():
    # a monotone but non-linear map still ranks perfectly → ρ = 1
    assert backtest.spearman([1, 2, 3, 4], [1, 4, 9, 16]) == pytest.approx(1.0)


def test_spearman_none_without_spread_or_points():
    assert backtest.spearman([5, 5, 5], [1, 2, 3]) is None        # no spread in preds
    assert backtest.spearman([1], [1]) is None                    # < 2 points


def test_mae_is_exact():
    assert backtest.mae([(3, 1, 1), (0, 4, 1)]) == 3.0            # |3-1| + |0-4| = 6, /2


def test_hit_rate_top_n_overlap():
    # one GW, 4 players; top-2 predicted vs top-2 actual
    triples = [(9, 8, 1), (7, 2, 1), (1, 6, 1), (0, 0, 1)]        # preds rank [0,1,2,3]; actuals [0,2,1,3]
    assert backtest.hit_rate(triples, n=2) == 0.5                 # {p0,p1} ∩ {p0,p2} = {p0} → 1/2


def test_mean_gw_spearman_averages_per_gameweek():
    gw1 = [(1, 1, 1), (2, 2, 1), (3, 3, 1)]                       # ρ = 1
    gw2 = [(1, 3, 2), (2, 2, 2), (3, 1, 2)]                       # ρ = -1
    assert backtest.mean_gw_spearman(gw1 + gw2) == pytest.approx(0.0)   # mean(1, -1)


# --- walk-forward: no leakage -------------------------------------------------------

def _history(points_by_code):
    """{code: {round: total_points}} → the gw_history_by_code shape (rows with round + total_points)."""
    return {code: [{"round": rnd, "total_points": pts} for rnd, pts in sorted(rounds.items())]
            for code, rounds in points_by_code.items()}


def test_pairs_never_leak_future_rounds():
    hist = _history({10: {1: 2, 2: 5, 3: 8, 4: 1}, 20: {1: 6, 2: 6, 3: 0, 4: 9}})
    seen_max_round = []

    def predict(before, n):
        # record the newest round the predictor was allowed to see for this N
        rounds_seen = [r["round"] for rows in before.values() for r in rows]
        seen_max_round.append((n, max(rounds_seen) if rounds_seen else None))
        return {code: 0.0 for code in before}                    # value irrelevant here

    backtest.pairs(hist, predict)
    for n, seen in seen_max_round:
        assert seen is None or seen < n                          # only rounds strictly before N


def test_pairs_builds_predicted_actual_triples():
    hist = _history({10: {1: 2, 2: 5}, 20: {1: 6, 2: 6}})
    triples = backtest.pairs(hist, lambda before, n: {10: 1.0, 20: 2.0})
    # rounds 1 and 2 each pair both codes with their actuals
    assert (1.0, 2, 1) in triples and (2.0, 6, 1) in triples
    assert (1.0, 5, 2) in triples and (2.0, 6, 2) in triples


# --- the sweep ----------------------------------------------------------------------

_ACTUALS = {c: {r: (c * 10 + r) for r in range(1, 6)} for c in range(1, 8)}   # 7 codes × 5 rounds (≥ MIN_GWS)
_HIST = _history(_ACTUALS)


def test_sweep_reports_insufficient_below_min_gws():
    thin = _history({1: {1: 3, 2: 4, 3: 5}})                     # only 3 rounds
    out = backtest.sweep(thin, lambda v: (lambda before, n: {}), [0.0, 0.1], min_gws=4)
    assert out["insufficient"] is True and out["gws"] == 3 and out["best"] is None


def test_sweep_picks_the_best_weight():
    # predictions rank-match the actuals exactly when v == 0.3, and get distorted as |v-0.3| grows
    def make_predict(v):
        d = abs(v - 0.3)

        def predict(before, n):
            return {c: _ACTUALS[c][n] - d * 1000 * (c % 2) for c in _ACTUALS}   # distortion flips ranks as d grows
        return predict

    out = backtest.sweep(_HIST, make_predict, [0.0, 0.1, 0.2, 0.3, 0.4, 0.5])
    assert out["insufficient"] is False and out["gws"] == 5
    assert out["best"] == 0.3                                    # ρ peaks at the undistorted value


def test_sweep_prefers_the_smaller_weight_on_a_flat_curve():
    # identical predictions regardless of v → identical ρ → the guard picks the smallest weight
    def flat(v):
        return lambda before, n: {c: _ACTUALS[c][n] for c in _ACTUALS}
    out = backtest.sweep(_HIST, flat, [0.0, 0.1, 0.2, 0.3])
    assert out["best"] == 0.0


# --- sqlite3.Row inputs (the shape the CLI actually passes) -------------------------
#
# Every test above hands the harness plain dicts. The CLI hands it `sqlite3.Row`s, which index but have no
# `.get` — so `rounds_with_actuals` raised AttributeError on the first real per-GW history that reached it.
# It stayed hidden all preseason because `gw_history_by_code` was empty and the loop body never ran; the GW1
# backfill is what executed it for the first time. These pin the real row type, not a stand-in for it.

def _rows(triples):
    """Real `sqlite3.Row` objects — a stand-in dict would not reproduce the bug these tests exist for."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE h (code INTEGER, round INTEGER, total_points INTEGER)")
    con.executemany("INSERT INTO h VALUES (?, ?, ?)", triples)
    return con.execute("SELECT * FROM h ORDER BY code, round").fetchall()


def test_rounds_with_actuals_accepts_sqlite_rows():
    rows = _rows([(7, 1, 14), (7, 2, 3), (9, 1, 2)])
    by_code = {7: [r for r in rows if r["code"] == 7], 9: [r for r in rows if r["code"] == 9]}
    assert backtest.rounds_with_actuals(by_code) == [1, 2]


def test_rounds_with_actuals_skips_rows_without_points_on_sqlite_rows():
    rows = _rows([(7, 1, 5), (7, 2, None)])       # GW2 fixture played but not yet scored
    assert backtest.rounds_with_actuals({7: rows}) == [1]


def test_pairs_walks_forward_over_sqlite_rows():
    rows = _rows([(7, 1, 10), (7, 2, 4)])
    seen = {}

    def predict(before, n):
        seen[n] = sum(len(v) for v in before.values())   # how many rounds the predictor was shown
        return {7: 5.0}

    out = backtest.pairs({7: rows}, predict)
    assert out == [(5.0, 10, 1), (5.0, 4, 2)]
    assert seen == {1: 0, 2: 1}                          # no leakage: round N sees only rounds < N
