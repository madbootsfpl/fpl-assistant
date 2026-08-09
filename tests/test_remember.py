"""Tests for the "remember me" cookie seam (ADR-099, US-325; read fixed to the component in Sprint 134).

Read and write both go through `remember._controller` (the cookie component) — monkeypatched to a tiny fake
for the roundtrip, or made to raise to prove graceful degradation (read → None, write/clear no-op, available →
False). The real iframe roundtrip is covered by the manual smoke, not here (AppTest has no browser).
"""

from src.web_streamlit import remember


class _FakeController:
    """A minimal stand-in for CookieController — a dict with get/set/remove."""

    def __init__(self, store):
        self._store = store

    def get(self, name):
        return self._store.get(name)

    def set(self, name, value, max_age=None):
        self._store[name] = value

    def remove(self, name):
        self._store.pop(name, None)


def _use_fake(monkeypatch):
    store = {}
    monkeypatch.setattr(remember, "_controller", lambda: _FakeController(store))
    return store


# --- read/write/clear roundtrip through the same component (same cookie jar) ----------

def test_write_then_read_roundtrips(monkeypatch):
    """The Sprint 134 fix: reading through the *same* component that writes returns the value (one jar)."""
    _use_fake(monkeypatch)
    remember.write("tester@example.com")
    assert remember.read() == "tester@example.com"


def test_read_is_none_when_nothing_set(monkeypatch):
    _use_fake(monkeypatch)
    assert remember.read() is None


def test_named_cookies_roundtrip_and_the_gate_delegates(monkeypatch):
    # US-333: named read/write_cookie back both fpl_beta (the gate) and fpl_anon (analytics), same jar.
    store = _use_fake(monkeypatch)
    remember.write_cookie("fpl_anon", "anon-xyz")
    assert remember.read_cookie("fpl_anon") == "anon-xyz"
    assert remember.read_cookie("missing") is None
    remember.write("beta-val")                                  # the gate helpers delegate to the named ones
    assert remember.read() == "beta-val" and store["fpl_beta"] == "beta-val"


def test_clear_forgets_the_value(monkeypatch):
    _use_fake(monkeypatch)
    remember.write("tester@example.com")
    remember.clear()
    assert remember.read() is None


def test_write_ignores_an_empty_value(monkeypatch):
    store = _use_fake(monkeypatch)
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


# --- available(): is there a component to wait on? -----------------------------------

def test_available_true_when_the_component_constructs(monkeypatch):
    monkeypatch.setattr(remember, "_controller", lambda: _FakeController({}))
    assert remember.available() is True


def test_available_false_when_the_component_is_missing(monkeypatch):
    def _boom():
        raise ImportError("streamlit-cookies-controller not installed")
    monkeypatch.setattr(remember, "_controller", _boom)
    assert remember.available() is False


# --- graceful degradation: component missing / erroring ------------------------------

def test_read_degrades_to_none_when_unavailable(monkeypatch):
    def _boom():
        raise ImportError("streamlit-cookies-controller not installed")
    monkeypatch.setattr(remember, "_controller", _boom)
    assert remember.read() is None


def test_write_and_clear_noop_when_unavailable(monkeypatch):
    def _boom():
        raise RuntimeError("no ScriptRunContext")
    monkeypatch.setattr(remember, "_controller", _boom)
    # Must not raise — the gate relies on these being safe no-ops.
    remember.write("tester@example.com")
    remember.clear()
