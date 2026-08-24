"""Cross-device squad persistence — a handle-keyed cloud store (ADR-094).

Save a squad under a user-chosen **handle** on one device, load it on another. Backed by a free
**Supabase** REST table `squads(handle text primary key, data jsonb, updated_at timestamptz)` via an
anon key; **no login** — the handle *is* the key (a hobby-beta trade-off, ADR-094).

**Off by default:** unset `FPL_STORE_URL` / `FPL_STORE_KEY` → `is_configured()` is False, so the UI hides
the feature and no write can happen — the public deploy stays read-only until the owner opts in. Best-effort
(tight timeout + one retry via `with_retry`); failures raise so the caller can degrade to the download/upload
path (ADR-054). This is the **one** deliberate server-side write the web edge makes (revising the ADR-053/054
read-only invariant); a guardrail test pins that it's secret-gated.
"""

import re

import requests

from src.api.retry import with_retry
from src.web_streamlit.access import secret

_TIMEOUT = 6
_HANDLE_RE = re.compile(r"[^a-z0-9_-]+")


def _config():
    """`(url, key)` from secrets/env, or `(None, None)` when unset."""
    return secret("FPL_STORE_URL"), secret("FPL_STORE_KEY")


def is_configured() -> bool:
    """True only when both the store URL and key are set — otherwise the feature is off (hidden + inert)."""
    url, key = _config()
    return bool(url and key)


def clean_handle(handle: str) -> str:
    """Normalise a handle to a safe key: lower-case, `[a-z0-9_-]` only, 2–32 chars ('' if it doesn't qualify).

    Guards the REST `handle=eq.<…>` filter and keeps keys predictable across devices. Not security — a handle
    is a shared key, per ADR-094."""
    h = _HANDLE_RE.sub("", (handle or "").strip().lower())
    return h if 2 <= len(h) <= 32 else ""


def _headers(key):
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def store_error(exc) -> str:
    """A human-readable reason from a failed store request — Supabase's own error message + hint when
    present, else the HTTP status, else the exception text. So the UI shows the *real* cause (e.g. a row-level
    security policy) instead of a blind 'couldn't save'. Pure — takes the raised exception."""
    response = getattr(exc, "response", None)
    if response is not None:
        try:
            data = response.json()
        except Exception:
            data = None
        if isinstance(data, dict) and data.get("message"):
            hint = data.get("hint") or data.get("details")
            return data["message"] + (f" ({hint})" if hint else "")
        return f"HTTP {getattr(response, 'status_code', '?')}"
    return str(exc) or "couldn't reach the store"


def save_squad(handle: str, squad: dict) -> None:
    """Upsert `squad` (the whole SquadStore dict) under `handle`. Raises on a bad handle or a failed write."""
    url, key = _config()
    if not (url and key):
        raise RuntimeError("cloud store not configured")
    h = clean_handle(handle)
    if not h:
        raise ValueError("handle must be 2–32 chars of letters, numbers, - or _")
    body = {"handle": h, "data": squad}
    headers = {**_headers(key), "Prefer": "resolution=merge-duplicates"}   # Supabase upsert on the PK

    def _post():
        r = requests.post(url, json=body, headers=headers, timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    with_retry(_post, retries=1)


def load_squad(handle: str) -> dict | None:
    """The squad saved under `handle`, or `None` (unconfigured, a bad handle, or nothing stored)."""
    url, key = _config()
    if not (url and key):
        return None
    h = clean_handle(handle)
    if not h:
        return None
    params = {"handle": f"eq.{h}", "select": "data"}

    def _get():
        r = requests.get(url, params=params, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    rows = with_retry(_get, retries=1).json()
    return rows[0]["data"] if rows else None


def exists(handle: str) -> bool:
    """True if a squad is already saved under `handle` (US-321) — a light select (just the key, not the
    data). `False` when unconfigured, a bad handle, or nothing stored. Used to warn before a Save overwrites."""
    url, key = _config()
    if not (url and key):
        return False
    h = clean_handle(handle)
    if not h:
        return False
    params = {"handle": f"eq.{h}", "select": "handle"}

    def _get():
        r = requests.get(url, params=params, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    try:
        return bool(with_retry(_get, retries=1).json())
    except requests.RequestException:
        return False        # best-effort hint — never block the Save (which will surface the real error)


def updated_at_by_handle(handles) -> dict:
    """`{handle: updated_at}` for the handles given — one batched read (ADR-120).

    The account store already stamps `updated_at` on every save, so "when did this tester last persist a squad?"
    is answerable without storing anything new. One request rather than one per tester: a beta in the tens
    would otherwise mean tens of round-trips on an Admin page render.

    Empty when unconfigured or on any failure — the Admin page must degrade to "unknown", never error.
    """
    handles = [h for h in {clean_handle(h) for h in (handles or [])} if h]
    if not handles:
        return {}
    url, key = _config()
    if not (url and key):
        return {}
    try:
        resp = requests.get(url, params={"select": "handle,updated_at",
                                         "handle": f"in.({','.join(handles)})"},
                            headers=_headers(key), timeout=8)
        resp.raise_for_status()
        return {r["handle"]: r.get("updated_at") for r in resp.json() if r.get("handle")}
    except Exception:                                    # noqa: BLE001 — best-effort, as everywhere in this module
        return {}


def delete_squad(handle: str) -> None:
    """Remove the squad saved under `handle` (a "clear my saved squad", ADR-094). No-op if unconfigured."""
    url, key = _config()
    if not (url and key):
        return
    h = clean_handle(handle)
    if not h:
        return

    def _delete():
        r = requests.delete(url, params={"handle": f"eq.{h}"}, headers=_headers(key), timeout=_TIMEOUT)
        r.raise_for_status()
        return r

    with_retry(_delete, retries=1)
