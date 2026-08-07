"""Tests for the live countdown clock's HTML (Sprint 103, ADR-088).

The JS tick runs only in a browser (AppTest doesn't execute the iframe), so we test the **pure** HTML builder:
it embeds the deadline ISO, fills the cells with the current remaining time (readable without JS), carries the
tick script, and colours by urgency.
"""

from datetime import datetime, timezone

from src.web_streamlit.countdown import _parts, countdown_html


def test_parts_splits_seconds_and_clamps_negatives():
    assert _parts(90_061) == (1, 1, 1, 1)          # 1d 1h 1m 1s
    assert _parts(-5) == (0, 0, 0, 0)              # a passed deadline clamps to zeros


def test_countdown_html_embeds_the_deadline_and_the_tick_and_initial_cells():
    now = datetime(2026, 8, 7, 12, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc)   # 18:30 UK
    html = countdown_html(1, deadline, now, "calm")

    assert deadline.isoformat() in html            # the target the JS ticks off
    assert "setInterval" in html and "GW1 deadline" in html
    assert "18:30 (UK)" in html                    # the subtitle, in UK time

    d, h, m, s = _parts((deadline - now).total_seconds())
    assert f'id="d">{d:02d}' in html and f'id="s">{s:02d}' in html   # server-filled → readable without JS


def test_countdown_html_is_urgency_coloured():
    now = datetime(2026, 8, 21, 16, 0, tzinfo=timezone.utc)
    deadline = datetime(2026, 8, 21, 17, 30, tzinfo=timezone.utc)
    assert "#ef4444" in countdown_html(1, deadline, now, "imminent")   # red
    assert "#f59e0b" in countdown_html(1, deadline, now, "today")      # amber
    assert "#22c55e" in countdown_html(1, deadline, now, "calm")       # green
