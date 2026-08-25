"""Tap a shirt to select a player (ADR-133).

The gesture testers kept asking for — *"FFH pops a menu on clicking a player"* — delivered as an **additional**
input, never a replacement. The dropdown beside it stays permanently, which is what keeps this cheap:

* `AppTest` drives the selectbox exactly as before, so the golden page loses **no** coverage — the component
  boundary is precisely where test coverage stops needing to reach.
* Keyboard and screen-reader users keep a working path.
* If the component is missing, blocked or broken, this falls back to the ordinary pitch and the page behaves
  exactly as it did before ADR-133. The failure mode is "the tap stops working", never a broken page.

`st-click-detector` ships a pre-built frontend, so there is no build step here (spike 185).
"""

import streamlit as st

from src.web_streamlit.pitch import pitch_html, render_pitch


def _detector():
    """The click component, or None if it isn't importable.

    Imported lazily and defensively: this runs on the golden page, and a dependency problem must degrade to a
    plain pitch rather than take the page down.
    """
    try:
        from st_click_detector import click_detector
    except Exception:                                    # noqa: BLE001 — any import failure degrades the same way
        return None
    return click_detector


def available() -> bool:
    """Is the tap actually live in this deployment?

    Exposed so the page can **say so**. The fallback is deliberately invisible to users — a pitch that quietly
    behaves as it always did — but that left no way to tell a working deploy from a broken one without tapping
    a shirt and inferring from the picker. A caption that mentions tapping only when tapping works is both the
    diagnostic and the only thing telling users the gesture exists at all.
    """
    return _detector() is not None


def parse(clicked):
    """A clicked anchor id → a player id, or None if it isn't one of ours.

    Ids are `sel:123`. The prefix is vestigial — ADR-135 briefly put `cap:` / `sub:` / `cmp:` action anchors on
    the shirt too and that is reverted — but it is kept because ids of *both* shapes may be sitting in a live
    session's component state, and neither must crash a render. A bare `123` reads as a selection as well.
    """
    if not clicked:
        return None
    text = str(clicked)
    action, _, raw = text.partition(":")
    if not raw:                                          # a bare id
        action, raw = "sel", text
    if action != "sel" or not raw.isdigit():
        return None
    return int(raw)


def render_tappable_pitch(xi, bench, *, select_key, label_for, key="pitch_tap", **kw):
    """Draw the pitch so tapping a shirt selects that player. Returns the tapped id, or None.

    `select_key` is the `session_state` key the *selectbox* uses, and `label_for` maps a player row to that
    selectbox's label — the tap writes the same state the dropdown does, so the ADR-108 panel downstream is
    reused **entirely unchanged**. Only the input is new.

    Selecting is *all* it does. ADR-135 tried carrying actions on the shirt as well and was reverted: a tap
    costs a full rerun (with a `decision_xp` recompute), so a two-tap flow cost two, and the menu collided
    with the hover card. One tap → one selection is the whole gesture.

    Must be called **before** the selectbox is created: Streamlit forbids writing a widget's state once that
    widget exists in the run, and the pitch already renders above the picker.
    """
    detector = _detector()
    if detector is None:
        # The component isn't here — draw the ordinary pitch and report no action, so every caller has one
        # shape to handle rather than two.
        render_pitch(xi, bench, **{k: v for k, v in kw.items() if k != "selected_id"})
        return None

    html = pitch_html(xi, bench, clickable=True, **kw)
    clicked = detector(html, key=key)

    # The component keeps handing back its **last** click on every rerun, so a tap must act once — on the run
    # where it happened. Without this, every later rerun re-wrote the selection back to the last-tapped shirt,
    # so the dropdown beside the pitch could never override a tap. (Found while debugging ADR-135; kept,
    # because it is a real bug in its own right.)
    seen_key = f"{key}__seen"
    if not clicked or st.session_state.get(seen_key) == clicked:
        return None
    st.session_state[seen_key] = clicked

    pid = parse(clicked)
    by_id = {p["id"]: p for p in list(xi) + list(bench)}
    player = by_id.get(pid)
    if player is None:                                   # not ours, or a stale id after a transfer — ignore
        return None
    st.session_state[select_key] = label_for(player)
    return player["id"]
