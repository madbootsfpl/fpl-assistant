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
import statistics
from dataclasses import dataclass, replace

from src import llm
from src.analytics import (
    DIFFERENTIAL_OWN,
    FULL_BUDGET,
    SQUAD_15,
    TREND_BYS,
    WEEKLY_BENCH_WEIGHT,
    analyse_squad,
    archetype_bands,
    available_players,
    baseline_rate,
    best_legal_xi,
    captain_picks,
    chip_advisor,
    decision_xp,
    gameweek_plan,
    minutes_weight_from_history,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
    team_fdr,
    team_schedule,
    trending,
)
from src.analytics.captain import _next_opponent
from src.squads import SquadStore
from src.storage import Storage
from src.ui.analyse import render_squad_analysis
from src.ui.chips import render_chip_advice
from src.ui.compare import render_compare
from src.ui.fdr import render_fdr_table
from src.ui.fixtures import render_squad_fixtures, render_squad_team_fixtures, render_team_fixtures
from src.ui.gameweek import render_gameweek_plan
from src.ui.shortlist import render_shortlist
from src.ui.squad import render_squad
from src.ui.startbench import render_start_bench
from src.ui.transfer import render_transfer_plan
from src.ui.trending import render_trending

_HORIZON = 5   # transfer/analyse are multi-week decisions (captain is next-GW)

# Keyword → intent. Order matters (first match wins); the LLM decides none of this.
_INTENT_KEYWORDS = {
    # chips first (ADR-082): distinctive chip phrases only, so they win before captain/bench/build without
    # hijacking them. NOT bare "bench boost"/"wildcard" (they stay with build_squad — "build me a squad for a
    # bench boost" must still build); NOT bare "captain"/"bench" (those stay their own intents).
    "chips": ("chip strategy", "which chip", "what chip", "chips", " chip ", "chip?", "use a chip",
              "triple captain", "free hit", "use my bench boost", "use my wildcard", "when to bench boost",
              "when to wildcard", "play my bench boost", "play my wildcard"),
    # trends: its phrases ("most transferred") are distinctive, so they win before "transfer" (ADR-057).
    "trends": ("trending", "most owned", "most picked", "most transferred", "most sold", "most bought",
               "in form", "risers", "fallers", "bandwagon", "most popular"),
    # worth (a single-player value verdict, ADR-061) before captain/transfer so "worth buying" isn't
    # caught by "buy"; the phrases are value-specific, so "worth captaining" still falls to captain.
    "worth": ("worth the money", "worth it", "good value", "value for money", "worth buying",
              "worth the price", "worth the cost"),
    "captain": ("captain", "armband"),
    "transfer": ("transfer", "sell", "buy", "swap"),
    "analyse": ("analyse", "analyze", "health", "how is my", "how's my", "how good"),
    # build_squad before start_bench so "build me a squad for a bench boost" isn't caught by "bench".
    "build_squad": ("build", "wildcard", "best squad", "best team", "best xi", "new squad",
                    "new team", "pick a squad", "pick a team"),
    "start_bench": ("start", "bench", "lineup", "line-up"),
    # gameweek after the specific intents: a holistic "what should I do this week" routes here, but a
    # pointed "who should I captain this week" still matches captain first (ADR-070). Phrase-based so
    # "this week" only fires the weekly plan, not a stray word.
    "gameweek": ("this week", "this gameweek", "gameweek plan", "gw plan", "weekly plan",
                 "plan for the week", "plan for this week", "what should i do", "what do i do",
                 "recommend my", "recommendation for my"),
    "shortlist": ("goalkeeper", "keeper", "defender", "midfielder", "forward", "striker",
                  "best value", "best players", "differential", "differentials"),
    "compare": ("compare", "versus", " vs ", "better", " or "),
    # fixtures is last: its keywords are distinctive, and "play" is broad, so let every more
    # specific intent match first (ADR-048).
    "fixtures": ("fixture", "schedule", "opponent", "difficulty", "fdr", "play"),
}

_RULES = (
    "Rules: do NOT rank or compare players, do NOT compute or invent any number, do NOT expand "
    "or rename teams (use the codes exactly as written), do NOT merge separate facts, and do NOT "
    "mention anything that is not in the facts."
)

_FALLBACK = (
    "I can answer about captaincy, transfers, your squad's health, your lineup, comparing players, "
    "building a squad, the best players in a position (incl. differentials), or whether a player is "
    'worth the money. Try: ask "who should I captain from <squad>?", ask "best differential '
    'midfielders under £8m", or ask "is Haaland worth the money?".'
)

