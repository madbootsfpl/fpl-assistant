"""Tests for the stat-board quality rating (ADR-071) — a pure, display-only helper.

Relative quintile bands over the pool of values shown, with a percentile anchor. Both directions
(lower-is-better xGC/90, higher-is-better xGI), ties, the extremes, and degenerate pools.
"""

from src.web_streamlit.ratings import quality_band, rating_cell


def _bands(values, *, higher_is_better):
    """The (emoji, label) for each value rated within the whole list — handy for asserting order."""
    return [(quality_band(v, values, higher_is_better=higher_is_better)["emoji"],
             quality_band(v, values, higher_is_better=higher_is_better)["label"]) for v in values]


def test_lower_is_better_puts_the_smallest_in_the_top_band():
    pool = [0.5, 1.0, 1.3, 1.5, 2.0]           # xGC/90-like: lowest is best
    best = quality_band(0.5, pool, higher_is_better=False)
    worst = quality_band(2.0, pool, higher_is_better=False)
    assert (best["emoji"], best["label"]) == ("🟢", "excellent")
    assert (worst["emoji"], worst["label"]) == ("🔴", "very poor")
    assert best["percentile"] == "top 1%"       # 0 beat it → clamped to 1%
    assert worst["percentile"] == "bottom 20%"  # US-426: worse half reads "bottom N%", not "top 80%"


def test_higher_is_better_flips_the_direction():
    pool = [1.0, 3.0, 5.0, 8.0, 12.0]          # xGI-like: highest is best
    assert quality_band(12.0, pool, higher_is_better=True)["label"] == "excellent"
    assert quality_band(1.0, pool, higher_is_better=True)["label"] == "very poor"


def test_quintiles_span_all_five_bands_across_a_spread_pool():
    pool = [1, 2, 3, 4, 5]                       # higher better → each lands in its own quintile
    labels = [b[1] for b in _bands(pool, higher_is_better=True)]
    assert labels == ["very poor", "poor", "average", "good", "excellent"]


def test_ties_share_a_band():
    # three equal-best values (lower better) all beat nobody → all 'excellent', same percentile
    pool = [1.0, 1.0, 1.0, 2.0, 3.0]
    for v in (1.0,):
        b = quality_band(v, pool, higher_is_better=False)
        assert b["label"] == "excellent" and b["percentile"] == "top 1%"


def test_single_element_and_empty_pool():
    assert quality_band(0.5, [0.5], higher_is_better=False)["label"] == "excellent"
    empty = quality_band(0.5, [], higher_is_better=False)
    assert empty == {"emoji": "", "label": "", "percentile": ""}


def test_rating_cell_formats_band_and_percentile():
    cell = rating_cell(0.5, [0.5, 1.0, 1.3, 1.5, 2.0], higher_is_better=False)
    assert cell == "🟢 excellent (top 1%)"
    assert rating_cell(0.5, [], higher_is_better=False) == ""   # empty pool → blank cell
