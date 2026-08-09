"""Persistent "remember me" for the beta gate (ADR-099).

A thin, **guarded** seam so a tester who has passed the access gate on a device is remembered
across a full browser refresh — `st.session_state` is wiped on a refresh/new tab, so the pass
otherwise has to be re-typed every time.

**Read and write both go through the cookie component** (`streamlit-cookies-controller`, the single
dependency, quarantined in `_controller()`). This is the fix from Sprint 134: an earlier version read
natively via `st.context.cookies`, but that reads the cookies the browser sends to the *Streamlit
server* on the top-level request, while the component writes `document.cookie` **inside its own
iframe** — two different cookie jars, so the native read never saw the component's write and nothing
persisted (verified on Safari + Chrome). Reading through the same component keeps write and read in the
*same* jar, so a remembered value survives a refresh.

The cost of component-read: the component delivers its value to Python on a **rerun**, not the first
run of a session — so `read()` returns `None` on a cold load's first run even when a valid cookie
exists. The gate handles this by waiting exactly one run (`access._maybe_wait_for_cookie`, showing a
neutral placeholder instead of flashing the prompt) — hence `available()`, which tells the gate whether
a `None` read might just be "still loading" vs "no component at all".

Everything degrades to a **no-op** (`read()` → `None`, `write`/`clear` do nothing, `available()` →
`False`) if the browser blocks cookies or the component is missing/erroring — so import, CI, AppTest and
private-mode paths stay safe and the gate falls back to its per-session behaviour ("off by default /
fail safe", ADR-099). The gate must therefore treat `read()` returning `None` as simply "not remembered".

What's stored is *what proves the pass* in the active gate mode — the registered email (registration
mode) or the shared code (shared-code mode). The gate **re-validates** that value on load
(`user_store.is_registered` / `== FPL_ACCESS_CODE`), so a pruned tester or a rotated code invalidates
the cookie: it remembers a pass, it does not grant access.
"""

COOKIE = "fpl_beta"       # first-party cookie name (the value = the registered email or the shared code)
TTL_DAYS = 30             # ~30-day remember; iOS Safari ITP caps JS-set cookies at ~7 regardless (ADR-099)
_DAY_SECONDS = 24 * 60 * 60


def _controller():
    """The cookie component — reads *and* writes the cookie (same iframe jar, so a write is readable back).

    Isolated so the one dependency and any failure live here (the callers below swallow exceptions).
    Constructing it renders the read component **once per session** (it caches into `st.session_state`),
    so constructing a fresh one per read/write/available is safe (no duplicate widget).
    """
    from streamlit_cookies_controller import CookieController
    return CookieController()


def read():
    """The remembered value from the cookie, or ``None`` if absent / unreadable / **not yet delivered**.

    Read through the component (same jar as `write`). The component syncs its value on a *rerun*, so this
    is ``None`` on the first run of a cold load even when a cookie exists — the gate waits one run for it
    (see `access._maybe_wait_for_cookie`), using `available()` to tell "still loading" from "no component".
    """
    try:
        return _controller().get(COOKIE) or None
    except Exception:
        return None


def available():
    """True if the cookie component can be constructed — so a ``None`` `read()` may just be "still loading",
    not "no component". The gate uses this to decide whether to wait one run for the cookie to arrive (and to
    never wait when there's no component, e.g. a headless test or a browser with the component blocked)."""
    try:
        _controller()
        return True
    except Exception:
        return False


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
    """Best-effort: forget the cookie (the "Log out" control drives this). No-op if the component is
    unavailable. Also deferred to a clean run by the gate, so a `st.rerun()` can't discard the remove."""
    try:
        _controller().remove(COOKIE)
    except Exception:
        return
