"""Tests for the reusable Player DNA section + the performance trend (Sprint 171, US-416, ADR-118)."""

import re

from src.analytics.explain import Verdict
from src.web_streamlit.player_dna_view import (
    form_dots_html,
    perf_trend_svg,
    render_player_dna,
    sparkline_svg,
    sparklines_html,
    trend_panel_html,
)
from src.web_streamlit.verdict_card import verdict_card_html


def _p(pid, position="FWD", *, code=None, xg=0.0, total_points=0, price=6.0, penalties_order=None,
       selected_by=5.0):
    return {"id": pid, "web_name": f"p{pid}", "position": position, "team": "AAA", "minutes": 2700,
            "xg": xg, "xa": 0.0, "ict_index": 0.0, "total_points": total_points, "price": price,
            "status": "a", "chance": None, "selected_by": selected_by, "penalties_order": penalties_order,
            "corners_order": None, "freekicks_order": None, "code": code if code is not None else pid}


# ---- the trend ---------------------------------------------------------------

def test_trend_svg_draws_a_polyline_with_a_dot_per_point():
    svg = perf_trend_svg([(1, 2), (2, 6), (3, 4)])
    assert svg.startswith("<svg") and "<polyline" in svg
    assert svg.count("<circle") == 3


def test_trend_panel_is_the_placeholder_when_empty():
    html = trend_panel_html([])
    assert "Fills in from Gameweek 1" in html and "<polyline" not in html


def test_trend_panel_draws_a_line_when_there_is_data():
    html = trend_panel_html([(1, 2), (2, 5)])
    assert "<polyline" in html and "GW1" in html and "GW2" in html


def test_trend_panel_states_the_score_after_one_gameweek_instead_of_drawing_a_line():
    """After GW1 every player has exactly one result. The line is normalised to a player's own min..max, so a
    single point had no range to sit in and pinned to the chart floor — a 14-point haul drew identically to a
    2-point one, both reading as a flatline at zero. One gameweek is a result, not a trend: say the number."""
    haul, blank = trend_panel_html([(1, 14)]), trend_panel_html([(1, 2)])
    assert "14" in haul and "2" in blank
    assert haul != blank                        # the thing that was broken: they used to render the same
    assert "<svg" not in haul                   # no chart, so no direction to misread
    assert "GW1" in haul and "draws from GW2" in haul


def test_trend_svg_centres_a_flat_run_instead_of_flooring_it():
    """A steady 6-a-week return has no range either. Pinned to the floor it reads as "scored nothing" — the
    opposite of the truth. Flat is flat, so it sits in the middle."""
    ys = re.findall(r'cy="([\d.]+)"', perf_trend_svg([(1, 6), (2, 6), (3, 6)], h=90))
    assert ys == ["45.0", "45.0", "45.0"]       # h/2, not h-pad


def test_trend_svg_still_scales_a_varied_run_to_its_own_range():
    """The fix must not flatten a real trend: min still floors, max still tops."""
    ys = [float(y) for y in re.findall(r'cy="([\d.]+)"', perf_trend_svg([(1, 2), (2, 9), (3, 5)], h=90))]
    assert ys[0] == 82.0 and ys[1] == 8.0 and 8.0 < ys[2] < 82.0


# ---- verdict tone now covers the owned-aware words ---------------------------

def test_verdict_tone_covers_owned_labels():
    assert "#01fc7a" in verdict_card_html(Verdict("Strong Hold", 90, "High"))   # good tone
    assert "#01fc7a" in verdict_card_html(Verdict("Buy", 90, "High"))
    assert "#ffb020" in verdict_card_html(Verdict("Sell", 40, "Low"))            # meh tone
    assert "#ff6b7d" in verdict_card_html(Verdict("Avoid", 12, "Low"))           # bad tone


# ---- the composed section ----------------------------------------------------

def test_render_player_dna_composes_in_order(monkeypatch):
    called = []
    monkeypatch.setattr("src.web_streamlit.player_dna_view.render_verdict_card",
                        lambda v: called.append("verdict"))
    monkeypatch.setattr("src.web_streamlit.player_dna_view.render_dna_card",
                        lambda d: called.append("radar"))
    monkeypatch.setattr("src.web_streamlit.player_dna_view.render_insights_card",
                        lambda i: called.append("insights"))
    monkeypatch.setattr("src.web_streamlit.player_dna_view.st.markdown",
                        lambda *a, **k: called.append("trend"))

    pool = [_p(1, xg=25.0, total_points=200, price=10.0, penalties_order=1, selected_by=30.0),
            _p(2, xg=5.0, total_points=80)]
    render_player_dna(pool[0], pool, {1: 6.0, 2: 3.0}, gw_history={}, owned=True)
    assert called == ["verdict", "radar", "insights", "trend"]

    called.clear()
    render_player_dna(None, pool, {}, gw_history={})
    assert called == []                     # no-op on a falsy player


# ---- W-D-L dots + per-stat sparklines (ADR-128; ADR-118's tracked GW1 follow-up) ----

def test_form_dots_render_a_pill_per_result():
    html = form_dots_html([(1, "W"), (2, "D"), (3, "L")])
    assert html.count('class="tr-dot ') == 3        # the wrapper is `tr-dots`, so match the pill exactly
    assert 'class="tr-dot w"' in html and 'class="tr-dot d"' in html and 'class="tr-dot l"' in html


