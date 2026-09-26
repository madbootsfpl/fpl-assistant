"""The owner's stats, and the door in front of them (ADR-305).

⭐⭐⭐ **The design is forced by one fact: the web build is public JavaScript.** Reading the `events` table
needs `FPL_ADMIN_STORE_KEY` — a service-role key that bypasses RLS, which `web_streamlit/analytics.py`
marks *"server-side only"*. So the client holds **no credential**: the owner types a password, it travels
per request, and the server does the reading.

⚠️ These pin the door as much as the data. This is the one authenticated endpoint on an otherwise open
API, and ⭐ *the only thing a failed attempt should teach is that it failed.*
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.service.http import admin
from src.service.http.app import app

KEY = "an-admin-key-for-tests"


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("FPL_ADMIN_KEY", KEY)
    monkeypatch.setenv("FPL_ADMIN_STORE_KEY", "service-role")
    monkeypatch.setenv("FPL_STORE_URL", "https://example.test/rest/v1/squads")


@pytest.fixture
def client():
    return TestClient(app)


def test_an_unconfigured_server_has_no_such_endpoint(client, monkeypatch):
    """⭐ *An endpoint that exists but cannot work is an endpoint somebody will spend an afternoon
    debugging* — and a 404 tells a stranger nothing about what this deployment is for."""
    monkeypatch.delenv("FPL_ADMIN_KEY", raising=False)
    monkeypatch.delenv("FPL_ADMIN_STORE_KEY", raising=False)

    assert client.post("/api/v1/admin/usage", json={"key": "anything"}).status_code == 404


def test_half_configured_is_still_no_endpoint(client, monkeypatch):
    """⚠️ A password with nothing to read is not a working stats page. ⭐ *Both halves, or neither.*"""
    monkeypatch.setenv("FPL_ADMIN_KEY", KEY)
    monkeypatch.delenv("FPL_ADMIN_STORE_KEY", raising=False)

    assert client.post("/api/v1/admin/usage", json={"key": KEY}).status_code == 404


def test_a_wrong_key_is_refused(client, configured):
    assert client.post("/api/v1/admin/usage", json={"key": "wrong"}).status_code == 401


def test_a_wrong_key_learns_nothing_from_the_refusal(client, configured):
    """⚠️⚠️ **No hint about the key, the store, or whether this deployment even has stats.** ⭐ *A error
    message is a place secrets go to be logged*, and this one is read by whoever is guessing."""
    body = client.post("/api/v1/admin/usage", json={"key": "wrong"}).text

    for leak in (KEY, "service-role", "example.test", "FPL_ADMIN"):
        assert leak not in body, f"the refusal leaked {leak!r}"


def test_the_key_is_compared_in_constant_time(configured):
    """⚠️ A plain `==` leaks the common prefix to anyone timing it, and this is the only door on an
    otherwise public API. ⭐ Asserted on the **mechanism**, because a timing test is flaky by nature."""
    import inspect

    source = inspect.getsource(admin.key_matches)
    assert "compare_digest" in source, "the key comparison is no longer constant-time"


def test_the_right_key_gets_aggregates_and_never_rows(client, configured, monkeypatch):
    """⭐ `usage.py` refused to store a manager id on the owner's own instruction — *"I am not interested
    in personal information"* — and ⚠️ *a promise kept by the writer and broken by the reader is not a
    promise.*"""
    rows = [
        {"duration_ms": 30, "ok": True, "version": "1.0.0+21", "page": "/api/v1/ask",
         "meta": {"platform": "ios"}, "anon_id": "aaa", "ts": "2026-09-26T10:00:00+00:00"},
        {"duration_ms": 900, "ok": False, "version": "1.0.0+20", "page": "/api/v1/ask",
         "meta": {"platform": "web"}, "anon_id": "bbb", "ts": "2026-09-26T11:00:00+00:00"},
    ]
    monkeypatch.setattr(admin, "_fetch", lambda days: rows)

    body = client.post("/api/v1/admin/usage", json={"key": KEY, "days": 7}).json()

    assert body["events"] == 2
    assert body["installs"] == 2
    assert body["failures"] == 1
    assert body["platforms"] == {"ios": 1, "web": 1}
    # ⚠️⚠️ **No identifiers reach the client**, in any field.
    text = str(body)
    assert "aaa" not in text and "bbb" not in text, "an install id reached the response"
    assert "anon_id" not in body


def test_a_store_that_cannot_be_read_degrades_rather_than_500s(client, configured, monkeypatch):
    """⚠️ *A stats page that errors is indistinguishable from a product that is broken*, and it is read
    at exactly the moment somebody is checking whether the product is broken."""
    def boom(days):
        raise ConnectionError("https://example.test/rest/v1/events is unreachable")

    monkeypatch.setattr(admin, "_fetch", boom)

    response = client.post("/api/v1/admin/usage", json={"key": KEY})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["events"] == 0, "an unreadable store must not look like a quiet one"
    # ⭐ The class, never the message: a Supabase error echoes the URL, and the URL carries the project ref.
    assert "example.test" not in response.text


def test_the_answer_is_never_cached(client, configured, monkeypatch):
    """⚠️ One person's private view of the whole beta, on a CDN-fronted domain."""
    monkeypatch.setattr(admin, "_fetch", lambda days: [])

    response = client.post("/api/v1/admin/usage", json={"key": KEY})

    assert "no-store" in response.headers.get("cache-control", "")


