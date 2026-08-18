"""Tests for the AI Verdict card renderer (Sprint 169, US-413, ADR-118)."""

from src.analytics import player_dna
from src.analytics.explain import Verdict
from src.web_streamlit.verdict_card import build_verdict, gauge_svg, verdict_card_html


def _p(pid, position, *, team="AAA", minutes=2000, xg=0.0, total_points=0, price=6.0,
       status="a", chance=None, penalties_order=None, web_name=None):
    return {"id": pid, "web_name": web_name or f"p{pid}", "position": position, "team": team,
            "minutes": minutes, "xg": xg, "xa": 0.0, "ict_index": 0.0, "total_points": total_points,
            "price": price, "status": status, "chance": chance, "penalties_order": penalties_order,
            "corners_order": None, "freekicks_order": None, "form": None, "selected_by": 5.0}


def test_gauge_arc_fills_with_the_score():
    lo = gauge_svg(10, "#01fc7a")
    hi = gauge_svg(90, "#01fc7a")
    assert lo.startswith("<svg") and lo.endswith("</svg>")
    # a higher score leaves a smaller dash *offset* (more of the ring drawn)
    def _off(svg):
        return float(svg.split('stroke-dashoffset="')[1].split('"')[0])
    assert _off(hi) < _off(lo)


def test_card_html_shows_label_score_and_grounded_lines():
    v = Verdict(label="Strong pick", score=87, band="High",
                edge=["Projects 30 points over 1 GW", "Penalty taker"],
                risk=["Premium price (£15.5m ties up budget)"])
    html = verdict_card_html(v)
    assert "Strong pick" in html and ">87<" in html
    assert "AI Verdict" in html
    assert "Edge" in html and "Penalty taker" in html
    assert "Risk" in html and "Premium price" in html.replace("&amp;", "&")


def test_card_tone_matches_the_verdict_word():
    strong = verdict_card_html(Verdict("Strong pick", 90, "High"))
    avoid = verdict_card_html(Verdict("Avoid", 12, "Low"))
    assert "#01fc7a" in strong                 # green tone
    assert "#ff6b7d" in avoid                   # red tone


def test_edge_and_risk_lines_are_optional():
    html = verdict_card_html(Verdict("Solid pick", 65, "Medium", edge=[], risk=[]))
    assert "Strong pick" not in html and "Solid pick" in html
    assert "Edge" not in html and "Risk" not in html   # nothing to show, nothing rendered


def test_build_verdict_reuses_dna_and_xp_and_flags_availability():
    target = _p(1, "FWD", xg=25.0, minutes=2700, total_points=200, price=15.5,
                penalties_order=1, web_name="Premium")
    pool = [target, _p(2, "FWD", xg=8.0, minutes=2700, total_points=120, price=7.0),
            _p(3, "FWD", xg=2.0, minutes=2700, total_points=60, price=5.0)]
    xp = {1: 6.0, 2: 4.0, 3: 2.0}
    dna = player_dna(target, pool)
    v = build_verdict(target, pool, xp, dna)
    assert v is not None and v.label in ("Strong pick", "Solid pick")
    assert v.score >= 60

    injured = _p(9, "FWD", xg=20.0, minutes=2700, total_points=180, price=10.0, status="i")
    vi = build_verdict(injured, [*pool, injured], {**xp, 9: 5.0}, player_dna(injured, [*pool, injured]))
    assert vi.label == "Avoid" and vi.risk[0].startswith("Unavailable")


def test_build_verdict_is_none_safe():
    assert build_verdict(None, [], {}, None) is None
    assert build_verdict(_p(1, "FWD"), [], {}, None) is None   # no dna