_NUDGE = (   # a follow-up ("why?", "and the next?") arrived before any question to build on (ADR-047)
    "Ask a question first, then follow up — e.g. \"who should I captain from <squad>?\", "
    'then "why?" or "and the second best?".'
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
    squad: dict | None = None        # a built squad (SquadStore shape) an edge can adopt (ADR-062)


def _squad_name(question: str, known_squads) -> str | None:
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


# --- squad resolution: prefer the session active squad, else the saved SquadStore (Sprint 066) ------
# The web edge loads a squad into the session (build/upload/import, ADR-054/055); `ask` must see it, not
# only the server-side saved squads. So every squad load/list goes through these, given the active squad.

def _load_squad(name, active_squad=None):
    """A squad by name — the **session active squad** wins when its name matches; else `SquadStore`."""
    if active_squad and name and name == active_squad.get("name"):
        return active_squad
    return SquadStore().load(name)


def _known_squad_names(active_squad=None):
    """Saved-squad names + the session active squad's name (so routing resolves "captain <its name>")."""
    names = SquadStore().names()
    if active_squad and active_squad.get("name") and active_squad["name"] not in names:
        return [active_squad["name"], *names]
    return names


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


def _captain_facts(pick: dict) -> dict:
    """Pre-humanised, self-describing facts for one captain pick — nothing to decode."""
    venue = "home against" if pick["venue"] == "H" else "away against"
    return {
        "player": f"{pick['web_name']} ({pick['team']})",
        "expected_points_next_gameweek": pick["xp"],
        "fixture": f"{venue} {pick['opponent']}",
        "is_penalty_taker": pick["penalty_taker"],
    }


def _decide_captain(store: Storage, squad_name: str | None, rank: int = 0, active_squad=None) -> dict | None:
    """Analytics DECIDE the captain (never the LLM); return the decision + humanised facts.

    `rank` (ADR-047) picks the Nth-best (0 = top); past the end returns a soft message so a
    conversational "and the next?" degrades gracefully.
    """
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    history_by_code = store.get_history_by_code()
    baselines = {c: baseline_rate(r) for c, r in history_by_code.items()}
    scope = "all players"
    if squad_name:
        squad = _load_squad(squad_name, active_squad)
        if squad is None:
            return None
        ids = set(squad["player_ids"])
        players = [p for p in players if p["id"] in ids]
        scope = f"squad '{squad_name}'"

    # xMins v0 (ADR-038): `ask` is a decision, so weight xP by expected minutes (default-on).
    picks = captain_picks(
        players, upcoming, baseline_by_code=baselines, limit=max(3, rank + 1),
        minutes_weight=minutes_weight_from_history(history_by_code),
        history_by_code=history_by_code,
    )
    if not picks:
        return None
    if rank >= len(picks):
        return {"message": "That's the last captain option I can rank — nothing more to add."}
    top = picks[rank]
    ordinal = f" #{rank + 1}" if rank else ""
    return {
        "headline": f"Captain pick{ordinal} ({scope}): {top['web_name']} — xP {top['xp']} next GW",
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
    """Pre-humanised facts for one transfer move. The gain is the **XI improvement** (ADR-046) —
    how much the swap lifts your best legal XI, not a raw player-xP delta."""
    return {
        "sell": f"{move['out']['web_name']} ({move['out']['team']}, xP {move['out']['xp']})",
        "buy": f"{move['in']['web_name']} ({move['in']['team']}, xP {move['in']['xp']})",
        "starting_XI_improvement_over_5_gameweeks": move["gain"],
    }


def _plan_facts(plan: list) -> dict:
    """Self-describing facts for a coordinated transfer plan (ADR-035); gains are XI improvements."""
    return {
        "transfers": [
            f"sell {m['out']['web_name']}, buy {m['in']['web_name']} (+{m['gain']} XI xP)"
            for m in plan
        ],
        "total_starting_XI_improvement_over_5_gameweeks": round(sum(m["gain"] for m in plan), 1),
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


def _squad_xp(store: Storage, squad_name: str, active_squad=None, *, horizon=_HORIZON):
    """Shared setup for transfer/analyse/gameweek: the squad's owned rows + xP (+ per-GW) over the horizon.

    xP is weighted by expected minutes (xMins v0, ADR-038) — `ask` is a decision, so default-on. `horizon`
    defaults to `_HORIZON` (5); the web's AI Tips passes the user's *Gameweeks ahead* choice (ADR-077).
    """
    squad = _load_squad(squad_name, active_squad)
    if squad is None:
        return None
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    ranked = decision_xp(players, upcoming, store.get_history_by_code(), horizon=horizon,
                         gw_history_by_code=store.get_gw_history_by_code())   # form: ADR-060, dormant now
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}
    gameweeks = ranked[0]["gameweeks"] if ranked else []
    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    return squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks, weight_by_id


def _decide_transfer(store: Storage, squad_name: str | None, count: int = 1,
                     rank: int = 0, active_squad=None) -> dict | None:
    data = _squad_xp(store, squad_name, active_squad)
    if data is None:
        return None
    squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks, _weight_by_id = data
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
            by_gameweek_by_id=by_gameweek_by_id, gameweeks=gameweeks, show_xmins=True,
        )
        return {
            "detail": detail,                       # the exact table, shown above the narration
            "facts": _plan_facts(plan),
            "subjects": [m["out"]["web_name"] for m in plan]
                        + [m["in"]["web_name"] for m in plan],
            "task": f"summarise this {len(plan)}-transfer plan in 2-3 short sentences",
        }

    moves = suggest_transfers(
        owned, players, xp_by_id, bench_ids=bench_ids, bank=0.0, limit=rank + 1
    )
    if not moves:
        return None
    if rank >= len(moves):
        return {"message": "That's the last positive-gain upgrade I can find — nothing more."}
    m = moves[rank]
    ordinal = f" #{rank + 1}" if rank else ""
    return {
        "headline": f"Transfer{ordinal} (squad '{squad_name}'): {m['out']['web_name']} → "
                    f"{m['in']['web_name']} (+{m['gain']} XI xP over {_HORIZON} GW)",
        "facts": _transfer_facts(m),
        "subjects": [m["out"]["web_name"], m["in"]["web_name"]],
        "task": f"explain in 2 short sentences why selling {m['out']['web_name']} and buying "
                f"{m['in']['web_name']} improves the starting XI",
    }


def _decide_analyse(store: Storage, squad_name: str | None, active_squad=None) -> dict | None:
    data = _squad_xp(store, squad_name, active_squad)
    if data is None:
        return None
    squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks, weight_by_id = data
    if not owned:
        return None
    bench_ids = set(squad.get("bench_ids") or [])
    xi_ids = ({p["id"] for p in owned if p["id"] not in bench_ids} if bench_ids
              else best_legal_xi(owned, xp_by_id))
    # The full squad-analysis table (XI + per-GW xP + weak links) as structured detail (ADR-036) —
    # the same analysis + renderer the `analyse` command uses, so `ask` reads like the command.
    # xP is xMins-weighted (ADR-038); the table shows the expected-minutes column.
    analysis = analyse_squad(
        owned, xi_ids, xp_by_id, horizon=_HORIZON,
        by_gameweek_by_id=by_gameweek_by_id, gameweeks=gameweeks, weight_by_id=weight_by_id,
    )
    detail = render_squad_analysis(analysis, squad_name, show_xmins=True)
    subjects = [w["web_name"] for w in analysis["weakest"]] + \
               [p["web_name"] for p in analysis["issues"]]
    return {
        "detail": detail,                       # the exact table, shown above the narration
        "facts": _analyse_facts(analysis),
        "subjects": subjects,
        "task": "summarise this squad's health in 2-3 short sentences",
    }


def _lineup_change(bring_in: list, drop: list, has_declared_bench: bool) -> str:
    """A one-line lineup verdict: the swap(s), 'already optimal', or 'no saved bench'."""
    if not has_declared_bench:
        return "Change: your squad has no saved bench — this is the best legal XI."
    if not bring_in and not drop:
        return "Change: none — your current XI is already the best legal XI."
    starts = ", ".join(p["web_name"] for p in bring_in)
    benched = ", ".join(p["web_name"] for p in drop)
    return f"Change: start {starts} — bench {benched}."


def _decide_start_bench(store: Storage, squad_name: str | None, active_squad=None) -> dict | None:
    """Analytics DECIDE the lineup (ADR-039): the best legal XI (xMins-weighted) vs the declared one."""
    data = _squad_xp(store, squad_name, active_squad)
    if data is None:
        return None
    squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks, weight_by_id = data
    if not owned:
        return None

    # The best legal XI on xMins-weighted xP — the SAME primitive `analyse` uses, so they agree
    # (ADR-040); the rest are the recommended bench (ADR-038/039).
    optimal_xi = best_legal_xi(owned, xp_by_id)

    declared_bench = set(squad.get("bench_ids") or [])
    declared_xi = {p["id"] for p in owned if p["id"] not in declared_bench} if declared_bench else optimal_xi
    byid = {p["id"]: p for p in owned}
    bring_in = [byid[i] for i in optimal_xi - declared_xi]
    drop = [byid[i] for i in declared_xi - optimal_xi]

    analysis = analyse_squad(owned, optimal_xi, xp_by_id, horizon=_HORIZON, weight_by_id=weight_by_id)
    change = _lineup_change(bring_in, drop, bool(declared_bench))
    detail = render_start_bench(
        analysis["xi"], analysis["bench"], change, squad_name, analysis["projected_xp"],
    )
    return {
        "detail": detail,                       # the recommended XI + bench, shown above the narration
        "facts": {
            "recommendation": change.removeprefix("Change: ").rstrip("."),
            "starting_XI_projected_points_over_5_gameweeks": analysis["projected_xp"],
        },
        # The lineup is about the whole squad, so every owned player may be named in the prose.
        "subjects": [p["web_name"] for p in owned],
        "task": "state the recommended lineup change (or that the XI is already optimal) in 2 short "
                "sentences",
    }


def _gameweek_facts(plan: dict) -> dict:
    """Self-describing facts for a gameweek plan (ADR-070) — every number present so the verifier
    (ADR-037) can trace it, and each field reads plainly so the LLM can't conflate them."""
    cap = plan["captain"]
    captain = ("none — no eligible captain" if not cap else
               f"{cap['web_name']} ({cap['team']}) — xP {cap['xp']} next GW, "
               f"{'home against' if cap['venue'] == 'H' else 'away against'} {cap['opponent']}")

    lu = plan["lineup"]
    if not lu["has_declared_bench"]:
        lineup = "no saved bench — the best legal XI is what's shown"
    elif not lu["bring_in"] and not lu["drop"]:
        lineup = "none — your current XI is already the best legal XI"
    else:
        lineup = (f"start {', '.join(p['web_name'] for p in lu['bring_in'])}; "
                  f"bench {', '.join(p['web_name'] for p in lu['drop'])}")

    tr = plan["transfer"]
    transfer = ("none — no positive-gain upgrade" if not tr else
                f"sell {tr['out']['web_name']} (xP {tr['out']['xp']}), "
                f"buy {tr['in']['web_name']} (xP {tr['in']['xp']}), +{tr['gain']} starting-XI xP")

    flags = ("none" if not plan["flags"] else
             f"{len(plan['flags'])}: " + ", ".join(
                 f"{f['web_name']} ({f['reason']}"
                 f"{'' if f['chance'] is None else f', {f['chance']}%'})"
                 for f in plan["flags"]))

    return {
        "captain": captain,
        "lineup_change": lineup,
        "transfer_to_consider": transfer,
        "flagged_players": flags,
    }


def _decide_gameweek(store: Storage, squad_name: str | None, active_squad=None,
                     *, horizon=_HORIZON) -> dict | None:
    """Analytics DECIDE a one-gameweek plan (ADR-070): captain · lineup · a transfer · flags.

    An assembly of the existing primitives (via `gameweek_plan`), humanised for narration and
    verified — the LLM never decides anything. Reuses `_squad_xp` so the horizon xP is the same the
    transfer/analyse tools use (no drift). `horizon` (ADR-077) drives the lineup/transfer window; the
    captain is always next-GW.
    """
    data = _squad_xp(store, squad_name, active_squad, horizon=horizon)
    if data is None:
        return None
    squad, players, owned, xp_by_id, _by_gw, _gws, _weight = data
    if not owned:
        return None

    history_by_code = store.get_history_by_code()
    baselines = {c: baseline_rate(r) for c, r in history_by_code.items()}
    plan = gameweek_plan(
        owned, players, store.get_upcoming_fixtures(), xp_by_id,
        baseline_by_code=baselines,
        minutes_weight=minutes_weight_from_history(history_by_code),
        history_by_code=history_by_code,
        bench_ids=squad.get("bench_ids") or [],
    )
    cap, tr = plan["captain"], plan["transfer"]
    # subjects = every owned player (the prose may name any starter) + the transfer buy (not owned),
    # so verify_grounding (ADR-037) doesn't flag a legitimately-named player.
    subjects = [p["web_name"] for p in owned] + ([tr["in"]["web_name"]] if tr else [])
    return {
        "detail": render_gameweek_plan(plan, squad_name, horizon=horizon),   # the plan, with/without prose
        "headline": f"This week (squad '{squad_name}'): captain "
                    f"{cap['web_name'] if cap else '—'}",
        "facts": _gameweek_facts(plan),
        "subjects": subjects,
        "task": "give a brief 'this week' recommendation in 3-4 short sentences — who to captain, any "
                "lineup change, one transfer to consider, and any injury/doubt flags — using ONLY the facts",
    }


def _chips_facts(advice: dict) -> dict:
    """Self-describing facts for the chip advice (ADR-082) — every number present so the verifier
    (ADR-037) can trace it, and each field reads plainly so the LLM can't conflate the chips."""
    tc = advice["triple_captain"]
    p = tc["player"]
    triple_captain = (
        f"GW{tc['gameweek']}: "
        + (f"{p['web_name']} ({p['team']})" if p else "no eligible starter")
        + f" — xP {tc['player_xp']} that GW (the squad's highest single-GW ceiling)")

    bb = advice["bench_boost"]
    bench_boost = (f"GW{bb['gameweek']}: all 15 project {bb['squad_total']} xP, "
                   f"of which the bench adds {bb['bench_points']}")

    fh = advice["free_hit"]
    free_hit = (f"GW{fh['gameweek']}: your best XI projects only {fh['xi_total']} xP "
                f"— your weakest single week")

    wc = advice["wildcard"]
    a, b = wc["window"]
    span = f"GW{a}" if a == b else f"GW{a} to GW{b}"
    wildcard = (f"{span}: your weakest stretch (average XI {wc['avg_xi']} xP) — reset before it")

    return {
        "triple_captain": triple_captain,
        "bench_boost": bench_boost,
        "free_hit": free_hit,
        "wildcard": wildcard,
    }


def _decide_chips(store: Storage, squad_name: str | None, active_squad=None,
                  *, horizon=_HORIZON) -> dict | None:
    """Analytics DECIDE when to play each chip (ADR-082): Triple Captain · Bench Boost · Free Hit · Wildcard.

    An assembly of the per-GW xP (`chip_advisor` over `by_gameweek`), humanised for narration and
    verified — the LLM never decides anything. Reuses `_squad_xp` so the horizon xP is the same the
    transfer/analyse/gameweek tools use (no drift). `horizon` (ADR-077) drives the window.
    """
    data = _squad_xp(store, squad_name, active_squad, horizon=horizon)
    if data is None:
        return None
    squad, _players, owned, _xp_by_id, by_gameweek_by_id, gameweeks, _weight = data
    if not owned:
        return None

    advice = chip_advisor(owned, by_gameweek_by_id, gameweeks)
    if advice is None:
        return None
    tc = advice["triple_captain"]
    # subjects = the named TC player (the prose may name them), so verify_grounding (ADR-037) doesn't flag it.
    subjects = [tc["player"]["web_name"]] if tc["player"] else []
    return {
        "detail": render_chip_advice(advice, squad_name, horizon=horizon),
        "headline": f"Chip strategy (squad '{squad_name}'): "
                    f"Triple Captain GW{tc['gameweek']}, Bench Boost GW{advice['bench_boost']['gameweek']}",
        "facts": _chips_facts(advice),
        "subjects": subjects,
        "task": "in 3-4 short sentences, say which gameweek to play each chip (Triple Captain, Bench Boost, "
                "Free Hit, Wildcard) and why, using ONLY the facts; note it sharpens in-season",
    }


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


def _decide_compare(store: Storage, question: str) -> dict | None:
    """Analytics DECIDE the comparison (ADR-039): match the named players, rank by xMins-weighted xP.

    Returns a soft `message` when < 2 players are found or a name is ambiguous — never a silent
    wrong pick. Otherwise a side-by-side detail + facts; the analytics state who's higher, the LLM
    only narrates.
    """
    players = store.get_players()
    matched = _match_players(question, players)

    ambiguous = [wn for wn, ps in matched.items() if len(ps) > 1]
    if ambiguous:
        return {"message": f"More than one player called '{ambiguous[0]}' — name the team too "
                           "(e.g. by club) so I compare the right one."}
    names = list(matched.keys())
    if len(names) < 2:
        found = f" I only recognised {names[0]}." if names else ""
        return {"message": f"Name two players to compare, e.g. ask \"Haaland or Saka?\".{found}"}

    upcoming = store.get_upcoming_fixtures()
    ranked = decision_xp(players, upcoming, store.get_history_by_code(), horizon=_HORIZON,
                         gw_history_by_code=store.get_gw_history_by_code())   # form: ADR-060, dormant now
    by_id = {r["id"]: r for r in ranked}

    rows = []
    for ps in matched.values():
        p = ps[0]
        r = by_id.get(p["id"], {})
        opponent, venue = _next_opponent(p["team_id"], upcoming)
        rows.append({
            **r, "web_name": p["web_name"], "team": p["team"], "position": p["position"],
            "status": p["status"], "chance": p["chance"],
            "opponent": opponent, "venue": venue,
            "penalty_taker": p["penalties_order"] == 1,
        })
    rows.sort(key=lambda r: -r.get("xp", 0))   # analytics decide the order: strongest xP first

    best = rows[0]
    detail = render_compare(rows, horizon=_HORIZON)
    return {
        "detail": detail,
        "facts": {
            "comparison": [
                f"{r['web_name']} ({r['team']}, {r['position']}): xP {r.get('xp', 0)} over "
                f"{_HORIZON} GW, ~{round((r.get('minutes_weight') or 0) * 90)} expected minutes"
                for r in rows
            ],
            "higher_expected_points": f"{best['web_name']} (xP {best.get('xp', 0)})",
        },
        "subjects": [r["web_name"] for r in rows],
        "task": f"in 2 short sentences, say why {best['web_name']} has the higher expected points",
    }


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


def _decide_build_squad(store: Storage, question: str) -> dict | None:
    """Analytics BUILD the squad (ADR-041/043/044/045): the optimal 15 on the unified xP, within
    budget, honouring any requested archetypes (≥N low-cost / ≥M premium / ≥K differential) and the
    bench mode ("for rotation" → a strong XI + playing bench; "for a bench boost" → the max-15)."""
    players = store.get_players()
    if not players:
        return None
    budget = _squad_budget(question)
    cheap, premium, differential = _archetype_counts(question)
    bands = archetype_bands(cheap=cheap, premium=premium)
    constrained = bool(bands) or bool(differential)
    bench_weight, bench_boost = _bench_mode(question)
    upcoming = store.get_upcoming_fixtures()
    ranked = decision_xp(players, upcoming, store.get_history_by_code(), horizon=_HORIZON,
                         gw_history_by_code=store.get_gw_history_by_code())   # form: ADR-060, dormant now
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}
    pool, _excluded = available_players(players)          # exclude injured/suspended (as `squad` does)
    result = select_squad(pool, budget=budget, formation=SQUAD_15, scores=xp_by_id,
                          band_minimums=bands, min_differentials=differential,
                          bench_weight=bench_weight)
    if result["status"] != "Optimal":
        want = (f" with {cheap or 0} low-cost, {premium or 0} premium and {differential or 0} "
                "differential") if constrained else ""
        return {"message": f"No legal squad fits £{budget:.1f}m{want} — try a larger budget or "
                           "fewer constraints."}

    picks = result["selected"]
    for p in picks:   # US-121: show xP + xMins in the squad table (objective xp)
        p["xp"] = xp_by_id.get(p["id"], 0)
        p["minutes_weight"] = weight_by_id.get(p["id"], 1.0)
    top = sorted(picks, key=lambda p: -xp_by_id.get(p["id"], 0))[:3]

    # US-131/132: the XI/bench xP breakout. A bench-aware build (ADR-045) already designated the XI;
    # else derive the best legal XI. Either way, the split is the comparison number.
    xi_ids = ({p["id"] for p in picks if not p["bench"]} if bench_weight is not None
              else best_legal_xi(picks, xp_by_id))
    xi_xp = round(sum(xp_by_id.get(pid, 0) for pid in xi_ids), 1)
    bench_xp = round(sum(xp_by_id.get(p["id"], 0) for p in picks if p["id"] not in xi_ids), 1)

    facts = {
        "budget": f"£{budget:.1f}m",
        "squad_cost": f"£{result['total_cost']:.1f}m",
        "starting_XI_points_over_5_gameweeks": xi_xp,
        "bench_points_over_5_gameweeks": bench_xp,
        "standout_picks": [f"{p['web_name']} ({p['position']}, xP {xp_by_id.get(p['id'], 0)})"
                           for p in top],
    }
    if constrained:
        facts["requested_structure"] = (f"at least {cheap or 0} low-cost, {premium or 0} premium "
                                        f"and {differential or 0} differential players")
    return {
        "detail": render_squad(result, budget=budget, objective="xp", full=True, xi_ids=xi_ids,
                               bench_boost=bench_boost),
        "facts": facts,
        "subjects": [p["web_name"] for p in picks],
        "task": "in 2 short sentences, state the starting XI's projected points and name a couple of "
                "standout picks",
        # ADR-062: the built 15 in SquadStore shape, so a web edge can offer "Use this squad →".
        "squad": {
            "name": "My squad",
            "player_ids": [p["id"] for p in picks],
            "player_names": [p["web_name"] for p in picks],
            "bench_ids": [p["id"] for p in picks if p["id"] not in xi_ids],
            "cost": result["total_cost"],
        },
    }


