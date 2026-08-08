"""Tests for the persisted chat context (ADR-091) — local, single-user, TTL'd.

Pure round-trip + staleness logic; no network, no real clock (the `now` is injected).
"""

from datetime import datetime, timedelta, timezone

from src import chat_context, config
from src.ask import Context

_T0 = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)


def _ctx():
    return Context(intent="captain", squad="RoboTS", question="who should I captain?", count=1, rank=0,
                   decision={"headline": "Captain: X", "facts": {"confidence": "69/100 (Medium)"}})


def _isolate(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CHAT_CONTEXT_PATH", str(tmp_path / "chat_context.json"))


def test_save_and_load_round_trips(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    chat_context.save_context(_ctx(), now=_T0)
    loaded = chat_context.load_context(now=_T0)
    assert loaded == _ctx()                                  # dataclass equality: every field survived


def test_load_returns_none_past_the_ttl(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    chat_context.save_context(_ctx(), now=_T0)
    assert chat_context.load_context(now=_T0 + timedelta(hours=1)) is not None     # fresh → resumes
    assert chat_context.load_context(now=_T0 + timedelta(hours=3)) is None         # stale → forgotten


def test_clear_and_save_none_forget_the_context(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    chat_context.save_context(_ctx(), now=_T0)
    chat_context.clear_context()
    assert chat_context.load_context(now=_T0) is None
    chat_context.save_context(_ctx(), now=_T0)
    chat_context.save_context(None, now=_T0)                 # saving None clears (a "forget")
    assert chat_context.load_context(now=_T0) is None


def test_load_is_none_when_absent_or_corrupt(monkeypatch, tmp_path):
    _isolate(monkeypatch, tmp_path)
    assert chat_context.load_context(now=_T0) is None        # no file yet
    (tmp_path / "chat_context.json").write_text("not json{")
    assert chat_context.load_context(now=_T0) is None        # corrupt → forgotten, not a crash
