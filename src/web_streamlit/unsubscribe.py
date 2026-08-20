"""Self-service "Remove me" / unsubscribe (ADR-122) — delete a person's rows across the shared Supabase store.

Makes the *"remove me = we delete your rows"* promise (ADR-106/102/098) self-service. Mirrors `waitlist.py`: a
small **requests-only** module reusing `FPL_STORE_URL`'s base + `FPL_STORE_KEY` (**no new secret**), **off** until
the store is configured. `remove_me` issues **best-effort `DELETE`s** and — like the waitlist write — **never
raises**: a lost or RLS-blocked delete degrades quietly (the owner can still remove the row by hand), because a
crash mid-unsubscribe is worse than a retry.

Endpoints derive from `FPL_STORE_URL` (`.../rest/v1/squads`): its **base** (`.../rest/v1`) gives the sibling
tables, and the URL itself is the `squads` endpoint. Removes:
- **`beta_waitlist`** + **`beta_users`** by `email` (their waitlist entry + their allow-list seat);
- **`squads`** (`handle`) + **`player_watchlist`** (`user_key`) — only with a `user_key` (a signed-in tester,
  the hashed key, ADR-106).
"""

import requests

from src.web_streamlit.access import secret
from src.web_streamlit.user_store import clean_email

_TIMEOUT = 6


def _base_and_key():
    """`(base, squads_url, key)` derived from `FPL_STORE_URL` (same project as squads / `beta_users`), or
    `(None, None, None)` when the store isn't configured. `base` = `.../rest/v1` (for the sibling tables);
    `squads_url` = `FPL_STORE_URL` itself (the `squads` endpoint)."""
    url, key = secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None, None
    base = url.rsplit("/", 1)[0]        # .../rest/v1/squads -> .../rest/v1
    return base, url, key


def is_configured() -> bool:
    """True when the (shared) Supabase store is configured — otherwise the feature is off (the UI hides it)."""
    base, _, key = _base_and_key()
    return bool(base and key)


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}"}


def _delete(endpoint, params, key) -> None:
    """One best-effort `DELETE ?<col>=eq.<val>` — swallows every failure (never raises)."""
    try:
        requests.delete(endpoint, params=params, headers=_headers(key), timeout=_TIMEOUT)
    except Exception:
        return


def remove_me(email, user_key: str | None = None) -> None:
    """Best-effort, fail-silent: delete a person's rows across the store (ADR-122).

    - **by email** (when it's a valid address): `beta_waitlist` + `beta_users`;
    - **by user_key** (when given — a signed-in tester): `squads` (`handle`) + `player_watchlist`.

    A **no-op** when the store isn't configured. **Never raises** — a lost/RLS-blocked delete degrades quietly (the
    owner can still remove the row by hand); the caller signs the user out regardless. `beta_users` needs a delete
    policy for its delete to take effect (BETA.md); the other three tables are RLS-off, so they delete today."""
    base, squads_url, key = _base_and_key()
    if not (base and key):
        return
    e = clean_email(email)
    if e:
        _delete(f"{base}/beta_waitlist", {"email": f"eq.{e}"}, key)
        _delete(f"{base}/beta_users", {"email": f"eq.{e}"}, key)
    if user_key:
        _delete(squads_url, {"handle": f"eq.{user_key}"}, key)          # the per-user squad (handle = user_key hash)
        _delete(f"{base}/player_watchlist", {"user_key": f"eq.{user_key}"}, key)
