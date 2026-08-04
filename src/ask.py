"""The `ask` command's brain (ADR-034): route → analytics decide → humanise → narrate.

The discipline (proven in the Sprint 031 spike): **the analytics decide; the LLM only
narrates.** A question is routed by *keyword* (the LLM never decides the route either); the
analytics make the decision and emit **pre-humanised, self-describing facts**; a prompt
tells the model to explain them and nothing else. The narrator is **injectable and optional**
— if it returns None (Ollama absent), `answer` degrades to the decision + facts.

This sprint (US-096) wires the `captain` intent; transfer + analyse follow in US-097.
"""

import json
import re
from dataclasses import dataclass

from src import llm
from src.analytics import (
    XI_FLEX,
    analyse_squad,
    baseline_rate,
    captain_picks,
    player_xp,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
)
from src.squads import SquadStore
from src.storage import Storage
from src.ui.analyse import render_squad_analysis
from src.ui.transfer import render_transfer_plan

_HORIZON = 5   # transfer/analyse are multi-week decisions (captain is next-GW)

# Keyword → intent. Order matters (first match wins); the LLM decides none of this.
_INTENT_KEYWORDS = {
    "captain": ("captain", "armband"),
    "transfer": ("transfer", "sell", "buy", "swap"),
    "analyse": ("analyse", "analyze", "health", "how is my", "how's my", "how good"),
}

_RULES = (
    "Rules: do NOT rank or compare players, do NOT compute or invent any number, do NOT expand "
    "or rename teams (use the codes exactly as written), do NOT merge separate facts, and do NOT "
    "mention anything that is not in the facts."
)

_FALLBACK = (
    "I can answer about captaincy, transfers, or your squad's health. "
    'Try: ask "who should I captain from <squad>?"'
)


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


def _squad_name(question: str, known_squads) -> str | None:
    """The saved-squad name mentioned anywhere in the question, if any.

    Matching against *known* names (not a preposition) is robust to phrasing — "for TS",
    "from TS", "analyse TS" all work — and it won't mistake a stray word ("for the weekend")
    for a squad, so captaincy's global mode still works.
    """
    tokens = set(question.replace("?", "").split())
    return next((name for name in known_squads if name in tokens), None)


def route(question: str, known_squads=None) -> tuple[str | None, str | None]:
    """(intent, squad_name) from a question, by keyword. intent is None if unrecognised.

    `known_squads` defaults to the saved squads; tests pass it explicitly (no I/O).
    """
    if known_squads is None:
        known_squads = SquadStore().names()
    squad = _squad_name(question, known_squads)
    q = question.lower()
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(k in q for k in keywords):
            return intent, squad
    return None, squad


def _captain_facts(pick: dict) -> dict:
    """Pre-humanised, self-describing facts for one captain pick — nothing to decode."""
    venue = "home against" if pick["venue"] == "H" else "away against"
    return {
        "player": f"{pick['web_name']} ({pick['team']})",
        "expected_points_next_gameweek": pick["xp"],
        "fixture": f"{venue} {pick['opponent']}",
        "is_penalty_taker": pick["penalty_taker"],
    }


def _decide_captain(store: Storage, squad_name: str | None) -> dict | None:
    """Analytics DECIDE the captain (never the LLM); return the decision + humanised facts."""
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    baselines = {c: baseline_rate(r) for c, r in store.get_history_by_code().items()}
    scope = "all players"
    if squad_name:
        squad = SquadStore().load(squad_name)
        if squad is None:
            return None
        ids = set(squad["player_ids"])
        players = [p for p in players if p["id"] in ids]
        scope = f"squad '{squad_name}'"

    picks = captain_picks(players, upcoming, baseline_by_code=baselines, limit=3)
    if not picks:
        return None
    top = picks[0]
    return {
        "headline": f"Captain pick ({scope}): {top['web_name']} — xP {top['xp']} next GW",
        "facts": _captain_facts(top),
        "subjects": [top["web_name"]],
        "task": f"explain in 2-3 short sentences why {top['web_name']} is a good captain pick "
                "this gameweek",
    }


def _transfer_count(question: str) -> int:
    """The N in 'which N transfers …' (a digit right before 'transfer(s)'); else 1."""
    tokens = question.lower().replace("?", "").split()
    for i, tok in enumerate(tokens[:-1]):
        if tok.isdigit() and tokens[i + 1].startswith("transfer"):
            return max(1, int(tok))
    return 1


def _transfer_facts(move: dict) -> dict:
    """Pre-humanised facts for one transfer move."""
    return {
        "sell": f"{move['out']['web_name']} ({move['out']['team']}, xP {move['out']['xp']})",
        "buy": f"{move['in']['web_name']} ({move['in']['team']}, xP {move['in']['xp']})",
        "expected_points_gain_over_5_gameweeks": move["gain"],
    }


def _plan_facts(plan: list) -> dict:
    """Self-describing facts for a coordinated transfer plan (ADR-035)."""
    return {
        "transfers": [
            f"sell {m['out']['web_name']}, buy {m['in']['web_name']} (+{m['gain']} xP)"
            for m in plan
        ],
        "total_expected_points_gain_over_5_gameweeks": round(sum(m["gain"] for m in plan), 1),
    }


