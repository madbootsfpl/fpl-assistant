"""No endpoint may ship markdown — ⭐ **the API speaks text, not Streamlit** (ADR-274).

⚠️⚠️ **This shipped.** The Trending caveat reached the phone as *"`**12 players**` stand out on two or
more of these boards"*, asterisks and all, at the top of the screen the owner had just asked to be made
prominent. The engine's notes are written for a page that renders markdown; the phone renders none.

⭐⭐ **A sweep, not a check on the two strings that were wrong** (ADR-184). The notes were written in the
analytics layer for one consumer and there are more of them than anyone has counted — *a guard against a
claim must sweep for the claim, not check the places you thought of.*
"""

import pathlib
import sys

import pytest

from src import service
from src.storage import Storage

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent
                       / "spikes" / "018-flutter-read-slice"))

#: ⚠️ `_` is not included. It appears inside real words the API legitimately carries (`web_name`,
#: `by_gameweek`), and a rule that fires on those is a rule someone turns off.
MARKDOWN = ("**", "__", "`")


def strings_in(value, path="") -> list[tuple[str, str]]:
    """Every string in an answer, with the path that reaches it — so a failure names the field."""
    if isinstance(value, dict):
        return [hit for k, v in value.items() for hit in strings_in(v, f"{path}.{k}")]
    if isinstance(value, list):
        return [hit for i, v in enumerate(value) for hit in strings_in(v, f"{path}[{i}]")]
    return [(path, value)] if isinstance(value, str) else []


@pytest.fixture(scope="module")
def answers():
    """Every endpoint's answer, built the way the shape sweep builds them (FPL calls stubbed).

    ⚠️⚠️ **Plus every trending board, because the shape sweep builds only one.** Written this way after
    the sweep was re-broken to check it: with the bug restored, only the *named* test failed — the sweep
    itself passed, because the board carrying the markdown was not among the answers it walks.

    ⭐ *A sweep that covers the surfaces it was pointed at is the failure a sweep exists to prevent*
    (ADR-184), and it is worth re-breaking a new guard to find out which kind you have written.
    """
    from test_player_shape import _answers  # noqa: PLC0415 — the sweep owns this construction

    from src.analytics.crowd import TREND_BYS

    store = Storage()
    try:
        built = _answers(store)
        for by in {*TREND_BYS, "look", "watch"}:
            built[f"trending:{by}"] = service.trending(
                service.TrendingRequest(by=by, limit=5), store=store)
        return built
    finally:
        store.close()


def test_no_answer_carries_markdown(answers):
    offenders = [
        f"{name}{path} = {text[:70]!r}"
        for name, answer in answers.items()
        for path, text in strings_in(answer)
        if any(mark in text for mark in MARKDOWN)
    ]
    assert not offenders, (
        "these reach a client as literal markdown:\n  " + "\n  ".join(offenders)
    )


def test_the_trending_notes_specifically_are_clean():
    """⚠️ The two that shipped wrong, pinned by name — ⭐ *a sweep proves the rule; a named case proves
    the bug is gone.*"""
    for by in ("look", "watch"):
        caveat = service.trending(service.TrendingRequest(by=by))["caveat"]
        assert caveat, f"{by} must still say something"
        assert "*" not in caveat, f"{by} still carries emphasis: {caveat[:60]!r}"


def test_plain_removes_bold_before_italic():
    """⚠️ Order matters: stripping `*` first would read `**x**` as an italic `*` wrapping `*x*`."""
    from src.service.answers import plain

    assert plain("**12 players** show *between* them") == "12 players show between them"
    assert plain("no emphasis here") == "no emphasis here"


def test_the_sweep_would_actually_catch_one():
    """⭐ *A guard that has never been shown to fail is a guard nobody has tested.*"""
    assert strings_in({"note": "**bold**"}) == [(".note", "**bold**")]
    assert any(mark in "**bold**" for mark in MARKDOWN)