_POS_WORDS = {"goalkeeper": "GK", "keeper": "GK", "defender": "DEF", "midfielder": "MID",
              "forward": "FWD", "striker": "FWD"}
_SHORTLIST_N = 8   # how many players a shortlist shows


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


def _decide_shortlist(store: Storage, question: str, rank: int = 0) -> dict | None:
    """Analytics rank the best players for a position/price query (ADR-042), on the unified xP.

    `rank` (ADR-047) is a page offset: a conversational "who else?" shows the next `_SHORTLIST_N`.
    """
    players = store.get_players()
    if not players:
        return None
    position, cap, by_value, differential = _shortlist_query(question)
    pool, _excluded = available_players(players)         # exclude injured/suspended
    cands = [p for p in pool
             if (position is None or p["position"] == position)
             and (cap is None or p["price"] <= cap)
             # differential (ADR-061): ≤ DIFFERENTIAL_OWN owned, 0% included (maximally differential)
             and (not differential or (p["selected_by"] or 0) <= DIFFERENTIAL_OWN)]
    if not cands:
        where = f" {position}" if position else ""
        under = f" under £{cap:.1f}m" if cap else ""
        diff = " differential" if differential else ""
        return {"message": f"No available{diff}{where} players{under} — try a higher price cap."}

    ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                         gw_history_by_code=store.get_gw_history_by_code())   # form: ADR-060, dormant now
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}

    def score(p):
        xp = xp_by_id.get(p["id"], 0)
        return xp / p["price"] if by_value and p["price"] else xp

    start = rank * _SHORTLIST_N
    top = sorted(cands, key=score, reverse=True)[start:start + _SHORTLIST_N]
    if not top:
        return {"message": "That's the end of the list — no more players to show."}
    rows = [{**p, "xp": xp_by_id.get(p["id"], 0), "minutes_weight": weight_by_id.get(p["id"], 1.0)}
            for p in top]
    scope = position or "players"
    diff_str = "differential " if differential else ""
    cap_str = f" ≤£{cap:.1f}m" if cap else ""
    metric = "value (xP per £m)" if by_value else "expected points (xP)"
    title = f"Best {diff_str}{scope}{cap_str} — by {metric}"
    if differential:
        title += f"  (≤{DIFFERENTIAL_OWN:.0f}% owned — sharpens at GW1)"
    facts = {
        "ranked_by": "xP per £m" if by_value else "xP over the next 5 GW",
        "top_players": [f"{r['web_name']} ({r['position']}, £{r['price']}m, xP {r['xp']})"
                        for r in rows[:3]],
    }
    if differential:
        facts["filter"] = f"differentials only (≤{DIFFERENTIAL_OWN:.0f}% owned)"
        facts["top_players"] = [
            f"{r['web_name']} ({r['position']}, £{r['price']}m, {r['selected_by']}% owned, xP {r['xp']})"
            for r in rows[:3]]
    return {
        "detail": render_shortlist(rows, title, show_own=differential),
        "facts": facts,
        "subjects": [r["web_name"] for r in rows],
        "task": "in 2 short sentences, summarise these top players (name a couple and why they lead)",
    }


