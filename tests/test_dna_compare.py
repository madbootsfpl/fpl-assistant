"""Comparing two fingerprints on one radar (ADR-197) — Player and Team share the builder.

Owner: *"could we do a compare DNA for both Team & a Player. For Player it's an extension of Boot Battle and
should include Performance trend too."* Two design decisions were agreed before building, and both are pinned
here because both are the kind that get "tidied" later.
"""

import inspect
import re

from src.analytics.player_dna import Axis
from src.web_streamlit.dna_card import radar_compare_svg


def _axes(*pcts):
    return [Axis(label=f"A{i}", sublabel="", percentile=p, value=None) for i, p in enumerate(pcts)]


def test_both_fingerprints_are_drawn_on_one_radar():
    """⭐ **One octagon, two polygons — not two charts side by side.** The value of a fingerprint comparison is
    the *shape difference*; two separate radars make the reader do the overlay in their head, which is exactly
    the work Boot Battle already does for them stat by stat."""
    svg = radar_compare_svg(_axes(80, 70, 60, 50, 40, 30, 20, 10),
                            _axes(10, 20, 30, 40, 50, 60, 70, 80), a_label="Salah", b_label="Son")
    assert svg.count("<polygon") >= 6, "four rings plus two data polygons"
    assert svg.count("<svg") == 1, "one radar, not two"
    assert "Salah" in svg and "Son" in svg, "both must be named — the legend is the whole key"


def test_an_unranked_axis_is_hollow_in_its_own_colour():
    """⚠️ **The case that cannot arise on a single radar, and the reason this needed a decision.**

    One radar sits an unranked axis on the mid ring with a hollow dot — *absent evidence is not a zero*
    (ADR-118/126). With **two** shapes, each may be unranked on a **different** axis, and drawing both plainly
    would silently imply they were level there. Each unranked vertex is drawn hollow in its own colour, so a
    reader can see *which* side is short of evidence and *where*.
    """
    svg = radar_compare_svg(_axes(80, None, 60, 50, 40, 30, 20, 10),
                            _axes(10, 20, None, 40, 50, 60, 70, 80), a_label="A", b_label="B")
    assert svg.count("stroke-dasharray") == 2, "one hollow vertex per side, on different axes"


def test_it_refuses_to_draw_when_either_side_is_too_thin():
    """A shape built mostly from missing data is a lie (ADR-118). With two clubs the pair declines **together**
    — a radar where one side is real and the other is guesswork is worse than no radar, because it looks like
    a comparison."""
    thin = _axes(70, None, None, None, None, None, None, None)
    full = _axes(10, 20, 30, 40, 50, 60, 70, 80)
    assert "Not enough games" in radar_compare_svg(thin, full, a_label="A", b_label="B")
    assert "Not enough games" in radar_compare_svg(full, thin, a_label="A", b_label="B")
    assert "<svg" in radar_compare_svg(full, full, a_label="A", b_label="B")


def test_neither_compare_renders_a_second_verdict():
    """⚠️ **The design decision, owner-agreed, and the one most likely to be "improved" later.**

    Each player has a verdict on his own DNA page. Two side by side would read as a ranking the model has not
    earned: a verdict is a heuristic 0–99 built from signals deliberately kept *out* of `decision_xp`
    (ADR-118). Putting two next to each other invites a subtraction nobody measured — the same overclaim
    ADR-194 removed from the lineup a day earlier. ⭐ *The shapes compare; the reader concludes.*
    """
    from src.web_streamlit import team_dna_card
    from src.web_streamlit.player_dna_view import render_dna_compare

    player_src = inspect.getsource(render_dna_compare)
    team_src = inspect.getsource(team_dna_card.render_team_compare)
    for name, src in (("player", player_src), ("team", team_src)):
        assert "render_verdict_card" not in src, f"the {name} compare must not render a verdict"
        assert "build_verdict" not in src, f"the {name} compare must not build a verdict"
    assert "gauge_svg" not in team_src, "nor a grade gauge, which reads as a league table of two"


def test_the_player_compare_carries_one_overlaid_performance_trend():
    """The owner asked for the trend by name — it is the half Boot Battle has never been able to show: the
    stat card answers *who is better at each stat*, the trend answers *which way each one is going*.

    ⚠️ **It began as two stacked panels and is now one overlay** (owner, 2026-09-16): stacking made the reader
    compare by memory across a scroll, which is the same argument that put both fingerprints on one octagon
    rather than two charts. This asserts the *claim* — both players, one chart — rather than the mechanism,
    because the mechanism has already changed once.
    """
    src = inspect.getsource(__import__("src.web_streamlit.player_dna_view", fromlist=["x"]).render_dna_compare)
    assert src.count("perf_trend_compare_svg") == 1, "one chart, not one per player"
    assert src.count("player_gw_points") == 2, "…fed a series for each player"
    assert "trend_panel_html" not in src, "…and not the single-player panel, twice"
    assert "for p in (a, b)" not in src


