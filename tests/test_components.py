"""Tests for the shared presentational primitives (ADR-163).

These exist because each page was deciding its own presentation and the decisions drifted — the owner found it
from outside on an iPhone. The tests pin the two properties that make a *shared* component worth having: it
behaves the same wherever it is used, and it degrades to nothing rather than to a broken box.
"""

from src.web_streamlit.components import banner_html, stat_strip_html


def test_the_strip_wraps_rather_than_holding_a_fixed_column_count():
    """The whole reason this isn't `st.metric` in `st.columns`: columns keep their ratio at any width, so a
    phone narrows each one until the label wraps. `flex-wrap` plus a flex-basis lets items reflow, and
    `clamp()` shrinks the number instead of breaking the line."""
    html = stat_strip_html([{"label": "Projected XI", "value": "91.8 xP"}])
    assert "flex-wrap:wrap" in html
    assert "flex:1 1 150px" in html          # ask for ~150px, wrap when it can't be had
    assert "clamp(" in html                  # …and shrink the value rather than wrapping it


def test_every_stat_renders_its_label_and_value():
    html = stat_strip_html([{"label": "Gap", "value": "+2.0"}, {"label": "Bench", "value": "18.7 xP"}])
    assert html.count('class="mb-item"') == 2
    for text in ("Gap", "+2.0", "Bench", "18.7 xP"):
        assert text in html


def test_a_tone_colours_the_value_and_an_unknown_tone_is_ignored():
    assert 'class="mb-v up"' in stat_strip_html([{"label": "Gap", "value": "+2", "tone": "up"}])
    assert 'class="mb-v down"' in stat_strip_html([{"label": "Gap", "value": "-2", "tone": "down"}])
    assert 'class="mb-v "' in stat_strip_html([{"label": "Gap", "value": "0", "tone": "rainbow"}])


def test_help_becomes_a_title_and_is_escaped():
    """`st.metric`'s tappable "?" can't be reproduced here, so help is a hover title — a stated tradeoff. What
    must hold is that it can't break out of the attribute."""
    html = stat_strip_html([{"label": "L", "value": "1", "help": 'a "quoted" <b>note</b>'}])
    assert "&quot;quoted&quot;" in html and "<b>note</b>" not in html


def test_a_label_or_value_cannot_inject_markup():
    html = stat_strip_html([{"label": "<script>x</script>", "value": "<b>9</b>"}])
    assert "<script>" not in html and "<b>9</b>" not in html


def test_an_empty_strip_renders_nothing_at_all():
    """A caller shouldn't have to check first — an empty box is worse than no box."""
    assert stat_strip_html([]) == "" and stat_strip_html(None) == ""


def test_a_missing_value_reads_as_a_dash_not_as_none():
    assert "None" not in stat_strip_html([{"label": "Captain"}])
    assert "—" in stat_strip_html([{"label": "Captain"}])


def test_the_banner_carries_its_kind_and_defaults_safely():
    assert 'class="mb-banner signal"' in banner_html("hi")
    assert 'class="mb-banner good"' in banner_html("hi", kind="good")
    assert 'class="mb-banner signal"' in banner_html("hi", kind="nonsense")
    assert banner_html("") == "" and banner_html(None) == ""


def test_the_banner_passes_markup_through_because_callers_compose_it():
    """Documented as trusted input: every caller builds the string from our own data, and the ones that matter
    carry <b> emphasis. The icon is escaped because it is the only part a caller might pass through."""
    assert "<b>Watkins</b>" in banner_html("<b>Watkins</b> — sold heavily")
    assert "<script>" not in banner_html("ok", icon="<script>")