# ---- worth intent (ADR-061) — a single-player value verdict ("is X worth the money?") --------------

_WORTH_GOOD = 1.15   # value ≥ this × the position median → "good value"
_WORTH_FAIR = 0.90   # value ≥ this × median → "fair value"; below → "pricey for the output"


def _value_verdict(ratio: float) -> str:
    """A fact-derived verdict tier from value ÷ the position-median value (ADR-061)."""
    if ratio >= _WORTH_GOOD:
        return "good value"
    if ratio >= _WORTH_FAIR:
        return "fair value"
    return "pricey for the output"


def _decide_worth(store: Storage, question: str) -> dict | None:
    """Analytics DECIDE a single player's value (ADR-061): xP/£m, rank among available same-position
    players, and how it sits vs the position median → a tiered verdict; the LLM only phrases it.

    Degrades to a message on an ambiguous name, no player, or a flagged target — never a guess.
    """
    players = store.get_players()
    if not players:
        return None
    matched = _match_players(question, players)
    ambiguous = [wn for wn, ps in matched.items() if len(ps) > 1]
    if ambiguous:
        return {"message": f"More than one player called '{ambiguous[0]}' — name the team too "
                           "so I value the right one."}
    if not matched:
        return {"message": 'Name a player, e.g. ask "is Haaland worth the money?".'}

    target = next(iter(matched.values()))[0]        # the first named player
    if target["status"] != "a":
        return {"message": f"{target['web_name']} is currently flagged (injured/doubtful), so a value "
                           "verdict wouldn't be meaningful right now."}

    ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                         gw_history_by_code=store.get_gw_history_by_code())   # form: ADR-060, dormant now
    xp_by_id = {r["id"]: r["xp"] for r in ranked}

    def _value(p):
        return xp_by_id.get(p["id"], 0) / p["price"]

    pool, _excluded = available_players(players)
    peers = [p for p in pool if p["position"] == target["position"] and p["price"]]
    ranked_peers = sorted(peers, key=_value, reverse=True)      # highest value per £m first
    median = statistics.median([_value(p) for p in peers]) if peers else 0.0
    tval = xp_by_id.get(target["id"], 0) / target["price"] if target["price"] else 0.0
    rank = next((i for i, p in enumerate(ranked_peers, start=1) if p["id"] == target["id"]), None)
    ratio = tval / median if median else 0.0
    verdict = _value_verdict(ratio)

    pos = target["position"]
    rank_str = f"{rank} of {len(peers)} {pos}s" if rank else f"unranked among {pos}s"
    return {
        "headline": f"{target['web_name']} (£{target['price']}m): {verdict} — {tval:.2f} xP/£m, "
                    f"{rank_str} by value; {pos} median {median:.2f}",
        "facts": {
            "player": f"{target['web_name']} ({target['team']}, {pos}, £{target['price']}m)",
            "expected_points": f"xP {xp_by_id.get(target['id'], 0)} over the next {_HORIZON} GW",
            "value": f"{tval:.2f} xP per £m",
            "position_rank_by_value": rank_str,
            "position_median_value": f"{median:.2f} xP per £m",
            "verdict": verdict,
        },
        "subjects": [target["web_name"]],
        "task": f"in 1-2 short sentences, say whether {target['web_name']} is worth the money, "
                "citing the value and the rank",
    }


