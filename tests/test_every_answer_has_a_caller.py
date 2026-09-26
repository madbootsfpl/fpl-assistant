"""Every service function is reachable from some surface (ADR-301).

⚠️⚠️⚠️ **Chatter was called by nobody for a month and every suite stayed green.** `community_signals`
shipped on the web in Sprint 068, sat on the Trending page until 26 Aug 2026, and was dropped by ADR-150's
reorganisation. From that day it was reachable from **no surface at all** — not the web, not the CLI, not
the app — and it went on passing its own unit tests the whole time, because unit tests ask *"does this
work?"* and never *"does anything still call it?"*

⭐⭐ **A feature does not have to be deleted to be lost.** It was removed from the one screen that used it
and the code stayed exactly where it was.

⭐ This is deliberately **not** a parity test. It does not care whether a thing is on one surface or three
— that is ADR-301's open decision. It cares only that the number is not **zero**.
"""

from __future__ import annotations

import ast
import pathlib

from src import service

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
ROUTES = SRC / "service" / "http" / "app.py"

#: ⚠️ Answers that are genuinely internal, with the reason written down. ⭐ *"Nothing calls this on
#: purpose" has to be stated, or the next reader cannot tell it from "nobody noticed".*
INTERNAL: dict[str, str] = {}


def _imported_from_service() -> set[str]:
    """Every name any module imports from `src.service`, alias or not.

    ⭐ Parsed rather than grepped: `from src.service import analysis as service_analysis` is how the web
    actually imports one of these, and a substring search for `analysis(` misses it — ⚠️ *a guard with a
    false negative is a guard that reports success it has not checked.*
    """
    found: set[str] = set()
    for path in SRC.rglob("*.py"):
        if path.is_relative_to(SRC / "service"):
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:  # pragma: no cover - a broken file is its own test's problem
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("src.service"):
                found.update(alias.name for alias in node.names)
            # `service.chatter(...)` — the CLI and the web both reach some answers this way.
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id in {"service", "svc"}:
                    found.add(node.attr)
    return found


def _served_over_http() -> set[str]:
    """Every answer a route hands to `_answer(...)`."""
    tree = ast.parse(ROUTES.read_text())
    return {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "service"
    }


def test_no_answer_is_reachable_from_nowhere() -> None:
    public = {
        name for name in service.__all__
        if callable(getattr(service, name)) and not name.endswith("Request")
    }
    reachable = _imported_from_service() | _served_over_http()

    orphans = sorted(public - reachable - set(INTERNAL))
    assert not orphans, (
        f"{orphans} are service answers that nothing calls — no HTTP route, no web page, no CLI.\n"
        f"This is what happened to `chatter` for a month: the screen that used it was reorganised away "
        f"and the code stayed, green and unreachable.\n"
        f"Either give it a caller, or add it to INTERNAL with the reason."
    )


def test_the_guard_can_actually_fail() -> None:
    """⭐ A sweep that finds everything reachable passes whether or not it is looking.

    ⚠️ *If `_imported_from_service` ever returns the whole world — a bad parse swallowed silently, say —
    the test above becomes vacuously true and the guard is gone with nothing going red.*
    """
    reachable = _imported_from_service() | _served_over_http()

    assert "chatter" in reachable, "the guard cannot see the endpoint that prompted it"
    assert "definitely_not_an_answer" not in reachable, (
        "the guard considers an invented name reachable — it is matching too broadly to mean anything"
    )
