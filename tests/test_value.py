"""Tests for the value analytics (points-per-£m and ranking)."""

from src.analytics.value import points_per_million, rank_players


def test_points_per_million_basic():
    assert points_per_million(200, 8.0) == 25.0


def test_points_per_million_zero_price_is_undefined():
    assert points_per_million(100, 0) is None


def test_points_per_million_missing_price_is_undefined():
    assert points_per_million(100, None) is None


def test_rank_by_value_puts_best_value_first():
    rows = [
        {"web_name": "Expensive", "price": 15.0, "total_points": 150},  # 10.0 / £m
        {"web_name": "Cheap", "price": 5.0, "total_points": 100},       # 20.0 / £m
    ]
    ranked = rank_players(rows, sort_by="value")

    assert ranked[0]["web_name"] == "Cheap"
    assert ranked[0]["value"] == 20.0


def test_rank_by_value_sorts_undefined_last():
    rows = [
        {"web_name": "NoPrice", "price": 0, "total_points": 100},   # undefined
        {"web_name": "Normal", "price": 5.0, "total_points": 50},   # 10.0 / £m
    ]
    ranked = rank_players(rows, sort_by="value")

    assert ranked[0]["web_name"] == "Normal"
    assert ranked[-1]["value"] is None


def test_rank_by_points_puts_top_scorer_first():
    rows = [
        {"web_name": "Low", "price": 5.0, "total_points": 100},
        {"web_name": "High", "price": 15.0, "total_points": 150},
    ]
    ranked = rank_players(rows, sort_by="points")

    assert ranked[0]["web_name"] == "High"
