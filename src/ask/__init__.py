"""Ask a question in English, get a grounded answer (ADR-325 split this from one 2,409-line module).

The layers, in the order a question moves through them — each one testable without the next:

    intents   the words -> an intent and its parameters (no store, no football)
    deciders  an intent -> a decision, by calling the analytics
    facts     a decision -> the numbers the answer is allowed to contain
    narrate   a decision -> prose, checked back against those facts
    context   what a follow-up needs to remember
    defaults  the two constants all of them share

This file keeps the conversation itself — `answer`, `converse`, `chat_transcript` — and re-exports the
public surface, so `from src.ask import route` means what it always did.

⭐ A barrel of pure-Python siblings is not the mistake ADR-323 found in `analytics/__init__`: that one put a
36 MB external solver on every import path. Nothing here imports anything the old single module did not.
"""
import re
from dataclasses import replace

from src import llm

# ⚠️ **As a module, so `_dispatch` has one patch point, not one per caller** (ADR-325).
from src.ask import deciders as _deciders

# ── the layers, and the public surface ─────────────────────────────────────────────────────────
# ⭐ Re-exported so `from src.ask import route` — and every name six other modules and the test suite
# already reach for — keeps meaning what it meant. ⚠️ The underscored ones were never really private: a
# name another file imports is part of the surface whether or not it wears an underscore.
from src.ask.context import (
    AskResult,
    Context,
    FollowUp,
    context_from_wire,
    context_to_wire,
    detect_followup,
)
from src.ask.deciders import (
    _captain_versus,
    _decide_analyse,
    _decide_captain,
    _decide_chips,
    _decide_compare,
    _decide_fixtures,
    _decide_gameweek,
    _decide_history,
    _decide_price,
    _decide_rules,
    _decide_shortlist,
    _decide_trends,
    _decide_worth,
    _dispatch,
    _known_squad_names,
    _lens_pick,
    _lineup_change,
    _load_squad,
    _price_a_rebuild,
    _squad_xp,
    _value_verdict,
)
from src.ask.defaults import (
    _HORIZON,
)
from src.ask.facts import (
    _analyse_facts,
    _captain_facts,
    _chips_facts,
    _gameweek_facts,
    _minutes_phrase,
    _plan_facts,
    _transfer_facts,
)
from src.ask.intents import (
    _INTENT_KEYWORDS,
    _POS_WORDS,
    _archetype_counts,
    _bench_mode,
    _fixture_horizon,
    _match_players,
    _match_team,
    _named_gameweek,
    _shortlist_query,
    _squad_budget,
    _squad_name,
    _transfer_count,
    captain_lens,
    chip_lens,
    route,
    scope_label,
)
from src.ask.narrate import (
    _FALLBACK,
    _INTENT_BLURB,
    _build_prompt,
    assemble,
    verify_grounding,
)
from src.storage import Storage

# Squad-scoped intents that default to the loaded squad when none is named (ADR-090); `analyse` is the router's
# fallback intent. Deliberately excludes fixtures/compare/worth/etc. so a *global* question isn't scoped.
_SQUAD_DEFAULT_INTENTS = frozenset({"captain", "transfer", "analyse", "start_bench", "gameweek", "chips"})

# An explicit "answer globally" cue — escapes the ADR-090 default (captaincy's global "best picks" mode).
_EXPLICIT_GLOBAL = re.compile(r"\b(all players|everyone|best overall|from all|any player)\b", re.IGNORECASE)

_NUDGE = (   # a follow-up ("why?", "and the next?") arrived before any question to build on (ADR-047)
    "Ask a question first, then follow up — e.g. \"who should I captain from <squad>?\", "
    'then "why?" or "and the second best?".'
)


def _needs_squad(intent: str, squad: str | None) -> AskResult | None:
    """The 'name a squad' prompt for the squad-scoped intents (or None if fine)."""
    if intent in ("transfer", "analyse", "start_bench", "gameweek", "chips") and not squad:
        verb = {"transfer": "what transfer", "analyse": "analyse",
                "start_bench": "who should I start", "gameweek": "what should I do this week",
                "chips": "which chip should I use"}[intent]
        return AskResult("", intent, message=f'Name a saved squad, e.g. ask "{verb} for <squad>?"')
    return None


