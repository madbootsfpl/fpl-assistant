"""Comparing two fingerprints on one radar (ADR-197) — Player and Team share the builder.

Owner: *"could we do a compare DNA for both Team & a Player. For Player it's an extension of Boot Battle and
should include Performance trend too."* Two design decisions were agreed before building, and both are pinned
here because both are the kind that get "tidied" later.
"""

import inspect

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


def test_the_player_compare_carries_the_performance_trend():
    """The owner asked for it by name, and it is the half Boot Battle has never been able to show: the stat
    card answers *who is better at each stat*, the trend answers *which way each one is going*."""
    src = inspect.getsource(__import__("src.web_streamlit.player_dna_view", fromlist=["x"]).render_dna_compare)
    assert "trend_panel_html" in src
    assert "player_gw_points" in src
    assert src.count("for p in (a, b)") == 1, "one trend per player, not one for the pair"
