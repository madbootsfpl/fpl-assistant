"""Question in, intent and parameters out. **No store, no football.**

⭐⭐ This is the layer that can be tested with strings alone, which is most of why it is worth having on its
own: every function here is a pure function of the words. `route` picks the intent; the rest read the
numbers, names, positions and lenses out of the same sentence.
"""

import re

from src.analytics import (
    FULL_BUDGET,
    WEEKLY_BENCH_WEIGHT,
)
from src.analytics.names import build_index, find_spoken_mentions
from src.fpl_rules import CHIP_NAMES
from src.squads import SquadStore

# Keyword → intent. Order matters (first match wins); the LLM decides none of this.
_INTENT_KEYWORDS = {
    # price predictor (ADR-092) FIRST among the price words: prediction-specific phrases ("who's about to
    # rise?", "price risers") so they beat rules' explanatory "price rise"/"price change" and trends' bare
    # "risers"/"fallers". A genuine rules question ("how do price rises work") carries none of these.
    "price": ("about to rise", "about to fall", "about to go up", "about to go down", "about to drop",
              "about to change price", "going to rise", "going to fall", "rise in price", "fall in price",
              "drop in price", "price prediction", "price predictions", "price risers", "price fallers",
              "who's rising", "who is rising", "who's going up", "predicted to rise", "predicted to fall",
              "who will rise", "who will fall", "likely to rise", "likely to fall"),
    # rules (ADR-085): question-shaped, general cues so a rules question ("how does bench boost work",
    # "how do transfers work") beats the squad intents — WITHOUT stealing squad commands, which are imperative
    # / squad-scoped ("fix my bench", "what transfer should I make") and match none of these.
    # ⚠️⚠️⚠️ **The apostrophe-less forms, and they matter more than they look** (ADR-317 B). `what's a`
    # was here and `whats a` was not, so *"whats a chip?"* fell past `rules` into `chips` and got a
    # strategy. Worse, two others landed on engines that **act** rather than explain: *"whats a wildcard?"*
    # reached `build_squad` and **built a squad**, *"explain the bench boost"* reached `start_bench`.
    # ⭐⭐ *A definition question answered by a machine that does something is the most confidently wrong
    # shape this router has* — and nobody types the apostrophe on a phone.
    "rules": ("how does", "how do ", "how is a", "how are", "what is a", "what are the", "what's a",
              # ⚠️⚠️⚠️ **"whats the" is NOT here, and it was.** It stole *"whats the best chip
              # strategy?"* into `rules` — a strategy question answered with a definition. ⭐ *"a" and "an"
              # announce a definition; "the" announces almost anything*, and the spot-check that missed it
              # used "whats **my** best chip strategy" by luck.
              "whats a", "whats an", "what're the",
              "what does", "what happens", "how many points", "how much do", "the rules", "fpl rules",
              "scoring", "clean sheet", "bonus point", "defensive contribution", "defcon", "price change",
              "price rise", "price fall", "sell-on", "auto sub", "auto-sub", "autosub", "when is the deadline",
              "double gameweek", "blank gameweek", "explain the rules",
              # new topics (US-282) — specific phrases so they win over the squad intents without hijacking them
              "yellow flag", "red flag", "chance of playing", "player flag", "before gameweek",
              "before the season", "unlimited transfers before", "preseason transfer", "one chip per",
              "two chips", "chips in one gameweek", "multiple chips", "bench points", "do bench players score",
              "does my bench score", "how many wildcards", "two wildcards", "second wildcard", "wildcard reset",
              "mini league", "mini-league", "classic league", "head to head", "head-to-head", "h2h",
              "how do leagues", "overall rank", "gameweek rank", "world rank", "team value", "selling price",
              "in the bank", "buy price", "squad value"),
    # chips (ADR-082): distinctive chip phrases only, so they win before captain/bench/build without
    # hijacking them. NOT bare "bench boost"/"wildcard" (they stay with build_squad — "build me a squad for a
    # bench boost" must still build); NOT bare "captain"/"bench" (those stay their own intents).
    "chips": ("chip strategy", "which chip", "what chip", "chips", " chip ", "chip?", "use a chip",
              "triple captain", "free hit", "use my bench boost", "use my wildcard", "when to bench boost",
              "when to wildcard", "play my bench boost", "play my wildcard",
              # Timing phrasings (2026-08-30). Without these, "wildcard now or wait?" fell through to
              # build_squad's bare "wildcard" and **built a squad** — a confidently wrong answer to a
              # question about when, measured as the only harmful mis-route in a 30-question corpus.
              # ⚠️⚠️ **The past tense was missing, and `build_squad` took it.** `chips` knew "use my
              # wildcard" and not "used my wildcard", so *"have i used my wildcard?"* fell past it to a
              # bare "wildcard" and **built a squad** — ⭐ *asking whether you spent a chip is not asking
              # to spend it, and the difference is one letter* (ADR-317 A).
              "have i used", "have i played", "did i use", "did i play", "chips have i",
              "can i still play", "do i still have", "still have my", "already played my",
              "wildcard now", "wildcard or wait", "wildcard this week", "wildcard yet",
              "when should i wildcard", "hold my wildcard", "save my wildcard"),
    # trends: its phrases ("most transferred") are distinctive, so they win before "transfer" (ADR-057).
    "trends": ("trending", "most owned", "most picked", "most transferred", "most sold", "most bought",
               "in form", "risers", "fallers", "bandwagon", "most popular"),
    # worth (a single-player value verdict, ADR-061) before captain/transfer so "worth buying" isn't
    # caught by "buy"; the phrases are value-specific, so "worth captaining" still falls to captain.
    "worth": ("worth the money", "worth it", "good value", "value for money", "worth buying",
              "worth the price", "worth the cost",
              # The negative framing is just as common and matched nothing (2026-08-30).
              "overpriced", "too expensive", "overrated"),
    # history (US-296): a single-player season record — distinctive phrases so it wins for "X's history" /
    # "how did X do last season" without stealing worth ("is X worth it") or the squad commands.
    "history": ("history", "last season", "last year", "how did", "track record", "past seasons",
                "season by season", "season record"),
    "captain": ("captain", "armband"),
    # "bring in" is how people actually phrase a transfer in — added 2026-08-30 after it fell through.
    "transfer": ("transfer", "sell", "buy", "swap", "bring in", "get rid of", "move on"),
    "analyse": ("analyse", "analyze", "health", "how is my", "how's my", "how good",
                # "is my team any good?" — the natural phrasing, which "how good" misses (2026-08-30).
                "team any good", "squad any good", "team look", "squad look"),
    # build_squad before start_bench so "build me a squad for a bench boost" isn't caught by "bench".
    "build_squad": ("build", "wildcard", "best squad", "best team", "best xi", "new squad",
                    "new team", "pick a squad", "pick a team"),
    "start_bench": ("start", "bench", "lineup", "line-up"),
    # gameweek after the specific intents: a holistic "what should I do this week" routes here, but a
    # pointed "who should I captain this week" still matches captain first (ADR-070). Phrase-based so
    # "this week" only fires the weekly plan, not a stray word.
    "gameweek": ("this week", "this gameweek", "gameweek plan", "gw plan", "weekly plan",
                 "plan for the week", "plan for this week", "what should i do", "what do i do",
                 "recommend my", "recommendation for my",
                 # A **named** gameweek (2026-08-30). Every phrasing above assumes *this* week, so
                 # "what's the best strategy for GW3?" matched nothing and fell to the fallback — even
                 # though "what should I do in GW3?" already answered it. The owner hit exactly that.
                 #
                 # Each is "<planning word> for/at GW<n>", never a bare "for gw": `gameweek` is checked
                 # BEFORE `shortlist`, so a loose "gw" would swallow "best midfielders for GW3". And a bare
                 # "strategy" is deliberately still unroutable — it is a modifier, not a topic ("transfer
                 # strategy" and "captaincy strategy" correctly reach their own intents, which are checked
                 # first), so guessing an intent for it would trade an honest miss for a confident wrong
                 # answer — the one failure the routing corpus measured as actually harmful.
                 "strategy for gw", "strategy for gameweek", "strategy in gw", "strategy in gameweek",
                 "plan for gw", "plan for gameweek", "approach gw", "approach gameweek",
                 "approach to gw", "approach to gameweek", "approach for gw", "approach for gameweek"),
    "shortlist": ("goalkeeper", "keeper", "defender", "midfielder", "forward", "striker",
                  "best value", "best players", "differential", "differentials"),
    "compare": ("compare", "versus", " vs ", "better", " or "),
    # fixtures is last: its keywords are distinctive, and "play" is broad, so let every more
    # specific intent match first (ADR-048).
    "fixtures": ("fixture", "schedule", "opponent", "difficulty", "fdr", "play"),
}
                                     # `detail` above was rendered from, so a button applies what is displayed


