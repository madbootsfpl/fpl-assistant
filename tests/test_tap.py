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
