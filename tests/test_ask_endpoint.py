"""Ask, on the wire (ADR-302, on ADR-036/054).

⭐⭐⭐ **The routing is a year old and no phone could reach it.** `src/ask.py` matches a question to one of
fifteen intents, loads what that intent needs, and returns a decision, the facts behind it and a rendered
detail block. These pin what the *service* adds: the squad as ids, a silenced narrator, plain text on the
wire, and an unroutable question answering rather than failing.
"""

from __future__ import annotations

import pytest

from src.service import AskRequest, ask_question
from src.storage import Storage


@pytest.fixture(scope="module")
def squad():
    store = Storage()
    try:
        need = {"GK": 2, "DEF": 5, "MID": 5, "FWD": 3}
        picked, per_club = [], {}
        for p in sorted(store.get_players(), key=lambda r: -r["price"]):
            pos = p["position"]
            if need.get(pos) and per_club.get(p["team"], 0) < 3:
                picked.append(p["id"])
                need[pos] -= 1
                per_club[p["team"]] = per_club.get(p["team"], 0) + 1
        return picked
    finally:
        store.close()


def ask(question: str, squad, **kw) -> dict:
    return ask_question(
        AskRequest(question=question, player_ids=squad, bench_ids=squad[-4:], **kw)
    )


def test_a_squad_question_routes_and_answers(squad):
    out = ask("who should I captain?", squad)

    assert out["intent"] == "captain"
    assert out["headline"], "the captain engine answered with nothing"
    assert out["facts"], "a decision with no facts behind it cannot be checked"


def test_the_squad_arrives_as_ids_and_becomes_the_active_squad(squad):
    """⭐ The web resolves a **saved squad by name**; a phone has none — it has the fifteen FPL says you
    own. ⚠️ *A client that uploaded rows would be defining the engine's input.*"""
    out = ask("analyse my squad", squad)

    assert out["intent"], f"a squad-scoped question did not route: {out}"
    # ⭐ The engine prints the caller's chosen name verbatim, so it has to read as a phrase.
    assert "your squad" not in out["headline"], (
        f"the squad name reads as a duplication: {out['headline']!r}"
    )


def test_an_unroutable_question_answers_rather_than_fails(squad):
    """⚠️⚠️ *"I could not understand that" is a normal outcome of a free-text box*, not an error.

    ⭐⭐ **And the engine does better than admitting defeat**: an unrecognised question routes to `chat`,
    whose answer is a list of what it *can* be asked. ⚠️ *A free-text box that only ever says "I don't
    understand" teaches people to stop typing* — this one teaches them what to type instead.
    """
    out = ask("what is the airspeed velocity of an unladen swallow?", squad)

    assert out["intent"] == "chat"
    assert out["message"], "an unroutable question said nothing at all"
    assert "captaincy" in out["message"], "the fallback does not say what it can answer"
    # ⭐ A message and a headline are different answers, and the client shows one *instead* of the other.
    assert not out["headline"]


def test_nothing_on_the_wire_carries_markdown(squad):
    """⭐ *The API speaks text, not Streamlit* (ADR-274) — the phone prints asterisks literally."""
    for question in ["who should I captain?", "what should I do this week?", "how do chips work?"]:
        out = ask(question, squad)
        for field in ("headline", "detail", "message"):
            assert "**" not in out[field], f"{question} → {field} carries markdown"
            assert "__" not in out[field], f"{question} → {field} carries markdown"


def test_the_narrator_is_silenced_rather_than_left_to_time_out(squad):
    """⚠️⚠️ **`ask.answer` narrates through Ollama on localhost, and there is none on the server.**

    ⭐ *The prose was always the optional half* — `AskResult.explanation` is documented as *"the LLM prose,
    or None when the model is unavailable"*. Left at its default, every request would spend a connection
    timeout discovering that, on a phone, for a field this endpoint does not even return.
    """
    calls = []

    def narrator(*args, **kwargs):
        calls.append(args)
        return None

    ask_question(
        AskRequest(question="who should I captain?", player_ids=squad),
        narrator=narrator,
    )
    # The injection point exists and is used — so the default is a *choice*, not an oversight.
    assert calls, "the narrator was never consulted; the seam is gone"

    # And the shipped answer carries no prose field at all.
    assert "explanation" not in ask("who should I captain?", squad)


