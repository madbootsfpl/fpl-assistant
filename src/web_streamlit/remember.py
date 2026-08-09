"""Persistent "remember me" for the beta gate (ADR-099).

A thin, **guarded** seam over a first-party browser cookie so a tester who has passed
the access gate on a device is remembered across a full browser refresh — `st.session_state`
is wiped on a refresh/new tab, so the pass otherwise has to be re-typed every time.

The whole point of this module is *isolation*: the cookie component (a single dependency,
`streamlit-cookies-controller`) is imported lazily and every call is wrapped so that a
missing or erroring component degrades to a **no-op** (`read()` → `None`, `write`/`clear`
do nothing). That keeps import, CI, AppTest and private-mode paths safe and lets the gate
fall back to its per-session behaviour — "off by default / fail safe" (ADR-099). The gate
must therefore treat `read()` returning `None` as simply "not remembered", never an error.

What's stored is *what proves the pass* in the active gate mode — the registered email
(registration mode) or the shared code (shared-code mode). The gate **re-validates** that
value on load (`user_store.is_registered` / `== FPL_ACCESS_CODE`), so a pruned tester or a
rotated code invalidates the cookie: it remembers a pass, it does not grant access.
"""

COOKIE = "fpl_beta"       # first-party cookie name (the value = the registered email or the shared code)
TTL_DAYS = 30             # ~30-day remember; iOS Safari ITP caps JS-set cookies at ~7 regardless (ADR-099)
_DAY_SECONDS = 24 * 60 * 60


def _controller():
    """The cookie component, or raise if unavailable.

    Isolated in one place so the dependency and any failure live here (the callers below
    swallow exceptions). Constructing it renders the read component on first use per session,
    then reuses the cached copy — so calling this per read/write is safe (no duplicate widget).
    """
    from streamlit_cookies_controller import CookieController
    return CookieController()


def read():
    """The remembered value, or ``None`` if unavailable / not set / still loading / erroring.

    On a cold browser run the component hasn't delivered the cookie yet, so this returns
    ``None`` on that first run and the real value on the follow-up rerun (the gate handles it).
    """
    try:
        value = _controller().get(COOKIE)
    except Exception:
        return None
    return value or None


def write(value, days=TTL_DAYS):
    """Best-effort: remember ``value`` for ~``days``. A no-op if ``value`` is empty or the
    component is unavailable (so a browser that blocks cookies just isn't remembered)."""
    if not value:
        return
    try:
        _controller().set(COOKIE, value, max_age=days * _DAY_SECONDS)
    except Exception:
        return


def clear():
    """Best-effort: forget the cookie (plumbing for a future "not you? / log out"). No-op if
    the component is unavailable."""
    try:
        _controller().remove(COOKIE)
    except Exception:
        return
