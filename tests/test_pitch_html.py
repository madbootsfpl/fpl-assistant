"""Tests for the pitch markup itself (ADR-084, split out by ADR-133).

`pitch_html` was extracted from `render_pitch` so a tappable pitch could hand its HTML to a component. That
split moved these assertions **out of AppTest and into a pure function** — the markup is now testable without
rendering a page at all, which is faster and stricter than reading it back out of `AppTest.markdown`.

Honest note: this is a *move*, not a free win. The pitch no longer appears in `AppTest.markdown` when it is
rendered through the component, so the page-level tests can no longer see inside it. What they can still assert
— that the page renders, that the picker exists, that the dropdown drives selection — they still do.
"""

from src.web_streamlit.pitch import pitch_html


def _p(pid, pos, name=None, team="ARS", price=6.0, **extra):
    row = {"id": pid, "web_name": name or f"p{pid}", "position": pos, "team": team, "price": price,
           "status": "a", "chance": None, "selected_by": 5.0, "penalties_order": None,
           "corners_order": None, "freekicks_order": None, "form": 3.0, "transfers_in_event": 0,
           "transfers_out_event": 0, "cost_change_event": 0, "minutes": 900, "total_points": 50,
           "xg": 1.0, "xa": 1.0, "xgi": 2.0, "xgc": 10.0, "defcon_per90": 5.0, "news": "", "code": pid}
    row.update(extra)
    return row


def _squad():
    xi = ([_p(1, "GK")] + [_p(i, "DEF") for i in range(2, 6)]
          + [_p(i, "MID") for i in range(6, 10)] + [_p(i, "FWD") for i in range(10, 12)])
    bench = [_p(12, "GK"), _p(13, "DEF"), _p(14, "MID"), _p(15, "FWD")]
    return xi, bench


def _html(**kw):
    xi, bench = _squad()
    return pitch_html(xi, bench, captain_id=1, xp_by_id={i: 4.0 for i in range(1, 16)},
                      photos={}, next_opp={}, **kw)


# ---- the markup, as the page used to assert it -------------------------------------

def test_the_pitch_lays_out_an_xi_and_a_bench():
    html = _html()
    assert "fpl-pitch" in html
    assert html.count('class="kit"') == 15          # the XI plus the four on the bench
    assert "bench-label" in html


def test_the_card_css_appears_exactly_once():
    """It carries the per-kit hover popovers; repeating it per card would bloat every pitch."""
    assert _html().count("linear-gradient(180deg,#111821,#0c121a)") == 1


def test_every_kit_carries_a_hover_popover():
    assert _html().count("kit-pop") >= 11


def test_the_captain_gets_an_armband():
    assert 'class="c-badge"' in _html()


# ---- the tappable variant (ADR-133) -------------------------------------------------

def test_a_plain_pitch_has_no_anchors():
    """Off by default, so every existing caller emits byte-for-byte what it did before."""
    assert "kit-a" not in _html()


def test_a_clickable_pitch_wraps_every_kit_in_an_anchor_carrying_the_player_id():
    html = _html(clickable=True)
    import re
    ids = re.findall(r'<a href="#" id="(\d+)" class="kit-a">', html)
    assert ids == [str(i) for i in list(range(1, 12)) + [12, 13, 14, 15]]
    assert html.count('class="kit"') == 15          # one anchor per card, none lost


def test_the_anchor_does_not_look_like_a_link():
    """A blue underlined shirt would be worse than no tap at all."""
    assert "text-decoration:none" in _html(clickable=True)


def test_clickable_changes_nothing_else_about_the_markup():
    plain, tappable = _html(), _html(clickable=True)
    import re
    stripped = re.sub(r'<a href="#" id="\d+" class="kit-a">', "", tappable).replace("</a>", "")
    stripped = stripped.replace("<style>.kit-a{text-decoration:none;color:inherit;display:block;}</style>", "")
    assert stripped == plain


# ---- ported from the AppTest suite (ADR-133 moved them here) ------------------------

def test_bench_cards_show_their_sub_role():
    """US-246: the bench is ordered by priority and each card carries its role badge."""
    xi, bench = _squad()
    roles = {12: "GK", 13: "1st", 14: "2nd", 15: "3rd"}
    html = pitch_html(xi, bench, captain_id=1, xp_by_id={}, photos={}, next_opp={}, bench_roles=roles)
    assert html.count('class="s-badge"') == 4
    # ordered by priority, so the first-choice sub's badge precedes the third's
    assert html.index(">1<") < html.index(">3<")


def test_set_piece_duty_shows_on_the_kit_card():
    """US-249/250 (ADR-081): a first-choice taker is flagged on the pitch, not just in a table."""
    xi, bench = _squad()
    xi[5] = _p(6, "MID", penalties_order=1, corners_order=1, freekicks_order=1)
    html = pitch_html(xi, bench, captain_id=1, xp_by_id={}, photos={}, next_opp={})
    assert sum(html.count(e) for e in ("⚽", "🚩", "🎯")) >= 3
