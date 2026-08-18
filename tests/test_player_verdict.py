"""Tests for the Player DNA AI Verdict heuristic (Sprint 169, US-412, ADR-118)."""

import sqlite3

from src.analytics.explain import player_verdict, verdict_label, verdict_score


def _row(**kw):
    base = {"position": "FWD", "price": 8.0, "penalties_order": None, "corners_order": None,
            "freekicks_order": None, "form": None, "selected_by": 5.0, "status": "a", "chance": None}
    base.update(kw)
    return base


# ---- verdict_score -----------------------------------------------------------

def test_score_rewards_projected_points_standing_most():
    elite = verdict_score(95, 50, 90)
    weak = verdict_score(10, 50, 90)
    assert elite > weak
    assert elite >= 75 and weak <= 45


def test_unavailable_caps_the_score_low_however_good():
    assert verdict_score(99, 99, 99, available=False) <= 20


def test_doubtful_is_capped_by_chance_of_playing():
    assert verdict_score(99, 99, 99, doubtful=True, chance=40) <= 40
    # a fit version of the same player is not capped
    assert verdict_score(99, 99, 99) > 40


def test_none_percentiles_are_neutral_not_zero():
    assert verdict_score(None, None, None) == 50


def test_score_is_monotonic_in_xp_percentile():
    assert verdict_score(20, 50, 50) < verdict_score(50, 50, 50) < verdict_score(90, 50, 50)


# ---- verdict_label -----------------------------------------------------------

def test_labels_at_each_threshold():
    assert verdict_label(85) == "Strong pick"
    assert verdict_label(65) == "Solid pick"
    assert verdict_label(50) == "Risky"
    assert verdict_label(20) == "Avoid"
    assert verdict_label(99, available=False) == "Avoid"     # flagged overrides a high score


# ---- player_verdict assembly -------------------------------------------------

def test_verdict_reuses_explain_worth_lines_and_leads_with_availability():
    row = _row(penalties_order=1, price=6.0)                  # a penalty taker, good value
    v = player_verdict(row, xp=30, xp_percentile=92, value=1.4, median=1.0, rank=2, n_peers=30,
                       value_percentile=80, consistency_percentile=95)
    assert v.label == "Strong pick" and v.score >= 78
    assert any("Penalty taker" in e or "Projects" in e for e in v.edge)   # grounded Edge from explain_worth

    flagged = player_verdict(_row(status="i"), xp=30, xp_percentile=92, value=1.4, median=1.0,
                             rank=2, n_peers=30, available=False)
    assert flagged.label == "Avoid"
    assert flagged.risk[0].startswith("Unavailable")         # availability surfaced first


def test_doubtful_risk_names_the_chance():
    v = player_verdict(_row(status="d", chance=50), xp=20, xp_percentile=60, value=1.0, median=1.0,
                       rank=10, n_peers=30, doubtful=True, chance=50)
    assert v.risk[0] == "Doubtful — 50% chance of playing"


def test_none_row_returns_none():
    assert player_verdict(None, xp=1, xp_percentile=1, value=1, median=1, rank=1, n_peers=1) is None


def test_accepts_sqlite3_row():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("create table pl (position, price, penalties_order, corners_order, freekicks_order, "
                "form, selected_by, status, chance)")
    con.execute("insert into pl values ('FWD', 6.0, 1, null, null, null, 5.0, 'a', null)")
    row = con.execute("select * from pl").fetchone()
    con.close()
    v = player_verdict(row, xp=30, xp_percentile=90, value=1.4, median=1.0, rank=2, n_peers=30,
                       value_percentile=80, consistency_percentile=90)
    assert v is not None and v.label == "Strong pick"
