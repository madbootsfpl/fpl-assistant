"""Self-service "Remove me" / unsubscribe (ADR-122) — delete a person's rows across the shared Supabase store.

Makes the *"remove me = we delete your rows"* promise (ADR-106/102/098) self-service. Mirrors `waitlist.py`: a
small **requests-only** module reusing `FPL_STORE_URL`'s base + `FPL_STORE_KEY` (**no new secret**), **off** until
the store is configured. `remove_me` issues **best-effort `DELETE`s** and — like the waitlist write — **never
raises**: a lost or RLS-blocked delete degrades quietly (the owner can still remove the row by hand), because a
crash mid-unsubscribe is worse than a retry.

Endpoints derive from `FPL_STORE_URL` (`.../rest/v1/squads`): its **base** (`.../rest/v1`) gives the sibling
tables, and the URL itself is the `squads` endpoint. Removes:
- **`beta_waitlist`** + **`beta_users`** by `email` (their waitlist entry + their allow-list seat);
- **`squads`** (`handle`) + **`player_watchlist`** (`user_key`) + **`user_prefs`** (`user_key`) — only with a
  `user_key` (a signed-in tester, the hashed key, ADR-106).

**It returns a per-table status, and that is not decoration (ADR-148).** Every delete here is fail-silent,
which is right at the edge — a crash mid-unsubscribe is worse than a retry, and nobody leaving should be shown
a stack trace. But this module backs a **promise**: *"remove me = we delete your rows"*. ADR-142 and ADR-147
both hit the same trap on writes — a table with RLS and no matching policy makes PostgREST answer
**`200 OK, zero rows`**, not an error — and a delete that quietly does nothing while telling someone their data
is gone is the worst version of that failure. So the statuses come back for a caller (or a test) to check,
while the UI keeps swallowing them.
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


def _delete(endpoint, params, key) -> str:
    """One best-effort `DELETE ?<col>=eq.<val>`. Never raises; returns what happened.

    `Prefer: return=representation` makes PostgREST send back the rows it actually removed, which is the only
    way to tell a real delete from one that **silently matched nothing** because the table has row-level
    security and no DELETE policy. Postgres does not raise for that — it narrows the statement to zero rows.
    """
    try:
        r = requests.delete(endpoint, params=params,
                            headers={**_headers(key), "Prefer": "return=representation"}, timeout=_TIMEOUT)
    except Exception as exc:                             # noqa: BLE001 — fail-silent at the edge, by design
        return f"failed: {exc}"
    if r.status_code >= 400:
        return f"refused (HTTP {r.status_code})"
    try:
        return "deleted" if r.json() else "nothing matched (no row, or no DELETE policy)"
    except Exception:                                    # noqa: BLE001 — a 204 with no body is a fine success
        return "deleted"


def remove_me(email, user_key: str | None = None) -> dict:
    """Best-effort, fail-silent: delete a person's rows across the store (ADR-122).

    - **by email** (when it's a valid address): `beta_waitlist` + `beta_users`;
    - **by user_key** (when given — a signed-in tester): `squads` (`handle`) + `player_watchlist` +
      `user_prefs` (ADR-147's cross-device preferences — added here because the promise has to cover every
      row we create, and a new table is exactly the thing an old promise silently stops covering).

    Returns `{table: status}` so a caller or a test can verify the promise was kept; the UI ignores it. A
    **no-op** (`{}`) when the store isn't configured. **Never raises** — the caller signs the user out
    regardless. `beta_users` needs a DELETE policy for its delete to take effect (BETA.md), and so does
    `user_prefs`, which ships with RLS enabled (ADR-147/148)."""
    base, squads_url, key = _base_and_key()
    if not (base and key):
        return {}
    out = {}
    e = clean_email(email)
    if e:
        out["beta_waitlist"] = _delete(f"{base}/beta_waitlist", {"email": f"eq.{e}"}, key)
        out["beta_users"] = _delete(f"{base}/beta_users", {"email": f"eq.{e}"}, key)
    if user_key:
        # the per-user squad (handle = the user_key hash)
        out["squads"] = _delete(squads_url, {"handle": f"eq.{user_key}"}, key)
        out["player_watchlist"] = _delete(f"{base}/player_watchlist", {"user_key": f"eq.{user_key}"}, key)
        out["user_prefs"] = _delete(f"{base}/user_prefs", {"user_key": f"eq.{user_key}"}, key)
    return out
