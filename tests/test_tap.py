"""Tests for the tap-a-shirt input (ADR-133).

The tap is deliberately **additive**: the dropdown stays, so these mostly pin the safety properties — that a
missing component degrades to the ordinary pitch, and that a tap writes exactly the state the dropdown writes,
so the ADR-108 panel downstream is reused unchanged.
"""

import src.web_streamlit.tap as tap


def _p(pid, name, team="ARS", pos="MID"):
    return {"id": pid, "web_name": name, "team": team, "position": pos, "price": 6.0}


def _label(p):
    return f"{p['web_name']} · {p['team']}"


def test_a_missing_component_falls_back_to_the_ordinary_pitch(monkeypatch):
    """The failure mode must be "the tap stops working", never a broken golden page."""
    rendered = {}
    monkeypatch.setattr(tap, "_detector", lambda: None)
    monkeypatch.setattr(tap, "render_pitch", lambda xi, bench, **kw: rendered.update(ok=True))
    out = tap.render_tappable_pitch([_p(1, "A")], [], select_key="k", label_for=_label,
                                    captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert out is None and rendered == {"ok": True}


def test_a_tap_writes_the_same_state_the_dropdown_writes(monkeypatch):
    """One selection state, two inputs — which is why the ADR-108 panel needs no changes at all."""
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: "7"))
    st.session_state.clear()
    out = tap.render_tappable_pitch([_p(7, "Virgil", "LIV", "DEF")], [], select_key="pa_pick",
                                    label_for=_label, captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert out == 7 and st.session_state["pa_pick"] == "Virgil · LIV"


def test_no_tap_leaves_the_selection_alone(monkeypatch):
    """A rerun for any other reason must not re-select whatever was tapped last."""
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: ""))
    st.session_state.clear()
    out = tap.render_tappable_pitch([_p(7, "Virgil")], [], select_key="pa_pick", label_for=_label,
                                    captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert out is None and "pa_pick" not in st.session_state


def test_a_stale_id_is_ignored_rather_than_crashing(monkeypatch):
    """The component holds the last id it saw; a transfer can retire that player between runs."""
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: "999"))
    st.session_state.clear()
    out = tap.render_tappable_pitch([_p(7, "Virgil")], [], select_key="pa_pick", label_for=_label,
                                    captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert out is None and "pa_pick" not in st.session_state


def test_an_import_failure_is_treated_as_no_component(monkeypatch):
    """Any import problem — missing, broken, incompatible — degrades the same way."""
    import builtins
    real = builtins.__import__

    def boom(name, *a, **kw):
        if name == "st_click_detector":
            raise ImportError("simulated")
        return real(name, *a, **kw)

    monkeypatch.setattr(builtins, "__import__", boom)
    assert tap._detector() is None


def test_the_caption_names_the_tap_only_when_the_tap_works(monkeypatch):
    """The fallback is invisible to users by design, which left no way to tell a working deploy from a broken
    one without tapping and inferring. The caption is now both the hint that the gesture exists and the signal
    that the component loaded."""
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: ""))
    assert tap.available() is True
    monkeypatch.setattr(tap, "_detector", lambda: None)
    assert tap.available() is False


# ---- the ids ------------------------------------------------------------------------

def test_both_id_shapes_read_as_a_selection():
    """`sel:7` is what the pitch emits. A bare `7` is the pre-ADR-135 form, and `cap:`/`sub:`/`cmp:` were
    ADR-135's action anchors — now reverted. All three shapes can be sitting in a live session's component
    state right now, so parsing must be total: select, or ignore, but never crash a render."""
    assert tap.parse("sel:7") == 7
    assert tap.parse("7") == 7


def test_a_retired_action_id_is_ignored():
    """A session still holding `cap:7` from the reverted menu must not silently act on it."""
    for stale in ("cap:7", "sub:3", "cmp:9"):
        assert tap.parse(stale) is None