def _analyse_facts(analysis: dict) -> dict:
    """Self-describing facts for a squad summary — the fix for the probe's field-conflation.

    `availability_problems` reads "none" or "N: names" so the model can't imply injuries that
    aren't there; the weakest starters are a clearly separate list.
    """
    issues = analysis["issues"]
    availability = (
        "none" if not issues
        else f"{len(issues)}: " + ", ".join(p["web_name"] for p in issues)
    )
    return {
        "projected_starting_XI_points_over_5_gameweeks": analysis["projected_xp"],
        "availability_problems": availability,
        "weakest_starters": [f"{w['web_name']} (xP {w['xp']})" for w in analysis["weakest"]],
    }


def _squad_xp(store: Storage, squad_name: str):
    """Shared setup for transfer/analyse: the squad's owned rows + xP (+ per-GW) over the horizon."""
    squad = SquadStore().load(squad_name)
    if squad is None:
        return None
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    baselines = {c: baseline_rate(r) for c, r in store.get_history_by_code().items()}
    ranked = player_xp(players, upcoming, horizon=_HORIZON, baseline_by_code=baselines)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}
    gameweeks = ranked[0]["gameweeks"] if ranked else []
    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    return squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks


def _decide_transfer(store: Storage, squad_name: str | None, count: int = 1) -> dict | None:
    data = _squad_xp(store, squad_name)
    if data is None:
        return None
    squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks = data
    if not owned:
        return None
    bench_ids = squad.get("bench_ids") or []

    if count > 1:
        # A coordinated N-transfer plan (ADR-035), with a per-GW table as structured detail (ADR-036).
        plan = suggest_transfer_plan(
            owned, players, xp_by_id, bench_ids=bench_ids, bank=0.0, count=count
        )
        if not plan:
            return None
        detail = render_transfer_plan(
            plan, squad_name, bank=0.0, horizon=_HORIZON,
            by_gameweek_by_id=by_gameweek_by_id, gameweeks=gameweeks,
        )
        return {
            "detail": detail,                       # the exact table, shown above the narration
            "facts": _plan_facts(plan),
            "subjects": [m["out"]["web_name"] for m in plan]
                        + [m["in"]["web_name"] for m in plan],
            "task": f"summarise this {len(plan)}-transfer plan in 2-3 short sentences",
        }

    moves = suggest_transfers(
        owned, players, xp_by_id, bench_ids=bench_ids, bank=0.0, limit=1
    )
    if not moves:
        return None
    m = moves[0]
    return {
        "headline": f"Transfer (squad '{squad_name}'): {m['out']['web_name']} → "
                    f"{m['in']['web_name']} (+{m['gain']} xP over {_HORIZON} GW)",
        "facts": _transfer_facts(m),
        "subjects": [m["out"]["web_name"], m["in"]["web_name"]],
        "task": f"explain in 2 short sentences why selling {m['out']['web_name']} and buying "
                f"{m['in']['web_name']} improves the squad",
    }


def _decide_analyse(store: Storage, squad_name: str | None) -> dict | None:
    data = _squad_xp(store, squad_name)
    if data is None:
        return None
    squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks = data
    if not owned:
        return None
    bench_ids = set(squad.get("bench_ids") or [])
    if bench_ids:
        xi_ids = {p["id"] for p in owned if p["id"] not in bench_ids}
    else:
        result = select_squad(owned, budget=200.0, formation=XI_FLEX, size=11, scores=xp_by_id)
        xi_ids = {p["id"] for p in result["selected"]}
    # The full squad-analysis table (XI + per-GW xP + weak links) as structured detail (ADR-036) —
    # the same analysis + renderer the `analyse` command uses, so `ask` reads like the command.
    analysis = analyse_squad(
        owned, xi_ids, xp_by_id, horizon=_HORIZON,
        by_gameweek_by_id=by_gameweek_by_id, gameweeks=gameweeks,
    )
    detail = render_squad_analysis(analysis, squad_name)
    subjects = [w["web_name"] for w in analysis["weakest"]] + \
               [p["web_name"] for p in analysis["issues"]]
    return {
        "detail": detail,                       # the exact table, shown above the narration
        "facts": _analyse_facts(analysis),
        "subjects": subjects,
        "task": "summarise this squad's health in 2-3 short sentences",
    }


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

    facts_numbers = _numbers(json.dumps(facts))
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
        f"FACTS:\n{json.dumps(decision['facts'], indent=2)}"
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
    )


def answer(question: str, *, store: Storage | None = None, narrator=llm.narrate) -> AskResult:
    """Route → analytics decide → narrate (or degrade). The narrator is injectable/optional."""
    intent, squad_name = route(question)
    if intent is None:
        return assemble(question, None, None, narrator)
    if intent in ("transfer", "analyse") and not squad_name:
        verb = "what transfer" if intent == "transfer" else "analyse"
        return AskResult(question, intent,
                         message=f'Name a saved squad, e.g. ask "{verb} for <squad>?"')

    own_store = store is None
    store = store or Storage()
    try:
        if intent == "transfer":
            decision = _decide_transfer(store, squad_name, _transfer_count(question))
        elif intent == "captain":
            decision = _decide_captain(store, squad_name)
        else:
            decision = _decide_analyse(store, squad_name)
        # The known player names for the verifier's name check (ADR-037).
        known_names = [p["web_name"] for p in store.get_players()] if decision else ()
    finally:
        if own_store:
            store.close()

    return assemble(question, intent, decision, narrator, known_names=known_names)
