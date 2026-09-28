"""Four chip questions, four answers (ADR-317 A/B/C).

⚠️⚠️⚠️ **The owner's report, in one line:** *"its not really credible if multiple questions give the same
answer."* Four questions routed to one intent and got one block — and two of them were not
chip-strategy questions at all: *"what's a chip?"* is a **rules** question, *"what chips have I played?"*
is a **fact**.

⭐ The shape ADR-308 gave captaincy, one intent along: **the qualifier is the question.**
"""

from __future__ import annotations

import pytest

from src.ask import chip_lens, route
from src.service import AskRequest, answers, ask_question
from src.storage import Storage

PLAYED = {"3xc": {"available": False, "played_in": 3},
          "bboost": {"available": True, "played_in": None},
          "freehit": {"available": True, "played_in": None},
          "wildcard": {"available": True, "played_in": None}}
UNKNOWN = {name: {"available": None, "played_in": None} for name in PLAYED}


@pytest.fixture
def ask(monkeypatch):
    """Ask, against the committed fixture, with a known chip history."""
    monkeypatch.setattr(answers.common, "_chip_status",
                        lambda manager_id, gameweek: PLAYED if manager_id else UNKNOWN)
    store = Storage()
    ids = [p["id"] for p in store.get_players()[:15]]

    def run(question: str, *, manager_id: int | None = 1013841, context=None):
        return ask_question(
            AskRequest(question=question, player_ids=ids, bench_ids=ids[-4:],
                       squad_name="TS", manager_id=manager_id, context=context),
            store=store,
        )

    yield run
    store.close()


# ── B · the qualifier reaches the right engine ───────────────────────────────

@pytest.mark.parametrize(
    ("question", "intent"),
    [
        ("whats a chip?", "rules"),
        ("whats a wildcard?", "rules"),
        ("whats the best chip strategy?", "chips"),
        ("what chips have i played?", "chips"),
        ("have i used my wildcard?", "chips"),
        ("can i still play my bench boost?", "chips"),
        ("build me a squad for a bench boost", "build_squad"),
    ],
)
def test_each_question_reaches_its_own_engine(question, intent):
    """⚠️⚠️ Two of these used to reach engines that **act** rather than explain: *"whats a wildcard?"*
    **built a squad**, *"have i used my wildcard?"* did too. ⭐ *A definition or a state question answered
    by a machine that does something is the most confidently wrong shape this router has.*"""
    assert route(question, [])[0] == intent


@pytest.mark.parametrize(
    ("question", "lens"),
    [
        ("whats the best chip strategy?", None),
        ("which chip should i use next?", None),
        ("what chips have i played?", "played"),
        ("have i used my wildcard?", "played"),
        ("can i still play my bench boost?", "holding"),
        ("whats the best way to use your chips before they expire?", "expiry"),
    ],
)
def test_the_lens_hears_the_qualifier(question, lens):
    assert chip_lens(question) == lens


# ── A · four questions, four answers ─────────────────────────────────────────

def test_the_owners_four_questions_no_longer_share_an_answer(ask):
    """⭐⭐ **The report, stated as a test.** ⚠️ Compared on the *answer*, not the heading — a heading that
    differs while the body repeats is the same failure wearing a label (ADR-308's own lesson)."""
    answers_given = {
        q: (ask(q).get("detail") or ask(q).get("message") or "")
        for q in ("whats the best way to use your chips before they expire?",
                  "whats the best chip strategy?",
                  "whats a chip?",
                  "what chips have i played?")
    }

    assert len(set(answers_given.values())) == 4, (
        "two of these still answer identically:\n  " + "\n  ".join(answers_given)
    )


def test_a_state_question_is_answered_with_state(ask):
    out = ask("what chips have i played?")

    assert "Triple Captain" in out["headline"] and "GW3" in out["headline"]
    assert "xP" not in out["headline"], "a fact answered with a projection"


def test_naming_a_chip_gets_a_yes_or_no(ask):
    """⭐ *A yes/no question answered with a paragraph has not been answered.*"""
    held = ask("can i still play my bench boost?")
    spent = ask("have i used my triple captain?")

    assert held["headline"].startswith("Yes")
    assert spent["headline"].startswith("No") and "GW3" in spent["headline"]


def test_expiry_names_the_deadline_and_what_is_left(ask):
    out = ask("whats the best way to use your chips before they expire?")

    assert "expire after GW" in out["headline"]
    assert "Triple Captain" not in out["headline"].split(":")[0], "a spent chip listed as expiring"


def test_without_a_manager_id_it_says_so_rather_than_guessing(ask):
    """⚠️⚠️⚠️ **The one place "I do not know" is the whole truth.** ⭐ *Inventing a chip list would be the
    worst failure this file could have* — and the answer still points at what it can do."""
    out = ask("what chips have i played?", manager_id=None)

    assert "cannot see" in (out.get("message") or "")
    assert "which chip should i use" in (out.get("message") or "").lower()


# ── C · follow-ups ───────────────────────────────────────────────────────────

def test_a_conversation_carries_between_questions(ask):
    """⭐⭐ `converse()` has carried *why* · *next* · *what about* since ADR-047, and the phone could reach
    none of them because `ask_question` called the one-shot entry point."""
    first = ask("who should i captain?")
    assert first["context"] and first["context"]["intent"] == "captain"

    nxt = ask("and the next?", context=first["context"])

    assert nxt["headline"] != first["headline"], "the follow-up repeated the first answer"
    assert "#2" in nxt["headline"]


def test_why_answers_from_the_reasons_not_from_prose(ask):
    """⚠️⚠️ **"Why?" used to return the identical answer.** It re-narrated the same decision with a deeper
    prompt — and on a deployment with no model, *which is every deployment*, that is the same block again.
    ⭐ The grounded reasons were already in `facts` (ADR-089); the prose was never where they lived."""
    first = ask("who should i captain?")

    why = ask("why?", context=first["context"])

    assert why["headline"].startswith("Why ")
    assert why["detail"] != first["detail"], "why returned the original answer"
    assert "For:" in why["detail"] and "Against:" in why["detail"]


def test_a_follow_up_with_no_context_is_nudged_not_guessed(ask):
    out = ask("why?")

    assert out.get("message"), "a follow-up to nothing invented something to follow"


def test_the_context_never_carries_the_decision(ask):
    """⚠️⚠️⚠️ **A client that could hand back a decision could hand back anything** — ⭐ *a server that
    trusts a decision it did not make has stopped being the thing that decides.* Five small fields travel;
    the decision is recomputed."""
    context = ask("who should i captain?")["context"]

    assert set(context) == {"intent", "squad", "question", "count", "rank"}