def test_an_unrecognised_id_is_ignored():
    for bad in ("", None, "bogus:1", "sel:x", "sel"):
        assert tap.parse(bad) is None


def test_a_replayed_click_fires_once(monkeypatch):
    """`click_detector` hands back its **last** click on every rerun. Without this guard every later rerun
    re-wrote the selection back to the last-tapped shirt, so the dropdown could never override a tap."""
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: "sel:7"))
    st.session_state.clear()
    fires = [tap.render_tappable_pitch([_p(7, "Virgil")], [], select_key="k", label_for=_label,
                                       captain_id=None, xp_by_id={}, photos={}, next_opp={})
             for _ in range(4)]
    assert fires[0] == 7
    assert all(f is None for f in fires[1:]), "a replayed click must not fire again"


def test_a_genuinely_new_click_still_fires(monkeypatch):
    """The guard must not swallow the next real tap."""
    import streamlit as st
    seq = iter(["sel:7", "sel:7", "sel:9"])
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: next(seq)))
    st.session_state.clear()
    xi = [_p(7, "Virgil"), _p(9, "Salah")]
    kw = dict(select_key="k", label_for=_label, captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert tap.render_tappable_pitch(xi, [], **kw) == 7
    assert tap.render_tappable_pitch(xi, [], **kw) is None
    assert tap.render_tappable_pitch(xi, [], **kw) == 9


def test_the_fallback_pitch_keeps_its_hover(monkeypatch):
    """ADR-139 leans on ADR-133's fallback being a *plain* pitch, so this pins the join between them.

    Hover is suppressed only on a tappable pitch, where a tap reveals the card in the panel instead. When the
    click component fails to load there is no tap — so the fallback must draw the ordinary pitch, hover and
    all, and the page degrades to exactly its old behaviour. The failure mode stays "the tap stops working",
    never "there is no way to see a card".
    """
    seen = {}
    monkeypatch.setattr(tap, "_detector", lambda: None)
    monkeypatch.setattr(tap, "render_pitch", lambda xi, bench, **kw: seen.update(kw))
    tap.render_tappable_pitch([_p(1, "A")], [], select_key="k", label_for=_label,
                              captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert seen.get("clickable") is not True, "the fallback must not claim to be tappable — hover depends on it"


# ---- The same gesture beyond the pitch (ADR-158) --------------------------------------------------
# The roadmap asked for the league-scan rows to inherit SELECTION — "a row tap that selects is ADR-133's shape
# and is still wanted; a row tap that opens a menu is ADR-135 again." These pin that it is the same gesture,
# with the same safety properties, rather than a second implementation of it.

_TEAMS = {"ARS": "Arsenal", "LIV": "Liverpool"}


def test_a_row_tap_selects_that_club(monkeypatch):
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: "team:LIV"))
    st.session_state.clear()
    out = tap.select_from_html("<a id='team:LIV'>", select_key="team_dna_pick",
                               label_by_id=_TEAMS, key="scan")
    assert out == "LIV" and st.session_state["team_dna_pick"] == "Liverpool"


def test_a_replayed_click_does_not_reselect_on_every_rerun(monkeypatch):
    """The component hands back its LAST click forever, so without the guard the picker could never override
    a tap — the bug found while debugging ADR-135, now shared by both surfaces because it is shared code."""
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: "team:LIV"))
    st.session_state.clear()
    assert tap.select_from_html("<a>", select_key="k", label_by_id=_TEAMS, key="scan") == "LIV"

    st.session_state["k"] = "Arsenal"                    # …the user then picks another club from the dropdown
    assert tap.select_from_html("<a>", select_key="k", label_by_id=_TEAMS, key="scan") is None
    assert st.session_state["k"] == "Arsenal", "the replayed click must not overwrite the picker"


