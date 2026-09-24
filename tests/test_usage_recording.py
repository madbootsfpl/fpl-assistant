"""What the API records about its own load — and what it must never record (ADR-280).

The owner: *"I want to see the distribution & number using the apps on the different platforms, the
reason, to make sure that we are scaled enough to support. **I am not interested in personal
information**."*

⭐⭐ **The negative tests are the point of this file.** A usage table that quietly grows a `manager_id`
column is the failure this feature has to be protected from, and it would be an easy, well-meaning commit
— *the id is right there in the request body.*
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.service.http import app as api
from src.service.http import usage


@pytest.fixture
def captured(monkeypatch):
    """Every payload the recorder would have posted, with the network replaced."""
    rows = []
    monkeypatch.setenv("FPL_STORE_URL", "https://example.invalid")
    monkeypatch.setenv("FPL_STORE_KEY", "not-a-real-key")
    monkeypatch.delenv("FPL_USAGE_OFF", raising=False)
    # ⚠️ The thread is replaced, not just the POST: a daemon thread racing the assertions would make
    # this test flaky, and ⭐ *a flaky test about privacy is a test people learn to re-run.*
    monkeypatch.setattr(usage.threading, "Thread",
                        lambda target, args, daemon: type("T", (), {"start": lambda s: rows.append(args[2])})())
    return rows


def test_it_records_the_platform_the_version_and_the_install(captured):
    usage.record(path="/api/v1/ticker", platform="android", version="1.0.0",
                 install="abc123", duration_ms=42, ok=True)
    assert len(captured) == 1
    row = captured[0]
    assert row["meta"]["platform"] == "android"
    assert row["version"] == "1.0.0"
    assert row["anon_id"] == "abc123"
    assert row["page"] == "/api/v1/ticker"
    assert row["duration_ms"] == 42
    assert row["ok"] is True


def test_a_row_carries_nothing_that_identifies_a_person(captured):
    """⚠️⚠️ **The promise, pinned.** ⭐ *The difference between "twelve Android devices" and "Tony opened
    Trending" is the whole of it* — and the manager id is one join away at all times."""
    usage.record(path="/api/v1/my-team", platform="ios", version="1.0.0",
                 install="xyz", duration_ms=10, ok=True)
    row = captured[0]

    forbidden = {"manager_id", "email", "ip", "ip_address", "player_ids", "squad", "name"}
    assert not (forbidden & set(row)), f"a personal field reached the row: {forbidden & set(row)}"
    assert not (forbidden & set(row["meta"])), "a personal field reached meta"


def test_the_middleware_reads_only_the_three_headers(captured):
    """⚠️ Not the client address, not the body. ⭐ *An IP is personal data in a way a random install id
    is not*, and the rate limiter next door reads one — so this one must be shown not to."""
    seen = {}

    def spy(**kwargs):
        seen.update(kwargs)

    with patch.object(usage, "record", spy):
        TestClient(api).post(
            "/api/v1/ticker", json={"next_n": 3},
            headers={"X-Madboots-Platform": "android", "X-Madboots-Version": "1.0.0",
                     "X-Madboots-Install": "abc", "X-Forwarded-For": "203.0.113.9"},
        )

    assert seen["platform"] == "android"
    assert seen["install"] == "abc"
    # ⚠️ The IP was present on the request and must appear nowhere in what was recorded.
    assert "203.0.113.9" not in str(seen), "the caller's IP reached the usage row"


def test_a_request_with_no_headers_still_works_and_still_counts(captured):
    """⭐ A browser, curl, or an older build sends none of these — ⚠️ *load is load*, and a row that
    refused to exist would under-report exactly when an unexpected client appeared."""
    usage.record(path="/api/v1/players", platform="", version="", install="",
                 duration_ms=5, ok=True)
    assert captured[0]["meta"]["platform"] == "unknown"
    assert captured[0]["anon_id"] is None


def test_nothing_is_written_when_no_store_is_configured(monkeypatch):
    """⭐ Off by default, exactly as the web analytics is (ADR-100): *no store, no thread, no write.*"""
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    assert usage.is_enabled() is False

    started = []
    monkeypatch.setattr(usage.threading, "Thread",
                        lambda **kw: started.append(kw) or type("T", (), {"start": lambda s: None})())
    usage.record(path="/x", platform="ios", version="1", install="a", duration_ms=1, ok=True)
    assert not started, "a write was attempted with no store configured"


def test_it_can_be_switched_off_without_a_deploy(captured, monkeypatch):
    """⭐ *A thing that records people should be possible to stop without a deploy.*"""
    monkeypatch.setenv("FPL_USAGE_OFF", "1")
    assert usage.is_enabled() is False
    usage.record(path="/x", platform="ios", version="1", install="a", duration_ms=1, ok=True)
    assert not captured


def test_a_broken_recorder_never_breaks_the_request(monkeypatch):
    """⚠️⚠️ **The first rule.** ⭐ *A lost event never matters; a broken request would.*"""
    monkeypatch.setenv("FPL_STORE_URL", "https://example.invalid")
    monkeypatch.setenv("FPL_STORE_KEY", "k")

    def explode(*a, **k):
        raise RuntimeError("the analytics store is on fire")

    monkeypatch.setattr(usage.threading, "Thread", explode)
    # ⭐ Must not raise.
    usage.record(path="/x", platform="ios", version="1", install="a", duration_ms=1, ok=True)

    with patch.object(usage, "record", explode):
        response = TestClient(api).post("/api/v1/ticker", json={"next_n": 3})
    assert response.status_code == 200, "a failing recorder took the request down with it"


def test_the_module_never_reads_a_manager_id_or_an_address():
    """⭐⭐ **A source sweep, not a behaviour check** (ADR-184). The behavioural tests above prove today's
    code is clean; this one fails the day somebody adds the join, which is the commit to worry about."""
    import ast
    import inspect

    # ⚠️⚠️ **Comments and docstrings stripped first, and that is not a detail.** The first version of
    # this sweep failed on its own module docstring, which names `X-Forwarded-For` precisely to say the
    # recorder must not read it. ⭐ *A guard that fires on the prose explaining the guard teaches people
    # to delete the prose* — the same trap as ADR-261's Dockerfile comments.
    tree = ast.parse(inspect.getsource(usage))
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                node.body = body[1:] or [ast.Pass()]
    code = ast.unparse(tree)

    for forbidden in ("manager_id", "client.host", "X-Forwarded-For", "request.body", "player_ids"):
        assert forbidden not in code, (
            f"`{forbidden}` appears in the usage recorder's CODE — it records load, not people"
        )