# ---- trends intent (Sprint 067, ADR-057) — community "trending" from free FPL crowd data -----------

_TREND_N = 8   # how many players a trending board shows

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


def _decide_trends(store: Storage, question: str) -> dict | None:
    """Rank players by a free crowd metric (ownership / transfers / form) — a community lens, never xP.

    Momentum (in/out/form) is 0 in preseason → a clear "live from GW1" message; ownership works now.
    """
    players = store.get_players()
    if not players:
        return None
    by, position = _trends_query(question)
    pool = [p for p in players if position is None or p["position"] == position]
    rows = trending(pool, by=by, limit=_TREND_N)
    label, header = TREND_BYS[by]

    if by in ("in", "out", "form") and all((r.get("trend") or 0) == 0 for r in rows):
        return {"message": 'No transfer/form data yet — trending lights up at GW1 (2026-08-21). '
                           'Try "most owned" meanwhile.'}

    scope = f"{position} " if position else ""
    return {
        "detail": render_trending(rows, f"Trending — {scope}{label}", header, by=by),
        "facts": {
            "ranked_by": f"{label} (free FPL crowd data)",
            "top": [f"{r['web_name']} ({r['position']}, {header} {r['trend']})" for r in rows[:3]],
        },
        "subjects": [r["web_name"] for r in rows],
        "task": "in 2 short sentences, say who's trending here (name a couple) — it's crowd data, not a prediction",
    }


