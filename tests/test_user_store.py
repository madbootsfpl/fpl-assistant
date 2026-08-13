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
    """A tiny in-memory Supabase: GET filters/counts, POST appends."""
    def fake_get(url, params=None, headers=None, timeout=None):
        assert url.endswith("/rest/v1/beta_users")                 # derived from the squads base
        if params and "email" in params:                          # is_registered
            e = params["email"].split("eq.", 1)[1]
            return _Resp([{"email": e}] if e in rows else [])
        return _Resp([{"email": e} for e in rows])                # count
    monkeypatch.setattr("requests.get", fake_get)
    monkeypatch.setattr("requests.post",
                        lambda url, json=None, headers=None, timeout=None: rows.append(json["email"]) or _Resp())


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


def test_is_registered_is_case_and_space_insensitive(configured, monkeypatch):
    # The allow-list bug (2026-08-13): a hand-typed `beta_users` row with capitals / stray spaces must still admit
    # the (lower-cased) Google email — the PostgREST `eq.` filter is case-sensitive, so we normalise both sides.
    _fake_store(monkeypatch, ["Colinbermingham@Live.ie", "  spaced@x.com  "])
    assert user_store.is_registered("colinbermingham@live.ie") is True   # capital C in the stored row
    assert user_store.is_registered("COLINBERMINGHAM@LIVE.IE") is True   # capitals in the query too
    assert user_store.is_registered("spaced@x.com") is True              # stored row had stray spaces
    assert user_store.is_registered("someone@else.com") is False
