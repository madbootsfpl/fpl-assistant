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
        FplClient().get_bootstrap_static()
