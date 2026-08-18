"""Tests for the AI Insights card renderer (Sprint 170, US-415, ADR-118)."""

from src.analytics.player_dna import Insight
from src.web_streamlit.insights_card import insights_card_html, render_insights_card


def test_card_has_a_titled_bullet_per_insight():
    ins = [Insight("good", "Elite goal threat: top 1% of forwards (xG/90 0.78)"),
           Insight("sp", "First-choice penalty taker — a steady points floor"),
           Insight("warn", "Premium at £15.5m — value only mid-pack")]
    html = insights_card_html(ins)
    assert "AI Insights" in html
    assert html.count('class="ins-row"') == 3
    assert "Elite goal threat" in html and "penalty taker" in html


def test_each_kind_gets_its_icon_and_tone():
    good = insights_card_html([Insight("good", "x")])
    warn = insights_card_html([Insight("warn", "y")])
    assert "✓" in good and "#01fc7a" in good
    assert "!" in warn and "#ffb020" in warn


def test_html_is_escaped():
    html = insights_card_html([Insight("info", "A & B <script>")])
    assert "&amp;" in html and "<script>" not in html


def test_empty_renders_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr("src.web_streamlit.insights_card.st.markdown", lambda *a, **k: calls.append(a))
    render_insights_card([])
    assert calls == []                      # no card when there are no insights
    render_insights_card([Insight("good", "z")])
    assert len(calls) == 1
