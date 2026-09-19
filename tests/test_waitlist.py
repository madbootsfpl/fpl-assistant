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


def test_add_posts_a_cleaned_email_and_reason(configured, monkeypatch):
    posted = {}
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None:
                        posted.update(url=url, body=json, headers=headers))
    waitlist.add("  Late@Example.com ", "bad_code")
    assert posted["url"].endswith("/beta_waitlist")
    assert posted["body"] == {"email": "late@example.com", "reason": "bad_code"}       # cleaned + the reason
    assert "Bearer anon-key" in posted["headers"]["Authorization"]


def test_the_write_is_a_PLAIN_INSERT_because_an_upsert_would_force_the_table_open(configured, monkeypatch):
    """⭐⭐ **The absent header is a security control, not an oversight** (docs/SUPABASE_RLS.md A1).

    This table holds the address of everyone who was **refused**, and the goal is that emails go in and
    nothing comes out. Measured on Postgres 17 across four grant/policy combinations: `ON CONFLICT` — both
    `DO UPDATE` and `DO NOTHING` — requires a **permissive `SELECT` policy**, because it has to read the
    conflicting row. So an upsert and a locked-down read are mutually exclusive: restoring
    `Prefer: resolution=merge-duplicates` would force `using (true)` back onto select, which *is* the
    exposure this stage removes.

    ⚠️ And it would fail **silently** — `add()` swallows everything, so the table would simply stop growing
    and it would look like nobody was being refused.
    """
    posted = {}
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None:
                        posted.update(headers=headers))
    waitlist.add("someone@example.invalid", "not_listed")
    assert "Prefer" not in posted["headers"], (
        "an upsert here requires a permissive SELECT policy on a table of refused addresses — "
        "see docs/SUPABASE_RLS.md A1")


def test_a_duplicate_email_is_tolerated_and_never_surfaces(configured, monkeypatch):
    """A repeat refusal now returns **409** instead of 200, and that is the intended behaviour: the row
    already exists, so the person is already on the waitlist. Only the *latest* `reason` is lost.

    ⭐ `requests.post` does not raise on an HTTP status, so the 409 never even reaches the `except` — the
    upsert's whole job was to avoid an error this function was already ignoring."""
    class _Conflict:
        status_code = 409
        text = '{"code":"23505","message":"duplicate key value violates unique constraint"}'

    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: _Conflict())
    waitlist.add("repeat@example.invalid", "full")          # must not raise, must not block the gate


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
