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
    from src.web_streamlit.access import _EMAIL, _OK, _user_cap, secret

    email = current_email()
    if not email:                                  # not signed in → the login screen
        st.image(brand.badge_path(), width=68)
        # ⚠️ **ADR-193 — the copy had to move with the posture.** While there is room under the cap this is
        # open-until-full, not invite-only, and a screen still saying *private beta · invite list* would be
        # describing a gate that no longer exists. ⭐ *Access copy is a claim about who can get in; it expires
        # the moment the rule does.*
        st.title(f"🔒 {brand.NAME} — beta")
        st.caption(f"**{brand.TAGLINE}** · sign in to get your squad synced across your devices. "
                   "Places are limited — if there is room you are in straight away.")
        st.login()                                 # "Sign in with Google" — the single provider under [auth] (ADR-106)
        st.caption("We store your Google **email** to admit you + sync your squad — nothing else. "
                   "*Remove me* = we delete your rows.")
        st.caption(brand.DISCLAIMER)
        st.stop()

    def _admit():
        """Mark the session passed and restore this user's squad — the same three steps whether they were
        already on the list or have just been auto-admitted, so the two routes cannot drift apart."""
        st.session_state[_OK] = True
        st.session_state[_EMAIL] = user_store.clean_email(email)
        # ADR-142: stamp the sign-in. Once per session, here, because this is the one place we know someone
        # has *arrived* — the Admin roster previously inferred activity from whether a squad had been saved,
        # which most people never do, so daily users read as "never". Best-effort and silent.
        user_store.touch_last_seen(email)
        from src.web_streamlit import squads
        squads.link_and_restore(user_key(email))   # US-362: link + restore the per-user squad (cross-device/reconnect)

    if user_store.is_registered(email):            # on the allow-list → admitted
        _admit()
        return

    # ⚠️ **ADR-193 — admit up to the cap, THEN waitlist.** Owner: *"people are getting stuck in the waitlist;
    # we need to auto-allow access up to the max number and then enter the waitlist."*
    #
    # Everyone not already on the list used to land on the waitlist and stay there until the owner added them
    # by hand, which made the cap decorative and the queue permanent. `user_store.register` has done exactly
    # this since ADR-098 — admit under the cap, report `"full"` at it — and the Google gate simply never
    # called it. **The machinery existed; only this branch was missing.**
    #
    # ⚠️ Best-effort by design: a store failure must land someone on the waitlist, never on a stack trace, so
    # the only path to `_admit()` here is an explicit `"in"`.
    cap = _user_cap()
    if cap is not None and user_store.is_configured():
        try:
            if user_store.register(email, cap) == "in":
                _admit()
                return
        except Exception:                          # noqa: BLE001 — unconfigured, malformed, or the store is down
            pass

    waitlist.add(email, "not_listed")              # cap reached (or no cap set) → capture + hold (ADR-102)
    st.image(brand.badge_path(), width=68)
    st.title(f"🔒 {brand.NAME} — beta")
    # ⚠️ *"We'll be in touch as spots open"* was a promise that needed a person to keep it, and nobody was
    # keeping it — which is how the queue became permanent. What is true now: a place frees automatically, and
    # the next sign-in takes it. Say the true thing, which also needs nobody.
    st.warning(f"**{user_store.clean_email(email)}** — the beta is **full** right now, so you're on the "
               "waitlist. Places free up as testers leave; **sign in again any time** and you'll be let "
               "straight in if one has.")
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
