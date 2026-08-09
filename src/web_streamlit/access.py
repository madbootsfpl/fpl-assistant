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
    A no-op once this session has passed. Call once, right after `st.set_page_config(...)`, on every page."""
    if st.session_state.get(_OK):
        return

    cap = _user_cap()
    if cap is not None:
        from src.web_streamlit import user_store  # lazy: user_store imports `secret` from here (avoid the cycle)
        if user_store.is_configured():
            _registration_gate(cap)                # stops the page unless admitted
            return

    # Shared-code / open (ADR-087) — unchanged when registration mode is off.
    code = secret("FPL_ACCESS_CODE")
    if not code:
        return
    st.title("🔒 FPL Assistant — private beta")
    st.caption("This is a closed beta. Enter the access code you were given to continue.")
    entered = st.text_input("Access code", type="password", key="_beta_code")
    if entered and entered == code:
        st.session_state[_OK] = True
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
                st.rerun()
            elif status == "full":
                st.warning(f"The beta is full right now ({cap} testers). More spots open as it grows.")
                if signup := secret("FPL_SIGNUP_URL"):
                    st.link_button("✋ Join the waitlist", signup)
    st.stop()