def test_an_unknown_or_stale_id_is_ignored(monkeypatch):
    import streamlit as st
    for clicked in ("team:XXX", "sel:7", "", "nonsense"):
        monkeypatch.setattr(tap, "_detector", lambda c=clicked: (lambda html, key=None: c))
        st.session_state.clear()
        assert tap.select_from_html("<a>", select_key="k", label_by_id=_TEAMS, key="scan") is None
        assert "k" not in st.session_state


def test_a_missing_component_selects_nothing_and_draws_nothing(monkeypatch):
    """Unlike the pitch, this draws no fallback — a strip and a pitch don't degrade to the same thing, so the
    caller renders its own plain HTML. What must hold is that it is silent, not that it is invisible."""
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: None)
    st.session_state.clear()
    assert tap.select_from_html("<a>", select_key="k", label_by_id=_TEAMS, key="scan") is None
    assert "k" not in st.session_state


# ---- Tapping the same thing twice clears it (US-444) -----------------------------------------------
# Owner: *"Clicking on a player shows the condensed player profile, however you cannot release it unless you
# leave the page and return."* The picker could always clear it — its first option is "—" — but nobody opens
# a dropdown to undo a tap; they tap again.

def test_tapping_the_pitch_background_clears_the_selection(monkeypatch):
    """US-444 rev — **tapping the same shirt twice cannot work**, and the first fix assumed it could.

    `st_click_detector` reports the id of the *last* element clicked. Click the same shirt again and the value
    is identical, so Streamlit sees no state change, does not rerun, and Python never hears about it. (Even on
    a rerun forced by something else, the replay guard correctly swallows it — it cannot distinguish a real
    second tap from the replay it exists to suppress.) The owner reported exactly this: *"the player double
    click and then release does not work."*

    The grass behind the shirts is a different anchor, so it always returns a different id and always gets
    through — and it is the other half of what was asked for: *"click pitch **or** the player again"*.
    """
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: tap.CLEAR_ID))
    st.session_state.clear()
    st.session_state["pa_pick"] = "Virgil · LIV"
    out = tap.render_tappable_pitch([_p(7, "Virgil", "LIV", "DEF")], [], select_key="pa_pick",
                                    label_for=_label, captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert out is None
    assert st.session_state["pa_pick"] == "—"


def test_the_background_tap_does_nothing_where_there_is_no_none_option(monkeypatch):
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: tap.CLEAR_ID))
    st.session_state.clear()
    st.session_state["pa_pick"] = "Virgil · LIV"
    tap.render_tappable_pitch([_p(7, "Virgil", "LIV", "DEF")], [], select_key="pa_pick", none_label=None,
                              label_for=_label, captain_id=None, xp_by_id={}, photos={}, next_opp={})
    assert st.session_state["pa_pick"] == "Virgil · LIV"


def test_tapping_a_different_shirt_moves_the_selection_rather_than_clearing_it(monkeypatch):
    import streamlit as st
    st.session_state.clear()
    st.session_state["pa_pick"] = "Virgil · LIV"
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: "9"))
    tap.render_tappable_pitch([_p(7, "Virgil", "LIV", "DEF"), _p(9, "Salah", "LIV", "MID")], [],
                              select_key="pa_pick", label_for=_label, captain_id=None, xp_by_id={},
                              photos={}, next_opp={})
    assert st.session_state["pa_pick"] == "Salah · LIV"


def test_a_surface_with_no_none_option_never_writes_one(monkeypatch):
    """The Team DNA scan's picker has no '—' entry, so clearing would write a state it cannot display."""
    import streamlit as st
    monkeypatch.setattr(tap, "_detector", lambda: (lambda html, key=None: "team:LIV"))
    st.session_state.clear()
    tap.select_from_html("<a>", select_key="k", label_by_id=_TEAMS, key="scan")
    st.session_state.pop("scan__seen")
    tap.select_from_html("<a>", select_key="k", label_by_id=_TEAMS, key="scan")
    assert st.session_state["k"] == "Liverpool", "no none_label → the tap re-selects rather than clearing"
