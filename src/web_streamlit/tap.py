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

from src.web_streamlit.pitch import pitch_html, render_pitch, set_piece_key


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


CLEAR_ID = "sel:clear"      # the pitch background — see `render_tappable_pitch`


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


def _fresh(clicked, key):
    """A click the current run hasn't acted on yet, else None.

    The component keeps handing back its **last** click on every rerun, so a tap must act once — on the run
    where it happened. Without this, every later rerun re-writes the selection back to the last tap, and the
    picker beside it can never override one. (Found while debugging ADR-135; it is a real bug in its own
    right, and it is shared by every tappable surface, which is why it lives here.)
    """
    seen_key = f"{key}__seen"
    if not clicked or st.session_state.get(seen_key) == clicked:
        return None
    st.session_state[seen_key] = clicked
    return clicked


def _write_selection(select_key, label, none_label):
    """Select `label`, or **clear** the selection when the same thing is tapped twice (US-444).

    A tap that only ever selects is a one-way door: the owner reported the condensed player card could not be
    dismissed without leaving the page and coming back. The dropdown beside it *could* clear it — its first
    option is the `none_label` — but nobody looks in a dropdown to undo a tap, they tap again.

    `none_label` is the caller's "nothing selected" option. Passing `None` means this surface has no such
    option, so tapping the selected item just re-selects it rather than writing a state the picker can't show.
    """
    if none_label is not None and st.session_state.get(select_key) == label:
        st.session_state[select_key] = none_label
        return False
    st.session_state[select_key] = label
    return True


def select_from_html(html, *, select_key, label_by_id, key, prefix="team", none_label=None):
    """Render clickable `html` and turn a tap on one of its anchors into a selection (ADR-158).

    The generalisation of ADR-133's gesture beyond the pitch: anchors carry `id="{prefix}:{something}"`, and
    `label_by_id` maps that something to the label of the **selectbox** named by `select_key` — so the tap
    writes exactly the state the dropdown writes, and everything downstream is reused unchanged.

    Returns the tapped id, or None. The caller renders its own non-clickable HTML when `available()` is
    False; this never draws a fallback, because a strip and a pitch do not degrade to the same thing.

    Must be called **before** the selectbox exists in the run — Streamlit forbids writing a widget's state
    once that widget has been created.
    """
    detector = _detector()
    if detector is None:
        return None
    clicked = _fresh(detector(html, key=key), key)
    if not clicked:
        return None
    action, _, raw = str(clicked).partition(":")
    if action != prefix or raw not in label_by_id:        # not ours, or stale after a data refresh
        return None
    _write_selection(select_key, label_by_id[raw], none_label)
    return raw


def render_tappable_pitch(xi, bench, *, select_key, label_for, key="pitch_tap", none_label="—", **kw):
    """Draw the pitch so tapping a shirt selects that player. Returns the id that was tapped, or None.

    **Tapping the selected shirt again clears the selection** (US-444) — `none_label` is the picker's
    "nothing selected" option, which the tap writes to undo itself. The return value says which shirt was
    tapped, not what happened to the selection; `session_state[select_key]` holds that.

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
    clicked = _fresh(detector(html, key=key), key)
    # ADR-178 — the set-piece key, on **this** path too. The fallback above delegates to `render_pitch`, which
    # prints it; this branch builds the HTML itself and would otherwise be the one pitch with no key — and it
    # is the golden page's pitch, so it would have been the only one that mattered. Found by mutation-testing
    # the guard: deleting the caption from `render_pitch` left every test green, because My Squad never called
    # it. The text has one definition (`set_piece_key`); only the emitting differs.
    if key_text := set_piece_key(list(xi) + list(bench)):
        st.caption(key_text)
    if not clicked:
        return None

    # US-444 rev — **tapping the same shirt twice cannot work, and this is why.** `st_click_detector` reports
    # the id of the *last* element clicked; clicking the same one again produces the identical value, so
    # Streamlit sees no state change, does not rerun, and the second tap never reaches Python at all. (Even
    # when something else forces a rerun, `_fresh` correctly suppresses it — it cannot tell a real second tap
    # from the replay it exists to swallow.)
    #
    # So the gesture is the other half of what the owner asked for: *"click pitch **or** the player again"*.
    # The grass behind the shirts is a different anchor, so it always returns a different id, and it always
    # gets through.
    if str(clicked) == CLEAR_ID:
        if none_label is not None:
            st.session_state[select_key] = none_label
        return None

    pid = parse(clicked)
    by_id = {p["id"]: p for p in list(xi) + list(bench)}
    player = by_id.get(pid)
    if player is None:                                   # not ours, or a stale id after a transfer — ignore
        return None
    _write_selection(select_key, label_for(player), none_label)
    return player["id"]