# ---- fixtures / FDR intent (ADR-048) ----------------------------------------

_FIXTURES_N = 8   # how many teams the league FDR ranking shows
_HARDEST_WORDS = ("hard", "tough", "difficult", "avoid", "worst", "nightmare")
_TEAM_ALIASES = {   # colloquial names the FPL `name` field doesn't carry
    "tottenham": "TOT", "spurs": "TOT", "man united": "MUN", "man utd": "MUN",
    "manchester united": "MUN", "man city": "MCI", "manchester city": "MCI", "forest": "NFO",
}


def _match_team(question: str, teams) -> str | list | None:
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


def _fixture_horizon(question: str) -> int:
    """The N in 'next N' / 'N gameweeks' (ADR-048); default 5, capped to a season."""
    m = re.search(r"next\s+(\d+)", question.lower()) or re.search(
        r"(\d+)\s*(?:game|gw|week|fixture)", question.lower())
    return max(1, min(int(m.group(1)), 38)) if m else 5


def _decide_fixtures(store: Storage, question: str, squad: str | None = None,
                     active_squad=None) -> dict | None:
    """Analytics answer a fixtures question (ADR-048/049): a team's schedule, a saved squad's
    players ranked by their fixture run, or the league FDR ranking.

    Grounded on FPL difficulty; reuses `team_fdr` / `team_schedule` + their renderers. Precedence:
    a specific team named → its schedule; else a saved squad named → the squad-scoped ranking; else
    the league ranking (easiest by default, hardest on a 'hard' cue).
    """
    upcoming = store.get_upcoming_fixtures()
    if not upcoming:
        return None
    horizon = _fixture_horizon(question)
    hardest = any(w in question.lower() for w in _HARDEST_WORDS)
    match = _match_team(question, store.get_teams())

    if isinstance(match, list):                          # two+ teams named → clarify, don't guess
        return {"message": f"More than one team matches — did you mean {', '.join(match)}? "
                           "Please name just one."}

    if not match and squad:                              # a saved squad → its fixture run
        # A "teams"/"by team" cue → the team-level lens (ADR-067); else the per-player view.
        by_team = any(c in question.lower() for c in ("teams", "clubs", "by team", "by club"))
        decide = _decide_squad_team_fixtures if by_team else _decide_squad_fixtures
        return decide(store, squad, upcoming, horizon, hardest, active_squad)

    if match:                                            # a single team → its schedule
        schedule = team_schedule(upcoming, match, source="fpl")[:horizon]
        if not schedule:
            return {"message": f"No upcoming fixtures for {match}."}
        diffs = [f["difficulty"] for f in schedule if f["difficulty"] is not None]
        facts = {
            "team": match,
            "next_fixtures": [
                f"GW{f['event']}: {'home' if f['venue'] == 'H' else 'away'} vs {f['opponent']} "
                f"(difficulty {f['difficulty']})" for f in schedule
            ],
            "average_difficulty": round(sum(diffs) / len(diffs), 1) if diffs else None,
        }
        return {
            "detail": render_team_fixtures(schedule, match, source="fpl"),
            "facts": facts,
            "subjects": [match],
            "task": f"in 2 short sentences, summarise {match}'s next {len(schedule)} fixtures — how "
                    "favourable the run is, naming a couple of opponents",
        }

    # no team, no squad → the league FDR ranking (team_fdr is easiest-first; reverse for hardest)
    ranked = team_fdr(upcoming, next_n=horizon, source="fpl")
    if not ranked:
        return None
    rows = list(reversed(ranked))[:_FIXTURES_N] if hardest else ranked[:_FIXTURES_N]
    which = "hardest" if hardest else "easiest"
    return {
        "detail": render_fdr_table(rows, next_n=horizon, source="fpl", hardest=hardest),
        "facts": {
            "ranking": f"{which} fixtures first, over the next {horizon} gameweeks",
            "teams": [f"{r['team']} (avg difficulty {r['avg_difficulty']}, next: "
                      f"{', '.join(r['opponents'])})" for r in rows[:5]],
        },
        "subjects": [r["team"] for r in rows],
        "task": f"in 2 short sentences, say which teams have the {which} fixtures over the next "
                f"{horizon} gameweeks (name a couple)",
    }


