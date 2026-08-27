"""Reading events out of headlines — the model proposes, this module decides (ADR-151).

The Watkins → Al-Hilal story was sitting in a feed the app already fetched, reduced to *"Watkins: 13
mentions"*. That is the story behind ADR-146's *"96,095 sold him and nothing in the data explains it"*, and
recovering it turns an unexplained flag into a sourced one.

**Why a model at all**, in a project that prefers simple solutions: spike 206 measured a deliberately narrow
rule-based extractor at **58% precision** (7 of 12), failing in exactly the ways rules fail — two negations
(*"Palmer in training — not injured"* read as an injury), a wrong player, and one that matched **Enzo
Maresca, a manager**. A local 8B model, zero-shot, fixed four of the five and **failed silent every time**.

**Why that does not break "analytics decide, the LLM narrates" (ADR-034/037).** The model never decides
anything here. It returns a *candidate*, and this module keeps it only when

* the `kind` is one of a **closed set**, and
* the name resolves to **exactly one** player in our own data (ADR-152).

Anything else is dropped. That is the same shape as `verify_grounding`: the model may suggest, the app must
verify. A model that starts hallucinating produces *fewer* events, never wrong ones.

**Precision over recall, deliberately.** ~10% of headlines carry a resolvable event and that is fine — this is
not a news reader, it exists to explain a flag we already show. A missed story costs nothing; a story pinned
to the wrong player costs the credibility of every flag on the page.
"""

import json
import re
import time

from src.analytics.names import build_index, find_mentions

KINDS = ("transfer", "injury", "return")      # a closed set — anything else is not an event we understand

# Vocabulary that must be present for a claimed kind to stand (ADR-151 rev). The model proposes; these can
# **veto**.
#
# Found by measurement: `qwen3:8b` scored 16/16 on the corpus, but the configured default `llama3.2` (3B)
# labelled *"Barry scores a hat-trick in the League Cup"*, *"Cole Palmer is Player of the Matchweek"* and
# *"Brentford attack is on fire!"* all as **transfers**. Resolution could not catch those — the names are
# real, only the *kind* was invented — so verification had a hole exactly where a smaller model fails.
#
# Rules alone were 58% precise (spike 206) and a model alone is only as good as the model. A model proposing
# and a rule vetoing is stronger than either: the rule cannot invent an event, and the model cannot claim one
# the text does not support.
_KIND_CUES = {
    # NB: a bare "£"/"€" is deliberately NOT a transfer cue. It was, and a live run produced
    # *"£4.0m defender boost, Sangare assist + Ampadu DefCons: FPL notes"* as a transfer — because **FPL
    # prices are in pounds too**. A fee needs a verb; the money alone means nothing. Removing it cost none of
    # the seven correct events in that run (each carries "sign", "joins", "agreed" or "closing in").
    "transfer": ("sign", "signs", "signed", "joins", "join ", "deal", "agree", "agreed", "here we go",
                 "medical", "loan", "bid", "move to", "transfer", "closing in", "swoop",
                 "verbal agreement", "turn attention"),
    "injury": ("injur", "out for", "ruled out", "sidelined", "hamstring", "knee", "ankle", "groin", "acl",
               "surgery", "knock", "doubt", "not available", "unavailable", "absence", "strain", "concussion"),
    "return": ("return", "back in training", "fit again", "available again", "back from", "recovered"),
}


def supports_kind(title: str, kind: str) -> bool:
    """Does the headline actually contain vocabulary for the event the model claims?

    A veto, not a detector. Rules were never good enough to *find* events (58% precision), but they are
    perfectly good at noticing that a sentence about a hat-trick contains no transfer language at all.
    """
    low = str(title or "").lower()
    return any(cue in low for cue in _KIND_CUES.get(kind, ()))

PROMPT = (
    'Extract football transfer/availability events from a headline.\n'
    'Return ONLY JSON: {"events":[{"player":"<name exactly as written>","kind":"transfer|injury|return|none"}]}\n'
    "Rules:\n"
    '- kind "none" when the headline reports no event about a player.\n'
    '- A negated statement ("not injured", "no injury") is NOT an injury.\n'
    "- Name PLAYERS only. Never a manager, club official, journalist or pundit.\n"
    "- List each player separately.\n"
    "Headline: "
)

_SOURCES = ("romano", "ornstein", "sky sports", "the athletic", "bbc", "guardian", "telegraph", "fabrizio")

# Headlines about **the game**, not about football. FPL's own vocabulary collides with the real thing:
# *"[FPL] Bruno Fernandes and Bryan Mbeumo have been transferred out over 277,000 times"* is a fact about
# managers clicking a button, and the model — reasonably — read "transferred out" as a transfer. It was the
# only false positive in an 18-event run over the live corpus, and it produced two of them.
#
# Cheap to exclude and safe to: a genuine club transfer is never phrased in gameweeks, price changes or
# ownership percentages.
_FPL_META = ("transferred out", "transferred in", "price change", "price rise", "price fall",
             "ownership", "captaincy", "differential", "gameweek", "wildcard", "bench boost",
             "triple captain", "free hit", "mini-league", "rate my team",
             # from a live run: an FPL listicle that named three players and reported no football event
             "fpl notes", "defcon")


def is_about_the_game(title: str) -> bool:
    """True when a headline is FPL-meta — about managers, not about footballers."""
    low = str(title or "").lower()
    return low.startswith("[fpl]") or any(cue in low for cue in _FPL_META)


