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


def render_tappable_pitch(xi, bench, *, select_key, label_for, key="pitch_tap", **kw):
    """Draw the pitch so tapping a shirt selects that player. Returns the tapped id, or None.

    `select_key` is the `session_state` key the *selectbox* uses, and `label_for` maps a player row to that
    selectbox's label — the tap writes the same state the dropdown does, so the ADR-108 panel downstream is
    reused **entirely unchanged**. Only the input is new.

    Must be called **before** the selectbox is created: Streamlit forbids writing a widget's state once that
    widget exists in the run, and the pitch already renders above the picker.
    """
    detector = _detector()
    if detector is None:
        render_pitch(xi, bench, **kw)
        return None

    html = pitch_html(xi, bench, clickable=True, **kw)
    clicked = detector(html, key=key)
    if not clicked:
        return None

    by_id = {str(p["id"]): p for p in list(xi) + list(bench)}
    player = by_id.get(str(clicked))
    if player is None:                                   # a stale id after a transfer — ignore, don't crash
        return None
    st.session_state[select_key] = label_for(player)
    return player["id"]