def squad_name(question: str, known_squads) -> str | None:
    """The saved-squad name mentioned anywhere in the question, if any.

    Matching against *known* names (not a preposition) is robust to phrasing — "for TS",
    "from TS", "analyse TS" all work — and it won't mistake a stray word ("for the weekend")
    for a squad, so captaincy's global mode still works. Possessive-aware (ADR-049): "TS's
    players" resolves to "TS", so the natural squad-scoped phrasing routes.
    """
    tokens = set()
    for raw in question.replace("?", "").split():
        tokens.add(raw)
        tokens.add(re.sub(r"['’]s$", "", raw).strip(".,!;:'’\""))   # "TS's" → "TS", "TS." → "TS"
    return next((name for name in known_squads if name in tokens), None)


# "GW3", "gw 3", "gameweek 3" — the number a question names, if any.
_GW_IN_QUESTION = re.compile(r"\b(?:gw|gameweek)\s*(\d{1,2})\b")


def _named_gameweek(question) -> int | None:
    """The gameweek a question explicitly names, or None.

    Exists because `gameweek` answers **the next gameweek, always** — it takes no GW argument and the captain
    is next-GW by construction. Every phrasing it originally knew said so out loud ("this week", "what should
    I do"), so the assumption was safe. Once it learned to match a *named* gameweek (2026-08-30), it could be
    asked about GW3 while GW2 is next and would answer the wrong week under a "This week" header — a
    confident answer to a question nobody asked, which is the failure this project treats as worse than a
    miss. So the number is read back out and the mismatch is stated.
    """
    match = _GW_IN_QUESTION.search((question or "").lower())
    return int(match.group(1)) if match else None


