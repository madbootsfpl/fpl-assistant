"""Tests for the Player DNA AI Insights engine (Sprint 170, US-414, ADR-118)."""

import sqlite3

from src.analytics.player_dna import player_dna, player_insights


def _p(pid, position, *, team="AAA", minutes=2000, xg=0.0, xa=0.0, ict_index=0.0, total_points=0,
       price=6.0, status="a", chance=None, selected_by=5.0, penalties_order=None, corners_order=None,
       freekicks_order=None, web_name=None):
    return {"id": pid, "web_name": web_name or f"p{pid}", "position": position, "team": team,
            "minutes": minutes, "xg": xg, "xa": xa, "ict_index": ict_index, "total_points": total_points,
            "price": price, "status": status, "chance": chance, "selected_by": selected_by,
            "penalties_order": penalties_order, "corners_order": corners_order,
            "freekicks_order": freekicks_order}


def _texts(insights):
    return " || ".join(i.text for i in insights)


def _elite_fwd_pool(**over):
    target = _p(1, "FWD", xg=25.0, minutes=2700, total_points=200, ict_index=300, price=15.5,
                penalties_order=1, selected_by=71.9, web_name="Elite", **over)
    pool = [target, _p(2, "FWD", xg=8.0, minutes=2700, total_points=120, ict_index=120),
            _p(3, "FWD", xg=2.0, minutes=2700, total_points=60, ict_index=70)]
    return target, pool


def test_strengths_surface_the_top_axes_with_top_n_wording():
    target, pool = _elite_fwd_pool()
    ins = player_insights(target, player_dna(target, pool))
    assert any(i.kind == "good" and "Elite" in i.text and "top 1%" in i.text for i in ins)


def test_penalty_taker_and_ownership_and_no_availability_line_when_fit():
    target, pool = _elite_fwd_pool()
    ins = player_insights(target, player_dna(target, pool))
    t = _texts(ins)
    assert "penalty taker" in t.lower()
    assert "71.9%" in t                       # ownership tier surfaced (essential/template)
    assert "Unavailable" not in t and "Doubtful" not in t


def test_availability_leads_when_flagged():
    target, pool = _elite_fwd_pool(status="i")
    ins = player_insights(target, player_dna(target, pool))
    assert ins[0].kind == "warn" and ins[0].text.startswith("Unavailable")


def test_doubtful_names_the_chance():
    target, pool = _elite_fwd_pool(status="d", chance=75)
    ins = player_insights(target, player_dna(target, pool))
    assert ins[0].text == "Doubtful — 75% chance to play"


def test_differential_ownership_insight():
    target = _p(1, "MID", xg=6.0, minutes=2700, total_points=110, selected_by=3.0)
    pool = [target, _p(2, "MID", xg=2.0, minutes=2700, total_points=60)]
    assert "Differential — only 3.0% owned" in _texts(player_insights(target, player_dna(target, pool)))


def test_premium_with_mid_value_caution():
    # a pricey forward whose value percentile is low → the premium caution fires
    target = _p(1, "FWD", xg=12.0, minutes=2700, total_points=120, price=12.5)
    pool = [target,
            _p(2, "FWD", xg=6.0, minutes=2700, total_points=150, price=5.0),   # far better value
            _p(3, "FWD", xg=5.0, minutes=2700, total_points=140, price=5.0)]
    assert any("Premium at £12.5m" in i.text and i.kind == "warn"
               for i in player_insights(target, player_dna(target, pool)))


def test_max_items_is_respected():
    target, pool = _elite_fwd_pool()
    assert len(player_insights(target, player_dna(target, pool), max_items=3)) == 3


def test_none_and_empty_are_safe():
    assert player_insights(None, None) == []
    target = _p(1, "FWD")
    assert player_insights(target, None) == []


def test_accepts_sqlite3_row():
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    cols = ("id", "web_name", "position", "team", "minutes", "xg", "xa", "ict_index", "total_points",
            "price", "status", "chance", "selected_by", "penalties_order", "corners_order", "freekicks_order")
    con.execute(f"create table pl ({', '.join(cols)})")
    for vals in [(1, "Row", "FWD", "AAA", 2700, 25.0, 3.0, 300.0, 200, 15.5, "a", None, 71.9, 1, None, None),
                 (2, "Row2", "FWD", "AAA", 2700, 5.0, 1.0, 90.0, 80, 6.0, "a", None, 5.0, None, None, None)]:
        con.execute(f"insert into pl values ({', '.join('?' for _ in cols)})", vals)
    rows = con.execute("select * from pl").fetchall()
    con.close()
    ins = player_insights(rows[0], player_dna(rows[0], rows))    # Row has no .get() — must not raise
    assert any("penalty taker" in i.text.lower() for i in ins)
