"""A liveness probe is not usage (ADR-306).

⚠️⚠️⚠️ **The owner's first look at his own stats panel was 96% noise.** 955 of 995 recorded events were
`/health`, and the whole of the real traffic — six squad loads, one Ask — sat underneath it, rounded to
0% and 1%.

⭐ `usage.py` exists to answer one question, in the owner's own words: *"the distribution & number using
the apps… to make sure that we are scaled enough."* Something polling a URL every few minutes is not a
person, and counting it makes the number that matters unreadable.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.service.http import usage
from src.service.http.app import app


@pytest.fixture
def recorded(monkeypatch):
    """Every path the middleware decided to record."""
    seen: list[str] = []
    monkeypatch.setattr(usage, "record", lambda **kw: seen.append(kw["path"]))
    return seen


def test_the_health_probe_is_not_recorded(recorded):
    TestClient(app).get("/api/v1/health")

    assert recorded == [], "the liveness probe is being counted as usage"


def test_a_real_request_still_is(recorded):
    """⚠️ The counterpart, and the expensive one to get wrong: ⭐ *a filter that catches everything is
    indistinguishable from recording being broken*, which ADR-281 already found the hard way."""
    TestClient(app).post("/api/v1/players", json={"horizon": 1, "limit": 1})

    assert recorded == ["/api/v1/players"]


def test_a_failing_request_is_still_recorded(recorded):
    """⭐ *A failure is usage too* — it is load, and it is the half that tells you something is wrong."""
    TestClient(app).post("/api/v1/ask", json={})

    assert recorded == ["/api/v1/ask"]


def test_the_skip_is_a_list_someone_can_read():
    assert "/api/v1/health" in usage.UNCOUNTED
    assert isinstance(usage.UNCOUNTED, frozenset)


def test_a_path_that_merely_contains_health_is_still_recorded(recorded):
    """⚠️⚠️ **Exact paths, not a substring match on the word "health".**

    A mutation replacing the set membership with `'health' in path` survived every test above, because
    nothing here ever asked for a path that merely *contains* it. ⭐ *A rule that matches by coincidence
    will one day silence an endpoint somebody wanted* — and it would do so invisibly, which is the whole
    failure mode this file exists to prevent.
    """
    TestClient(app).get("/api/v1/team-dna/health-check")

    assert recorded == ["/api/v1/team-dna/health-check"], (
        "a path containing 'health' was dropped — the skip is matching by coincidence"
    )


def test_the_probe_still_answers_normally():
    """⭐ Not counting it must not change it — ⚠️ *the platform is using this to decide whether to keep
    the service in rotation.*"""
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["service"] == "madboots"
