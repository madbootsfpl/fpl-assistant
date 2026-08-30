"""The tripwire for `conftest.py`'s autouse stub — proof the suite cannot reach a language model.

Without this, `_no_language_model` is a fixture nobody can tell is working: if it silently stopped covering
a seam, the suite would still pass, just slower and against a real Ollama on whichever machine had one
running. That is precisely the failure it was written to end, so it needs a test that fires.

The check is at the **network** boundary rather than on `llm.narrate`, because that is the one place every
route out of the process must pass through — it catches a call that slips past the stub by any means,
including the stale-default seam that motivated the fixture.
"""

import urllib.request

import pytest

from src import ask, llm
from src.storage import Storage


@pytest.fixture
def _explode_on_network(monkeypatch):
    """Any HTTP call from here on is a test failure, not a slow test."""
    def boom(*a, **k):
        raise AssertionError("a test reached the network — the language-model stub is not covering this path")

    monkeypatch.setattr(urllib.request, "urlopen", boom)


def test_llm_helpers_are_stubbed(_explode_on_network):
    """The module-level seam: a direct call returns None without touching the network."""
    assert llm.narrate("hello") is None
    assert llm.extract("hello") is None


def test_ask_does_not_reach_a_model_through_its_captured_default(_explode_on_network):
    """The seam that actually bites: `narrator=llm.narrate` is bound at import, not looked up per call.

    If `conftest` patched only the `llm` module, this test would hit `boom` and fail — which is how it was
    verified rather than assumed.
    """
    store = Storage()
    try:
        result = ask.answer("who should I captain?", store=store)
    finally:
        store.close()
    # The analytics still answer; only the written narration is absent, exactly as when Ollama is off.
    assert result is not None


def test_the_stub_is_what_ollama_being_absent_looks_like():
    """The stub returns `None` because that is `src.llm`'s own contract for "unavailable" — not a sentinel
    invented for tests, which would make the tested path differ from the real degraded one."""
    assert llm.narrate("x") is None and llm.extract("x") is None
