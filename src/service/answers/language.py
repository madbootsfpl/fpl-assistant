"""The language answers — a question in words, and the buzz.

`ask_question` hands the real engine (`src.ask`) a request; `chatter` fetches and caches the subreddit.
"""


from src.analytics import (
    player_summary,
)
from src.kits import photo_url

# ⭐⭐ **Imported as a module, not as names** (ADR-324). `common`'s helpers are shared by more than one
# answer family, and a test that fakes one — `_chip_status` is faked in three suites — must be able to
# reach every consumer from one place. ⚠️ *Binding a shared function into each module's globals gives it
# as many patch points as there are importers*, which is how a fake silently applies to one caller and
# not the next.
from src.service.answers import common
from src.service.inputs import load, opened
from src.service.requests import (
    AskRequest,
    ChatterRequest,
)
from src.storage import Storage

#: How long a fetched buzz list is reused (ADR-300).
#:
#: ⚠️⚠️ **Reddit rate-limits, and `RedditRssClient` says so in its own docstring:** *"cache +
#: rate-limit-respect live at the caller."* Without this, two taps a minute apart is two fetches, and the
#: second came back *"Reddit didn't respond"* the first time I tried it — ⭐ *a tab that fails when you
#: open it twice is a tab people conclude is broken.*
#:
#: ⭐ Ten minutes because the subreddit does not turn over faster than that, and *a cache shorter than the
#: thing it is caching changes is a rate limiter with extra steps.*
CHATTER_TTL_SECONDS = 600

#: The last fetched buzz, and when it expires. ⭐ **Keyed by nothing**: `player_ids` only flags rows and
#: `limit` slices them, so one fetch serves every caller — ⚠️ *a cache keyed on the caller's options is a
#: cache that misses on the first thing that differs.*
_CHATTER: dict = {"until": 0.0, "rows": None, "note": ""}


def ask_question(request: AskRequest, *, store: Storage | None = None, narrator=None) -> dict:
    """A question in words → the engine's answer (ADR-302, on ADR-036/054).

    ⭐⭐⭐ **The routing is the feature, and it has existed since Sprint 036.** `src/ask.py` matches a
    question to one of fifteen intents, loads what that intent needs, and hands back a decision, the facts
    behind it and a rendered detail block. The phone has never been able to ask.

    ⚠️⚠️ **No narrator, and that is deliberate rather than a limitation.** `ask.answer` defaults to
    `llm.narrate`, which talks to **Ollama on localhost** — there is none on the server, so every request
    would spend its connection timeout discovering that. ⭐ *The prose was always the optional half*:
    `AskResult.explanation` is documented as *"the LLM prose, or None when the model is unavailable"*, and
    the decision, the facts and the detail are computed by the analytics either way.

    ⚠️ Markdown is stripped on the way out — `plain()`, ADR-274 — because *the API speaks text, not
    Streamlit*, and a phone prints asterisks literally.
    """
    from src import ask as ask_engine

    request.validate()
    store, ours = opened(store)
    try:
        # ⭐ The fifteen the caller owns, presented as the session squad — which is what `active_squad`
        # was built for (ADR-054/055), so squad-scoped questions resolve without a saved name.
        active = {
            # ⭐ Named so the engine's own sentence reads: *"Captain pick (The 4-4-2 Towers)"*.
            # ⚠️ "your squad" produced *"squad 'your squad'"*, which looks like a bug rather than
            # a phrase — *the caller chooses this word and the engine prints it verbatim.*
            #
            # ⚠️⚠️ **This was hard-coded to "yours" and every answer said so**, while `my_team` had been
            # returning the real FPL team name in `squad.name` all along — ⭐ *the API knew the name and the
            # answer did not, because `ask` had no field to carry it.* Still falls back, because a caller
            # that sends no name must get a sentence that reads.
            "name": request.squad_name.strip() or "yours",
            "player_ids": list(request.player_ids),
            "bench_ids": list(request.bench_ids),
        } if request.player_ids else None

        # ⭐⭐⭐ **`converse`, not `answer`** (ADR-317 C). `converse()` has carried *why* · *and the next?*
        # · *what about defenders?* since ADR-047, and the phone could never reach any of them because
        # `ask_question` called the one-shot entry point — ⚠️ *the machinery was built, tested and
        # unreachable, which is the shape of half this month's findings.*
        #
        # ⚠️ **The context is rebuilt, never trusted.** The client holds five small fields; the decision
        # behind them is recomputed here.
        settings = {"horizon": request.horizon, "free": request.free, "bank": request.bank,
                    "chip_status": common._chip_status(request.manager_id, _next_gameweek(store))}
        context = ask_engine.context_from_wire(request.context, store, active_squad=active, **settings)
        result, next_context = ask_engine.converse(
            request.question,
            context,
            store=store,
            # ⚠️ Silences the narrator without pretending it answered — see above.
            narrator=narrator or (lambda *a, **k: None),
            active_squad=active,
            **settings,
        )
    finally:
        if ours:
            store.close()

    return {
        # ⭐ Hand back so the next question can be a follow-up. ⚠️ Null when there is nothing to follow —
        # *a client that stores an empty context will send it, and "why?" about nothing is a worse answer
        # than the nudge.*
        "context": ask_engine.context_to_wire(next_context),
        "question": result.question,
        # ⭐ Which engine answered, so a client can say so — ⚠️ *"I could not understand that" and "the
        # captain engine has nothing to say" are different answers and must not draw the same.*
        "intent": result.intent,
        "headline": common.plain(result.headline or ""),
        "detail": common.plain(result.detail or ""),
        # ⚠️ Present only when the router found nothing — the client shows this *instead*, never beside.
        "message": common.plain(result.message or ""),
        # ⭐ The facts behind the decision, already humanised by `ask` into strings a person can read.
        "facts": result.facts or {},
    }


