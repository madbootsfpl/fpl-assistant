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


def events_url(store_url: str) -> str:
    """The `events` endpoint, derived from `FPL_STORE_URL` **exactly as the web app derives it**.

    ⚠️⚠️ **`FPL_STORE_URL` is a full TABLE url**, not a base — `https://…/rest/v1/squads`. So the events
    table is its **sibling**: strip the last segment, append `events`.

    ⭐⭐ *This was reimplemented rather than matched, and it cost a silent failure.* The first version
    appended `/rest/v1/events` to the whole thing, producing `…/rest/v1/squads/rest/v1/events` — a 404
    that the fail-silent writer swallowed exactly as designed, so the API recorded **nothing** while
    reporting no error at all.

    ⚠️ It cannot simply import the web app's copy: `src/web_streamlit` is excluded from the API image
    (ADR-261). `tests/test_usage_recording.py` pins that both derive the same URL from the same input,
    which is the cheapest thing that stops two copies of one rule drifting.
    """
    return f"{store_url.rsplit('/', 1)[0]}/{_TABLE}"


def _endpoint() -> tuple[str | None, str | None]:
    url, key = os.environ.get("FPL_STORE_URL"), os.environ.get("FPL_STORE_KEY")
    if not url or not key:
        return None, None
    return events_url(url), key


def is_enabled() -> bool:
    """⚠️ Configured **and** not switched off. ⭐ *A thing that records people should be possible to stop
    without a deploy.*"""
    if os.environ.get("FPL_USAGE_OFF"):
        return False
    return _endpoint()[0] is not None


#: ⚠️⚠️ **What the last write did.** ⭐ *Fail-silent hid a total failure*: the events endpoint was being
#: built wrongly, every write 404'd, and the panel read exactly like "nobody has used the app yet" —
#: indistinguishable from success by anyone, including the two people looking at it.
#:
#: ⭐ So the silence is still silent **towards the request** — that rule does not move — and no longer
#: silent towards the owner. One word, no url, no key, no payload.
_last: str = "never"


def status() -> str:
    """`off` · `never` · `ok` · `failing` — ⭐ enough to tell *not configured* from *configured and
    broken*, which is the distinction that cost an afternoon."""
    if not is_enabled():
        return "off"
    return _last


def _post(url: str, key: str, payload: dict) -> None:
    """One best-effort write. ⚠️ Swallows everything — nothing here may surface into a request."""
    global _last
    try:
        response = requests.post(
            url, json=payload, timeout=_TIMEOUT,
            headers={"apikey": key, "Authorization": f"Bearer {key}",
                     "Content-Type": "application/json", "Prefer": "return=minimal"},
        )
        # ⚠️ The status code matters: a 404 from a wrong endpoint does not raise, and that is precisely
        # how this failed unnoticed.
        _last = "ok" if response.status_code < 400 else f"failing ({response.status_code})"
    except Exception as exc:
        _last = f"failing ({exc.__class__.__name__})"
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
