"""The rate limit on a public, unauthenticated API (ADR-256).

⭐⭐ **Two endpoints have a real price and the rest do not.** `feedback` relays to the owner's own sink and
can be spammed into uselessness; `build` runs an integer-programming solver, and its CPU is the one cost a
stranger would be choosing. Everything else is *ids in, analysis out* over public FPL data.

⚠️⚠️ **It is a cost control, not a security boundary**, and the tests say so out loud — because the next
reader will otherwise assume a limiter is protecting something.
"""

import pytest

from src.service.http.limits import (
    DEFAULT_LIMIT,
    LIMITS,
    RateLimiter,
    caller,
    limit_for,
)


class _Clock:
    """⭐ A hand-wound clock. ⚠️ *A test that sleeps for a window is a test nobody runs twice* — and one
    that measures wall time is measuring the machine (ADR-183)."""

    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class _Request:
    def __init__(self, headers=None, host="1.2.3.4"):
        self.headers = headers or {}
        self.client = type("C", (), {"host": host})() if host else None


# ── which rule applies ───────────────────────────────────────────────────────────────────────────

def test_the_expensive_endpoints_are_the_limited_ones():
    """⭐ The **cost** of an endpoint sets its number, not its popularity."""
    assert limit_for("/api/v1/feedback")[0] < limit_for("/api/v1/squad/build")[0]
    assert limit_for("/api/v1/squad/build")[0] < DEFAULT_LIMIT[0]
    assert limit_for("/api/v1/squad/analysis") == DEFAULT_LIMIT


def test_the_default_is_generous_enough_for_the_app_itself():
    """⚠️⚠️ **The app makes several calls per screen.** A limit that catches normal use is a limit that
    gets removed rather than fixed — ⭐ *and the removal will not come with an ADR.*

    My Team alone fetches the squad, and moving through the tabs adds the week's plan, the board and the
    club table. A tester flicking between them for a minute must not be throttled.
    """
    allowance, window = DEFAULT_LIMIT
    assert window <= 60
    assert allowance >= 120, f"{allowance} in {window}s is below a busy minute of ordinary use"


# ── the window ───────────────────────────────────────────────────────────────────────────────────

def test_it_allows_exactly_the_allowance_then_refuses():
    clock = _Clock()
    limiter = RateLimiter(now=clock)
    allowance, _ = LIMITS["/feedback"]
    for i in range(allowance):
        ok, _ = limiter.check("ip", "/api/v1/feedback")
        assert ok, f"refused on request {i + 1} of {allowance}"
    ok, retry = limiter.check("ip", "/api/v1/feedback")
    assert not ok
    assert retry > 0, "a limit that does not say when to come back is retried immediately and forever"


def test_the_window_slides_rather_than_resetting():
    """⭐⭐ **Sliding, not fixed.** A fixed window lets *twice* the allowance through across a boundary —
    the bug every naïve counter ships with — because the last second of one window and the first of the
    next are a single burst to whoever is being limited.

    ⚠️⚠️ **An earlier version of this test could not tell the two apart.** It exhausted the allowance in
    one instant and checked that *one more* was permitted after the window — which a fixed window does too,
    having just reset everything. ⭐ *The difference is not whether the limit expires, it is how MUCH comes
    back*, so the hits are spread across the window and only the oldest is aged out.
    """
    clock = _Clock()
    limiter = RateLimiter(now=clock)
    allowance, window = LIMITS["/squad/build"]

    # ⚠️ Spread across **less** than the window — `window / (allowance + 1)` — so every hit is still live
    # when the last one lands. A first attempt used `window / allowance`, which aged the oldest out before
    # the newest arrived and never reached the limit at all.
    gap = window / (allowance + 1)
    for _ in range(allowance):
        assert limiter.check("ip", "/api/v1/squad/build")[0]
        clock.t += gap
    assert not limiter.check("ip", "/api/v1/squad/build")[0], "the allowance was not reached"

    # Advance just past the OLDEST hit only. A sliding window returns exactly that one.
    clock.t += gap * 1.5
    allowed = 0
    for _ in range(allowance):
        if limiter.check("ip", "/api/v1/squad/build")[0]:
            allowed += 1
    assert allowed <= 2, (
        f"{allowed} requests came back when one hit aged out — the window reset instead of sliding, "
        f"which is the double-burst bug"
    )
    assert allowed >= 1, "nothing came back at all, so the window is not expiring"