_PRONOUNS = ("he", "him", "his", "she", "her", "they", "them", "their")
_PRONOUN_RE = re.compile(r"\b(" + "|".join(_PRONOUNS) + r")\b", re.IGNORECASE)


def _resolve_pronoun(question: str, context: "Context | None") -> str:
    """Rewrite a pronoun → the last turn's **sole** subject (ADR-080), so "is he worth it?" means the last
    player. Only when the antecedent is unambiguous (exactly one subject); a no-op otherwise. Substitutes
    the player's *name* for whatever pronoun the user typed (possessives → `name's`) — it never assigns a
    pronoun to anyone."""
    if context is None or not context.decision:
        return question
    subjects = context.decision.get("subjects") or []
    if len(subjects) != 1:
        return question
    antecedent = subjects[0]

    def _repl(m):
        return f"{antecedent}'s" if m.group(0).lower() in ("his", "their") else antecedent

    return _PRONOUN_RE.sub(_repl, question)


def _fresh(question: str, context: "Context | None", store: Storage, narrator, active_squad=None,
           horizon=_HORIZON, free: int = 1, bank: float = 0.0, chip_status=None):
    """A fresh (non-follow-up) question: route → decide → assemble. Returns (result, new_context).

    A successful answer becomes the new context; a fallback/soft-failure leaves the running
    context untouched (so a later "why?" still refers to the last *good* turn). `active_squad` is the
    session squad so "captain <its name>" / "analyse my team" use the loaded team (Sprint 066).
    `horizon` (ADR-077) is threaded to the gameweek intent for the AI Tips view.
    """
    question = _resolve_pronoun(question, context)          # "is he worth it?" → the last player (ADR-080)
    intent, squad = route(question, _known_squad_names(active_squad))
    # Default squad questions to the loaded session squad (ADR-090): when a squad is active and none was named
    # and the question isn't explicitly global, use it. This fixes "my-team" (hyphen) — no phrase-matching —
    # and makes a bare "who should I captain?" scope to your team; an explicit-global cue escapes to all players
    # (captaincy's global mode). Gated to the squad-scoped intents so a global fixtures/compare question isn't
    # scoped. The CLI has no active_squad, so it stays global-by-default.
    if not squad and intent in _SQUAD_DEFAULT_INTENTS and active_squad and active_squad.get("name") \
            and not _EXPLICIT_GLOBAL.search(question):
        squad = active_squad["name"]
    if intent is None:   # nothing grounded matched → the labelled free-form tail (ADR-085), or the help text
        return assemble(question, "chat", {"free_form": True, "question": question}, narrator), context
    prompt = _needs_squad(intent, squad)
    if prompt is not None:
        return replace(prompt, question=question), context

    count = _transfer_count(question)
    decision = _deciders._dispatch(intent, store, question, squad, count=count, active_squad=active_squad,
                         chip_status=chip_status,
                         horizon=horizon, free=free, bank=bank)
    known = [p["web_name"] for p in store.get_players()] if decision else ()
    result = assemble(question, intent, decision, narrator, known_names=known)
    new_context = context
    if decision and "facts" in decision:
        new_context = Context(intent=intent, squad=squad, question=question, count=count,
                              rank=0, decision=decision)
    return result, new_context


def _why_detail(decision: dict, subject: str) -> str:
    """The reasons behind a pick, from the facts the engine already computed (ADR-089).

    ⭐ *An explanation that only exists when a language model is attached is not an explanation, it is a
    flourish* — and every shipped surface runs without one.
    """
    facts = decision.get("facts") or {}
    lines = [f"Why {subject}", ""]
    for label, key in (("For", "why"), ("Against", "risk"), ("Confidence", "confidence")):
        value = facts.get(key)
        if not value:
            continue
        # ⭐ One reason per line: the engine joins them with "; " for a prompt, and a reader wants a list.
        parts = [p.strip() for p in str(value).split(";")] if key != "confidence" else [str(value)]
        lines.append(f"  {label}:")
        lines += [f"    · {p}" for p in parts if p]
        lines.append("")
    if len(lines) <= 2:
        # ⚠️ Nothing grounded to show — say so rather than printing a heading over an empty block.
        return f"I do not have a recorded reason for {subject} beyond the numbers above."
    return "\n".join(lines).rstrip()


