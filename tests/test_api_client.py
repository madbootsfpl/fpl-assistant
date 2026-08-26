"""Tests for the FPL API client.

These tests never touch the live FPL API. The network call is replaced with a
saved sample response (tests/fixtures/bootstrap_static_sample.json), so the
tests are fast, offline and deterministic — and can't trip rate limits.
"""

import json
from pathlib import Path

import pytest
import requests

from src.api.client import FplApiError, FplClient

FIXTURE = Path(__file__).parent / "fixtures" / "bootstrap_static_sample.json"


def load_sample() -> dict:
    return json.loads(FIXTURE.read_text())


class FakeResponse:
    """Stand-in for a requests.Response, enough for the client's needs."""

    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        # The sample always represents a successful (200) response.
        pass

    def json(self) -> dict:
        return self._payload


def test_get_bootstrap_static_returns_parsed_json(monkeypatch):
    sample = load_sample()

    def fake_get(url, timeout, headers):
        return FakeResponse(sample)

    monkeypatch.setattr("src.api.client.requests.get", fake_get)

    data = FplClient().get_bootstrap_static()

    assert "elements" in data
    assert len(data["elements"]) == len(sample["elements"])
    assert data["teams"][0]["short_name"] == "ARS"


def test_get_bootstrap_static_wraps_network_errors(monkeypatch):
    def fake_get(url, timeout, headers):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr("src.api.client.requests.get", fake_get)

    with pytest.raises(FplApiError):
        # A connection error is transient, so it retries — inject a no-op sleep so the
        # test stays instant.
        FplClient(sleep=lambda s: None).get_bootstrap_static()


# --- retry-with-backoff (ADR-021): FPL is required, so it retries hard (2 retries) ---

class StatusResponse:
    """A stand-in requests.Response: raise_for_status raises HTTPError on a 4xx/5xx."""

    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload or {"elements": []}

    def raise_for_status(self):
        if self.status_code >= 400:
            resp = requests.Response()
            resp.status_code = self.status_code
            raise requests.HTTPError(response=resp)

    def json(self):
        return self._payload


def sequence_get(items):
    """A fake requests.get yielding `items` (StatusResponse or Exception) in order."""
    it = iter(items)

    def _get(*a, **k):
        item = next(it)
        if isinstance(item, Exception):
            raise item
        return item

    return _get


def test_get_json_retries_transient_then_succeeds(monkeypatch):
    sleeps = []
    monkeypatch.setattr(
        "src.api.client.requests.get",
        sequence_get([StatusResponse(502), StatusResponse(502), StatusResponse(200)]),
    )
    data = FplClient(sleep=sleeps.append).get_bootstrap_static()

    assert data == {"elements": []}    # succeeded on the 3rd attempt
    assert sleeps == [0.5, 1.0]        # FPL retries hard: two backoffs


def test_get_json_does_not_retry_permanent(monkeypatch):
    sleeps = []
    monkeypatch.setattr("src.api.client.requests.get", sequence_get([StatusResponse(404)]))
    with pytest.raises(FplApiError) as exc:
        FplClient(sleep=sleeps.append).get_bootstrap_static()

    assert "after 1 attempt" in str(exc.value)
    assert sleeps == []                # no retry on a permanent error


def test_get_json_exhausts_retries_then_raises(monkeypatch):
    sleeps = []
    monkeypatch.setattr("src.api.client.requests.get", sequence_get([StatusResponse(503)] * 3))
    with pytest.raises(FplApiError) as exc:
        FplClient(sleep=sleeps.append).get_bootstrap_static()

    assert "after 3 attempt" in str(exc.value)   # required source → still fatal
    assert sleeps == [0.5, 1.0]


def test_get_league_standings_asks_for_the_first_page(monkeypatch):
    """ADR-141. Pins the URL, because this endpoint is paginated and the page number is *not* optional in
    practice — FPL returns page 1 by default today, but the app depends on knowing which 50 it got, and a
    silently different page would change every number on the view.
    """
    seen = {}

    def fake_get(url, timeout, headers):
        seen["url"] = url
        return FakeResponse({"league": {"name": "Overall"}, "standings": {"results": [], "has_next": True}})

    monkeypatch.setattr(requests, "get", fake_get)
    out = FplClient().get_league_standings(314)

    assert seen["url"].endswith("/leagues-classic/314/standings/?page_standings=1")
    assert out["league"]["name"] == "Overall"


def test_a_league_fetch_failure_raises_the_client_error_like_any_other(monkeypatch):
    """The page catches `FplApiError` to show "check the id" — so it has to actually be raised, not leak a
    `requests` exception."""
    def boom(url, timeout, headers):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(FplApiError):
        FplClient(retries=0, sleep=lambda _s: None).get_league_standings(1)
