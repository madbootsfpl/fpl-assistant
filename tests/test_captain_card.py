"""Tests for the web-native Captain Pick card (Sprint 116, US-294).

Pure HTML builder — the pitch pattern (ADR-084): one self-contained block, every value escaped, theme-neutral.
Display-only; no Streamlit context needed here.
"""

from src.analytics.explain import Explanation
from src.web_streamlit.captain_card import captain_card_html

_RANKED = [
    {"web_name": "B.Fernandes", "team": "MUN", "position": "MID", "xp": 5.9},
    {"web_name": "Haaland", "team": "MCI", "position": "FWD", "xp": 5.7},
    {"web_name": "Rice", "team": "ARS", "position": "MID", "xp": 4.5},
]
_EX = Explanation(reasons=["Highest projected points", "Penalty taker"],
                  risks=["Away fixture", "Only +0.2 pts ahead of Haaland"], confidence=69, band="Medium")


def test_card_shows_pick_confidence_why_risks_and_alternatives():
    h = captain_card_html(_RANKED, _EX, scope="from squad 'RoboTS'", team_names={"MUN": "Man Utd"})
    assert ".cap-card" in h and "🥇 Captain Pick" in h and "from squad &#x27;RoboTS&#x27;" in h
    assert "B.Fernandes" in h and "Man Utd · MID" in h and "5.9 pts" in h    # pick + projected chip
    assert "69/100 · Medium" in h and "cc-med" in h                          # confidence pill (Medium band)
    assert "✓ Penalty taker" in h and "⚠ Away fixture" in h                  # Edge / Risk
    assert "🥈 Haaland 5.7" in h and "🥉 Rice 4.5" in h                       # Alternatives
    assert 'class="cc-brand"' in h and 'aria-label="MADBOOTS"' in h          # US-355: the MADBOOTS mark


def test_card_band_drives_the_pill_class():
    # anchor on the applied class attribute (the CSS block defines all three classes)
    high = captain_card_html(_RANKED, Explanation([], [], 90, "High"))
    low = captain_card_html(_RANKED, Explanation([], [], 30, "Low"))
    assert 'cc-conf cc-high' in high and 'cc-conf cc-med' not in high
    assert 'cc-conf cc-low' in low


def test_card_escapes_every_value():
    h = captain_card_html([{"web_name": "<script>x", "team": "X", "position": "MID", "xp": 1.0}], None)
    assert "<script>x" not in h and "&lt;script&gt;x" in h                   # a hostile name can't break markup


def test_card_is_empty_safe():
    assert captain_card_html([], _EX) == ""                                  # no picks → no card
    solo = captain_card_html([_RANKED[0]], None)                            # no explanation, no runner-ups
    assert "B.Fernandes" in solo and "Alternatives" not in solo and 'class="cc-conf' not in solo