def route(question: str, known_squads=None) -> tuple[str | None, str | None]:
    """(intent, squad_name) from a question, by keyword. intent is None if unrecognised.

    `known_squads` defaults to the saved squads; tests pass it explicitly (no I/O).
    """
    if known_squads is None:
        known_squads = SquadStore().names()
    squad = squad_name(question, known_squads)
    q = question.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(k in q for k in keywords):
            return intent, squad
    return None, squad


#: ⭐⭐⭐ **One captaincy engine, one intent** (ADR-308) — the owner's own instinct, and the right one:
#: *six analytics functions would be six places for the definition of "best captain" to drift apart.*
#:
#: ⚠️⚠️ **These existed as questions long before they existed as answers.** Measured against the owner's
#: list (ADR-307): *"who should be my **vice**-captain?"*, *"who is the **safest** captain?"* and *"who is
#: the best **differential** captain?"* all returned the **same top pick**, confidently, because the
#: router matched `captain` and dropped the word that made the question specific. ⭐ *A wrong answer
#: wearing the shape of a right one* — and `src/ask.py` already carried the principle in its routing
#: table, where a bare "strategy" is left unroutable on purpose.
CAPTAIN_LENSES: dict[str, tuple[str, ...]] = {
    # ⭐ Order is deliberately *not* load-bearing — `captain_lens` compares phrase **length**, so
    # "vice-captain" beats "vice" wherever either sits. ⚠️ *A table whose correctness depends on its own
    # line order is a table the next edit breaks silently.*
    "vice": ("vice-captain", "vice captain", "vice", "second captain", "backup captain"),
    "safest": ("safest", "safe captain", "most reliable", "least risky", "nailed on", "nailed-on"),
    "differential": ("differential", "punt", "low owned", "low-owned", "under the radar"),
    "rotation": ("rotation risk", "rotation", "be rested", "get rested", "start this week",
                 "minutes risk"),
}


