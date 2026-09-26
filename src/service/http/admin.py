"""Owner-only usage stats, read server-side (ADR-305).

⭐⭐⭐ **The whole design is forced by one fact: the web build is public JavaScript.** Reading the `events`
table needs `FPL_ADMIN_STORE_KEY` — a **service-role** key that bypasses RLS completely, and which
`web_streamlit/analytics.py` marks *"server-side only"*. Anyone can open `madboots.com/app/web/` and read
the bundle, so ⚠️ *a key shipped to the client is a key published*, and that is true of the mobile binary
too — only less obviously.

⭐ So the client holds **no credential at all**. The owner types a password; it travels per request; the
server compares it against `FPL_ADMIN_KEY` and does the reading itself.

⚠️⚠️ **Aggregates, never rows.** `usage.py` was built on the owner's own words — *"I am not interested in
personal information"* — and returning the stream would undo that one endpoint later. ⭐ *A promise kept
by the writer and broken by the reader is not a promise.*

⚠️ **Inert unless both secrets are set**, exactly like the Streamlit page: no key, no endpoint.
"""

from __future__ import annotations

import hmac
import os
import statistics
from collections import Counter
from datetime import UTC, datetime, timedelta

import requests

#: ⚠️ Short. This is one person pressing a button, and a slow Supabase must not hold a worker.
_TIMEOUT = 8


def _secret(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def is_enabled() -> bool:
    """Both halves present: a password to check, and a key to read with.

    ⭐ *An endpoint that answers when it cannot do the work is an endpoint that lies* — without the store
    key there is nothing to read, and without the password there is nobody to check.
    """
    return bool(_secret("FPL_ADMIN_KEY") and _secret("FPL_ADMIN_STORE_KEY")
                and _secret("FPL_STORE_URL"))


def key_matches(given: str) -> bool:
    """⚠️ **Constant-time.** A plain `==` leaks the length and the common prefix to anyone timing it, and
    this is the one door on an otherwise public API."""
    expected = _secret("FPL_ADMIN_KEY")
    if not expected:
        return False
    return hmac.compare_digest(given.strip(), expected)


def _events_url() -> str:
    """The `events` table, derived exactly as every other consumer derives it (ADR-100/280)."""
    return f"{_secret('FPL_STORE_URL').rsplit('/', 1)[0]}/events"


def _fetch(days: int) -> list[dict]:
    """Rows since `days` ago, newest first — ⚠️ read with the **service-role** key, server-side only."""
    key = _secret("FPL_ADMIN_STORE_KEY")
    since = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    response = requests.get(
        _events_url(),
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        params={
            "select": "ts,event,page,duration_ms,ok,version,meta,anon_id",
            "ts": f"gte.{since}",
            "order": "ts.desc",
            # ⚠️ A ceiling, because this is a display and the table only grows.
            "limit": "5000",
        },
        timeout=_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def _percentile(values: list[float], fraction: float) -> int | None:
    """⭐ The slow tail is the number that matters — *a median hides the request that made someone give
    up.* ⚠️ `None` rather than 0 when there is nothing to measure."""
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * fraction))
    return int(ordered[index])


def summarise(rows: list[dict], days: int) -> dict:
    """Aggregates only — ⭐ *the shape `usage.py` promised when it refused to store a manager id.*"""
    durations = [r["duration_ms"] for r in rows
                 if isinstance(r.get("duration_ms"), (int, float))]
    platforms = Counter(
        (r.get("meta") or {}).get("platform", "unknown") for r in rows
    )
    return {
        "days": days,
        "events": len(rows),
        # ⭐ Distinct installs, not people: *an install id is tied to nothing and must not be spoken of
        # as a user.*
        "installs": len({r.get("anon_id") for r in rows if r.get("anon_id")}),
        "platforms": dict(platforms.most_common()),
        "versions": dict(Counter(r["version"] for r in rows if r.get("version")).most_common(6)),
        "pages": dict(Counter(r["page"] for r in rows if r.get("page")).most_common(12)),
        # ⚠️ `ok` is nullable in the table; only rows that recorded a verdict are counted.
        "failures": sum(1 for r in rows if r.get("ok") is False),
        "median_ms": int(statistics.median(durations)) if durations else None,
        "p95_ms": _percentile(durations, 0.95),
        "slowest_ms": int(max(durations)) if durations else None,
    }


def usage(days: int = 7) -> dict:
    """The owner's view, or an honest empty one.

    ⚠️ **Never raises.** A Supabase that is slow or down must answer *"could not read"* rather than a
    500 — ⭐ *a stats page that errors is indistinguishable from a product that is broken*, and this one
    is read at exactly the moment somebody is checking whether the product is broken.
    """
    try:
        rows = _fetch(days)
    except Exception as exc:  # noqa: BLE001 - every failure degrades the same way
        # ⚠️ The class, never the message: a Supabase error can echo the URL, and the URL carries the
        # project ref. ⭐ *An error string is a place secrets go to be logged.*
        return {"ok": False, "reason": f"could not read the events table ({type(exc).__name__})",
                **summarise([], days)}
    return {"ok": True, "reason": "", **summarise(rows, days)}