def _apply_followup(fu: FollowUp, context: "Context", store: Storage, narrator, active_squad=None):
    """Resolve a follow-up against `context` → (result, new_context), or None if it can't apply
    here (e.g. 'what about defenders?' after a captain pick → let it fall through to a fresh Q)."""
    known = [p["web_name"] for p in store.get_players()]

    if fu.kind == "why":
        if not context.decision or "facts" not in context.decision:
            return None
        subject = (context.decision.get("subjects") or ["this pick"])[0]
        detailed = {**context.decision,
                    "task": f"explain in 3-4 short sentences, in more depth, why {subject} is the "
                            "pick here — using ONLY the facts",
                    # ⭐⭐⭐ **"Why?" has to say something new without a model, and it can** (ADR-317 C).
                    # ⚠️⚠️ It used to re-narrate the same decision with a deeper `task`, which on a
                    # deployment with no Ollama — *which is every deployment* (ADR-309) — produced the
                    # **identical answer**. The owner's complaint, arriving through a different door: *the
                    # same answer to a different question is indistinguishable from not having listened.*
                    #
                    # ⭐ The grounded reasons were already computed and sitting in `facts` (ADR-089):
                    # `why`, `risk` and `confidence`. The prose was never where the explanation lived.
                    "detail": _why_detail(context.decision, subject),
                    "headline": f"Why {subject}?"}
        return assemble(context.question, context.intent, detailed, narrator, known_names=known), context

    if fu.kind == "next":
        if context.intent not in ("captain", "transfer", "shortlist"):
            return None
        nrank = context.rank + 1
        decision = _deciders._dispatch(context.intent, store, context.question, context.squad,
                             count=context.count, rank=nrank, active_squad=active_squad)
        if not decision or "facts" not in decision:       # past the end → show the soft message,
            msg = (decision or {}).get("message", "That's all I have.")   # keep the current rank
            return AskResult(context.question, context.intent, message=msg), context
        result = assemble(context.question, context.intent, decision, narrator, known_names=known)
        return result, replace(context, rank=nrank, decision=decision)

    if fu.kind == "whatabout":                            # shortlist-only (ADR-047)
        if context.intent != "shortlist":
            return None
        new_q = _swap_position(context.question, fu.position)
        decision = _deciders._dispatch("shortlist", store, new_q, None)
        result = assemble(new_q, "shortlist", decision, narrator, known_names=known)
        keep = decision if (decision and "facts" in decision) else context.decision
        return result, replace(context, question=new_q, rank=0, decision=keep)

    return None


def _swap_position(question: str, new_code: str) -> str:
    """Rewrite a shortlist question to a new position, keeping the rest (price cap, value)."""
    new_word = next(word for word, code in _POS_WORDS.items() if code == new_code)
    for word in _POS_WORDS:                               # replace an existing position word…
        rewritten, n = re.subn(rf"\b{word}s?\b", new_word, question, flags=re.IGNORECASE)
        if n:
            return rewritten
    return f"{question} {new_word}"                       # …or, if none, name the position


def converse(question: str, context: "Context | None", *, store: Storage,
             narrator=llm.narrate, active_squad=None, horizon=_HORIZON, free: int = 1,
             bank: float = 0.0, chip_status=None) -> tuple[AskResult, "Context | None"]:
    """One conversational turn (ADR-047): a follow-up on `context`, else a fresh question.

    Returns ``(result, new_context)``. `context` is None at the start of a chat; a follow-up with
    no context yet returns a gentle nudge. The one-shot `answer` is `converse` with no context.
    `active_squad` (the session squad) lets squad-scoped intents see the loaded team (Sprint 066).
    """
    fu = detect_followup(question)
    if fu is not None:
        if context is None:
            return AskResult(question, None, message=_NUDGE), None
        applied = _apply_followup(fu, context, store, narrator, active_squad)
        if applied is not None:
            return applied
        # a detected follow-up that doesn't apply here → treat the line as a fresh question.
    return _fresh(question, context, store, narrator, active_squad, horizon=horizon,
                  free=free, bank=bank, chip_status=chip_status)


