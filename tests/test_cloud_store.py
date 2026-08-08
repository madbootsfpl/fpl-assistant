"""Tests for the handle-keyed cloud squad store (ADR-094, US-309).

No live network — `requests` is monkeypatched; the store is configured via env vars (the `secret` helper
falls back to `os.environ`).
"""

import pytest

from src.web_streamlit import cloud_store


class _Resp:
    def __init__(self, data=None):
        self._data = [] if data is None else data

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "anon-key-123")


# --- config gate -------------------------------------------------------------------------------

def test_is_configured_false_without_secrets(monkeypatch):
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    assert cloud_store.is_configured() is False
    assert cloud_store.load_squad("tony17") is None        # inert: no read
    with pytest.raises(RuntimeError):
        cloud_store.save_squad("tony17", {"name": "x"})    # inert: no write


def test_is_configured_true_when_both_secrets_set(configured):
    assert cloud_store.is_configured() is True


# --- handle hygiene ----------------------------------------------------------------------------

def test_clean_handle_sanitises_and_bounds():
    assert cloud_store.clean_handle("Tony 17!") == "tony17"     # lower-case, strip non [a-z0-9_-]
    assert cloud_store.clean_handle("  My-Team_1 ") == "my-team_1"
    assert cloud_store.clean_handle("a") == ""                  # too short
    assert cloud_store.clean_handle("x" * 40) == ""             # too long
    assert cloud_store.clean_handle("!!") == ""                 # nothing usable


# --- save / load / delete ----------------------------------------------------------------------

def test_save_upserts_with_auth_and_the_handle_key(configured, monkeypatch):
    seen = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        seen.update(url=url, body=json, headers=headers)
        return _Resp()

    monkeypatch.setattr("requests.post", fake_post)
    cloud_store.save_squad("Tony17", {"name": "My XI", "player_ids": [1, 2, 3]})

    assert seen["url"].endswith("/rest/v1/squads")
    assert seen["body"] == {"handle": "tony17", "data": {"name": "My XI", "player_ids": [1, 2, 3]}}
    assert seen["headers"]["Prefer"] == "resolution=merge-duplicates"      # upsert
    assert seen["headers"]["Authorization"] == "Bearer anon-key-123"


def test_save_rejects_a_bad_handle(configured, monkeypatch):
    monkeypatch.setattr("requests.post", lambda *a, **k: _Resp())
    with pytest.raises(ValueError):
        cloud_store.save_squad("!", {"name": "x"})             # cleans to '' → refuse (no write)


def test_load_returns_the_row_data_or_none(configured, monkeypatch):
    def fake_get(url, params=None, headers=None, timeout=None):
        assert params["handle"] == "eq.tony17"                 # the eq. filter is built from the clean handle
        return _Resp([{"data": {"name": "Loaded XI", "player_ids": [7]}}])

    monkeypatch.setattr("requests.get", fake_get)
    assert cloud_store.load_squad("tony17") == {"name": "Loaded XI", "player_ids": [7]}

    monkeypatch.setattr("requests.get", lambda *a, **k: _Resp([]))   # nothing stored
    assert cloud_store.load_squad("tony17") is None


def test_delete_targets_the_handle(configured, monkeypatch):
    seen = {}
    monkeypatch.setattr("requests.delete",
                        lambda url, params=None, headers=None, timeout=None: seen.update(params=params) or _Resp())
    cloud_store.delete_squad("tony17")
    assert seen["params"] == {"handle": "eq.tony17"}
