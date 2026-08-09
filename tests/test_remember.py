"""Tests for the "remember me" cookie seam (ADR-099, US-325).

The two halves are seamed for testing without a browser:
- **read** goes through `remember._request_cookies` (native `st.context.cookies`) — monkeypatched to a dict.
- **write/clear** go through `remember._controller` (the cookie component) — monkeypatched to a tiny fake,
  or made to raise to prove graceful degradation.
The real iframe roundtrip is covered by the manual smoke, not here (AppTest has no browser).
"""

from src.web_streamlit import remember


class _FakeController:
    """A minimal stand-in for CookieController — a dict with set/remove."""

    def __init__(self, store):
        self._store = store

    def set(self, name, value, max_age=None):
        self._store[name] = value

    def remove(self, name):
        self._store.pop(name, None)


# --- read: native request cookies ----------------------------------------------------

def test_read_returns_the_cookie_value(monkeypatch):
    monkeypatch.setattr(remember, "_request_cookies", lambda: {remember.COOKIE: "tester@example.com"})
    assert remember.read() == "tester@example.com"


def test_read_is_none_when_the_cookie_is_absent(monkeypatch):
    monkeypatch.setattr(remember, "_request_cookies", lambda: {})
    assert remember.read() is None


def test_read_degrades_to_none_when_context_raises(monkeypatch):
    def _boom():
        raise RuntimeError("no request context")
    monkeypatch.setattr(remember, "_request_cookies", _boom)
    assert remember.read() is None


# --- write / clear: the cookie component ---------------------------------------------

def test_write_sets_via_the_component(monkeypatch):
    store = {}
    monkeypatch.setattr(remember, "_controller", lambda: _FakeController(store))
    remember.write("tester@example.com")
    assert store[remember.COOKIE] == "tester@example.com"


def test_write_ignores_an_empty_value(monkeypatch):
    store = {}
    monkeypatch.setattr(remember, "_controller", lambda: _FakeController(store))
    remember.write("")
    remember.write(None)
    assert store == {}


def test_write_passes_a_multi_day_expiry(monkeypatch):
    """A *remember*, not a session cookie — a positive, multi-day max_age is sent."""
    captured = {}

    class _Capture(_FakeController):
        def set(self, name, value, max_age=None):
            captured["max_age"] = max_age
            super().set(name, value, max_age=max_age)

    monkeypatch.setattr(remember, "_controller", lambda: _Capture({}))
    remember.write("code123")
    assert captured["max_age"] == remember.TTL_DAYS * 24 * 60 * 60
    assert captured["max_age"] > 0


def test_clear_removes_via_the_component(monkeypatch):
    store = {remember.COOKIE: "x"}
    monkeypatch.setattr(remember, "_controller", lambda: _FakeController(store))
    remember.clear()
    assert remember.COOKIE not in store


# --- graceful degradation: component missing / erroring ------------------------------

def test_write_and_clear_noop_when_the_component_is_unavailable(monkeypatch):
    def _boom():
        raise ImportError("streamlit-cookies-controller not installed")
    monkeypatch.setattr(remember, "_controller", _boom)
    # Must not raise — the gate relies on these being safe no-ops.
    remember.write("tester@example.com")
    remember.clear()
