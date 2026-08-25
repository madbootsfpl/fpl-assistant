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
    """A clicked anchor id → `(action, player_id)`, or `(None, None)` if it isn't one of ours.

    Ids are `sel:123` / `cap:123` / `sub:123` / `cmp:123` (ADR-135) — the action and the player in one string,
    because the component hands back a single id and a tap has to say *what* as well as *who*. Bare numeric ids
    from before ADR-135 still read as a selection, so a stale component value can't crash a render.
    """
    if not clicked:
        return None, None
    text = str(clicked)
    action, _, raw = text.partition(":")
    if not raw:                                    # a bare id — the pre-ADR-135 form
        action, raw = "sel", text
    if action not in ("sel", "cap", "sub", "cmp") or not raw.isdigit():
        return None, None
    return action, int(raw)


def render_tappable_pitch(xi, bench, *, select_key, label_for, key="pitch_tap", **kw):
    """Draw the pitch so tapping a shirt selects that player. Returns the tapped id, or None.

    `select_key` is the `session_state` key the *selectbox* uses, and `label_for` maps a player row to that
    selectbox's label — the tap writes the same state the dropdown does, so the ADR-108 panel downstream is
    reused **entirely unchanged**. Only the input is new.

    Returns `(action, player_id)` — `sel` also writes the selection, the rest are for the caller to act on
    (ADR-135). `(None, None)` when nothing was tapped.

    Must be called **before** the selectbox is created: Streamlit forbids writing a widget's state once that
    widget exists in the run, and the pitch already renders above the picker.
    """
    detector = _detector()
    if detector is None:
        # The component isn't here — draw the ordinary pitch and report no action, so every caller has one
        # shape to handle rather than two.
        render_pitch(xi, bench, **{k: v for k, v in kw.items() if k not in ("selected_id", "armed")})
        return None, None

    html = pitch_html(xi, bench, clickable=True, **kw)
    clicked = detector(html, key=key)
    action, pid = parse(clicked)
    if action is None:
        return None, None

    by_id = {p["id"]: p for p in list(xi) + list(bench)}
    player = by_id.get(pid)
    if player is None:                                   # a stale id after a transfer — ignore, don't crash
        return None, None
    if action == "sel":
        st.session_state[select_key] = label_for(player)
    return action, player["id"]