def test_the_compare_supplies_its_own_dark_ground():
    """⚠️ **The phone bug, reported with a screenshot.**

    The radar's furniture is hard-coded for a dark ground — `rgba(255,255,255,.10)` rings, `#cdd6e2` labels,
    `#0c121a` dot outlines. The single card supplies that ground itself (`.dna-card`); the compare rendered the
    **bare `<svg>`**, so on a light-themed phone it sat on white with near-invisible labels while everything
    around it stayed dark.

    ⭐ *A component that hard-codes one theme's colours is not portable to a container that does not supply
    them* — and it looks fine on the developer's machine, because the developer is in dark mode.
    """
    from src.web_streamlit.dna_card import compare_card_html

    html = compare_card_html(_axes(80, 70, 60, 50, 40, 30, 20, 10),
                             _axes(10, 20, 30, 40, 50, 60, 70, 80),
                             a_label="Man City", b_label="Aston Villa",
                             title="🧬 Team DNA — compare", caption="Percentile rank against every club")
    assert 'class="dna-card"' in html, "the compare must carry the same dark card the single radar does"
    assert ".dna-card{background:" in html, "…and ship the CSS that paints it"
    assert html.index('class="dna-card"') < html.index("<svg"), "the ground must wrap the chart"
    # …including when it declines to draw, or the refusal renders on white too.
    thin = _axes(70, None, None, None, None, None, None, None)
    declined = compare_card_html(thin, _axes(10, 20, 30, 40, 50, 60, 70, 80), a_label="A", b_label="B",
                                 title="t", caption="c")
    assert 'class="dna-card"' in declined and "Not enough games" in declined


def test_the_axes_are_chips_not_a_table():
    """Owner: *"rather than a table could we use the legend as used in single club with the comparing club data
    alongside it."* The table was a second reading order for the eight facts the chart already showed, and on
    a phone every cell wrapped onto three lines. One chip per axis, two values, tinted by **shape colour** —
    in a comparison the question is *whose is this*; the radar answers *how good* by position on the ring."""
    from src.web_streamlit.dna_card import compare_card_html

    html = compare_card_html(_axes(89, 100, 60, 50, 40, 30, 20, 10),
                             _axes(0, 16, 30, 40, 50, 60, 70, 80),
                             a_label="Man City", b_label="Aston Villa", title="t", caption="c")
    assert html.count('class="dna-chip"') == 8, "one chip per axis"
    assert html.count('class="dna-p2"') == 16, "two values per chip"
    assert "| Axis |" not in html and "|---|" not in html, "no markdown table"
    assert ">89<" in html and ">0<" in html, "both sides' percentiles are present"


def test_the_compare_radar_matches_the_single_one():
    """Owner: *"same size and thickness as the original single club radar."* Two charts of the same thing at
    different scales read as two different charts — and the compare sits one expander below the single view,
    so the mismatch was directly visible."""
    import inspect

    from src.web_streamlit import dna_card

    src = inspect.getsource(dna_card.radar_compare_svg)
    single = inspect.getsource(dna_card.radar_svg)
    assert "size: int = 360" in src and "size: int = 360" in single
    assert "R = size / 2 - 74" in src and "R = size / 2 - 74" in single
    assert 'stroke-width="2"' in src, "the data polygon matches the single radar's weight"


def _ys(svg):
    return [float(m) for m in re.findall(r'<circle cx="[\d.]+" cy="([\d.]+)"', svg)]


def test_both_trends_share_one_scale():
    """⚠️ **The correctness point of overlaying two lines, and the easiest thing to get wrong.**

    `perf_trend_svg` normalises each line to *that player's own* min..max — correct for a single chart, where
    the question is *which way is he going*. For a comparison it is flatly wrong: a player returning 2,3,2 and
    one returning 9,14,9 would draw the **same shape**, and the overlay would say they were level.

    ⭐ *A chart that answers one question can be silently wrong for the neighbouring one.*
    """
    from src.web_streamlit.player_dna_view import perf_trend_compare_svg

    svg = perf_trend_compare_svg([(1, 2), (2, 3), (3, 2)], [(1, 9), (2, 14), (3, 9)],
                                 a_label="Low", b_label="High")
    ys = _ys(svg)
    low, high = ys[:3], ys[3:]
    # smaller y = higher on the chart. The 9–14 returner must sit clear of the 2–3 one.
    assert max(high) < min(low), f"the two lines must share a scale: {low} vs {high}"


def test_a_missed_gameweek_breaks_the_line_rather_than_crossing_it():
    """⚠️ **A first cut drew one polyline through whatever gameweeks a player had**, so a missed week was
    crossed by a straight segment — a continuous line under a caption promising a gap. ⭐ *The break has to be
    real, or the caption is a claim the chart does not support.* Same rule as the radar's unranked axis: a
    blank is absent evidence, not a zero."""
    from src.web_streamlit.player_dna_view import perf_trend_compare_svg

    svg = perf_trend_compare_svg([(1, 2), (2, 3), (3, 2), (4, 4)],   # played every week
                                 [(1, 9), (2, 14), (4, 9)],          # missed GW3
                                 a_label="A", b_label="B")
    assert svg.count("<polyline") == 2, "A's unbroken run, plus B's GW1–2 — B's lone GW4 point cannot join"
    assert svg.count("<circle") == 7, "every appearance still gets a dot"
    assert ">3<" in svg, "the missed gameweek still appears on the axis"


def test_the_trend_uses_the_radar_colours():
    """Owner: *"could they be overlayed with the same colour scheme as Player DNA."* Purple is the first
    player and teal the second on both charts, so the eye carries one mapping down the card instead of
    relearning it per chart."""
    from src.web_streamlit.dna_card import _A_STROKE, _B_STROKE
    from src.web_streamlit.player_dna_view import perf_trend_compare_svg

    svg = perf_trend_compare_svg([(1, 2)], [(1, 9)], a_label="A", b_label="B")
    assert _A_STROKE in svg and _B_STROKE in svg


def test_an_empty_trend_renders_nothing_at_all():
    """Preseason, or two players with no appearances between them. An empty chart frame is worse than no
    chart — it looks like a result."""
    from src.web_streamlit.player_dna_view import perf_trend_compare_svg

    assert perf_trend_compare_svg([], [], a_label="A", b_label="B") == ""
    assert perf_trend_compare_svg(None, None, a_label="A", b_label="B") == ""
