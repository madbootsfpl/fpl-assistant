"""Per-user preferences that follow you across devices (ADR-147) — today, your Leagues starting point.

**The problem it fixes.** 🏆 Leagues (ADR-141) asks for a manager id, looks up every league behind it, and
then forgets all of it the moment the tab closes. Re-typing an eight-digit number every visit undercuts the
feature it belongs to — the owner's words: *"when a league is loaded it must persist from session to session
and between devices."*

**Cross-device is the part that decides the design.** A cookie would survive a refresh and nothing else, so
this uses the same per-user store the squad (ADR-106) and the ⭐ watchlist (ADR-117) already use: keyed by
`auth.user_key(email)`, endpoint derived from `FPL_STORE_URL`, **no new secret**.

**It remembers the manager id, not just the league — and that ordering matters.** A stored league id restores
one league; a stored manager id restores the *list*, so every league you are in comes back and the picker
opens where you left it. The league is stored too, as the last choice; the manager id is what makes it useful.

Signed out, or with no store, it degrades to **session-only** — which is exactly today's behaviour, so the
page keeps working for anyone browsing without an account.
"""

import requests

from src.api.retry import with_retry
from src.web_streamlit.access import secret

_TIMEOUT = 6
_KEY = "_prefs"                 # session_state: the current {manager_id, league_id}
_RESTORED = "_prefs_restored"   # guard: pulled from the cloud once per session
_FIELDS = ("manager_id", "league_id")


def _endpoint():
    """`(url, key)` for the `user_prefs` table — derived from `FPL_STORE_URL`'s base, or `(None, None)`."""
    url, key = secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None
    base = url.rsplit("/", 1)[0]           # .../rest/v1/squads -> .../rest/v1
    return f"{base}/user_prefs", key


def is_configured() -> bool:
    url, key = _endpoint()
    return bool(url and key)


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _user_key():
    """The signed-in user's stable key (a hash of the email, ADR-106), or None → session-only."""
    try:
        from src.web_streamlit import auth
        email = auth.current_email()
        return auth.user_key(email) if email else None
    except Exception:                                    # noqa: BLE001 — no auth configured is not an error
        return None


def _load(uk):
    """A user's stored prefs, `{}` if none, or `None` on failure — so the caller keeps whatever it has."""
    url, key = _endpoint()
    if not (url and key):
        return None

    def _get():
        r = requests.get(url, params={"select": ",".join(_FIELDS), "user_key": f"eq.{uk}"},
                         headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    try:
        rows = with_retry(_get, retries=1).json()
        if not rows:
            return {}
        return {f: rows[0].get(f) for f in _FIELDS if rows[0].get(f) is not None}
    except Exception:                                    # noqa: BLE001
        return None


def _save(uk, values) -> str:
    """Upsert a user's prefs. Returns a **status string** — never raises.

    The status exists because of ADR-142: an identical write failed silently for a day because a table had
    SELECT and INSERT policies and no UPDATE policy, and PostgREST reports that as `200 OK, zero rows`
    rather than an error. Nothing in the app should show a tester an error over a stored preference, but the
    operator needs to be able to find out *why* when nothing sticks.
    """
    url, key = _endpoint()
    if not (url and key):
        return "store not configured"
    try:
        r = requests.post(url, json={"user_key": uk, **values},
                          headers={**_headers(key), "Prefer": "resolution=merge-duplicates,return=representation"},
                          timeout=_TIMEOUT)
    except Exception as exc:                             # noqa: BLE001
        return f"write failed: {exc}"
    if r.status_code >= 400:
        return f"refused by the store (HTTP {r.status_code}): {r.text[:160]}"
    try:
        if not r.json():
            return ("the write reached no rows — `user_prefs` likely has row-level security with no "
                    "INSERT/UPDATE policy (Postgres does not raise for that, it narrows the write to nothing)")
    except Exception:                                    # noqa: BLE001 — a 204 with no body is a fine success
        pass
    return "ok"


def recall() -> dict:
    """The remembered prefs, restoring from the cloud **once per session** when signed in.

    `{}` when there is nothing stored, nobody signed in, or no store — all of which mean the same thing to a
    caller: start empty, exactly as the page did before this existed.
    """
    import streamlit as st
    if _KEY not in st.session_state:
        st.session_state[_KEY] = {}
        uk = _user_key()
        if uk and not st.session_state.get(_RESTORED):
            loaded = _load(uk)
            if loaded:
                st.session_state[_KEY] = loaded
            st.session_state[_RESTORED] = True
    return dict(st.session_state[_KEY])


def remember(**values) -> str:
    """Store one or more prefs (`manager_id=…`, `league_id=…`). Session always; cloud when signed in.

    Writes only what changed. A preference re-saved on every rerun would be a network call per page view for
    a value that moves about twice a season, and Streamlit reruns constantly.
    """
    import streamlit as st
    values = {k: v for k, v in values.items() if k in _FIELDS and v is not None}
    if not values:
        return "nothing to store"
    current = recall()
    if all(str(current.get(k)) == str(v) for k, v in values.items()):
        return "unchanged"
    st.session_state[_KEY] = {**current, **values}
    uk = _user_key()
    if not uk:
        return "session only (not signed in)"
    return _save(uk, st.session_state[_KEY])
