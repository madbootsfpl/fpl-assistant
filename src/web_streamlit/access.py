"""Beta access gate + shared config helpers for the Streamlit edge (Sprint 102, ADR-087).

An **opt-in** access-code gate: when `FPL_ACCESS_CODE` is configured (a Streamlit secret or an env var) the app
asks for the code once per session; when it's **unset** the app is open (its current public behaviour). Config
is read through `_secret`, which try/excepts `st.secrets` (it *raises* when there's no `secrets.toml`) and
falls back to `os.environ` — so a missing secrets file never crashes local/CI, and everything stays off by
default. No accounts, no server-side state (the gate flag lives in `st.session_state`).
"""

import os

import streamlit as st

_OK = "_beta_ok"          # session flag: this session entered the right code


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


def require_access() -> None:
    """Gate the page behind `FPL_ACCESS_CODE` when it's set (ADR-087). A no-op when unset (the app is open) or
    once this session has entered the code. Otherwise it renders a prompt and **stops the page** until the
    right code is given. Call once, right after `st.set_page_config(...)`, on every page."""
    code = secret("FPL_ACCESS_CODE")
    if not code or st.session_state.get(_OK):
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
