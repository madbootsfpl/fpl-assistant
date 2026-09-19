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


def _rpc(name: str):
    """`(url, key)` for a Postgres function exposed over PostgREST, or `(None, None)` when unconfigured.

    ⭐ **A sibling of the table endpoint, not a replacement for the pattern.** Stage B moves the gate from
    *reading a table* to *asking a question*: `anon` loses SELECT on `beta_users` entirely and gains EXECUTE
    on two `security definer` functions instead (docs/SUPABASE_RLS.md B1).
    """
    url, key = secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")
    if not (url and key):
        return None, None
    base = url.rsplit("/", 1)[0]        # .../rest/v1/squads -> .../rest/v1
    return f"{base}/rpc/{name}", key


def is_configured() -> bool:
    """True when the (shared) Supabase store is configured — so registration can read/write `beta_users`."""
    url, key = _endpoint()
    return bool(url and key)


def _admin_endpoint():
    """`(url, key)` for the **owner's** reads of `beta_users`, using a service-role key (Stage B).

    ⚠️⚠️ **`FPL_ADMIN_STORE_KEY` is a service-role key and it bypasses RLS completely.** It exists because
    Stage B revokes `anon`'s access to this table, and the Admin roster genuinely needs the whole list — a
    need no narrow function can serve, because "every address" *is* the question.

    ⭐ **Safe here for one specific reason: Streamlit renders server-side**, so this key never leaves the
    server. That reason does **not** transfer — it must never be compiled into a mobile client, where it
    would hand every reader unrestricted access to every table.

    `(None, None)` when unset, so the roster degrades to empty rather than breaking the page.
    """
    url, key = secret("FPL_STORE_URL"), secret("FPL_ADMIN_STORE_KEY")
    if not (url and key):
        return None, None
    return f"{url.rsplit('/', 1)[0]}/beta_users", key


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def is_registered(email: str) -> bool:
    """True if `email` is on the allow-list — **one boolean, not the list** (Stage B1).

    ⭐⭐ **This used to fetch every address and compare in Python**, because a PostgREST `eq.` filter is
    case-*sensitive* and a hand-typed `beta_users` row like `Colin@x.ie` has to admit `colin@x.ie`. So the
    single most sensitive read in the app — the whole tester allow-list — happened on every gate check, to
    work around a capitalisation quirk.

    `lower(trim(…))` in SQL does the same job inside the database. ⭐ *The security fix and the workaround's
    removal are the same change* — and what comes back now is `true`/`false`, so even a correct guess learns
    only whether that one address is listed.

    `False` when unconfigured, malformed, or the call fails: the gate must fail **closed**.
    """
    url, key = _rpc("is_allow_listed")
    if not (url and key):
        return False
    e = clean_email(email)
    if not e:
        return False

    def _post():
        r = requests.post(url, json={"p_email": e}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    try:
        return bool(with_retry(_post, retries=1).json())
    except Exception:                                    # noqa: BLE001 — an unreachable store must not admit
        return False


def all_emails() -> list[str]:
    """Every allow-listed email, normalised (ADR-120). **Owner-only** — the Admin page is gated by
    `FPL_ADMIN_KEY`, and this is the same list the owner already holds in Supabase.

    Deliberately *not* an analytics field: the anonymity invariant (ADR-100) stays intact because the roster is
    a **separate join** the owner performs over their own allow-list, never a de-anonymisation of an event.
    Empty when unconfigured, like every other read here."""
    url, key = _admin_endpoint()
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
    """Admit `email` to the beta up to `cap`. Returns `"in"` (already listed, or newly inserted) or `"full"`.

    Raises `ValueError` on a malformed email and `RuntimeError` when unconfigured; a store failure propagates
    so the gate can show the real cause (`cloud_store.store_error`).

    ⭐ **The cap is now enforced inside one locked transaction** (Stage B1). This was three round trips —
    check, count, insert — and the docstring used to admit the consequence: *"a count-then-insert race could
    let two simultaneous sign-ups exceed the cap by one — accepted for a hobby beta."*

    ⚠️ **Measured, because "one function" is not the same as "atomic":** a first version of the SQL moved all
    three steps into a function and the cap still broke — four concurrent calls against a cap of 5 admitted
    **6**, because `select count(*)` takes no lock. The function now takes `share row exclusive` on the table,
    and the same test admits exactly 5.
    """
    url, key = _rpc("register_beta_user")
    if not (url and key):
        raise RuntimeError("user store not configured")
    e = clean_email(email)
    if not e:
        raise ValueError("enter a valid email address")

    def _post():
        r = requests.post(url, json={"p_email": e, "p_cap": cap}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    status = with_retry(_post, retries=1).json()
    if status == "invalid":                              # the database's own view of a malformed address
        raise ValueError("enter a valid email address")
    return status


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

    **It returns a status because the first version did not, and that made it undiagnosable.** The caller at
    admit ignores this return; the Admin page shows it. **Same code path either way** — a diagnostic that
    exercises a *different* path proves nothing.

    ⭐ **Stage B turned this from three round trips into one.** It used to read the whole allow-list to find
    the stored spelling (a PostgREST `eq.` filter is case-sensitive and the list is hand-maintained), then
    PATCH that exact row. The RPC does the `lower(trim(…))` match inside the database — so the case problem,
    the extra read, and `anon`'s access to the table all go at once.
    """
    url, key = _rpc("touch_last_seen")
    e = clean_email(email or "")
    if not (url and key):
        return "store not configured"
    if not e:
        return "no email"
    try:
        r = requests.post(url, json={"p_email": e}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
    except Exception as exc:                             # noqa: BLE001 — never raise at admit
        return f"couldn't stamp last_seen: {exc}"
    return "stamped" if r.json() else f"{e} isn't on the allow-list"


def last_seen_by_email(emails=None) -> dict:
    """`{email: last_seen}` for allow-listed testers — one batched read, `{}` if unavailable.

    An empty dict is also what you get before the column exists, which is exactly what the Admin page needs to
    say "this signal isn't on yet" rather than quietly showing everyone as never-seen.
    """
    url, key = _admin_endpoint()   # owner-only: the whole roster (Stage B)
    if not (url and key):
        return {}
    try:
        r = requests.get(url, params={"select": "email,last_seen"}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return {clean_email(row["email"]): row.get("last_seen")
                for row in r.json() if row.get("email") and row.get("last_seen")}
    except Exception:                                    # noqa: BLE001 — including "column does not exist"
        return {}
