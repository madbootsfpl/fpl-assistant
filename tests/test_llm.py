"""Tests for the local-model edge (ADR-034/151/157).

The model is never load-bearing — every function here returns None on any failure and the caller degrades.
What is worth pinning is that **narration and extraction are separate choices**: they run under different
conditions (a person waiting vs an unattended `refresh`) and one shared constant was quietly deciding for
both. Offline: `urlopen` is stubbed, no Ollama required.
"""

import io
import json
import urllib.request

import pytest

from src import config, llm

# These test `llm` itself, so they opt out of `conftest`'s autouse stub (which replaces exactly the two
# functions under test here). They remain offline — `_capture` stubs `urlopen` in every one.
pytestmark = pytest.mark.real_llm


def _capture(monkeypatch, response="ok"):
    """Stub `urlopen` and hand back the list of request bodies it was given."""
    sent = []

    def fake_urlopen(req, timeout=None):
        sent.append({**json.loads(req.data), "_timeout": timeout})
        return io.BytesIO(json.dumps({"response": response}).encode())

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    return sent


def test_extraction_and_narration_read_different_model_knobs(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_MODEL", "prose-model")
    monkeypatch.setattr(config, "OLLAMA_EXTRACT_MODEL", "json-model")
    sent = _capture(monkeypatch)

    llm.extract("x")
    llm.narrate("x")
    assert [s["model"] for s in sent] == ["json-model", "prose-model"]


def test_extraction_gets_its_own_timeout(monkeypatch):
    """Extraction runs unattended in `refresh`; narration runs while someone waits for a sentence."""
    monkeypatch.setattr(config, "OLLAMA_TIMEOUT", 11)
    monkeypatch.setattr(config, "OLLAMA_EXTRACT_TIMEOUT", 222)
    sent = _capture(monkeypatch)

    llm.extract("x")
    llm.narrate("x")
    assert [s["_timeout"] for s in sent] == [222, 11]


def test_an_explicit_model_still_wins(monkeypatch):
    """The measurement harness passes a model per call — that has to override the default."""
    sent = _capture(monkeypatch)
    llm.extract("x", model="something-else", timeout=5)
    assert sent[0]["model"] == "something-else" and sent[0]["_timeout"] == 5


def test_extraction_asks_for_determinism_and_no_thinking(monkeypatch):
    sent = _capture(monkeypatch)
    llm.extract("x")
    assert sent[0]["options"]["temperature"] == 0
    assert sent[0]["think"] is False          # a reasoning model must not narrate its way to the JSON


def test_a_missing_model_costs_nothing_but_the_answer(monkeypatch):
    def boom(req, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", boom)
    assert llm.extract("x") is None
    assert llm.narrate("x") is None
