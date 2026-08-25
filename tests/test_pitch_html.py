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


def test_a_clickable_pitch_gives_every_kit_a_select_anchor():
    """ADR-135 changed the id from a bare number to `sel:<id>`, because a tap now has to say *what* as well as
    *who*. Every card still gets exactly one."""
    html = _html(clickable=True)
    import re
    ids = re.findall(r'<a href="#" id="sel:(\d+)" class="kit-a">', html)
    assert ids == [str(i) for i in list(range(1, 12)) + [12, 13, 14, 15]]
    # `class="kit` also matches kit-a / kit-pop / kit-acts, so count the card container exactly.
    assert len(re.findall(r'<div class="kit[" ]', html)) == 15


def test_actions_appear_on_the_selected_card_only():
    """The decision that keeps this a *density* change: three icons on fifteen cards would trade page height
    for pitch noise. Only the card you're acting on carries them."""
    import re
    # ADR-135 rev: a labelled **menu**, not a row of icons on the card — a 104px card had no room for three
    # actions, so they came out tiny, unlabelled and fighting the hover popover (owner screenshot, 2026-08-25).
    assert 'class="kit-menu"' not in _html(clickable=True)
    one = _html(clickable=True, selected_id=4)
    assert one.count('class="kit-menu"') == 1
    for label in ("Make captain", "Substitute", "Compare"):
        assert label in one, f"the menu should name its actions, not just glyph them: {label}"
    assert set(re.findall(r'id="(\w+):4"', one)) == {"sel", "cap", "sub", "cmp"}


def test_an_armed_action_is_visibly_armed():
    """A two-tap flow you can't see you're in is worse than the picker it replaced."""
    armed = _html(clickable=True, selected_id=4, armed="sub")
    assert 'class="armed"' in armed and "now tap who swaps in" in armed
    assert 'class="armed"' not in _html(clickable=True, selected_id=4)


def test_the_action_anchors_are_siblings_never_nested():
    """HTML forbids <a> inside <a> — a browser silently closes the outer one, which would break selection."""
    import re
    html = _html(clickable=True, selected_id=4)
    assert not re.search(r'<a [^>]*>(?:(?!</a>).)*<a ', html, re.S)


def test_the_anchor_does_not_look_like_a_link():
    """A blue underlined shirt would be worse than no tap at all."""
    assert "text-decoration:none" in _html(clickable=True)


def test_a_plain_pitch_is_unchanged_by_all_of_this():
    """Every non-tapping caller — Squad Lab's build pitch, older tests — must emit exactly what it always did."""
    plain = _html()
    assert "kit-a" not in plain and "kit-acts" not in plain and "<a " not in plain
    assert plain.count('class="kit"') == 15


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


def test_every_link_state_is_pinned_because_the_iframe_ships_bootstrap():
    """The component renders inside an iframe carrying `bootstrap.min.css`, which styles `a:visited` blue and
    underlined — so the card you had just clicked turned into a visible hyperlink while the others looked fine
    (owner screenshot, 2026-08-25). Styling only the base `a` state is not enough inside someone else's CSS."""
    html = _html(clickable=True, selected_id=4)
    for state in (":link", ":visited", ":hover", ":active", ":focus"):
        assert f".kit-a{state}" in html, f"unpinned link state on the card: {state}"
        assert f".kit-menu a{state}" in html, f"unpinned link state in the menu: {state}"


def test_the_hover_popover_is_suppressed_while_a_card_is_selected():
    """One surface at a time. The menu and the hover card were opening together and fighting for the space."""
    assert ".kit.selected .kit-pop{display:none" in _html(clickable=True, selected_id=4)
