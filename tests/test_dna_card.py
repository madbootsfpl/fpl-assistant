"""Tests for the Player DNA radar renderer (Sprint 168, US-411, ADR-118)."""

from src.analytics.player_dna import player_dna
from src.web_streamlit.dna_card import _band, dna_card_html, radar_svg


def _p(pid, position, *, team="AAA", minutes=2000, xg=0.0, xa=0.0, ict_index=0.0,
       total_points=0, price=6.0, penalties_order=None, web_name=None):
    return {"id": pid, "web_name": web_name or f"p{pid}", "position": position, "team": team,
            "minutes": minutes, "xg": xg, "xa": xa, "ict_index": ict_index,
            "total_points": total_points, "price": price, "penalties_order": penalties_order,
            "corners_order": None, "freekicks_order": None}


def _dna():
    pool = [
        _p(1, "FWD", xg=25.0, minutes=2700, total_points=200, ict_index=300, penalties_order=1,
           web_name="Elite"),
        _p(2, "FWD", xg=8.0, minutes=2700, total_points=120),
        _p(3, "FWD", xg=2.0, minutes=2700, total_points=60),
    ]
    return player_dna(pool[0], pool)


def test_band_thresholds():
    assert _band(90)[0] == "#01fc7a"          # elite → green
    assert _band(70)[0] != _band(90)[0]        # strong → teal (different)
    assert _band(30)[0] == "#ffb020"           # below par → amber
    assert _band(None)[0] == "#3a4150"         # unranked → muted


def test_radar_svg_has_eight_axes_and_vertices():
    svg = radar_svg(_dna())
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert "dnaFill" in svg                      # the purple→teal gradient
    for label in ("Goal Threat", "Creativity", "Set Pieces", "FPL Output",
                  "Consistency", "Value", "Bonus Potl", "Team Attack"):
        assert label in svg
    assert svg.count("<circle") == 8            # one vertex dot per axis
    # 4 rings + 1 data polygon
    assert svg.count("<polygon") == 5


def test_card_html_has_a_chip_per_axis_and_a_caption():
    html = dna_card_html(_dna())
    assert html.count('class="dna-chip"') == 8
    assert "🧬 Player DNA" in html
    assert "forwards" in html                    # FWD → "forwards"
    assert "vs 3 with real minutes" in html      # the pool size is surfaced honestly


def test_low_minutes_adds_a_caution_note():
    target = _p(9, "FWD", xg=3.0, minutes=200, web_name="NewSigning")   # below the 450 floor
    peers = [_p(1, "FWD", xg=10.0, minutes=2700), _p(2, "FWD", xg=1.0, minutes=2700)]
    dna = player_dna(target, [target, *peers])
    assert dna.low_minutes is True
    assert "Limited minutes" in dna_card_html(dna)
    # a fully-ranked player carries no such note
    assert "Limited minutes" not in dna_card_html(_dna())


def test_name_is_escaped():
    pool = [_p(1, "MID", xg=5, minutes=2700, web_name="A & <b>B</b>"),
            _p(2, "MID", xg=1, minutes=2700)]
    svg = radar_svg(player_dna(pool[0], pool))
    assert "&amp;" in svg and "<b>B</b>" not in svg   # raw markup neutralised


def test_none_dna_card_html_is_never_called_on_none():
    # render_dna_card(None) is a no-op; dna_card_html expects a real dna. Guard the engine's None path.
    assert player_dna(_p(1, None), [_p(1, None)]) is None
