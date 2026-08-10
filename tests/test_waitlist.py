"""Tests for the beta waitlist store (ADR-102, US-347).

No live network — `requests` is monkeypatched. The store reuses the squads `FPL_STORE_URL`/`FPL_STORE_KEY` (the
`beta_waitlist` endpoint is derived). `add()` is **best-effort + fail-silent** — it must never raise.
"""

import pytest

from src.web_streamlit import waitlist


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("FPL_STORE_URL", "https://proj.supabase.co/rest/v1/squads")
    monkeypatch.setenv("FPL_STORE_KEY", "anon-key")


def test_endpoint_derives_the_waitlist_table(configured):
    url, key = waitlist._endpoint()
    assert url == "https://proj.supabase.co/rest/v1/beta_waitlist" and key == "anon-key"   # sibling of beta_users


def test_add_upserts_a_cleaned_email_and_reason(configured, monkeypatch):
    posted = {}
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None:
                        posted.update(url=url, body=json, headers=headers))
    waitlist.add("  Late@Example.com ", "bad_code")
    assert posted["url"].endswith("/beta_waitlist")
    assert posted["body"] == {"email": "late@example.com", "reason": "bad_code"}       # cleaned + the reason
    assert "merge-duplicates" in posted["headers"]["Prefer"]                           # idempotent upsert on the PK
    assert "Bearer anon-key" in posted["headers"]["Authorization"]


def test_add_is_a_noop_without_the_store(monkeypatch):
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    monkeypatch.setattr("requests.post", lambda *a, **k: pytest.fail("no waitlist write without the store"))
    waitlist.add("x@y.com", "full")                    # off by default → a no-op
    assert waitlist.is_configured() is False


def test_add_ignores_a_malformed_or_empty_email(configured, monkeypatch):
    monkeypatch.setattr("requests.post", lambda *a, **k: pytest.fail("no write for a bad/empty email"))
    waitlist.add("not-an-email", "bad_code")
    waitlist.add("", "full")
    waitlist.add(None, "full")


def test_add_swallows_a_store_failure(configured, monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("supabase down")
    monkeypatch.setattr("requests.post", boom)
    waitlist.add("x@y.com", "full")                    # best-effort: must NOT raise (never blocks the gate)
