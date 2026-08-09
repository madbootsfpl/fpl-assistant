"""Persistent "remember me" for the beta gate (ADR-099).

A thin, **guarded** seam so a tester who has passed the access gate on a device is remembered
across a full browser refresh — `st.session_state` is wiped on a refresh/new tab, so the pass
otherwise has to be re-typed every time.

The read and write halves are deliberately asymmetric, because Streamlit is:

- **read** — native + read-only via `st.context.cookies` (the cookies the browser sent with the
  page request). Available **immediately** on a cold load, with **no component and no "loading"
  rerun** — so restoring a session never flashes the gate.
- **write** — Streamlit has no native "set cookie", and a DIY `document.cookie` runs in a
  sandboxed component iframe (wrong origin), so setting one needs a small cookie component
  (`streamlit-cookies-controller`, the single dependency). It is imported lazily and quarantined
  in `_controller()`.

Everything degrades to a **no-op** (`read()` → `None`, `write`/`clear` do nothing) if the browser
blocks cookies or the component is missing/erroring — so import, CI, AppTest and private-mode paths
stay safe and the gate falls back to its per-session behaviour ("off by default / fail safe",
ADR-099). The gate must therefore treat `read()` returning `None` as simply "not remembered".

What's stored is *what proves the pass* in the active gate mode — the registered email (registration
mode) or the shared code (shared-code mode). The gate **re-validates** that value on load
(`user_store.is_registered` / `== FPL_ACCESS_CODE`), so a pruned tester or a rotated code invalidates
the cookie: it remembers a pass, it does not grant access.
"""

import streamlit as st

COOKIE = "fpl_beta"       # first-party cookie name (the value = the registered email or the shared code)
TTL_DAYS = 30             # ~30-day remember; iOS Safari ITP caps JS-set cookies at ~7 regardless (ADR-099)
_DAY_SECONDS = 24 * 60 * 60


def _request_cookies():
    """The cookies the browser sent with this page request (read-only, native — no component/iframe)."""
    return st.context.cookies


def read():
    """The remembered value from this request's cookies, or ``None`` if absent / unreadable.

    Native and instant on a cold load (no component, no "loading" rerun), so the gate can restore a
    remembered session without ever flashing the prompt.
    """
    try:
        return _request_cookies().get(COOKIE) or None
    except Exception:
        return None


def _controller():
    """The cookie component — used only to *write* (Streamlit reads cookies natively but can't set them).

    Isolated so the one dependency and any failure live here (the callers below swallow exceptions).
    Constructing it renders once per session then reuses the cached copy, so a per-call construct is safe.
    """
    from streamlit_cookies_controller import CookieController
    return CookieController()


def write(value, days=TTL_DAYS):
    """Best-effort: remember ``value`` for ~``days`` via a first-party cookie. A no-op if ``value`` is
    empty or the component is unavailable (a browser that blocks cookies just isn't remembered).

    Note for callers: render this on a *clean* run — a ``st.rerun()`` immediately after would discard the
    set component before it reaches the browser. The gate defers the write to the post-login run for this.
    """
    if not value:
        return
    try:
        _controller().set(COOKIE, value, max_age=days * _DAY_SECONDS)
    except Exception:
        return


def clear():
    """Best-effort: forget the cookie (plumbing for a future "not you? / log out"). No-op if the
    component is unavailable."""
    try:
        _controller().remove(COOKIE)
    except Exception:
        return
