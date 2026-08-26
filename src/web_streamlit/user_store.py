"""Beta-user registration store (ADR-098) — a capped email allowlist in the **same Supabase project** as the
cross-device squads (`cloud_store`).

Reuses `FPL_STORE_URL`'s base + `FPL_STORE_KEY` (the `beta_users` endpoint is derived — **no new secret**).
**Soft control:** a self-declared email is the identity; the shared code (`access.py`) gates *who can* register;
the cap bounds *how many*. Best-effort + secret-gated. Off unless `FPL_USER_CAP` is set (the gate checks that);
failures raise so the gate can surface the real cause via `cloud_store.store_error`.
"""

import re
from datetime import datetime, timezone

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


# --- last seen (ADR-142) --------------------------------------------------------------
# The Admin roster used to call a tester "active" when their **squad row** had been saved recently — which is
# not "used the app", and read as if it were. Most people sign in and browse; they never press save. So 18 of
# 25 testers showed ⚪ never while at least two were using it daily.
#
# This stamps a real sign-in time on the owner's own allow-list row. It is **not** a de-anonymisation of the
# ADR-100 event stream: that stays anonymous and untouched. This is the allow-list, which already holds the
# email, learning when that person last arrived.
#
# Both functions are best-effort and silent, and that matters more than usual here: the `last_seen` column has
# to be added by hand (see the ADR), so until it exists every call 400s. A tester must never see an error
# because an admin panel wants a nicer number.

def touch_last_seen(email: str) -> str:
    """Stamp `beta_users.last_seen = now` for this email. Returns a short **status string**, never raises.

    Called once per session at admit, not per page view — a page-view stamp would be a write on every
    navigation for no extra signal, since the roster only asks *which day* someone was last here.

    **It returns a status because the first version did not, and that made it undiagnosable.** Silent
    best-effort is right for a tester's page — nobody should see an error because an admin panel wants a nicer
    number — but it left the owner staring at a column of NULLs with no way to learn whether the write was
    never attempted, never matched, or refused by a row-level-security policy. The caller at admit ignores this
    return; the Admin page shows it. **Same code path either way**: a diagnostic that exercises a *different*
    path proves nothing.

    **The lookup is case-insensitive, the hard way.** A PostgREST `eq.` filter is case-*sensitive*, and the
    allow-list is hand-maintained — it currently holds both `markcondron88@gmail.com` and
    `Markcondron88@gmail.com`. `eq.<cleaned>` silently matches **no row** for the capitalised one, which is the
    exact trap `is_registered` above documents. So we read the stored spelling first and patch *that*. One
    extra read per session, at the one moment we already do several.
    """
    url, key = _endpoint()
    e = clean_email(email or "")
    if not (url and key):
        return "store not configured"
    if not e:
        return "no email"
    try:
        got = requests.get(url, params={"select": "email"}, headers=_headers(key), timeout=_TIMEOUT)
        got.raise_for_status()
        stored = next((row["email"] for row in got.json()
                       if clean_email(row.get("email", "")) == e), None)
    except Exception as exc:                             # noqa: BLE001
        return f"couldn't read the allow-list: {exc}"
    if stored is None:
        return f"{e} isn't on the allow-list"

    try:
        r = requests.patch(url, params={"email": f"eq.{stored}"},
                           json={"last_seen": datetime.now(timezone.utc).isoformat()},
                           headers={**_headers(key), "Prefer": "return=representation"}, timeout=_TIMEOUT)
    except Exception as exc:                             # noqa: BLE001
        return f"write failed: {exc}"
    if r.status_code >= 400:
        # Named on purpose. A 401/403 here almost always means the table has SELECT and INSERT policies (the
        # gate needs both) but no UPDATE policy — invisible until something tries to write.
        return f"refused by the store (HTTP {r.status_code}): {r.text[:160]}"
    try:
        if not r.json():
            return "wrote nothing — no row matched (is the `last_seen` column present?)"
    except Exception:                                    # noqa: BLE001 — a 204 with no body is a fine success
        pass
    return "ok"


def last_seen_by_email(emails=None) -> dict:
    """`{email: last_seen}` for allow-listed testers — one batched read, `{}` if unavailable.

    An empty dict is also what you get before the column exists, which is exactly what the Admin page needs to
    say "this signal isn't on yet" rather than quietly showing everyone as never-seen.
    """
    url, key = _endpoint()
    if not (url and key):
        return {}
    try:
        r = requests.get(url, params={"select": "email,last_seen"}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return {clean_email(row["email"]): row.get("last_seen")
                for row in r.json() if row.get("email") and row.get("last_seen")}
    except Exception:                                    # noqa: BLE001 — including "column does not exist"
        return {}