def _decide_squad_fixtures(store: Storage, squad: str, upcoming, horizon: int,
                           hardest: bool, active_squad=None) -> dict | None:
    """A saved squad's players ranked by their team's fixture run (ADR-049): a join (player → its
    team's FDR) + a sort. Grounded per player; easiest by default, hardest on a cue."""
    saved = _load_squad(squad, active_squad)
    if saved is None:
        return None
    by_id = {p["id"]: p for p in store.get_players()}
    owned = [by_id[i] for i in saved["player_ids"] if i in by_id]   # departed ids drop out
    if not owned:
        return {"message": f"Squad '{squad}' has no current players to check."}

    fdr = {r["team"]: r for r in team_fdr(upcoming, next_n=horizon, source="fpl")}
    rows = [
        {"web_name": p["web_name"], "team": p["team"],
         "avg_difficulty": r["avg_difficulty"], "opponents": r["opponents"]}
        for p in owned
        if (r := fdr.get(p["team"])) is not None and r["avg_difficulty"] is not None
    ]
    if not rows:
        return None
    rows.sort(key=lambda x: x["avg_difficulty"], reverse=hardest)
    which = "hardest" if hardest else "easiest"
    return {
        "detail": render_squad_fixtures(rows, squad, next_n=horizon, source="fpl", hardest=hardest),
        "facts": {
            "ranking": f"{squad}'s players by their team's {which} fixture run, next {horizon} GWs",
            "players": [f"{r['web_name']} ({r['team']}, avg difficulty {r['avg_difficulty']}, "
                        f"next: {', '.join(r['opponents'])})" for r in rows[:5]],
        },
        "subjects": [r["web_name"] for r in rows],
        "task": f"in 2 short sentences, say which of {squad}'s players have the {which} fixtures over "
                f"the next {horizon} gameweeks (name a couple, with their opponents)",
    }


