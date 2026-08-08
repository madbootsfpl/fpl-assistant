"""Persist one conversational `Context` across CLI runs (ADR-091).

Local, single-user state — like the `SquadStore` (ADR-024): the CLI `ask`/`chat` save the last turn's `Context`
to a small git-ignored JSON file and reload it, so a follow-up ("why?", "and the next?") works across separate
invocations. A short TTL guards against a stale follow-up resurfacing an old turn. The multi-user **web never
uses this** — it keeps per-session `st.session_state`; persisting server-side would break the read-only
guarantee. Saving is best-effort: continuity is a nice-to-have, never a reason to crash a turn.
"""

import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src import config
from src.ask import Context

_TTL = timedelta(hours=2)   # ignore a saved context older than this — a stale "why?" shouldn't resurface it


def _path() -> Path:
    return Path(config.CHAT_CONTEXT_PATH)


def save_context(ctx, *, now: datetime | None = None) -> None:
    """Persist the last turn's `Context` (best-effort). `None` clears it (e.g. after a 'forget')."""
    if ctx is None:
        clear_context()
        return
    now = now or datetime.now(timezone.utc)
    try:
        path = _path()
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"saved_at": now.isoformat(), "context": asdict(ctx)}
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload))
        tmp.replace(path)                        # atomic-ish: never leaves a half-written file
    except (OSError, TypeError, ValueError):
        pass                                     # persistence must never crash a turn


def load_context(*, now: datetime | None = None, ttl: timedelta = _TTL):
    """The saved `Context`, or `None` when absent / unreadable / older than `ttl` (a stale-follow-up guard)."""
    now = now or datetime.now(timezone.utc)
    try:
        raw = _path().read_text()
    except OSError:
        return None
    try:
        payload = json.loads(raw)
        saved_at = datetime.fromisoformat(payload["saved_at"])
        if now - saved_at > ttl:
            return None
        return Context(**payload["context"])
    except (ValueError, KeyError, TypeError):
        return None                              # corrupt / shape-drifted → forget it, don't crash


def clear_context() -> None:
    """Forget the saved conversation."""
    try:
        _path().unlink()
    except OSError:
        pass
