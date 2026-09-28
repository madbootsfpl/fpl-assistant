"""Decision in, words out — and the check that the words are true.

⭐⭐ `verify_grounding` is the point of this module: the model writes the prose, and then its numbers and
names are checked against the facts the engine produced. ⚠️ *A narrator that can introduce a number is a
narrator that can invent one.*
"""

import json
import re

from src.ask.context import (
    AskResult,
)

_RULES = (
    "Rules: do NOT rank or compare players, do NOT compute or invent any number, do NOT expand "
    "or rename teams (use the codes exactly as written), do NOT merge separate facts, and do NOT "
    "mention anything that is not in the facts. "
    # ADR-168 §🔬 — the caveat rule. Measured on four answers: the narration walked every ✓ Edge bullet and
    # silently dropped the ⚠ Risk ones, most damagingly on `transfer`, where it reframed "selling Hume
    # (13.9 xP)" as "selling Hume frees £0.5m" — a risk rendered as a benefit — and never mentioned the
    # 4%-owned warning at all. The facts always contained them; the prompt never asked for them.
    #
    # It is stated as an obligation with a fixed form because "mention the risk" was evidently not enough:
    # both models had the risk and both were inconsistent about using it.
    "If the facts contain a 'risk' entry, you MUST state it in the last sentence, beginning with "
    "'The risk is' — as a risk, never reworded into a benefit. If 'risk' is absent or 'none noted', "
    "add nothing."
)

# What each intent answers, in plain words — the single source of the "I can answer about…" message.
#
# **Derived, not hand-written** (2026-08-30). The old message was prose maintained by hand, and it had drifted
# to advertise **8 of 15** intents: `chips`, `gameweek`, `price`, `rules`, `trends`, `history` and `fixtures`
# were all reachable and none was mentioned. The owner asked *"what's th best strategy for GW3?"*, got the
# fallback, and the two intents that would have answered — `gameweek` ("what should I do in GW3?") and
# `chips` — were precisely the ones it omitted. A capability list that under-sells the product is the same
# failure as one that over-sells it (ADR-168): the sentence stopped describing the code and nobody could see.
#
# `test_ask.py` pins every intent to a blurb in both directions, so a new intent cannot ship undescribed and
# a deleted one cannot linger in the copy.
_INTENT_BLURB = {
    "captain": "captaincy",
    "transfer": "transfers",
    "gameweek": "a plan for the week",
    "chips": "chip timing (wildcard, bench boost, triple captain, free hit)",
    "analyse": "your squad's health",
    "start_bench": "your lineup",
    "build_squad": "building a squad",
    "shortlist": "the best players in a position (incl. differentials)",
    "worth": "whether a player is worth the money",
    "compare": "comparing players",
    "fixtures": "fixtures and difficulty",
    "trends": "what the crowd is doing (most owned, most transferred, in form)",
    "price": "price changes",
    "history": "a player's past seasons",
    "rules": "the FPL rules and scoring",
}


def _capabilities() -> str:
    """The blurbs as one bullet per line.

    A list, not a sentence: fifteen comma-separated clauses is a wall nobody reads to the end of, and this
    text renders in **monospace** everywhere it appears (`st.code` on the web, plain stdout in the CLI), so a
    bullet per line is both scannable and safe — markdown would render literally.
    """
    return "\n".join(f"  \u2022 {blurb}" for blurb in _INTENT_BLURB.values())


_FALLBACK = (
    "I can answer about:\n"
    f"{_capabilities()}\n\n"
    # One example per *shape* of question: squad-scoped, whole-gameweek, single-player. The middle one is the
    # question that exposed the drift, so the next person who asks it finds the door rather than this message.
    'Try: ask "who should I captain from <squad>?", ask "what should I do in GW3?", '
    'or ask "is Haaland worth the money?".'
)


def _numbers(text: str) -> set:
    """Number-like tokens in `text` (e.g. '7.4', '22')."""
    return set(re.findall(r"\d+(?:\.\d+)?", text))


def _significant_tokens(text: str) -> set:
    """Lower-cased whole words of ≥4 letters — distinctive enough to match a player by.

    Whole-word (not substring) so 'ward' never matches 'forward'; ≥4 letters so short
    surnames ('Son', 'Sá') don't collide with common words. Keeps the name check quiet.
    """
    return {t.lower() for t in re.findall(r"[A-Za-z]{4,}", text)}