def _decide_squad_team_fixtures(store: Storage, squad: str, upcoming, horizon: int,
                                hardest: bool, active_squad=None) -> dict | None:
    """A saved squad's **teams** ranked by their fixture run (ADR-067): group the owned players by team
    (with a player-count) + join `team_fdr` + sort. Grounded per team; easiest by default, hardest on a cue."""
    saved = _load_squad(squad, active_squad)
    if saved is None:
        return None
    by_id = {p["id"]: p for p in store.get_players()}
    owned = [by_id[i] for i in saved["player_ids"] if i in by_id]   # departed ids drop out
    if not owned:
        return {"message": f"Squad '{squad}' has no current players to check."}

    names_by_team: dict = {}
    for p in owned:
        names_by_team.setdefault(p["team"], []).append(p["web_name"])
    fdr = {r["team"]: r for r in team_fdr(upcoming, next_n=horizon, source="fpl")}
    rows = [
        {"team": t, "n": len(names), "players": names,
         "avg_difficulty": r["avg_difficulty"], "opponents": r["opponents"]}
        for t, names in names_by_team.items()
        if (r := fdr.get(t)) is not None and r["avg_difficulty"] is not None
    ]
    if not rows:
        return None
    rows.sort(key=lambda x: x["avg_difficulty"], reverse=hardest)
    which = "hardest" if hardest else "easiest"
    return {
        "detail": render_squad_team_fixtures(rows, squad, next_n=horizon, source="fpl", hardest=hardest),
        "facts": {
            "ranking": f"{squad}'s teams by their {which} fixture run, next {horizon} GWs",
            "teams": [f"{r['team']} ({r['n']} player{'s' if r['n'] != 1 else ''}, avg difficulty "
                      f"{r['avg_difficulty']}, next: {', '.join(r['opponents'])})" for r in rows[:5]],
        },
        "subjects": [r["team"] for r in rows],
        "task": f"in 2 short sentences, say which of {squad}'s teams have the {which} fixtures over the "
                f"next {horizon} gameweeks (name a couple, with their opponents)",
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
    )


def _dispatch(intent: str, store: Storage, question: str, squad: str | None,
              *, count: int = 1, rank: int = 0, active_squad=None, horizon=_HORIZON) -> dict | None:
    """Run the decision engine for `intent` (shared by `answer` and `converse`).

    `count`/`rank` are threaded so a conversational follow-up can ask for an N-transfer plan or
    the Nth-best pick (ADR-047); the intents that don't rank ignore them. `active_squad` is the
    session squad so squad-scoped intents see the loaded team, not only saved squads (Sprint 066).
    `horizon` (ADR-077) is consumed by the gameweek intent; the others keep the `_HORIZON` default.
    """
    if intent == "transfer":
        return _decide_transfer(store, squad, count, rank=rank, active_squad=active_squad)
    if intent == "captain":
        return _decide_captain(store, squad, rank=rank, active_squad=active_squad)
    if intent == "start_bench":
        return _decide_start_bench(store, squad, active_squad=active_squad)
    if intent == "gameweek":
        return _decide_gameweek(store, squad, active_squad=active_squad, horizon=horizon)
    if intent == "chips":
        return _decide_chips(store, squad, active_squad=active_squad, horizon=horizon)
    if intent == "compare":
        return _decide_compare(store, question)
    if intent == "build_squad":
        return _decide_build_squad(store, question)
    if intent == "shortlist":
        return _decide_shortlist(store, question, rank=rank)
    if intent == "worth":
        return _decide_worth(store, question)
    if intent == "trends":
        return _decide_trends(store, question)
    if intent == "fixtures":
        return _decide_fixtures(store, question, squad, active_squad=active_squad)
    return _decide_analyse(store, squad, active_squad=active_squad)


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
           horizon=_HORIZON):
    """A fresh (non-follow-up) question: route → decide → assemble. Returns (result, new_context).

    A successful answer becomes the new context; a fallback/soft-failure leaves the running
    context untouched (so a later "why?" still refers to the last *good* turn). `active_squad` is the
    session squad so "captain <its name>" / "analyse my team" use the loaded team (Sprint 066).
    `horizon` (ADR-077) is threaded to the gameweek intent for the AI Tips view.
    """
    question = _resolve_pronoun(question, context)          # "is he worth it?" → the last player (ADR-080)
    intent, squad = route(question, _known_squad_names(active_squad))
    # "my team" / "my squad" → the loaded session squad (when one is active and no name matched).
    if not squad and active_squad and active_squad.get("name") \
            and re.search(r"\bmy (team|squad|side|xi)\b", question, re.IGNORECASE):
        squad = active_squad["name"]
    if intent is None:
        return assemble(question, None, None, narrator), context
    prompt = _needs_squad(intent, squad)
    if prompt is not None:
        return replace(prompt, question=question), context

    count = _transfer_count(question)
    decision = _dispatch(intent, store, question, squad, count=count, active_squad=active_squad,
                         horizon=horizon)
    known = [p["web_name"] for p in store.get_players()] if decision else ()
    result = assemble(question, intent, decision, narrator, known_names=known)
    new_context = context
    if decision and "facts" in decision:
        new_context = Context(intent=intent, squad=squad, question=question, count=count,
                              rank=0, decision=decision)
    return result, new_context


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
                            "pick here — using ONLY the facts"}
        return assemble(context.question, context.intent, detailed, narrator, known_names=known), context

    if fu.kind == "next":
        if context.intent not in ("captain", "transfer", "shortlist"):
            return None
        nrank = context.rank + 1
        decision = _dispatch(context.intent, store, context.question, context.squad,
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
        decision = _dispatch("shortlist", store, new_q, None)
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
             narrator=llm.narrate, active_squad=None) -> tuple[AskResult, "Context | None"]:
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
    return _fresh(question, context, store, narrator, active_squad)


def answer(question: str, *, store: Storage | None = None, narrator=llm.narrate,
           active_squad=None, horizon=_HORIZON) -> AskResult:
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
        result, _context = _fresh(question, None, store, narrator, active_squad, horizon=horizon)
        return result
    finally:
        if own_store:
            store.close()


_EXIT_WORDS = {"quit", "exit", "q", "bye", "done"}


def chat_transcript(lines, *, store: Storage, narrator=llm.narrate, active_squad=None):
    """Thread a `Context` across `lines`, yielding an AskResult per answered line (ADR-047).

    The pure heart of the `chat` REPL: blank lines are skipped, an exit word stops the session,
    and every other line is a conversational turn whose context carries to the next. Kept free of
    I/O (input/print) so it's unit-tested with a list of lines and a fake narrator.
    """
    context = None
    for line in lines:
        text = line.strip()
        if text.lower() in _EXIT_WORDS:
            return
        if not text:
            continue
        result, context = converse(text, context, store=store, narrator=narrator,
                                   active_squad=active_squad)
        yield result
