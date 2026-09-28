"""What a conversation remembers between turns.

`Context` is what travels on the wire, `FollowUp` is what a short question turns into, and `AskResult` is
what every entry point returns. ⚠️ `context_from_wire` re-dispatches on rehydration — only *"why"* needs the
previous decision, so the rest is recomputed rather than trusted from a client.
"""

import re
from dataclasses import dataclass, replace

from src.ask import deciders as _deciders
from src.ask.defaults import _HORIZON
from src.ask.intents import _POS_WORDS
from src.storage import Storage


@dataclass
class AskResult:
    question: str
    intent: str | None
    headline: str | None = None      # the analytics decision, one line
    facts: dict | None = None        # the pre-humanised facts
    explanation: str | None = None   # the LLM prose, or None when the model is unavailable
    message: str | None = None       # for an unrecognised question or an empty result
    detail: str | None = None        # a pre-rendered structured table (e.g. a plan; ADR-036)
    trust: dict | None = None        # verify_grounding result when there's narration (ADR-037)
    squad: dict | None = None        # a built squad (SquadStore shape) an edge can adopt (ADR-062)
    plan: dict | None = None         # the gameweek plan an edge can ACT on (ADR-070/174) — same object the


# ---- conversational follow-ups (ADR-047) ------------------------------------
# A follow-up builds on the last turn. Detection is deterministic (the LLM never decides it) and
# fires only on short, *subject-less* lines: every non-position word must be filler, so "why?" is a
# follow-up but "why is Haaland good?" (carries a subject) stays a fresh question.

_WHY_WORDS = {"why", "not", "explain", "how", "come", "reason", "because", "that", "this", "again",
              "so", "is", "it", "the", "one", "them", "him", "her", "though", "really", "then"}
_WHY_HINTS = ("why", "explain", "reason", "because", "come")
_NEXT_WORDS = {"next", "second", "third", "2nd", "3rd", "who", "else", "another", "someone", "best",
               "the", "one", "and", "option", "pick", "give", "me", "show", "other", "some", "are",
               "there", "any"}
_NEXT_HINTS = ("next", "second", "third", "2nd", "3rd", "else", "another")
_WHATABOUT_WORDS = {"what", "about", "how", "and", "the", "a", "instead", "of", "some"}


@dataclass
class FollowUp:
    kind: str                       # "why" | "next" | "whatabout"
    position: str | None = None     # for "whatabout": the new position code (GK/DEF/MID/FWD)


@dataclass
class Context:
    """The last successful turn, so a follow-up can build on it (ADR-047)."""
    intent: str
    squad: str | None = None
    question: str = ""              # the (possibly rewritten) question that produced this turn
    count: int = 1                  # transfer count
    rank: int = 0                   # how many "next" steps in — the current pick / shortlist page
    decision: dict | None = None    # the decision itself, so "why" can re-narrate its facts


#: The parts of a `Context` that travel back to a stateless client (ADR-317 C).
#:
#: ⚠️⚠️⚠️ **`decision` is deliberately NOT among them.** It is the engine's own output, and a client that
#: could hand it back could hand back anything — ⭐ *a server that trusts a decision it did not make has
#: stopped being the thing that decides.* The decision is **recomputed** from these five fields instead,
#: which costs one dispatch and buys the guarantee.
CONTEXT_WIRE = ("intent", "squad", "question", "count", "rank")


def context_to_wire(context: "Context | None") -> dict | None:
    """A `Context` reduced to what a client may hold between turns."""
    if context is None or not context.intent:
        return None
    return {field: getattr(context, field) for field in CONTEXT_WIRE}


def context_from_wire(payload, store: Storage, *, active_squad=None, horizon=_HORIZON,
                      free: int = 1, bank: float = 0.0, chip_status=None) -> "Context | None":
    """Rebuild the last turn from what the client sent back, **re-deciding** rather than trusting it.

    ⭐ Only *"why"* needs the decision at all — *"and the next?"* and *"what about defenders?"* re-dispatch
    anyway — so the cost is one engine call on a follow-up, and never on a fresh question.

    ⚠️ Returns None on anything malformed. *A follow-up that cannot be rebuilt is a fresh question*, which
    is the same thing that happens at the start of a chat and needs no special case.
    """
    if not isinstance(payload, dict) or not payload.get("intent"):
        return None
    try:
        context = Context(
            intent=str(payload["intent"]),
            squad=payload.get("squad") or None,
            question=str(payload.get("question") or ""),
            count=int(payload.get("count") or 1),
            rank=int(payload.get("rank") or 0),
        )
        decision = _deciders._dispatch(context.intent, store, context.question, context.squad,
                             count=context.count, rank=context.rank, active_squad=active_squad,
                             horizon=horizon, free=free, bank=bank, chip_status=chip_status)
    except (KeyError, TypeError, ValueError):
        return None
    return replace(context, decision=decision)


def detect_followup(question: str) -> FollowUp | None:
    """A follow-up (why / next / what-about), or None for a fresh question — by trigger only.

    A line only counts as a follow-up when it is *subject-less*: apart from a position word (for
    what-about), every token must be filler for that family. So "why?" / "and the second best?" /
    "what about defenders?" match, but "why is Haaland good?" or "best defenders" do not.
    """
    toks = set(re.findall(r"[a-z0-9]+", question.lower()))
    if not toks:
        return None
    # what about <position>: a position word (singular or plural), "about", and only filler else
    pos = next((code for word, code in _POS_WORDS.items()
                if word in toks or f"{word}s" in toks), None)
    pos_forms = {form for word in _POS_WORDS for form in (word, f"{word}s")}
    if pos and "about" in toks and (toks - pos_forms) <= _WHATABOUT_WORDS:
        return FollowUp("whatabout", position=pos)
    if toks <= _NEXT_WORDS and any(h in toks for h in _NEXT_HINTS):
        return FollowUp("next")
    if toks <= _WHY_WORDS and any(h in toks for h in _WHY_HINTS):
        return FollowUp("why")
    return None
