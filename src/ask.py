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
    FULL_BUDGET,
    SQUAD_15,
    WEEKLY_BENCH_WEIGHT,
    analyse_squad,
    archetype_bands,
    available_players,
    baseline_rate,
    best_legal_xi,
    captain_picks,
    decision_xp,
    minutes_weight_from_history,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
)
from src.analytics.captain import _next_opponent
from src.squads import SquadStore
from src.storage import Storage
from src.ui.analyse import render_squad_analysis
from src.ui.compare import render_compare
from src.ui.shortlist import render_shortlist
from src.ui.squad import render_squad
from src.ui.startbench import render_start_bench
from src.ui.transfer import render_transfer_plan

_HORIZON = 5   # transfer/analyse are multi-week decisions (captain is next-GW)

# Keyword → intent. Order matters (first match wins); the LLM decides none of this.
_INTENT_KEYWORDS = {
    "captain": ("captain", "armband"),
    "transfer": ("transfer", "sell", "buy", "swap"),
    "analyse": ("analyse", "analyze", "health", "how is my", "how's my", "how good"),
    # build_squad before start_bench so "build me a squad for a bench boost" isn't caught by "bench".
    "build_squad": ("build", "wildcard", "best squad", "best team", "best xi", "new squad",
                    "new team", "pick a squad", "pick a team"),
    "start_bench": ("start", "bench", "lineup", "line-up"),
    "shortlist": ("goalkeeper", "keeper", "defender", "midfielder", "forward", "striker",
                  "best value", "best players"),
    "compare": ("compare", "versus", " vs ", "better", " or "),
}

_RULES = (
    "Rules: do NOT rank or compare players, do NOT compute or invent any number, do NOT expand "
    "or rename teams (use the codes exactly as written), do NOT merge separate facts, and do NOT "
    "mention anything that is not in the facts."
)