def test_form_dots_render_nothing_before_a_team_has_played():
    """Additive by design — with no results the card is exactly what it was, not a row of empty circles."""
    assert form_dots_html([]) == "" and form_dots_html(None) == ""


def test_sparklines_need_two_gameweeks_to_draw():
    """A line through one point is not a trend. Inviting a reader to see a direction that isn't there is the
    bug this project has now fixed three times over."""
    assert sparklines_html({"BPS": [(1, 20)]}) == ""
    assert "<svg" in sparklines_html({"BPS": [(1, 20), (2, 35)]})


def test_sparklines_skip_only_the_stats_without_enough_data():
    html = sparklines_html({"BPS": [(1, 20), (2, 35)], "xG": [(1, 0.3)]})
    assert "BPS" in html and "xG" not in html


def test_sparkline_centres_a_flat_run_rather_than_flooring_it():
    import re
    ys = re.findall(r"\d+\.\d+,(\d+\.\d+)", sparkline_svg([(1, 6), (2, 6), (3, 6)], h=30))
    assert ys == ["15.0", "15.0", "15.0"]        # h/2, not h-pad


def test_trend_panel_stays_intact_when_the_extras_are_absent():
    html = trend_panel_html([(1, 14)])
    # `tr-dot` also appears in the stylesheet, so assert on the rendered elements, not the substring.
    assert "14" in html
    assert '<span class="tr-dot' not in html and '<div class="tr-sp"' not in html


# ---- Rolling form windows on the trend card (ADR-159) ---------------------------------------------

def _windows(rows):
    from src.analytics.form import form_windows
    return form_windows(rows)


def _wk(minutes, points):
    return {"minutes": minutes, "total_points": points}


def test_the_card_shows_both_windows_and_the_gap_when_it_has_one():
    from src.web_streamlit.player_dna_view import form_windows_html
    html = form_windows_html(_windows([_wk(90, 2), _wk(90, 2), _wk(90, 3),
                                       _wk(90, 9), _wk(90, 8), _wk(90, 10)]))
    assert "Last 3" in html and "Last 6" in html
    assert "▲ +2.0" in html and "sharper lately" in html
    assert "not in xP" in html, "the reader must not think this moves the projection"


def test_the_card_refuses_to_draw_a_direction_it_cannot_measure():
    """The state the app is actually in today: one gameweek played. A 0.0 gap rendered as a level arrow would
    read as *steady form* rather than *no evidence yet* — the same mistake as a line through one point."""
    from src.web_streamlit.player_dna_view import form_windows_html
    html = form_windows_html(_windows([_wk(90, 6)]))
    assert "Not enough gameweeks yet" in html
    assert "▲" not in html and "▼" not in html and "▬" not in html
    assert "Last 6" not in html, "a second window covering the same match is not a second window"


def test_the_card_renders_nothing_at_all_without_minutes():
    from src.web_streamlit.player_dna_view import form_windows_html
    assert form_windows_html(_windows([])) == ""
    assert form_windows_html(_windows([_wk(0, 0)])) == ""
    assert form_windows_html(None) == ""


def test_the_trend_panel_degrades_to_exactly_what_it_was_without_windows():
    """`windows` is additive, like the dots and the sparklines before it."""
    assert trend_panel_html([(1, 2), (2, 5)]) == trend_panel_html([(1, 2), (2, 5)], windows=None)


# ---- The price strip on the trend card (ADR-160) --------------------------------------------------

def test_the_strip_names_the_move_and_draws_a_line_when_there_is_one():
    from src.web_streamlit.player_dna_view import price_strip_html
    html = price_strip_html([("GW1", 8.0), ("now", 7.9)], -0.1, 7.9)
    assert "£7.9m" in html and "▼ -0.1" in html
    assert "they have dropped £0.1m" in html
    assert "<svg" in html
    assert 'tr-pr-d down' in html, "red for a fall — the colour is the fast channel (ADR-140)"


def test_a_rise_is_the_other_glyph_and_the_other_colour():
    from src.web_streamlit.player_dna_view import price_strip_html
    html = price_strip_html([("GW1", 4.5), ("now", 4.6)], 0.1, 4.6)
    assert "▲ +0.1" in html and "tr-pr-d up" in html and "they have risen" in html


def test_an_unmoved_price_says_so_instead_of_drawing_a_flat_line():
    """607 of 616 players today. A blank strip would have been the alternative, and 'nothing has happened' is
    a real answer to 'what has his price done'."""
    from src.web_streamlit.player_dna_view import price_strip_html
    html = price_strip_html([("GW1", 15.5)], 0.0, 15.5)
    assert "£15.5m" in html and "Unchanged since the season started" in html
    assert "<svg" not in html and "▲" not in html and "▼" not in html


def test_no_price_means_no_strip():
    from src.web_streamlit.player_dna_view import price_strip_html
    assert price_strip_html([], None, None) == ""


def test_the_trend_panel_is_unchanged_without_a_price():
    assert trend_panel_html([(1, 2), (2, 5)]) == trend_panel_html([(1, 2), (2, 5)], price=None)