def chatter(request: ChatterRequest, *, store: Storage | None = None, client=None) -> dict:
    """What r/FantasyPL is talking about (ADR-300, built on ADR-059).

    ⭐⭐⭐ **Almost none of this is new.** `community_signals` has counted whole-word player mentions against
    the squad index since Sprint 067 — resolving shared `web_name`s properly (ADR-152), degrading on any
    403 / 429 / timeout / parse error, and never raising. ⚠️ *It was wired to Streamlit and to nothing
    else*, so the phone has never been able to ask for it: the expensive half was paid for a year ago and
    has been invisible to every tester since the app shipped.

    ⚠️⚠️ **Mention frequency, not sentiment**, and the note says so. ⭐ *A count of names is not an opinion
    about players*, and a screen that blurs the two is inventing analysis it did not do.

    ⚠️ Degrades like everything else here: an unreachable Reddit returns an empty list and a sentence, not
    an error — ⭐ *a tab that can go dark must have something true to draw when it does.*
    """
    import time as _time

    from src.community import community_signals

    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, 1, store)
        players = {p["id"]: p for p in data.players}
        # ⚠️ **One guard, not two.** This also tested `rows is not None`, which made the "only cache
        # a success" rule below unfalsifiable — a mutation that cached failures survived every test,
        # because this line quietly refused to serve them. ⭐ *Defence in depth on a rule nobody can
        # break is defence against nothing, and it hides which line is doing the work.*
        fresh = _time.time() < _CHATTER["until"]
        if fresh:
            rows, note = _CHATTER["rows"], _CHATTER["note"]
        else:
            # ⭐ Fetched wide and sliced per caller, so one request serves every `limit`.
            rows, note = community_signals(data.players, limit=25, client=client)
            # ⚠️ **A failure is not cached.** Reddit blocking one request must not blank the tab for ten
            # minutes — ⭐ *caching an outage makes a blip into a symptom.*
            if rows:
                _CHATTER.update(
                    rows=rows, note=note, until=_time.time() + CHATTER_TTL_SECONDS
                )
        rows = (rows or [])[: request.limit]
    finally:
        if ours:
            store.close()

    owned_ids = set(request.player_ids)
    out = []
    for row in rows or []:
        raw = players.get(row.get("id"))
        if raw is None:
            continue
        out.append({
            # ⭐ The **same player shape as every other answer** — `test_player_shape.py` refused a
            # flattened one within minutes the last time, and it was right to.
            "player": player_summary(raw, data.xp_by_id),
            # ⭐⭐ **Our own mugshot, not a thumbnail from the feed** (ADR-300). Reddit entries carry no
            # reliable image, and ⚠️ *an image that identifies the subject is worth more than one that
            # decorates the page* — this one we can supply without asking anyone's permission.
            "photo": photo_url(raw["code"]),
            "mentions": row.get("mentions", 0),
            "owned": row["id"] in owned_ids,
            # ⚠️ Capped: a busy player can be in a dozen threads and ⭐ *a row that scrolls is a row that
            # has stopped being a summary.* The count above is the whole number; these are the evidence.
            "posts": [
                {"title": post.get("title", ""), "link": post.get("link", "")}
                for post in (row.get("posts") or [])[:3]
            ],
        })

    return {
        "rows": out,
        # ⭐ The service's own sentence, carried rather than re-derived — *two places that describe the
        # same outcome are two places that will disagree about it.*
        "note": note,
        # ⚠️ **Named on every row's behalf, once.** The tab is about attention, not quality.
        "measures": "mentions",
    }


def _next_gameweek(store) -> int | None:
    """The gameweek chip availability should be judged against — ⭐ *the one you are about to play.*

    ⚠️ Availability is **per half**, not per season (ADR-234): a wildcard spent in GW4 leaves the
    second-half one untouched. So the answer depends on which half we are in, and that needs a gameweek.

    ⚠️ `sqlite3.Row` has no `.get` — the third time this session — so the rows are read through the same
    tolerant accessor the analytics use.
    """
    from src.analytics.names import _get

    events = sorted({_get(f, "event") for f in store.get_upcoming_fixtures() if _get(f, "event")})
    return events[0] if events else None