def test_the_money_reaches_the_plan(squad):
    """⚠️ *A plan that ignores what you can afford is a plan for somebody else.*

    ⭐ `ask.py` carries the reason in a comment at the call site: both were *"hard-coded here (1 and
    £0.0m) while the Transfer tab collected them three tabs away, so the surface a manager reads was
    advising a position he was not in."* This endpoint must not reintroduce that.

    ⚠️ Asserted on the **plan**, which is the intent that consumes them. The single-transfer intent
    (`_decide_transfer`) takes neither — a pre-existing gap in the engine, not something this endpoint
    introduced, and ⭐ *a test that pretended otherwise would be testing my hope rather than the code.*
    """
    poor = ask("what should I do this week?", squad, free=1, bank=0.0)
    rich = ask("what should I do this week?", squad, free=2, bank=8.0)

    assert poor["intent"] == rich["intent"] == "gameweek"
    assert poor != rich, "the bank and the free transfers changed nothing in the plan"


@pytest.mark.parametrize("question", ["", "   ", "\n"])
def test_an_empty_question_is_refused(question):
    with pytest.raises(ValueError):
        ask_question(AskRequest(question=question))


def test_an_enormous_question_is_refused():
    """⚠️ *An unbounded free-text field on a public endpoint is somebody else's CPU* — this string is
    routed and matched against squad names and gameweeks."""
    with pytest.raises(ValueError):
        ask_question(AskRequest(question="a" * 501))


def test_markdown_is_stripped_at_the_seam_whatever_the_engine_emits(squad, monkeypatch):
    """⚠️⚠️ **The sweep above cannot see this, and that is why it is here.**

    Asserting *"no asterisks in today's answers"* passes whether or not `plain()` is called, because the
    intents these questions reach happen not to emit any. ⭐ *A guard that only fires on data you already
    have is a guard against nothing* — the engine's notes were written for a page that renders markdown,
    and ADR-274 shipped precisely because one of them changed.

    So this feeds markdown **through** the service and checks what comes out the other side.
    """
    from src import ask as ask_engine

    loud = ask_engine.AskResult(
        question="q",
        intent="captain",
        headline="Captain **Saka** — xP 6.7",
        detail="Pick __him__ this week",
        message="I can answer about **captaincy**",
        facts={"player": "Saka (ARS)"},
    )
    monkeypatch.setattr(ask_engine, "answer", lambda *a, **k: loud)

    out = ask("who should I captain?", squad)

    assert out["headline"] == "Captain Saka — xP 6.7"
    assert out["detail"] == "Pick him this week"
    assert out["message"] == "I can answer about captaincy"
    # ⭐ And the facts are passed through untouched — they are values, not prose.
    assert out["facts"] == {"player": "Saka (ARS)"}


def test_a_stat_identifier_survives_the_stripper():
    """🔴 **The dangerous direction, pinned.**

    `plain()` removes markdown *emphasis*, and the obvious "completion" of it — also stripping single
    underscores — would quietly break the played-week card, which prints FPL's own stat identifiers as
    text: `defensive_contribution`, `goals_scored`, `clean_sheets` (ADR-299). ⚠️ *The rule is not "remove
    punctuation", it is "remove emphasis", and a lone underscore between two letters is neither.*
    """
    from src.service.answers import plain

    assert plain("defensive_contribution 11 → +2") == "defensive_contribution 11 → +2"
    assert plain("__bold__ and **bold** and *italic*") == "bold and bold and italic"
