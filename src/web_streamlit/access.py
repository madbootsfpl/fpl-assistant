"""Beta access gate + shared config helpers for the Streamlit edge (Sprint 102, ADR-087).

An **opt-in** access-code gate: when `FPL_ACCESS_CODE` is configured (a Streamlit secret or an env var) the app
asks for the code once per session; when it's **unset** the app is open (its current public behaviour). Config
is read through `_secret`, which try/excepts `st.secrets` (it *raises* when there's no `secrets.toml`) and
falls back to `os.environ` — so a missing secrets file never crashes local/CI, and everything stays off by
default. No accounts, no server-side state (the gate flag lives in `st.session_state`).
"""

import os

import streamlit as st

_OK = "_beta_ok"          # session flag: this session passed the gate
_EMAIL = "_beta_email"    # session: the registered tester email (registration mode, ADR-098)
_PENDING = "_beta_remember"  # session: a value to write to the "remember me" cookie on the next clean run (ADR-099)
_CLEAR = "_beta_clear"    # session: a pending cookie *clear* to render on the next clean run (logout, ADR-099)
_FORGOTTEN = "_beta_forgotten"  # session: logged out — ignore the cookie for the rest of this session (ADR-099)


def secret(key: str, default: str | None = None) -> str | None:
    """A config value from `st.secrets`, else `os.environ`, else `default`. Never raises — `st.secrets`
    itself raises when there's no secrets file, so it's read inside a try/except."""
    try:
        val = st.secrets.get(key)          # raises StreamlitSecretNotFoundError when no secrets.toml
    except Exception:
        val = None
    if val is not None:
        return val
    return os.environ.get(key, default)


def _user_cap():
    """`FPL_USER_CAP` as a non-negative int (registration mode), or `None` (unset/invalid → the code/open gate)."""
    raw = secret("FPL_USER_CAP")
    try:
        cap = int(raw)
    except (TypeError, ValueError):
        return None
    return cap if cap >= 0 else None


def require_access() -> None:
    """Gate the page (ADR-087/098). By precedence: **registration** (`FPL_USER_CAP` set + the store configured —
    a shared code + an email, admitted up to the cap), else **shared-code** (`FPL_ACCESS_CODE`), else **open**.
    A no-op once this session has passed. Call once, right after `st.set_page_config(...)`, on every page.

    A "remember me" cookie (ADR-099) lets a device that has passed the gate skip it after a browser refresh: on
    load the cookie is read (natively, no flash) and **re-validated** before it's trusted; on a fresh pass the
    value is written back. Any cookie failure degrades to today's per-session gate. A "Log out" control clears
    both (the cookie clear is deferred here too, so a `st.rerun()` can't drop it)."""
    _flush_clear()                 # render a pending logout cookie-clear on this clean run (before any stop/rerun)
    if st.session_state.get(_OK):
        _flush_remember()          # write the "remember me" cookie on this clean run (post-login/refresh)
        return

    cap = _user_cap()
    if cap is not None:
        from src.web_streamlit import user_store  # lazy: user_store imports `secret` from here (avoid the cycle)
        if user_store.is_configured():
            if _remembered_registration(user_store):   # a still-valid cookie → skip the gate
                return
            _registration_gate(cap)                    # stops the page unless admitted
            return

    # Shared-code / open (ADR-087) — unchanged when registration mode is off.
    code = secret("FPL_ACCESS_CODE")
    if not code:
        return
    if _remembered_code(code):     # a cookie holding the current code → skip the gate
        return
    _code_gate(code)               # stops the page unless the right code is entered


def _flush_remember() -> None:
    """Write a pending "remember me" cookie, once, on a clean run. Deferred from the gate's success because a
    `st.rerun()` there would discard the set component before it reached the browser (ADR-099)."""
    value = st.session_state.pop(_PENDING, None)
    if value:
        from src.web_streamlit import remember
        remember.write(value)


def gate_active() -> bool:
    """True when *some* gate is configured — **registration** (`FPL_USER_CAP` set + the store configured) or
    **shared-code** (`FPL_ACCESS_CODE` set). False = the open/public deploy (so the account/logout UI stays off
    by default there)."""
    cap = _user_cap()
    if cap is not None:
        from src.web_streamlit import user_store
        if user_store.is_configured():
            return True
    return bool(secret("FPL_ACCESS_CODE"))