_FALLBACK = (
    "I can answer about captaincy, transfers, your squad's health, your lineup, comparing players, "
    'building a squad, or the best players in a position. Try: ask "who should I captain from '
    '<squad>?", ask "build me a squad for £100m", or ask "best midfielders under £8m".'
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
    history_by_code = store.get_history_by_code()
    baselines = {c: baseline_rate(r) for c, r in history_by_code.items()}
    scope = "all players"
    if squad_name:
        squad = SquadStore().load(squad_name)
        if squad is None:
            return None
        ids = set(squad["player_ids"])
        players = [p for p in players if p["id"] in ids]
        scope = f"squad '{squad_name}'"

    # xMins v0 (ADR-038): `ask` is a decision, so weight xP by expected minutes (default-on).
    picks = captain_picks(
        players, upcoming, baseline_by_code=baselines, limit=3,
        minutes_weight=minutes_weight_from_history(history_by_code),
        history_by_code=history_by_code,
    )
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
    """Shared setup for transfer/analyse: the squad's owned rows + xP (+ per-GW) over the horizon.

    xP is weighted by expected minutes (xMins v0, ADR-038) — `ask` is a decision, so default-on.
    """
    squad = SquadStore().load(squad_name)
    if squad is None:
        return None
    players = store.get_players()
    upcoming = store.get_upcoming_fixtures()
    ranked = decision_xp(players, upcoming, store.get_history_by_code(), horizon=_HORIZON)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    by_gameweek_by_id = {r["id"]: r["by_gameweek"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}
    gameweeks = ranked[0]["gameweeks"] if ranked else []
    owned = [p for p in players if p["id"] in set(squad["player_ids"])]
    return squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks, weight_by_id


def _decide_transfer(store: Storage, squad_name: str | None, count: int = 1) -> dict | None:
    data = _squad_xp(store, squad_name)
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


def _decide_start_bench(store: Storage, squad_name: str | None) -> dict | None:
    """Analytics DECIDE the lineup (ADR-039): the best legal XI (xMins-weighted) vs the declared one."""
    data = _squad_xp(store, squad_name)
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
    ranked = decision_xp(players, upcoming, store.get_history_by_code(), horizon=_HORIZON)
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
    ranked = decision_xp(players, upcoming, store.get_history_by_code(), horizon=_HORIZON)
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
    }


_POS_WORDS = {"goalkeeper": "GK", "keeper": "GK", "defender": "DEF", "midfielder": "MID",
              "forward": "FWD", "striker": "FWD"}
_SHORTLIST_N = 8   # how many players a shortlist shows


def _shortlist_query(question: str) -> tuple:
    """(position, price_cap, by_value) from a 'best <position> [under £X]' question (ADR-042)."""
    ql = question.lower()
    position = next((code for word, code in _POS_WORDS.items() if re.search(rf"\b{word}s?\b", ql)),
                    None)
    m = re.search(r"under £?\s*(\d+(?:\.\d+)?)|£\s*(\d+(?:\.\d+)?)", ql)
    cap = float(m.group(1) or m.group(2)) if m else None
    return position, cap, "value" in ql


def _decide_shortlist(store: Storage, question: str) -> dict | None:
    """Analytics rank the best players for a position/price query (ADR-042), on the unified xP."""
    players = store.get_players()
    if not players:
        return None
    position, cap, by_value = _shortlist_query(question)
    pool, _excluded = available_players(players)         # exclude injured/suspended
    cands = [p for p in pool
             if (position is None or p["position"] == position)
             and (cap is None or p["price"] <= cap)]
    if not cands:
        where = f" {position}" if position else ""
        under = f" under £{cap:.1f}m" if cap else ""
        return {"message": f"No available{where} players{under} — try a higher price cap."}

    ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code())
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    weight_by_id = {r["id"]: r["minutes_weight"] for r in ranked}

    def score(p):
        xp = xp_by_id.get(p["id"], 0)
        return xp / p["price"] if by_value and p["price"] else xp

    top = sorted(cands, key=score, reverse=True)[:_SHORTLIST_N]
    rows = [{**p, "xp": xp_by_id.get(p["id"], 0), "minutes_weight": weight_by_id.get(p["id"], 1.0)}
            for p in top]
    scope = position or "players"
    cap_str = f" ≤£{cap:.1f}m" if cap else ""
    metric = "value (xP per £m)" if by_value else "expected points (xP)"
    return {
        "detail": render_shortlist(rows, f"Best {scope}{cap_str} — by {metric}"),
        "facts": {
            "ranked_by": "xP per £m" if by_value else "xP over the next 5 GW",
            "top_players": [f"{r['web_name']} ({r['position']}, £{r['price']}m, xP {r['xp']})"
                            for r in rows[:3]],
        },
        "subjects": [r["web_name"] for r in rows],
        "task": "in 2 short sentences, summarise these top players (name a couple and why they lead)",
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
    )


def answer(question: str, *, store: Storage | None = None, narrator=llm.narrate) -> AskResult:
    """Route → analytics decide → narrate (or degrade). The narrator is injectable/optional."""
    intent, squad_name = route(question)
    if intent is None:
        return assemble(question, None, None, narrator)
    if intent in ("transfer", "analyse", "start_bench") and not squad_name:
        verb = {"transfer": "what transfer", "analyse": "analyse",
                "start_bench": "who should I start"}[intent]
        return AskResult(question, intent,
                         message=f'Name a saved squad, e.g. ask "{verb} for <squad>?"')

    own_store = store is None
    store = store or Storage()
    try:
        if intent == "transfer":
            decision = _decide_transfer(store, squad_name, _transfer_count(question))
        elif intent == "captain":
            decision = _decide_captain(store, squad_name)
        elif intent == "start_bench":
            decision = _decide_start_bench(store, squad_name)
        elif intent == "compare":
            decision = _decide_compare(store, question)
        elif intent == "build_squad":
            decision = _decide_build_squad(store, question)
        elif intent == "shortlist":
            decision = _decide_shortlist(store, question)
        else:
            decision = _decide_analyse(store, squad_name)
        # The known player names for the verifier's name check (ADR-037).
        known_names = [p["web_name"] for p in store.get_players()] if decision else ()
    finally:
        if own_store:
            store.close()

    return assemble(question, intent, decision, narrator, known_names=known_names)