def _source(title: str) -> str | None:
    """The reporting outlet named in the headline, if any — what makes the claim checkable rather than a rumour."""
    low = title.lower()
    return next((s.title() for s in _SOURCES if s in low), None)


def parse_response(raw: str) -> list[dict]:
    """The model's reply → `[{player, kind}]`. A malformed reply yields `[]`, never an exception.

    Models wrap JSON in prose, fences and thinking. Rather than trust the shape, take the outermost braces and
    parse; if that fails, this headline simply produces nothing.
    """
    if not raw:
        return []
    try:
        blob = raw[raw.index("{"):raw.rindex("}") + 1]
        events = json.loads(blob).get("events")
    except (ValueError, AttributeError, json.JSONDecodeError):
        return []
    if not isinstance(events, list):
        return []
    out = []
    for e in events:
        if isinstance(e, dict) and e.get("player") and e.get("kind") in KINDS:
            out.append({"player": str(e["player"]), "kind": e["kind"]})
    return out


def resolve(candidate: dict, title: str, index) -> dict | None:
    """One model candidate → a stored event, or `None` when the name does not resolve to exactly one player.

    The resolver (ADR-152) is longest-match-first and refuses to guess between players sharing a surname, so
    "Ollie Watkins" lands on Watkins, "Enzo Maresca" lands on nobody, and an ambiguous "Kamara" is dropped.
    Requiring **exactly one** match is what makes a hallucinated name harmless: it resolves to zero.
    """
    if not supports_kind(title, candidate["kind"]):
        return None                       # the model claimed an event the words do not support
    hits = find_mentions(candidate["player"], index)
    if len(hits) != 1:
        return None
    (element_id, _n), = hits.items()
    return {"element_id": element_id, "title": title, "kind": candidate["kind"], "source": _source(title)}


def extract(titles, players, ask, *, seen_at=None, budget_seconds: float = 180.0, clock=None) -> list[dict]:
    """Resolved events for a batch of headlines. `ask(prompt) -> str` is the model call, injected.

    Injected rather than imported so this stays pure and testable offline — and so the caller decides *which*
    model, or none at all. A model that errors on one headline costs that headline, not the batch.

    **`budget_seconds` is not a nicety.** This runs inside `refresh`, whose job is the player data; a model
    that has gone slow, or a per-call timeout of 60s across 112 headlines, could hold that hostage for close
    to two hours. Found the hard way: an unbudgeted run had to be killed at ten minutes. The budget stops
    cleanly and keeps whatever it already resolved — a partial read is worth having, a hung refresh is not.
    """
    index = build_index(players)
    now = clock or time.monotonic
    started = now()
    seen, out = set(), []
    for title in titles or []:
        if now() - started > budget_seconds:
            break
        text = str(title or "").strip()
        if not text or is_about_the_game(text):
            continue
        try:
            raw = ask(PROMPT + text)
        except Exception:                                # noqa: BLE001 — one bad call must not lose the batch
            continue
        for candidate in parse_response(raw):
            event = resolve(candidate, text, index)
            if event is None:
                continue
            key = (event["element_id"], event["title"])
            if key in seen:                              # the same story from two feeds
                continue
            seen.add(key)
            out.append({**event, "seen_at": seen_at})
    return out


def event_phrase(event) -> str:
    """A short, checkable clause for a stored event — the sentence ADR-146's flag was missing.

    Names the outlet when the headline does, because *"Romano reports"* is a different claim from *"someone on
    Reddit said"*, and the reader is entitled to tell them apart.
    """
    kind = {"transfer": "a move", "injury": "an injury", "return": "a return"}.get(event["kind"], "news")
    who = f"{event['source']} reports " if event.get("source") else "reported: "
    title = re.sub(r"\s+", " ", str(event.get("title") or "")).strip()
    return f"{who}{kind} — “{title[:150]}”"


def reported_leaving(events, exodus, *, today=None) -> dict | None:
    """The event proving a player is on his way **out of the league**, or `None` (ADR-153).

    Requires **two independent signals to agree**: a transfer headline *and* a heavy sell-off our own data
    cannot explain (ADR-146). Neither alone is enough, and the measurement says why.

    On the live seed, five transfer headlines resolved. Only **one** also carried an exodus:

    | player | headline | exodus |
    |---|---|---|
    | **Watkins** → Al-Hilal | ✓ | **−167,825** |
    | Pinnock → Coventry · Disasi → Palace · Baleba → Man Utd · Hadjam → Brighton | ✓ | none |

    The four without one are moves **within or into** the league — the player is still perfectly playable, and
    the crowd knows it, which is exactly why they are not selling. **The exodus is what distinguishes "he is
    leaving football we can see" from "he changed shirts".** Asking a model for the direction of a transfer
    would be a second thing to get wrong; the crowd already answers it for free.

    **And only while a transfer window is open** (ADR-154). Outside one he cannot go anywhere: a September
    story about a January move changes nothing about this gameweek, and acting on it would cost a real
    transfer for something that cannot happen yet. `today=None` skips the check, for callers that have already
    made it.

    Deliberately conservative, because being wrong costs a real transfer: no exodus, no claim.
    """
    if not exodus or not events:
        return None
    if today is not None:
        from src.fpl_rules import transfer_window_open
        if not transfer_window_open(today):
            return None
    return next((e for e in events if e.get("kind") == "transfer"), None)