def verify_grounding(text: str, facts: dict, *, known_names=(), subjects=()) -> dict:
    """Flag numbers and player names in a narration not backed by the facts (ADR-037).

    - **numbers:** every number in `text` should appear in `facts`; the rest are unverified.
    - **names:** a **known** FPL player (from `known_names`) named in `text` who isn't a
      `subject` of this answer is flagged. Conservative (≥4-letter whole-word tokens) to avoid
      crying wolf. Returns ``{"numbers": [...], "names": [...]}`` — empty means it checks out.
    """
    if not text:
        return {"numbers": [], "names": []}

    # ensure_ascii=False so a '£' stays '£' — otherwise its £ escape injects stray digits
    # (00, 3) that corrupt the number set and wrongly flag a grounded figure (e.g. £100.0m).
    facts_numbers = _numbers(json.dumps(facts, ensure_ascii=False))
    unverified_numbers = sorted(n for n in _numbers(text) if n not in facts_numbers)

    words = _significant_tokens(text)
    subject_tokens = set().union(*(_significant_tokens(s) for s in subjects)) if subjects else set()
    unverified_names = sorted({
        name for name in known_names
        if (toks := _significant_tokens(name))          # a matchable (≥4-letter) name
        and toks <= words                               # all its tokens appear in the text
        and not (toks & subject_tokens)                 # …and it isn't a subject of the answer
    })

    return {"numbers": unverified_numbers, "names": unverified_names}


def _build_prompt(decision: dict) -> str:
    return (
        f"You are an FPL assistant. The analytics have ALREADY made the decision. Your job: "
        f"{decision['task']}, using ONLY the facts below.\n{_RULES}\n"
        "Write only the explanation itself — no preamble, and do not restate the task.\n\n"
        f"FACTS:\n{json.dumps(decision['facts'], indent=2, ensure_ascii=False)}"
    )


def _free_form_prompt(question: str) -> str:
    """A scoped prompt for the free-form tail (ADR-085): general FPL rules/tactics only, and **never** a
    specific player/pick recommendation (those come from the grounded tools + are verified)."""
    return (
        "You are a helpful Fantasy Premier League assistant. Answer this general FPL question in 2-4 short "
        "sentences with rules or tactical guidance only. Do NOT recommend specific players, prices, or picks "
        "— those come from the app's data tools. If it isn't about FPL, say you only help with FPL.\n\n"
        f"QUESTION: {question}"
    )


def assemble(question: str, intent: str | None, decision: dict | None, narrator,
             known_names=()) -> AskResult:
    """Turn a decision into an AskResult — narrating, verifying, and degrading if needed.

    Pure given `decision` + `narrator` (so it's unit-tested without a live model): a narrator
    returning None (Ollama absent) yields a result with the decision + facts but no prose. When
    there IS narration, it's verified against the facts (ADR-037) and the result carried in `trust`.
    """
    if intent is None:
        return AskResult(question, None, message=_FALLBACK)
    if decision is None:
        return AskResult(question, intent,
                         message="No result — run `refresh`, and check the squad name.")
    if decision.get("message"):   # a soft, specific failure (e.g. compare: not found / ambiguous)
        return AskResult(question, intent, message=decision["message"])
    if decision.get("free_form"):   # a general FPL question — ungrounded, clearly labelled (ADR-085)
        prose = narrator(_free_form_prompt(decision.get("question", question)))
        if not prose:                                  # no model → the honest help message
            return AskResult(question, intent, message=_FALLBACK)
        return AskResult(question, intent, explanation=prose, trust={"free_form": True})
    explanation = narrator(_build_prompt(decision))   # str, or None if unavailable
    trust = None
    if explanation:
        trust = verify_grounding(
            explanation, decision["facts"],
            known_names=known_names, subjects=decision.get("subjects", ()),
        )
    return AskResult(
        question, intent, headline=decision.get("headline"), facts=decision["facts"],
        explanation=explanation, detail=decision.get("detail"), trust=trust,
        squad=decision.get("squad"),   # a build answer carries the 15 an edge can adopt (ADR-062)
        plan=decision.get("plan"),     # a gameweek answer carries the plan an edge can act on (ADR-174)
    )