def test_the_door_is_rate_limited():
    """⭐ *A rate limit is the difference between a secret and a secret you can guess at leisure.*"""
    from src.service.http.limits import limit_for

    per, window = limit_for("/api/v1/admin/usage")
    assert (per, window) == (10, 60), f"the admin door allows {per} attempts per {window}s"


@pytest.mark.parametrize("days", [0, 91, -1])
def test_an_absurd_window_is_refused(client, configured, days):
    assert client.post("/api/v1/admin/usage",
                       json={"key": KEY, "days": days}).status_code == 422


def test_a_median_of_nothing_is_none_not_zero():
    """⚠️ *No timings at all is not "instant"* — a client printing `0ms` would be reporting a
    performance nobody achieved."""
    empty = admin.summarise([], 7)

    assert empty["median_ms"] is None
    assert empty["p95_ms"] is None
    assert empty["slowest_ms"] is None


def test_the_slow_tail_is_reported_not_just_the_middle():
    """⭐ *A median hides the request that made someone give up.*"""
    rows = [{"duration_ms": 20} for _ in range(99)] + [{"duration_ms": 9000}]

    out = admin.summarise(rows, 7)

    assert out["median_ms"] == 20
    assert out["slowest_ms"] == 9000
    assert out["p95_ms"] is not None and out["p95_ms"] >= 20


def test_an_unset_key_matches_nothing_even_asked_directly(monkeypatch):
    """🔴 **The dangerous default, tested at the function rather than through the route.**

    A mutation making `key_matches` return `True` for an unset key survived every test above, because
    `is_enabled()` 404s first and nothing ever reaches the comparison. ⚠️⚠️ *A security guard that is only
    correct because a different guard runs first is a guard that becomes wrong the day somebody reorders
    them* — and this one fails open.

    ⭐ `key_matches` is a public function. It has to be right on its own.
    """
    monkeypatch.delenv("FPL_ADMIN_KEY", raising=False)

    assert admin.key_matches("") is False
    assert admin.key_matches("anything") is False
    # ⚠️ And a blank key configured is still no key — an empty secret is the shape an unset one takes in
    # a deployment that set the variable and left it empty.
    monkeypatch.setenv("FPL_ADMIN_KEY", "   ")
    assert admin.key_matches("") is False
    assert admin.key_matches("   ") is False
