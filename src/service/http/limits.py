"""A rate limit for a public, unauthenticated API (ADR-256).

⭐⭐ **Two things need protecting, and they are not the same thing.** `feedback` relays to the owner's own
sink and can be spammed into uselessness; `build` runs an integer-programming solver and is the one way a
stranger could run up a bill. Everything else is *ids in, analysis out* over public FPL data — generous
limits there, strict ones where the cost is real.

⚠️⚠️ **In-process, and that is a real limitation stated rather than hidden.** On a scale-to-zero platform
instances come and go, so this bounds sustained abuse from one caller against one instance — not a
distributed flood, and not abuse spread across a cold start. ⭐ *A Redis-backed limiter would be the honest
answer at ten thousand users and over-engineering at ten; the point is to know which one this is.*
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

#: path suffix → (requests, seconds). ⭐ The **cost** of the endpoint sets the number, not its popularity.
LIMITS: dict[str, tuple[int, int]] = {
    # ⚠️ The one that reaches a human. Five an hour is plenty for a real tester and useless to a script.
    "/feedback": (5, 3600),
    # ⚠️ The LP solver — the only endpoint whose CPU cost a stranger controls.
    "/squad/build": (20, 60),
    # ⭐ The whole board, ~97 KB. Cheap to compute, expensive to send.
    "/players": (60, 60),
}

#: Everything else. ⭐ Generous, because the app itself makes several calls per screen and a limit that
#: catches normal use is a limit that will be removed rather than fixed.
DEFAULT_LIMIT: tuple[int, int] = (240, 60)


def limit_for(path: str) -> tuple[int, int]:
    """The (requests, window) for a path — the longest matching suffix wins."""
    for suffix, rule in LIMITS.items():
        if path.endswith(suffix):
            return rule
    return DEFAULT_LIMIT


def caller(request: Request, *, trust_proxy: bool = True) -> str:
    """Who is asking.

    ⚠️⚠️ **Behind a proxy, `request.client.host` is the proxy** — every caller would share one bucket and
    the first busy tester would lock out the rest. So the **left-most** `X-Forwarded-For` entry is used
    when present, which is what the platform's own edge put there.

    ⚠️ That header is trivially spoofed by anyone talking to the service **directly**. ⭐ *This is a cost
    control, not a security boundary* — someone willing to forge a header to make more free analysis
    requests has defeated a limit that was never load-bearing. It is recorded here so nobody later mistakes
    it for authentication.
    """
    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimiter:
    """A sliding window per (caller, path-rule). ⭐ Sliding, not fixed: a fixed window lets twice the limit
    through across a boundary, which is the bug every naïve counter ships with."""

    def __init__(self, *, now=time.monotonic):
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._now = now

    def check(self, key: str, path: str) -> tuple[bool, int]:
        """`(allowed, retry_after_seconds)`."""
        allowance, window = limit_for(path)
        # ⭐ Bucketed by the **rule**, not the raw path: `/squad/analysis` and `/squad/captain` share the
        # default allowance, and giving each its own would multiply the real limit by the endpoint count.
        rule = next((s for s in LIMITS if path.endswith(s)), "*")
        hits = self._hits[(key, rule)]
        now = self._now()

        while hits and now - hits[0] >= window:
            hits.popleft()
        if len(hits) >= allowance:
            return False, max(1, int(window - (now - hits[0])) + 1)
        hits.append(now)
        return True, 0

    def forget(self) -> None:
        """Drop everything — ⚠️ for tests. Production never calls it: the window does the forgetting."""
        self._hits.clear()


def rate_limit_middleware(limiter: RateLimiter):
    """The ASGI middleware. ⭐ Returns **429 with `Retry-After`**, because a limit that does not say when
    to come back is a limit a client retries immediately and forever."""

    async def middleware(request: Request, call_next):
        # ⚠️ Health is never limited: it is what a platform polls to decide whether to keep the instance,
        # and rate-limiting it would make the service look unhealthy under exactly the load the limit
        # exists for.
        if request.url.path.endswith("/health"):
            return await call_next(request)

        allowed, retry_after = limiter.check(caller(request), request.url.path)
        if not allowed:
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_after)},
                content={"detail": f"Too many requests — try again in {retry_after}s."},
            )
        return await call_next(request)

    return middleware
