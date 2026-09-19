"""Tests for the capped beta-user registration store (ADR-098, US-323).

No live network — `requests` is monkeypatched; the store is configured via env vars (reusing the squads
`FPL_STORE_URL`/`FPL_STORE_KEY`, from which the `beta_users` endpoint is derived).
"""

import pytest

from src.web_streamlit import user_store


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
    monkeypatch.setenv("FPL_STORE_KEY", "anon-key")


def _fake_store(monkeypatch, rows):
    """A tiny in-memory Supabase: the table GET for the admin reads, and the two Stage B **RPCs**.

    ⚠️ **The fake implements the protocol, not the logic.** `is_allow_listed` matches case-insensitively and
    `register_beta_user` enforces the cap under a lock — *in SQL*. A fake reimplementing that would be testing
    itself (⭐ *ask "if I deleted the thing under test, would this still pass?"*). The real behaviour is covered
    against a live Postgres in `tests/test_stage_b_sql.py`; what is checked here is that the app calls the
    right endpoint with the right payload and respects the answer.
    """
    def fake_get(url, params=None, headers=None, timeout=None):
        assert url.endswith("/rest/v1/beta_users")                 # the admin reads still use the table
        return _Resp([{"email": e} for e in rows])
    monkeypatch.setattr("requests.get", fake_get)

    def fake_post(url, json=None, headers=None, timeout=None):
        if url.endswith("/rpc/is_allow_listed"):
            return _Resp(json["p_email"] in rows)
        if url.endswith("/rpc/register_beta_user"):
            e = json["p_email"]
            if e in rows:
                return _Resp("in")
            if json["p_cap"] is not None and len(rows) >= json["p_cap"]:
                return _Resp("full")
            rows.append(e)
            return _Resp("in")
        raise AssertionError(f"unexpected POST to {url}")           # a direct table write would be a regression
    monkeypatch.setattr("requests.post", fake_post)


# ---- config + endpoint + email hygiene -------------------------------------

def test_endpoint_derives_beta_users_from_the_squads_url(configured):
    assert user_store.is_configured() is True
    assert user_store._endpoint()[0] == "https://proj.supabase.co/rest/v1/beta_users"


def test_not_configured_without_the_store_secrets(monkeypatch):
    monkeypatch.delenv("FPL_STORE_URL", raising=False)
    monkeypatch.delenv("FPL_STORE_KEY", raising=False)
    assert user_store.is_configured() is False
    assert user_store.count() == 0 and user_store.is_registered("a@b.com") is False
    with pytest.raises(RuntimeError):
        user_store.register("a@b.com", 10)


def test_clean_email_normalises_and_rejects():
    assert user_store.clean_email("  Foo@Bar.com ") == "foo@bar.com"
    assert user_store.clean_email("nope") == ""                    # no @/domain
    assert user_store.clean_email("") == ""


# ---- register: cap logic ---------------------------------------------------

def test_register_admits_new_emails_up_to_the_cap(configured, monkeypatch):
    rows = []
    _fake_store(monkeypatch, rows)
    assert user_store.register("A@b.com", 2) == "in" and rows == ["a@b.com"]   # cleaned + inserted
    assert user_store.register("c@d.com", 2) == "in" and user_store.count() == 2
    assert user_store.register("e@f.com", 2) == "full"                         # at the cap
    assert user_store.count() == 2                                             # not inserted


def test_register_is_idempotent_for_a_known_email(configured, monkeypatch):
    rows = ["a@b.com"]
    _fake_store(monkeypatch, rows)
    assert user_store.register("a@b.com", 1) == "in"               # already in → admitted, no new row
    assert rows == ["a@b.com"]                                     # even though we're at the cap


def test_register_rejects_a_bad_email(configured, monkeypatch):
    _fake_store(monkeypatch, [])
    with pytest.raises(ValueError):
        user_store.register("not-an-email", 10)


def test_is_registered_reflects_the_row(configured, monkeypatch):
    _fake_store(monkeypatch, ["a@b.com"])
    assert user_store.is_registered("A@b.com") is True            # cleaned + found
    assert user_store.is_registered("z@z.com") is False


def test_is_registered_asks_a_BOOLEAN_QUESTION_instead_of_fetching_the_list():
    """⭐⭐ The Stage B change, pinned at the call site. This used to `GET /beta_users?select=email` — the whole
    tester allow-list, on every gate check — because a PostgREST `eq.` filter is case-sensitive and a
    hand-typed row like `Colin@x.ie` must admit `colin@x.ie`. The matching moved into SQL, so what crosses the
    wire now is one address and one boolean.

    ⚠️ The case-insensitivity itself is **no longer testable here**; it is covered against a real Postgres in
    `tests/test_stage_b_sql.py`. What this guards is that nobody reinstates the table read."""
    import inspect

    src = inspect.getsource(user_store.is_registered)
    assert '_rpc("is_allow_listed")' in src
    assert "requests.get" not in src, "the allow-list must never be fetched to answer this"


def test_the_gate_fails_CLOSED_when_the_store_is_unreachable(configured, monkeypatch):
    """⚠️ The direction matters more than the failure: an unreachable store must **refuse** entry, not grant
    it. The alternative is an outage that opens the beta to everyone."""
    def boom(*a, **k):
        raise OSError("network down")
    monkeypatch.setattr("requests.post", boom)
    assert user_store.is_registered("anyone@example.invalid") is False
