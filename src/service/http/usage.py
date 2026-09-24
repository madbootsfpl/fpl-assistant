"""How much the API is being asked to do, and by which platform — ⭐ **capacity, not curiosity**
(ADR-280).

The owner: *"I want to see the distribution & number using the apps on the different platforms, the
reason, to make sure that we are scaled enough to support. **I am not interested in personal
information**."*

So a row is four facts and a duration:

| | |
|---|---|
| `platform` | `ios` · `android` · `web`, from a header the app sets |
| `version` | which build — ⭐ *an old build in the wild is invisible until something breaks on it* |
| `install` | a random id the app generated, ⚠️ **tied to nothing** |
| `page` | the endpoint, so load can be attributed to a screen |

⚠️⚠️ **What is deliberately NOT recorded, and each for a reason:**

* **The manager id** — the API receives it on four endpoints. ⭐ *The difference between "twelve Android
  devices" and "Tony opened Trending" is the whole of the promise here*, and the join is the thing that
  would break it. It is never read in this module.
* **The IP address** — the rate limiter reads one (`X-Forwarded-For`) and this must not. ⚠️ *An IP is
  personal data in a way a random install id is not.*
* **The request body** — squads, player ids, a tester's feedback text. None of it.

⭐⭐ **And it can never affect the app.** Every write is fire-and-forget on a daemon thread, wrapped so no
error can reach the request — the same rule the web client has followed since ADR-100, for the same
reason: *a lost event never matters; a broken request would.*

**Off unless configured.** Writes only when the Supabase store is configured, exactly as the web
analytics does; no store, no thread, no write.
"""

import os
import threading
from datetime import UTC, datetime

import requests

#: ⚠️ Tight. A slow analytics endpoint must not hold a worker thread open behind a request that has
#: already been answered.
_TIMEOUT = 3

#: ⭐ The same `events` table the web app writes to (ADR-100) — *one place to read, whichever surface a
#: tester used.* The endpoint is derived from the store URL; no new secret.
_TABLE = "events"


def _endpoint() -> tuple[str | None, str | None]:
    url, key = os.environ.get("FPL_STORE_URL"), os.environ.get("FPL_STORE_KEY")
    if not url or not key:
        return None, None
    return f"{url.rstrip('/')}/rest/v1/{_TABLE}", key


def is_enabled() -> bool:
    """⚠️ Configured **and** not switched off. ⭐ *A thing that records people should be possible to stop
    without a deploy.*"""
    if os.environ.get("FPL_USAGE_OFF"):
        return False
    return _endpoint()[0] is not None


def _post(url: str, key: str, payload: dict) -> None:
    """One best-effort write. ⚠️ Swallows everything — nothing here may surface into a request."""
    try:
        requests.post(
            url, json=payload, timeout=_TIMEOUT,
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
        )
    except Exception:
        return


def record(*, path: str, platform: str, version: str, install: str,
           duration_ms: int, ok: bool) -> None:
    """Record one request. ⭐ Returns immediately; the write happens on a daemon thread."""
    try:
        if not is_enabled():
            return
        url, key = _endpoint()
        if not url:
            return
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            # ⚠️ The install id goes in `anon_id`, the column the web app already uses for its random
            # returning-user id — ⭐ *the same meaning in the same column, so one query answers both.*
            "anon_id": install or None,
            "session_id": None,
            "version": version or None,
            "event": "api",
            "page": path,
            "duration_ms": duration_ms,
            "ok": ok,
            "meta": {"platform": platform or "unknown"},
        }
        threading.Thread(target=_post, args=(url, key, payload), daemon=True).start()
    except Exception:
        return


def usage_middleware():
    """FastAPI middleware recording one row per request.

    ⚠️ **Timed around the handler, not inside it** — ⭐ *what a caller waits for is the number that
    answers "are we scaled enough", and a handler's own view of itself leaves out the queueing.*
    """
    import time

    async def middleware(request, call_next):
        started = time.monotonic()
        response = await call_next(request)
        try:
            record(
                path=request.url.path,
                # ⚠️ Headers only, and only these three. The request object carries a client address and
                # a body; neither is read here.
                platform=request.headers.get("X-Madboots-Platform", ""),
                version=request.headers.get("X-Madboots-Version", ""),
                install=request.headers.get("X-Madboots-Install", ""),
                duration_ms=int((time.monotonic() - started) * 1000),
                ok=response.status_code < 400,
            )
        except Exception:
            pass        # ⭐ A request that succeeded must not fail because counting it did.
        return response

    return middleware
