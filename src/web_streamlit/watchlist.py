"""The ⭐ Watchlist — a per-user shortlist of players to keep an eye on (ADR-117).

Held in `st.session_state` and, when signed in **and** the store is configured, mirrored per-user in Supabase
(keyed by `auth.user_key`, endpoint derived from `FPL_STORE_URL` — **no new secret**), so it follows you across
devices like your squad (ADR-106). **Best-effort + off by default:** no store/login → session-only; a sync hiccup
never blocks a ⭐. Capped at `MAX` — a *maximum*, not a target.
"""

import requests

from src.api.retry import with_retry
from src.web_streamlit.access import secret

MAX = 30
_TIMEOUT = 6
_KEY = "_watchlist"                # session_state: the list of watched player ids
_RESTORED = "_watchlist_restored"  # guard: restored from the cloud once per session


def _endpoint():
    """`(url, key)` for the `player_watchlist` table — derived from `FPL_STORE_URL`'s base, or `(None, None)`."""
    url, key = secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None
    base = url.rsplit("/", 1)[0]           # .../rest/v1/squads -> .../rest/v1
    return f"{base}/player_watchlist", key


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
    except Exception:
        return None


def _load(uk):
    """The stored ids for a user, `[]` if none, or None on a failure (so the caller keeps the session list)."""
    url, key = _endpoint()
    if not (url and key):
        return None

    def _get():
        r = requests.get(url, params={"select": "player_ids", "user_key": f"eq.{uk}"},
                         headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    try:
        rows = with_retry(_get, retries=1).json()
        return [int(i) for i in rows[0]["player_ids"]] if rows and rows[0].get("player_ids") is not None else []
    except Exception:
        return None


def _save(uk, ids):
    """Best-effort upsert of a user's watchlist — never raises (a lost sync is acceptable, a broken ⭐ is not)."""
    url, key = _endpoint()
    if not (url and key):
        return
    try:
        headers = {**_headers(key), "Prefer": "resolution=merge-duplicates"}   # upsert on the user_key PK
        requests.post(url, json={"user_key": uk, "player_ids": list(ids)}, headers=headers, timeout=_TIMEOUT)
    except Exception:
        return


def ids() -> list:
    """The current watchlist ids — restores from the cloud **once per session** when signed in (like the squad)."""
    import streamlit as st
    if _KEY not in st.session_state:
        st.session_state[_KEY] = []
        uk = _user_key()
        if uk and not st.session_state.get(_RESTORED):
            loaded = _load(uk)
            if loaded is not None:
                st.session_state[_KEY] = loaded
            st.session_state[_RESTORED] = True
    return list(st.session_state[_KEY])


def contains(pid) -> bool:
    return int(pid) in ids()


def is_full() -> bool:
    return len(ids()) >= MAX


def add(pid) -> bool:
    """Add `pid` if not already watched and not full; persist. Returns True if it was added (False if full/dupe)."""
    import streamlit as st
    cur = ids()
    pid = int(pid)
    if pid in cur or len(cur) >= MAX:
        return False
    cur.append(pid)
    st.session_state[_KEY] = cur
    if (uk := _user_key()):
        _save(uk, cur)
    return True


def remove(pid) -> None:
    """Drop `pid` from the watchlist and persist (a no-op if it wasn't there)."""
    import streamlit as st
    pid = int(pid)
    cur = [i for i in ids() if i != pid]
    st.session_state[_KEY] = cur
    if (uk := _user_key()):
        _save(uk, cur)
