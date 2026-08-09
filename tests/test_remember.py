"""Tests for the "remember me" cookie seam (ADR-099, US-325).

No browser and no real cookie component: `remember._controller` is the injection seam —
monkeypatched to a tiny fake for the roundtrip, or made to raise to prove graceful
degradation (a missing/erroring component ⇒ read() is None, write()/clear() no-op). The
real iframe roundtrip is covered by the manual smoke, not here (AppTest has no browser).
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


# --- roundtrip: write → read → clear -------------------------------------------------

def test_write_then_read_roundtrips(monkeypatch):
    _use_fake(monkeypatch)
    remember.write("tester@example.com")
    assert remember.read() == "tester@example.com"


def test_clear_forgets_the_value(monkeypatch):
    _use_fake(monkeypatch)
    remember.write("tester@example.com")
    remember.clear()
    assert remember.read() is None


def test_read_is_none_when_nothing_set(monkeypatch):
    _use_fake(monkeypatch)
    assert remember.read() is None


def test_write_ignores_empty_value(monkeypatch):
    store = _use_fake(monkeypatch)
    remember.write("")
    remember.write(None)
    assert store == {}
    assert remember.read() is None


def test_write_passes_a_multi_day_expiry(monkeypatch):
    """The cookie is a *remember*, not a session cookie — a positive max_age is sent."""
    captured = {}

    class _Capture(_FakeController):
        def set(self, name, value, max_age=None):
            captured["max_age"] = max_age
            super().set(name, value, max_age=max_age)

    monkeypatch.setattr(remember, "_controller", lambda: _Capture({}))
    remember.write("code123")
    assert captured["max_age"] == remember.TTL_DAYS * 24 * 60 * 60
    assert captured["max_age"] > 0


# --- graceful degradation: component missing/erroring --------------------------------

def _break_controller(monkeypatch):
    def _boom():
        raise ImportError("streamlit-cookies-controller not installed")
    monkeypatch.setattr(remember, "_controller", _boom)


def test_read_degrades_to_none_when_unavailable(monkeypatch):
    _break_controller(monkeypatch)
    assert remember.read() is None


def test_write_and_clear_noop_when_unavailable(monkeypatch):
    _break_controller(monkeypatch)
    # Must not raise — the gate relies on these being safe no-ops.
    remember.write("tester@example.com")
    remember.clear()


def test_read_swallows_a_runtime_error(monkeypatch):
    class _Angry:
        def get(self, name):
            raise RuntimeError("no ScriptRunContext")

    monkeypatch.setattr(remember, "_controller", lambda: _Angry())
    assert remember.read() is None