def logout() -> None:
    """Log out of the beta on this device: drop the session flags, **queue** the cookie clear (deferred, like the
    write — a `st.rerun()` now would discard the remove component), and set `_FORGOTTEN` so the stale cookie can't
    re-admit this session (it's cleared from the browser on the next request). Then rerun to show the gate."""
    st.session_state[_FORGOTTEN] = True
    st.session_state[_CLEAR] = True
    for key in (_OK, _EMAIL, _PENDING):
        st.session_state.pop(key, None)
    st.rerun()


def _flush_clear() -> None:
    """Render a pending cookie *clear* once, on a clean run (this runs before the gate's `st.stop()`, which — unlike
    `st.rerun()` — keeps the run's output, so the remove component reaches the browser). Mirrors `_flush_remember`."""
    if st.session_state.pop(_CLEAR, None):
        from src.web_streamlit import remember
        remember.clear()


def _remembered_code(code: str) -> bool:
    """True (and passes the session) if the "remember me" cookie holds the *current* shared code — so rotating
    `FPL_ACCESS_CODE` invalidates every remember cookie. A stale/absent cookie → False (the gate shows)."""
    if st.session_state.get(_FORGOTTEN):       # just logged out — ignore the (not-yet-cleared) cookie this session
        return False
    from src.web_streamlit import remember
    if remember.read() == code:
        st.session_state[_OK] = True
        return True
    return False


def _remembered_registration(user_store) -> bool:
    """True (and passes the session) if the cookie holds an email that is *still registered* — so a pruned
    tester's stale cookie fails. A store hiccup or an unknown/absent email → False (the gate shows)."""
    if st.session_state.get(_FORGOTTEN):       # just logged out — ignore the (not-yet-cleared) cookie this session
        return False
    from src.web_streamlit import remember
    email = remember.read()
    if not email:
        return False
    try:
        registered = user_store.is_registered(email)
    except Exception:
        return False
    if registered:
        st.session_state[_OK] = True
        st.session_state[_EMAIL] = user_store.clean_email(email)
        return True
    return False


def _code_gate(code: str) -> None:
    """The shared-code prompt (ADR-087). On the right code, remember it and rerun; the write is deferred to the
    post-login run via `_PENDING` so the rerun doesn't drop it. Stops the page until the code is entered."""
    st.title("🔒 FPL Assistant — private beta")
    st.caption("This is a closed beta. Enter the access code you were given to continue.")
    entered = st.text_input("Access code", type="password", key="_beta_code")
    if entered and entered == code:
        st.session_state[_OK] = True
        st.session_state[_PENDING] = code
        st.rerun()
    elif entered:
        st.error("That code isn't right — check the one you were sent.")
    st.stop()


def _registration_gate(cap: int) -> None:
    """The capped email-registration gate (ADR-098): a shared invite code (if set) + an email, admitted up to
    `cap`. Remembers the email in the session; at the cap → a waitlist note. Stops the page until admitted."""
    from src.web_streamlit import user_store
    from src.web_streamlit.cloud_store import store_error

    code = secret("FPL_ACCESS_CODE")
    st.title("🔒 FPL Assistant — private beta")
    st.caption("A closed beta with limited spots. Enter your invite code and email to join.")
    with st.form("beta_register"):
        entered_code = st.text_input("Invite code", type="password") if code else None
        email = st.text_input("Your email", help="So we know who's testing — used only for the beta.")
        joined = st.form_submit_button("Join the beta")

    if joined:
        if code and (entered_code or "") != code:
            st.error("That invite code isn't right — check the one you were sent.")
        else:
            try:
                status = user_store.register(email, cap)
            except ValueError as exc:                       # a malformed email
                status = None
                st.error(str(exc).capitalize() + ".")
            except Exception as exc:                         # a store failure — show the real cause
                status = None
                st.error(f"Couldn't reach the beta register — **{store_error(exc)}**. Try again shortly.")
            if status == "in":
                st.session_state[_OK] = True
                st.session_state[_EMAIL] = user_store.clean_email(email)
                st.session_state[_PENDING] = user_store.clean_email(email)   # remember me (ADR-099)
                st.rerun()
            elif status == "full":
                st.warning(f"The beta is full right now ({cap} testers). More spots open as it grows.")
                if signup := secret("FPL_SIGNUP_URL"):
                    st.link_button("✋ Join the waitlist", signup)
    st.stop()