def answer(question: str, *, store: Storage | None = None, narrator=llm.narrate,
           active_squad=None, horizon=_HORIZON, free: int = 1, bank: float = 0.0, chip_status=None) -> AskResult:
    """Route → analytics decide → narrate (or degrade). The narrator is injectable/optional.

    The one-shot entry point: a single `converse` turn with no prior context (so a follow-up-only
    line falls through to the normal fallback, exactly as before). `active_squad` (the session
    squad, ADR-054/055) lets squad-scoped questions use the loaded team, not only saved squads.
    `horizon` (ADR-077) sets the gameweek-plan window for the AI Tips view; defaults to `_HORIZON` (5)
    so the CLI / Ask tab are unchanged.
    """
    own_store = store is None
    store = store or Storage()
    try:
        result, _context = _fresh(question, None, store, narrator, active_squad, horizon=horizon,
                                  chip_status=chip_status,
                                  free=free, bank=bank)
        return result
    finally:
        if own_store:
            store.close()


_EXIT_WORDS = {"quit", "exit", "q", "bye", "done"}
_RESET_WORDS = {"forget", "reset", "start over", "new chat", "forget it"}


def is_reset(text: str) -> bool:
    """True when a line asks to forget the conversation (ADR-091) — so `ask`/`chat` can clear the context."""
    return (text or "").strip().lower() in _RESET_WORDS


def chat_transcript(lines, *, store: Storage, narrator=llm.narrate, active_squad=None, context=None):
    """Thread a `Context` across `lines`, yielding `(AskResult, context)` per answered line (ADR-047).

    The pure heart of the `chat` REPL: blank lines are skipped, an exit word stops the session, a
    reset word ("forget") drops the context, and every other line is a conversational turn whose
    context carries to the next. `context` seeds the thread so a **saved** context resumes a chat
    (ADR-091). Kept free of I/O (input/print) so it's unit-tested with a list of lines; the caller
    persists the yielded context.
    """
    for line in lines:
        text = line.strip()
        if text.lower() in _EXIT_WORDS:
            return
        if not text:
            continue
        if is_reset(text):
            context = None
            yield AskResult(text, None, message="Okay — I've forgotten the last turn. Ask me anything."), None
            continue
        result, context = converse(text, context, store=store, narrator=narrator,
                                   active_squad=active_squad)
        yield result, context

__all__ = [
    "AskResult", "Context", "FollowUp", "_FALLBACK",
    "_HORIZON", "_INTENT_BLURB", "_INTENT_KEYWORDS", "_analyse_facts",
    "_archetype_counts", "_bench_mode", "_build_prompt", "_captain_facts",
    "_captain_versus", "_chips_facts", "_decide_analyse", "_decide_captain",
    "_decide_chips", "_decide_compare", "_decide_fixtures", "_decide_gameweek",
    "_decide_history", "_decide_price", "_decide_rules", "_decide_shortlist",
    "_decide_trends", "_decide_worth", "_dispatch", "_fixture_horizon",
    "_gameweek_facts", "_known_squad_names", "_lens_pick", "_lineup_change",
    "_load_squad", "_match_players", "_match_team", "_minutes_phrase",
    "_named_gameweek", "_plan_facts", "_price_a_rebuild", "_shortlist_query",
    "_squad_budget", "_squad_name", "_squad_xp", "_transfer_count",
    "_transfer_facts", "_value_verdict", "answer", "assemble",
    "captain_lens", "chat_transcript", "chip_lens", "context_from_wire",
    "context_to_wire", "converse", "detect_followup", "is_reset",
    "route", "scope_label", "verify_grounding",
]