def test_callers_do_not_share_a_bucket():
    clock = _Clock()
    limiter = RateLimiter(now=clock)
    allowance, _ = LIMITS["/feedback"]
    for _ in range(allowance):
        limiter.check("first", "/api/v1/feedback")
    assert not limiter.check("first", "/api/v1/feedback")[0]
    assert limiter.check("second", "/api/v1/feedback")[0], "one caller exhausted another's allowance"


def test_endpoints_sharing_a_rule_share_a_bucket():
    """⚠️⚠️ **Otherwise the real limit is the default times the endpoint count.** Thirteen endpoints each
    with their own 240/minute is 3,120/minute — ⭐ *a limit that scales with the API surface is not a
    limit.*"""
    clock = _Clock()
    limiter = RateLimiter(now=clock)
    allowance, _ = DEFAULT_LIMIT

    half = allowance // 2
    for _ in range(half):
        assert limiter.check("ip", "/api/v1/squad/analysis")[0]
    for _ in range(allowance - half):
        assert limiter.check("ip", "/api/v1/squad/captain")[0]
    assert not limiter.check("ip", "/api/v1/squad/route")[0], (
        "a third default endpoint had its own allowance"
    )


# ── who is asking ────────────────────────────────────────────────────────────────────────────────

def test_behind_a_proxy_the_forwarded_address_wins():
    """⚠️⚠️ **`request.client.host` is the proxy** on every hosting platform. Without this, every caller
    shares one bucket and the first busy tester locks out the rest — ⭐ *a limiter that throttles everyone
    at once looks exactly like an outage.*"""
    request = _Request({"x-forwarded-for": "9.9.9.9, 10.0.0.1"}, host="10.0.0.1")
    assert caller(request) == "9.9.9.9"


def test_without_a_proxy_header_the_socket_address_is_used():
    assert caller(_Request(host="5.6.7.8")) == "5.6.7.8"


def test_an_unknown_caller_still_gets_a_bucket():
    """⭐ Not an exception, and not a free pass: one shared bucket for callers with no address at all."""
    assert caller(_Request(host=None)) == "unknown"


def test_the_forwarded_header_is_documented_as_spoofable():
    """⚠️⚠️ **This is the claim that must not rot.** `X-Forwarded-For` is trivially forged by anyone
    talking to the service directly, so the limiter is a **cost control, not a security boundary**.

    ⭐ *A future reader who mistakes it for authentication would be building on sand* — so the source has
    to say so, and this fails if that sentence is ever removed.
    """
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "src" / "service" / "http" / "limits.py").read_text()
    assert "not a security boundary" in source
    assert "spoofed" in source or "forge" in source


# ── the middleware ───────────────────────────────────────────────────────────────────────────────

def test_health_is_never_limited(client):
    """⚠️⚠️ **It is what the platform polls to decide whether to keep the instance.** Rate-limiting it
    would make the service look unhealthy under exactly the load the limit exists for — ⭐ *a limiter that
    takes the service down has done the attacker's work.*"""
    for _ in range(DEFAULT_LIMIT[0] + 20):
        assert client.get("/api/v1/health").status_code == 200


def test_a_refusal_says_when_to_come_back(client):
    allowance, _ = LIMITS["/feedback"]
    body = {"message": "hello there, this is a test note", "screen": "test"}
    seen = [client.post("/api/v1/feedback", json=body).status_code for _ in range(allowance + 1)]
    assert seen[-1] == 429, f"never refused: {seen}"

    refused = client.post("/api/v1/feedback", json=body)
    assert refused.status_code == 429
    assert int(refused.headers["retry-after"]) > 0


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from src.service.http import app as api

    # ⚠️ `app.state`, not a module global: `src/service/http/__init__.py` binds the FastAPI **object** over
    # its own submodule, so even the full dotted path hands you the app rather than the module — ⭐ *a
    # package that promotes a name shadows the module that defines it.*
    api.state.limiter.forget()
    with TestClient(api) as c:
        yield c
    api.state.limiter.forget()
