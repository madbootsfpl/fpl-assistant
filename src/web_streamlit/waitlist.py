"""Beta waitlist store (ADR-102) — captures the email of a would-be tester whose registration **failed** (the cap
is full, or the invite code was wrong), so the owner can invite them later.

A `beta_waitlist(email primary key, reason, created_at)` table in the **same Supabase project** as the squads /
`beta_users` — endpoint derived from `FPL_STORE_URL`'s base, reusing `FPL_STORE_KEY` (**no new secret**).
**Best-effort + fail-silent:** `add()` never raises and never blocks the registration gate — a lost waitlist entry
is acceptable, a broken registration is not (ADR-102). Off by default (only written from the secret-gated gate).
"""

import requests

from src.web_streamlit.access import secret
from src.web_streamlit.user_store import clean_email

_TIMEOUT = 6


def _endpoint():
    """`(url, key)` for the `beta_waitlist` table — derived from `FPL_STORE_URL`'s base (same project), or
    `(None, None)` when the store isn't configured."""
    url, key = secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None
    base = url.rsplit("/", 1)[0]        # .../rest/v1/squads -> .../rest/v1
    return f"{base}/beta_waitlist", key


def is_configured() -> bool:
    """True when the (shared) Supabase store is configured."""
    url, key = _endpoint()
    return bool(url and key)


def add(email, reason: str = "full") -> None:
    """Best-effort: record `email` + `reason` (`"full"` at the cap · `"bad_code"` on a wrong invite code) on a
    **failed** registration (ADR-102). A **no-op** when the store isn't configured, the email is malformed, or the
    write fails — it must **never** raise or block the gate.

    ⭐ **A plain INSERT, not an upsert, and that is a security decision** (docs/SUPABASE_RLS.md A1). This table
    holds the address of everyone who was **refused**, and the goal is that emails go in and nothing comes
    out. Measured on Postgres 17: `ON CONFLICT` — `DO UPDATE` **and** `DO NOTHING` — requires a permissive
    `SELECT` policy, because it must read the conflicting row. So an upsert and a locked-down read are
    **mutually exclusive**: keeping `Prefer: resolution=merge-duplicates` would have forced `using (true)`
    on select, which *is* the exposure.

    ⚠️ **A repeat refusal now returns 409 and is ignored**, which is the intended behaviour and not a
    degradation worth fixing: the row already exists, so the person is already on the waitlist. What is lost
    is only the *latest* `reason` (`not_listed` → `full`). ⭐ *The upsert's whole job was to avoid an error
    this function already swallows* — `requests.post` does not raise on an HTTP status, so the 409 never even
    reaches the `except`.
    """
    try:
        url, key = _endpoint()
        if not url:
            return
        e = clean_email(email)
        if not e:
            return
        headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        requests.post(url, json={"email": e, "reason": reason}, headers=headers, timeout=_TIMEOUT)
    except Exception:
        return
