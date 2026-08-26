"""Google auth (Streamlit `st.login` / OIDC) — the hard-identity gate + per-user persistence anchor (ADR-106).

**Off by default:** when there's no `[auth]` in Streamlit secrets, `is_configured()` is False and the app uses the
existing shared-code / registration / open gate (byte-identical — local, CI, and the open deploy are unchanged).

When `[auth]` **is** configured, `require_access` (in `access.py`) hands off to `gate()`: **Sign in with Google** →
admitted iff the email is on the **allow-list** (`beta_users`, ADR-098), else added to the **waitlist** (ADR-102,
`reason="not_listed"`). The signed-in email anchors the per-user squad (US-362) — keyed by a **hash** of the email so
the squads table never stores a raw address.
"""

import hashlib

import streamlit as st


def is_configured() -> bool:
    """True when Google-auth mode is on — a `[auth]` section is present in Streamlit secrets. Absent (no
    `secrets.toml`, local/CI/open deploy) → False, and `st.secrets` itself raises, so it's read defensively."""
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def current_email() -> str | None:
    """The signed-in user's email, or None. `st.user` is only meaningful in auth mode — read it defensively so a
    non-auth context never raises."""
    try:
        if getattr(st.user, "is_logged_in", False):
            return st.user.email
    except Exception:
        return None
    return None


def user_key(email: str) -> str:
    """A stable per-user cloud handle — a truncated **sha256** of the cleaned email. Passes `cloud_store.clean_handle`
    (hex = letters + digits) and keeps the squads table from storing raw emails (ADR-106)."""
    from src.web_streamlit.user_store import clean_email
    return hashlib.sha256(clean_email(email).encode()).hexdigest()[:32]


def render_account() -> None:
    """The sidebar account line + a **Log out** (Google) for an admitted, signed-in user — auth mode's counterpart
    to the cookie-gate's `_render_account`."""
    from src.web_streamlit import access
    from src.web_streamlit.access import _EMAIL
    with st.sidebar:
        email = st.session_state.get(_EMAIL)
        st.caption(f"🔓 Signed in as {email}" if email else "🔓 Signed in")
        if st.button("Log out", key="_auth_logout", use_container_width=True):
            st.logout()
    access.render_leave_beta()                     # a self-service "Remove me" / unsubscribe (ADR-122)


def gate() -> None:
    """The Google-auth gate (ADR-106). **Not signed in** → the Sign-in-with-Google screen (stops the page).
    **Signed in + on the allow-list** (`beta_users`) → mark the session passed (`_OK`/`_EMAIL`) and return.
    **Signed in but not invited** → add to the waitlist + a *"not on the list yet"* screen with Log out (stops)."""
    from src.web_streamlit import brand, user_store, waitlist
    from src.web_streamlit.access import _EMAIL, _OK, secret

    email = current_email()
    if not email:                                  # not signed in → the login screen
        st.image(brand.badge_path(), width=68)
        st.title(f"🔒 {brand.NAME} — private beta")
        st.caption(f"**{brand.TAGLINE}** · sign in to get your squad synced across your devices.")
        st.login()                                 # "Sign in with Google" — the single provider under [auth] (ADR-106)
        st.caption("We store your Google **email** to admit you + sync your squad — nothing else. "
                   "*Remove me* = we delete your rows.")
        st.caption(brand.DISCLAIMER)
        st.stop()

    if user_store.is_registered(email):            # on the allow-list → admitted
        st.session_state[_OK] = True
        st.session_state[_EMAIL] = user_store.clean_email(email)
        # ADR-142: stamp the sign-in. Once per session, here, because this is the one place we know someone
        # has *arrived* — the Admin roster previously inferred activity from whether a squad had been saved,
        # which most people never do, so daily users read as "never". Best-effort and silent.
        user_store.touch_last_seen(email)
        from src.web_streamlit import squads
        squads.link_and_restore(user_key(email))   # US-362: link + restore the per-user squad (cross-device/reconnect)
        return

    waitlist.add(email, "not_listed")              # signed in but not invited → capture + hold (ADR-102)
    st.image(brand.badge_path(), width=68)
    st.title(f"🔒 {brand.NAME} — private beta")
    st.warning(f"**{user_store.clean_email(email)}** isn't on the invite list yet — you're on the waitlist. "
               "We'll be in touch as spots open.")
    if signup := secret("FPL_SIGNUP_URL"):
        st.link_button("✋ Join the waitlist", signup)
    if st.button("Log out", key="_auth_logout_denied"):
        st.logout()
    if st.button("Remove me from the waitlist", key="_auth_unsub_denied"):   # the promised "remove me" (ADR-122)
        from src.web_streamlit import unsubscribe
        unsubscribe.remove_me(email)               # no user_key — not admitted, so no saved squad/watchlist
        st.logout()
    st.caption(brand.DISCLAIMER)
    st.stop()