def scope_label(squad_name: str) -> str:
    """How an answer names the squad it is about — ⭐ *the team's own name, and nothing else.*

    ⚠️⚠️ It used to read **`squad 'yours'`**, and both halves were wrong. The placeholder was there because
    the phone had no field to send a team name (fixed in `AskRequest`), and the `squad '…'` wrapper existed
    to make a *placeholder* sound like a label — ⭐ *scaffolding for a stand-in, kept after the real thing
    arrived.* With a real name it reads as a stutter: *"Captain pick (squad 'The 4-4-2 Towers')"*.

    ⭐ Saved squads on the web read the same way — *"(Demo XI)"* — because a name is a name.
    """
    return squad_name


def captain_lens(question: str) -> str | None:
    """Which captaincy question was actually asked — or `None` for *"who should I captain?"*.

    ⭐ The longest phrase wins, so a question naming two lenses gets the more specific one — *"is my
    vice-captain a rotation risk"* is about the vice — rather than whichever the dict listed first.

    ⚠️ Note "captain" itself is **not** in the table: routing to the captain intent happens upstream, and
    this only ever chooses *which* captain question was asked.
    """
    low = f" {question.lower()} "
    best, hit = None, 0
    for lens, phrases in CAPTAIN_LENSES.items():
        for phrase in phrases:
            if phrase in low and len(phrase) > hit:
                best, hit = lens, len(phrase)
    return best


#: ⭐ Phrasings that are asking *"which of these two?"* — the shape that makes a missing name a defect
#: rather than a detail.
_COMPARISON_WORDS = (" better ", " or ", " vs ", " versus ", " compared to ", " instead of ")


def _looks_like_a_comparison(question: str) -> bool:
    return any(word in f" {question.lower()} " for word in _COMPARISON_WORDS)


def _named_in(question: str, players) -> list:
    """The players a question names, in the order the engine ranks them — ⭐ *resolved, never regexed.*"""
    index = build_index(players)
    # ⭐⭐ **Spoken-tolerant** (ADR-315): exact matching first and unchanged, then one conservative pass over
    # what it did not claim — because a phone's recogniser has never heard of Semenyo and returns *"semenio"*.
    # ⚠️ Ask only: the same index feeds the buzz counter over thousands of Reddit sentences, where a fuzzy
    # pass would credit players to ordinary words at scale.
    hits = find_spoken_mentions(question.lower(), index)
    by_id = {p["id"]: p for p in players}
    return [by_id[pid] for pid in hits if pid in by_id]


def _transfer_count(question: str) -> int:
    """The N in 'which N transfers …' (a digit right before 'transfer(s)'); else 1."""
    tokens = question.lower().replace("?", "").split()
    for i, tok in enumerate(tokens[:-1]):
        if tok.isdigit() and tokens[i + 1].startswith("transfer"):
            return max(1, int(tok))
    return 1


