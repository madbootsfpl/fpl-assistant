"""Beta-user registration store (ADR-098) — a capped email allowlist in the **same Supabase project** as the
cross-device squads (`cloud_store`).

Reuses `FPL_STORE_URL`'s base + `FPL_STORE_KEY` (the `beta_users` endpoint is derived — **no new secret**).
**Soft control:** a self-declared email is the identity; the shared code (`access.py`) gates *who can* register;
the cap bounds *how many*. Best-effort + secret-gated. Off unless `FPL_USER_CAP` is set (the gate checks that);
failures raise so the gate can surface the real cause via `cloud_store.store_error`.
"""

import re

import requests

from src.api.retry import with_retry
from src.web_streamlit.access import secret

_TIMEOUT = 6
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def clean_email(email: str) -> str:
    """A normalised email (lower-cased, trimmed) if it looks valid, else `''`. Soft validation — the address is
    self-declared (ADR-098), so this just rejects the obviously-not-an-email, not spoofing."""
    e = (email or "").strip().lower()
    return e if _EMAIL_RE.match(e) else ""


def _endpoint():
    """`(url, key)` for the `beta_users` table — derived from `FPL_STORE_URL`'s base (same project as squads),
    or `(None, None)` when the store isn't configured."""
    url, key = secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None
    base = url.rsplit("/", 1)[0]        # .../rest/v1/squads -> .../rest/v1
    return f"{base}/beta_users", key


def is_configured() -> bool:
    """True when the (shared) Supabase store is configured — so registration can read/write `beta_users`."""
    url, key = _endpoint()
    return bool(url and key)


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def is_registered(email: str) -> bool:
    """True if `email` is in the beta — matched **case-insensitively** (capitalisation and leading/trailing spaces are
    normalised on **both** sides via `clean_email`), so a hand-typed `beta_users` entry like `Colin@x.ie` still admits
    `colin@x.ie`. `False` when unconfigured or the email is malformed. A PostgREST `eq.` filter is case-*sensitive*, so
    we fetch the list and compare normalised — cheap: the gate caches the admit, so this runs once per session."""
    url, key = _endpoint()
    if not (url and key):
        return False
    e = clean_email(email)
    if not e:
        return False

    def _get():
        r = requests.get(url, params={"select": "email"}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    return any(clean_email(row.get("email", "")) == e for row in with_retry(_get, retries=1).json())


def all_emails() -> list[str]:
    """Every allow-listed email, normalised (ADR-120). **Owner-only** — the Admin page is gated by
    `FPL_ADMIN_KEY`, and this is the same list the owner already holds in Supabase.

    Deliberately *not* an analytics field: the anonymity invariant (ADR-100) stays intact because the roster is
    a **separate join** the owner performs over their own allow-list, never a de-anonymisation of an event.
    Empty when unconfigured, like every other read here."""
    url, key = _endpoint()
    if not (url and key):
        return []

    def _get():
        r = requests.get(url, params={"select": "email"}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    try:
        rows = with_retry(_get, retries=1).json()
    except Exception:                                    # noqa: BLE001 — best-effort, like the rest of this module
        return []
    return sorted({e for row in rows if (e := clean_email(row.get("email", "")))})


def count() -> int:
    """How many testers are registered (0 when unconfigured). A small select — fine for a cap in the tens."""
    url, key = _endpoint()
    if not (url and key):
        return 0

    def _get():
        r = requests.get(url, params={"select": "email"}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    return len(with_retry(_get, retries=1).json())


def register(email: str, cap: int) -> str:
    """Admit `email` to the beta up to `cap`. Returns:

    - `"in"` — already registered (no write), or newly inserted (under the cap);
    - `"full"` — a new email but the cap is reached.

    Raises `ValueError` on a malformed email and `RuntimeError` when unconfigured; a store failure propagates so
    the gate can show the real cause (`cloud_store.store_error`). *(A count-then-insert race could let two
    simultaneous sign-ups exceed the cap by one — accepted for a hobby beta.)*"""
    url, key = _endpoint()
    if not (url and key):
        raise RuntimeError("user store not configured")
    e = clean_email(email)
    if not e:
        raise ValueError("enter a valid email address")
    if is_registered(e):
        return "in"
    if count() >= cap:
        return "full"

    def _post():
        r = requests.post(url, json={"email": e}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    with_retry(_post, retries=1)
    return "in"
