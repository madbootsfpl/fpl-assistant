# ADR-302 — Ask reaches the phone

**Date:** 2026-09-26
**Status:** ✅ **Built.**
**From:** the owner — *"build ask"*, closing the gap ADR-301 named as the only genuine capability the app
lacked.

---

## What was already there

⭐⭐⭐ **`src/ask.py` has routed questions since Sprint 036.** Fifteen intents; a question is matched, the
intent loads what it needs, and back come a decision, the **facts** behind it and a rendered **detail**
block. ⚠️ It was reachable from the CLI and from Streamlit, and from no phone.

## What the service adds, and why each part

⭐ **The squad travels as ids and becomes the `active_squad`** (ADR-054/055). The web resolves a *saved
squad by name*; a phone has none — it has the fifteen FPL says you own. ⚠️ *A client that uploaded rows
would be defining the engine's input*, which is the rule every endpoint here already follows.

⭐⭐ **The bank and the free transfers go with it**, and `ask.py` records why at its own call site: both
were *"hard-coded here (1 and £0.0m) while the Transfer tab collected them three tabs away, so the surface
a manager reads was advising a position he was not in."* ⚠️ *A plan that ignores what you can afford is a
plan for somebody else.*

⚠️⚠️ **No narrator, deliberately.** `ask.answer` defaults to `llm.narrate`, which talks to **Ollama on
localhost**; there is none on the server, so every request would spend its connection timeout discovering
that. ⭐ *The prose was always the optional half* — `AskResult.explanation` is documented as *"the LLM
prose, or None when the model is unavailable"*, and the decision and its facts are computed by the
analytics either way. The seam is kept and tested, so the default is a **choice** rather than an oversight.

## Three things found on the way

⚠️⚠️⚠️ **`plain()` promised markdown emphasis and stripped only asterisks.** Found by feeding markdown
**through** the service rather than looking for some in today's answers — ⭐ *a guard that only fires on
data you already have is a guard against nothing.*

🔴 **And the obvious completion of it would be a bug.** A single `_` is deliberately left alone: FPL's stat
identifiers reach the screen as text — `defensive_contribution`, `goals_scored` — and the played-week card
prints them (ADR-299). Stripping single underscores renders that line *"defensivecontribution"*. ⚠️ *The
rule is not "remove punctuation", it is "remove emphasis", and a lone underscore between two letters is
neither.* Pinned by a test that fails in the dangerous direction.

⚠️⚠️ **A fast failure crashed the app.** `FutureBuilder` subscribes on the **next frame**; an immediate
500 — or being offline — rejects before then, and Dart reports a rejection nobody was listening to as an
**unhandled error**. The screen renders the message correctly and the app still dies. ⭐ *A network error
is normally slow enough to hide this, which is exactly why it would have shipped* — a mock returning 500
in microseconds is what surfaced it.

⭐⭐ **An unrecognised question does better than admitting defeat.** It routes to `chat`, whose whole answer
is a list of what it *can* be asked. ⚠️ *A free-text box that only ever says "I don't understand" teaches
people to stop typing* — this one teaches them what to type instead, so the client shows that message
**instead of** a headline, never beside one.

## Where it lives

⭐ **First in More.** Every other row there is a named screen you go to on purpose; this is where you go
when you do not know which screen you want — ⚠️ *and that is the commonest state a manager is in on a
Friday night.* The owner's chosen order (ADR-284) is otherwise untouched: game things, then app things.

⚠️ **No chat history, no thread, no "typing…".** One question, one answer, replaced by the next. ⭐ *A
conversation implies the thing remembers, and this does not*: every question is routed from scratch, which
is precisely what `ask.answer` is.

## Tests

13 service, 9 widget — mutation-tested **12/12** and **8/8**, after the fixture gaps they exposed. ⚠️ The
sharpest was the money: the committed sample has **1 free transfer and no bank**, which are exactly the
values a hard-coding would use, so a mutation replacing `team.freeTransfers` with `1` survived everything
until the fixture was given different numbers. ⭐ *A fixture whose values match the bug cannot see it.*

## What this leaves

📌 Streamlit now holds **one** product feature the app lacks: the **browsable Headlines list** (ADR-093,
and ADR-300's withdrawn objection). Everything else it owns is the owner's — Admin — or content — Help and
the videos.