#: ⭐⭐⭐ **One chips engine, one intent** (ADR-317 A) — the shape ADR-308 gave captaincy, one intent along.
#:
#: ⚠️⚠️ **Four questions were getting one answer.** *"What chips have I played?"* is a **fact**, not a
#: recommendation; *"before they expire"* is the same recommendation over a **shorter list**; *"can I still
#: play my bench boost?"* is a **yes or no**. All three got the full four-chip strategy block, which is why
#: the owner said it was not credible — ⭐ *the same answer to different questions is indistinguishable from
#: not having listened.*
CHIP_LENSES: dict[str, tuple[str, ...]] = {
    "played": ("have i played", "have i used", "chips have i", "already played", "already used",
               "which chips have", "what chips have", "did i play", "did i use"),
    "holding": ("can i still play", "do i still have", "have i still got", "still have my",
                "can i still use", "do i have my"),
    "expiry": ("before they expire", "before it expires", "expire", "expiring", "run out", "left to use"),
}


def chip_lens(question: str) -> str | None:
    """Which chip question was asked — or `None` for *"which chip should I use?"*.

    ⭐ Longest phrase wins, the same rule `captain_lens` uses, so *"what chips have i played"* is a `played`
    question rather than an `expiry` one because it names the more specific thing.
    """
    low = f" {question.lower()} "
    best, hit = None, 0
    for lens, phrases in CHIP_LENSES.items():
        for phrase in phrases:
            if phrase in low and len(phrase) > hit:
                best, hit = lens, len(phrase)
    return best


def _chip_named(question: str) -> str | None:
    """The FPL chip a question names, if it names one — for *"can I still play my bench boost?"*."""
    low = question.lower()
    for fpl in CHIP_NAMES:
        spoken = {"bboost": ("bench boost", "benchboost"), "3xc": ("triple captain", "triple-captain"),
                  "freehit": ("free hit", "freehit"), "wildcard": ("wildcard", "wild card")}[fpl]
        if any(word in low for word in spoken):
            return fpl
    return None


def _bounded(haystack: str, needle: str, start: int) -> bool:
    """True if `needle` at `start` in `haystack` is bounded by non-letters (a whole name).

    So "Isak" doesn't match inside "mistaken"; "b.fernandes" still matches (bounded by space/'?').
    """
    end = start + len(needle)
    before = haystack[start - 1] if start > 0 else " "
    after = haystack[end] if end < len(haystack) else " "
    return not before.isalpha() and not after.isalpha()


def _match_players(question: str, players) -> dict:
    """Player web_names named in `question` → {web_name: [players]} in question order (ADR-039).

    Bounded substring match; a name that is a substring of another matched name is dropped
    (`Fernandes` ⊂ `B.Fernandes`); a web_name shared by >1 player yields a list (ambiguous).
    """
    ql = question.lower()
    hits = []   # (position, web_name, player)
    for p in players:
        wn = (p["web_name"] or "").lower()
        if not wn:
            continue
        i = ql.find(wn)
        if i != -1 and _bounded(ql, wn, i):
            hits.append((i, p["web_name"], p))

    lower = {h[1].lower() for h in hits}
    hits = [h for h in hits if not any(h[1].lower() != o and h[1].lower() in o for o in lower)]

    matched: dict = {}
    for _i, wn, p in sorted(hits, key=lambda h: h[0]):
        matched.setdefault(wn, []).append(p)
    return matched


def _squad_budget(question: str) -> float:
    """The budget in a build-a-squad question — '£100m' / '85m' / '£90' — else the £100m default."""
    m = re.search(r"£\s*(\d+(?:\.\d+)?)|\b(\d+(?:\.\d+)?)\s*m\b", question.lower())
    return float(m.group(1) or m.group(2)) if m else FULL_BUDGET


def _archetype_counts(question: str) -> tuple:
    """(low_cost, premium, differential) counts from a build request (ADR-043); None when absent.

    Matches a number a word or two before an archetype word — "3 low cost players", "1 premium",
    "2 differentials". `differential` is parsed but not yet buildable (needs ownership data).
    """
    ql = question.lower()

    def count(*words):
        m = re.search(r"(\d+)\s+(?:\w+\s+){0,2}?(?:" + "|".join(words) + r")", ql)
        return int(m.group(1)) if m else None

    return (count("low cost", "low-cost", "budget", "cheap", "enabler"),
            count("premium"), count("differential"))


def _bench_mode(question: str) -> tuple:
    """(bench_weight, is_bench_boost) from a build request (ADR-045).

    "bench boost" → the max-15 (all 15 score); "rotation"/"weekly" → a bench-aware XI (w = 0.1,
    a strong XI + a cheap playing bench); else the default.
    """
    ql = question.lower()
    if "bench boost" in ql or "benchboost" in ql:
        return None, True
    if "rotation" in ql or "weekly" in ql:
        return WEEKLY_BENCH_WEIGHT, False
    return None, False


_POS_WORDS = {"goalkeeper": "GK", "keeper": "GK", "defender": "DEF", "midfielder": "MID",
              "forward": "FWD", "striker": "FWD"}


def _shortlist_query(question: str) -> tuple:
    """(position, price_cap, by_value, differential) from a 'best <position> [under £X]' question.

    `differential` (ADR-061) filters to low-owned players; cued by "differential(s)" / "off-template" /
    "low-owned". Value ("value") ranks by xP/£m (ADR-042).
    """
    ql = question.lower()
    position = next((code for word, code in _POS_WORDS.items() if re.search(rf"\b{word}s?\b", ql)),
                    None)
    m = re.search(r"under £?\s*(\d+(?:\.\d+)?)|£\s*(\d+(?:\.\d+)?)", ql)
    cap = float(m.group(1) or m.group(2)) if m else None
    differential = "differential" in ql or "off-template" in ql or "low-owned" in ql or "low owned" in ql
    return position, cap, "value" in ql, differential

# (by, cues) in precedence order — the more specific "out" phrases before the broad "in"/"owned".
_TREND_CUES = (
    ("out", ("most transferred out", "most sold", "fallers", "transferred out", "sold")),
    ("in", ("most transferred in", "trending", "risers", "bandwagon", "transferred in",
            "most bought", "bought")),
    ("form", ("in form", "in-form")),
    ("owned", ("most owned", "most picked", "most popular", "owned", "picked", "popular")),
)


def _trends_query(question: str) -> tuple:
    """(by, position) from a trends question — which board (`TREND_BYS`) + an optional position filter."""
    ql = question.lower()
    by = next((b for b, cues in _TREND_CUES if any(c in ql for c in cues)), "in")
    position = next((code for word, code in _POS_WORDS.items() if re.search(rf"\b{word}s?\b", ql)), None)
    return by, position
_TEAM_ALIASES = {   # colloquial names the FPL `name` field doesn't carry
    "tottenham": "TOT", "spurs": "TOT", "man united": "MUN", "man utd": "MUN",
    "manchester united": "MUN", "man city": "MCI", "manchester city": "MCI", "forest": "NFO",
}


def match_team(question: str, teams) -> str | list | None:
    """Resolve a team from a question (ADR-048): the code (str), None (→ league mode), or a list
    (ambiguous → clarify). Never a silent wrong guess.

    Matches the full `name` (a substring, so multi-word names like "Man City" work), the
    `short_name` as a **case-sensitive** whole word (so a typed code "LIV"/"NEW" matches but the
    common word "new" doesn't), and a small alias set.
    """
    ql = question.lower()
    hits = set()
    for t in teams:
        if re.search(rf"\b{re.escape(t['short_name'])}\b", question):   # case-sensitive: "NEW" not "new"
            hits.add(t["short_name"])
        if t["name"].lower() in ql:
            hits.add(t["short_name"])
    for alias, code in _TEAM_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", ql):
            hits.add(code)
    if len(hits) > 1:
        return sorted(hits)
    return next(iter(hits), None)


def fixture_horizon(question: str) -> int:
    """The N in 'next N' / 'N gameweeks' (ADR-048); default 5, capped to a season."""
    m = re.search(r"next\s+(\d+)", question.lower()) or re.search(
        r"(\d+)\s*(?:game|gw|week|fixture)", question.lower())
    return max(1, min(int(m.group(1)), 38)) if m else 5
