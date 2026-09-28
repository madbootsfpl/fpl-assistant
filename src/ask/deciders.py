"""One function per intent: store in, decision out. **The engine.**

⭐ `_dispatch` at the foot is the whole table — intent to decider, and the only place that mapping exists.
Everything here calls the analytics; nothing here talks to the narrator or to the screen.

⚠️ **Reached as a module, not by name, where a test fakes it.** `_dispatch`, `_squad_xp` and the analytics
this layer imports are all faked in the suite; binding them into a caller's globals would give each one as
many patch points as it has importers (ADR-325).
"""

import statistics
from datetime import UTC, datetime

from src.analytics import (
    DIFFERENTIAL_OWN,
    PRICE_DOWN,
    PRICE_UP,
    SQUAD_15,
    TREND_BYS,
    analyse_squad,
    archetype_bands,
    available_players,
    baseline_rate,
    best_legal_xi,
    captain_picks,
    chip_advisor,
    decision_xp,
    explain_captain,
    explain_chips,
    explain_gameweek,
    explain_squad,
    explain_transfer,
    explain_worth,
    gameweek_plan,
    is_unavailable,
    minutes_weight_from_history,
    player_history,
    price_detector,
    price_pressure,
    rebuild_value,
    select_squad,
    suggest_transfer_plan,
    suggest_transfers,
    team_fdr,
    team_schedule,
    trending,
)
from src.analytics.captain import _next_opponent
from src.analytics.crowd import exodus_detector
from src.analytics.headlines import leavers
from src.ask.defaults import _HORIZON
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
    _archetype_counts,
    _bench_mode,
    _chip_named,
    _looks_like_a_comparison,
    _match_players,
    _named_gameweek,
    _named_in,
    _shortlist_query,
    _squad_budget,
    _trends_query,
    captain_lens,
    chip_lens,
    fixture_horizon,
    match_team,
    scope_label,
)
from src.fpl_rules import CHIP_NAMES, chip_deadline, match_rules
from src.squads import SquadStore
from src.storage import Storage
from src.ui.analyse import render_squad_analysis
from src.ui.captain import render_captain_pick
from src.ui.chips import render_chip_advice
from src.ui.compare import render_compare
from src.ui.explain import MODEL_NOTE, render_explanation
from src.ui.fdr import render_fdr_table
from src.ui.fixtures import render_squad_fixtures, render_squad_team_fixtures, render_team_fixtures
from src.ui.gameweek import render_gameweek_plan
from src.ui.history import render_player_history
from src.ui.price import render_price_movers
from src.ui.rules import render_rules
from src.ui.shortlist import render_shortlist
from src.ui.squad import render_squad
from src.ui.startbench import render_start_bench
from src.ui.transfer import render_transfer_plan
from src.ui.trending import render_trending

# ⚠️⚠️ **Defined here, not in `defaults`, and that placement is load-bearing for a guard** (ADR-325).
# Only the deciders use it — and `tests/test_tiebreak_wiring.py` resolves `**_TIE_BREAK` by finding
# where the name is defined **in the same file**. Moving it one module away turned that guard into four
# false positives. ⭐ *Its own docstring warned about this — "a guard that follows only the indirection
# you happened to write is a guard against yourself"* — so the constant lives beside its only caller.

# ⭐ **Stated rather than defaulted (ADR-209/220).** `ask` always ranks over `_HORIZON`, which is already the
# window the tie-break band was sized against — so this changes nothing today. ⚠️ *That is exactly why it is
# worth writing down*: the band's default silently matches only while the horizon stays 5, and the next
# person to make this configurable would inherit a mismatch with nothing to warn them.
# `horizon_xp` is None because the ranking window **is** the wider one — there is no longer view to consult.
_TIE_BREAK = {"window": _HORIZON, "horizon_xp": None}

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


def _lens_pick(picks: list, lens: str | None, owned_by: dict) -> tuple[int, str | None]:
    """The index the lens selects, and a note when the lens could not be honoured.

    ⚠️⚠️ **A note, never a redirect.** The owner's rule: *"if they use Ask they will want the answer from
    there and not to be directed somewhere else to find it."* ⭐ So when a lens cannot be applied the
    answer still carries the pick it *can* stand behind, and says plainly which question it answered.
    """
    if not lens:
        return 0, None
    if lens == "vice":
        # ⭐ The engine has always been able to do this — `rank` is an existing parameter. Only the word
        # was unrecognised, which is why this was the cheapest fix on the whole list.
        if len(picks) < 2:
            return 0, ("There is only one player I can rank as captain in this squad, so I cannot "
                       "separate a vice from him.")
        return 1, None
    if lens == "safest":
        # ⚠️ Safest is **expected minutes**, not expected points. ⭐ *A captain who does not play is the
        # only captaincy outcome that cannot be recovered from*, which is what "safe" means here — and
        # xP is the tie-break rather than the criterion.
        order = sorted(
            range(len(picks)),
            key=lambda i: (not picks[i].get("doubtful", False),
                           picks[i].get("minutes_weight") or 0.0,
                           picks[i].get("xp") or 0.0),
            reverse=True,
        )
        return order[0], None
    if lens == "differential":
        owned = [(i, owned_by.get(picks[i]["id"])) for i in range(len(picks))]
        known = [(i, o) for i, o in owned if o is not None]
        if not known:
            return 0, ("I do not have ownership for these players, so I cannot tell you which is the "
                       "differential — this is the highest-scoring captain instead.")
        # ⭐ Least-owned first, xP as the tie-break: *a differential is a bet on other people not having
        # him*, so ownership is the criterion and points decide between equals.
        known.sort(key=lambda pair: (pair[1], -(picks[pair[0]].get("xp") or 0.0)))
        return known[0][0], None
    if lens == "rotation":
        # ⭐ The question is about **the pick**, not a different pick: *"is my captain at rotation risk?"*
        # wants the same man, described honestly.
        return 0, None
    return 0, None


def _captain_versus(picks: list, named: list, players, scope: str, team_names: dict) -> dict:
    """Two named players, compared as captains.

    ⚠️⚠️ **Both may be outside the shortlist**, and that is itself the answer: a player the captaincy
    engine did not rank is a player it does not think you should captain. ⭐ *Saying "he is not in your
    top options" is more useful than silently substituting somebody who is.*
    """
    ranked = {p["id"]: (i, p) for i, p in enumerate(picks)}
    lines, best, best_xp = [], None, None
    for row in named[:2]:
        place = ranked.get(row["id"])
        if place is None:
            lines.append(f"{row['web_name']} ({row['team']}) — not among the captain options I can rank "
                         f"for this squad")
            continue
        index, pick = place
        lines.append(f"{pick['web_name']} ({pick['team']}) — xP {pick['xp']}, "
                     f"{_minutes_phrase(pick)}, #{index + 1} of my captain options")
        if best_xp is None or (pick["xp"] or 0) > best_xp:
            best, best_xp = pick, pick["xp"] or 0

    if best is None:
        # ⭐ Still an answer, and still from here — the owner's rule: *if they use Ask they want the
        # answer from Ask, not to be sent somewhere else to find it.*
        top = picks[0]
        return {
            "headline": (f"Neither is among the captain options I can rank ({scope}). "
                         f"My pick is {top['web_name']} — xP {top['xp']} next GW."),
            "detail": "\n".join(lines),
            "facts": _captain_facts(top),
            "subjects": [top["web_name"]],
            # ⚠️⚠️⚠️ **`task` is not optional — omitting it is a 500, not a missing sentence.**
            # `_build_prompt` reads `decision['task']` with a hard subscript, and it is evaluated as the
            # **argument** to `narrator(...)`, so it runs even where the narrator is silenced — which is
            # every request the API serves. ⭐ *A field only the optional half consumes still has to be
            # there, because the call that discards it is made after the one that builds it.*
            "task": f"in 2-3 short sentences, say why {top['web_name']} is your captain pick, noting that "
                    "neither player asked about is among the ranked options",
        }
    return {
        "headline": f"Better captain ({scope}): {best['web_name']} — xP {best['xp']} next GW",
        "detail": "\n".join(lines),
        "facts": _captain_facts(best, "rotation"),
        "subjects": [best["web_name"]],
        "task": f"in 2-3 short sentences, say why {best['web_name']} is the better captain of the two, "
                "using ONLY the facts",
    }


def _decide_captain(store: Storage, squad_name: str | None, rank: int = 0, active_squad=None,
                    lens: str | None = None, question: str | None = None) -> dict | None:
    """Analytics DECIDE the captain (never the LLM); return the decision + humanised facts.

    `rank` (ADR-047) picks the Nth-best (0 = top); past the end returns a soft message so a
    conversational "and the next?" degrades gracefully.
    """
    players = store.get_players()
    # ⚠️⚠️ **Names resolve against the whole market, never against the squad.** Asking *"is Salah a better
    # captain than Haaland?"* with Salah unowned found **one** name, fell through to the ordinary path,
    # and answered *"Captain pick: Haaland"* — ⭐ *silently dropping the player the question was about*,
    # which is the failure this ADR exists to stop and which it had just reintroduced one function along.
    market = players
    upcoming = store.get_upcoming_fixtures()
    history_by_code = store.get_history_by_code()
    baselines = {c: baseline_rate(r) for c, r in history_by_code.items()}
    team_names = {t["short_name"]: t["name"] for t in store.get_teams()}   # "MUN" → "Man Utd" (US-277)
    scope = "all players"
    if squad_name:
        squad = _load_squad(squad_name, active_squad)
        if squad is None:
            return None
        ids = set(squad["player_ids"])
        players = [p for p in players if p["id"] in ids]
        scope = scope_label(squad_name)

    # xMins v0 (ADR-038): `ask` is a decision, so weight xP by expected minutes (default-on).
    picks = captain_picks(
        # ⚠️ A lens has to see the whole shortlist, not the top three: the safest or least-owned captain
        # is routinely outside them. ⭐ *A filter applied to a truncated list is a filter that answers
        # about the truncation.*
        players, upcoming, baseline_by_code=baselines,
        limit=max(3, rank + 1) if not lens else 15,
        minutes_weight=minutes_weight_from_history(history_by_code, store.get_gw_history_by_code()),
        history_by_code=history_by_code,
    )
    if not picks:
        return None
    if rank >= len(picks):
        return {"message": "That's the last captain option I can rank — nothing more to add."}

    # ⭐⭐ **The lens chooses which of the shortlist answers the question actually asked** (ADR-308).
    # ⚠️ It moves `rank`, so everything downstream — the explanation, the card, the runner-up — is about
    # the player the reader asked about rather than the one the engine happened to rank first.
    owned_by = {p["id"]: p["selected_by"] for p in players} if lens == "differential" else {}

    # ⭐⭐ **Named players win over every other lens** (ADR-308). *"Is Haaland a better captain than
    # Salah?"* is a question about two men, and answering it with whoever the engine ranked first is the
    # most confident way to ignore somebody. ⚠️ Resolved with the **same index the buzz counter uses**
    # (ADR-152), so a bare "Palmer" is not credited to two players.
    named = _named_in(question, market) if question else []
    if len(named) >= 2:
        return _captain_versus(picks, named, market, scope, team_names)

    # ⚠️⚠️⚠️ **A comparison with a name I could not resolve must say so.** *"Is Mbappé a better captain
    # than Haaland?"* resolves one name, falls through here, and would answer *"Captain pick: Haaland"* —
    # ⭐ *which is a correct sentence and a dishonest answer*, because it silently drops the half of the
    # question the reader was actually asking about.
    #
    # ⭐⭐ **It still answers.** The owner's rule: *"if they use Ask they will want the answer from there
    # and not to be directed somewhere else to find it."* So the pick comes with the note, in one reply.
    unresolved = _looks_like_a_comparison(question) and len(named) < 2 if question else False

    if lens:
        rank, note = _lens_pick(picks, lens, owned_by)
    else:
        note = None
    if unresolved:
        known = f" I did recognise {named[0]['web_name']}." if named else ""
        note = ("I could not place one of those players — check the spelling, or he may not be in the "
                f"game this season.{known}")

    top = picks[rank]
    ordinal = f" #{rank + 1}" if rank and not lens else ""
    # Explainability (ADR-089): grounded Why/Risk/Confidence for the chosen pick — the slice makes it [0]
    # and the next-best the runner-up (for the "narrow lead" risk).
    explanation = explain_captain(picks[rank:], {p["id"]: p for p in players})
    facts = _captain_facts(top, lens)
    if explanation is not None:
        facts["confidence"] = f"{explanation.confidence}/100 ({explanation.band})"
        facts["why"] = "; ".join(explanation.reasons) or "none"
        facts["risk"] = "; ".join(explanation.risks) or "none noted"
    # The structured Captain Pick card (US-277): medal · Team·Pos · Projected · Confidence · Why · Risks ·
    # Alternatives · Model note. Global vs scoped read differently (US-280): "Best Captain Picks — all players"
    # (with a nudge on how to scope) vs "Captain Pick — from squad 'X'". A "next" follow-up (rank>0) is flagged.
    is_global = squad_name is None
    scope_bits = [f"Option #{rank + 1}"] if rank else []
    scope_bits.append(scope if is_global else f"from {scope}")    # "all players" | "from squad 'X'"
    heading = "Best Captain Picks" if is_global else "Captain Pick"
    nudge = ('Showing all players — say "captain from my team" (with a squad loaded) to scope to your squad.'
             if is_global else "")
    detail = render_captain_pick(picks[rank:], explanation, scope=" · ".join(scope_bits),
                                 team_names=team_names, heading=heading, nudge=nudge)
    return {
        "detail": detail,   # shown with or without prose (the block is the truth)
        # ⭐⭐ **The headline names the question it answered**, so a reader can see at a glance whether the
        # qualifier landed — ⚠️ *the failure this fixes was invisible precisely because the answer looked
        # identical whichever of the five was asked.*
        "headline": (f"{_LENS_HEADING.get(lens, 'Captain pick')}{ordinal} ({scope}): "
                     f"{top['web_name']} — xP {top['xp']} next GW"
                     + (f" · {note}" if note else "")),
        "facts": facts,
        "subjects": [top["web_name"]],
        "task": f"explain in 2-3 short sentences why {top['web_name']} is a good captain pick this gameweek, "
                "reflecting the confidence and the ✓ reasons / ⚠ risks — using ONLY the facts",
    }


#: How each lens names itself. ⭐ *A heading that repeats the question is a heading that proves it was
#: heard* — and it is the only part of the answer a reader checks before trusting the rest.
_LENS_HEADING: dict[str | None, str] = {
    None: "Captain pick",
    "vice": "Vice-captain",
    "safest": "Safest captain",
    "differential": "Differential captain",
    "rotation": "Captain, and his minutes",
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
    # ADR-156 — the transfer ranking values a reported leaver at zero, like the lineup does (ADR-154).
    reported_out = leavers(owned, store.headline_events_by_id(), exodus_detector(players),
                           today=datetime.now(UTC).date())

    if count > 1:
        # A coordinated N-transfer plan (ADR-035), with a per-GW table as structured detail (ADR-036).
        plan = suggest_transfer_plan(
            owned, players, xp_by_id, bench_ids=bench_ids, bank=0.0, count=count,
            reported_out=reported_out, **_TIE_BREAK,
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
        owned, players, xp_by_id, bench_ids=bench_ids, bank=0.0, limit=rank + 1,
        reported_out=reported_out, **_TIE_BREAK,
    )
    if not moves:
        return None
    if rank >= len(moves):
        return {"message": "That's the last positive-gain upgrade I can find — nothing more."}
    m = moves[rank]
    ordinal = f" #{rank + 1}" if rank else ""
    # Explainability (ADR-089): grounded Why/Risk/Confidence for the swap, from the buy's full row.
    explanation = explain_transfer(m, {p["id"]: p for p in players}.get(m["in"]["id"], {}), horizon=_HORIZON)
    facts = _transfer_facts(m)
    if explanation is not None:
        facts["confidence"] = f"{explanation.confidence}/100 ({explanation.band})"
        facts["why"] = "; ".join(explanation.reasons) or "none"
        facts["risk"] = "; ".join(explanation.risks) or "none noted"
    detail = "\n".join([f"Transfer{ordinal} ({scope_label(squad_name)}): {m['out']['web_name']} → "
                        f"{m['in']['web_name']}", "", render_explanation(explanation), "", MODEL_NOTE])
    return {
        "detail": detail,   # self-contained Why/Risk/Confidence block (the truth, LLM or not)
        "headline": f"Transfer{ordinal} ({scope_label(squad_name)}): {m['out']['web_name']} → "
                    f"{m['in']['web_name']} (+{m['gain']} XI xP over {_HORIZON} GW)",
        "facts": facts,
        "subjects": [m["out"]["web_name"], m["in"]["web_name"]],
        "task": f"explain in 2-3 short sentences why selling {m['out']['web_name']} and buying "
                f"{m['in']['web_name']} improves the XI, reflecting the confidence + ✓ reasons / ⚠ risks "
                "— using ONLY the facts",
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


def decide_gameweek(store: Storage, squad_name: str | None, active_squad=None,
                     *, horizon=_HORIZON, question=None, free: int = 1, bank: float = 0.0) -> dict | None:
    """Analytics DECIDE a one-gameweek plan (ADR-070): captain · lineup · a transfer · flags.

    An assembly of the existing primitives (via `gameweek_plan`), humanised for narration and
    verified — the LLM never decides anything. Reuses `_squad_xp` so the horizon xP is the same the
    transfer/analyse tools use (no drift). `horizon` (ADR-077) drives the lineup/transfer window; the
    captain is always next-GW.
    """
    data = _squad_xp(store, squad_name, active_squad, horizon=horizon)
    if data is None:
        return None
    squad, players, owned, xp_by_id, _by_gw, gws, _weight = data
    if not owned:
        return None

    history_by_code = store.get_history_by_code()
    baselines = {c: baseline_rate(r) for c, r in history_by_code.items()}
    # ADR-153 — the headlines read at refresh (ADR-151). Empty on a snapshot built without a model, in which
    # case the plan reads exactly as it did before.
    events_by_id = store.headline_events_by_id()
    # ADR-173 — the same squad priced over a wider window, so the plan can say what a swap is worth beyond
    # next week. Deliberately the *same players* re-priced rather than a second search: re-running the search
    # could name a different move, and then the two numbers would be answering different questions.
    _WIDE = 5
    wide = _squad_xp(store, squad_name, active_squad, horizon=_WIDE) if horizon < _WIDE else None
    horizon_xp = wide[3] if wide else None

    plan = gameweek_plan(
        owned, players, store.get_upcoming_fixtures(), xp_by_id,
        baseline_by_code=baselines,
        minutes_weight=minutes_weight_from_history(history_by_code, store.get_gw_history_by_code()),
        history_by_code=history_by_code,
        bench_ids=squad.get("bench_ids") or [],
        events_by_id=events_by_id,
        horizon_xp=horizon_xp,
        # ADR-210 — bound to the whole board (`players`), not the fifteen the plan is about.
        exodus_for=exodus_detector(players),
        # ADR-191 — the manager's ACTUAL position, not a default. `free` decides how many moves the week's
        # answer recommends; `bank` decides what they can afford and whether ADR-186's cliff is real.
        # Both had been hard-coded here (1 and £0.0m) while the Transfer tab collected them three tabs away,
        # so the surface a manager reads was advising a position he was not in.
        free=free, bank=bank,
    )
    plan["horizon_gw"] = _WIDE
    cap, tr = plan["captain"], plan["transfer"]
    # Explainability (ADR-089): per-recommendation Why/Confidence (captain + transfer reused) + an overall read.
    explanation = explain_gameweek(plan, {p["id"]: p for p in players}, xp_by_id, horizon=horizon)
    facts = _gameweek_facts(plan)
    overall = explanation["overall"] if explanation else None
    if overall is not None:   # the plan-level confidence + why/risk in the facts, so narration verifies (US-274)
        facts["confidence"] = f"{overall.confidence}/100 ({overall.band})"
        facts["why"] = "; ".join(overall.reasons)
        facts["risk"] = "; ".join(overall.risks)
    # subjects = every owned player (the prose may name any starter) + the transfer buy (not owned) + any
    # dead-slot replacement (ADR-136, also not owned), so verify_grounding (ADR-037) doesn't flag a
    # legitimately-named player. Miss one and the answer carries a false "⚠ Unverified" against a name the
    # analytics themselves chose — which undermines the verifier exactly where it should be trusted.
    subjects = ([p["web_name"] for p in owned]
                + ([tr["in"]["web_name"]] if tr else [])
                + [r["in"]["web_name"] for r in (plan.get("replacements") or [])])
    # If the question named a gameweek that is not the one being planned, say so *before* the plan rather
    # than letting a "This week" header quietly answer a different question (see `_named_gameweek`).
    named, planned = _named_gameweek(question), (gws[0] if gws else None)
    scope = None
    if named is not None and planned is not None and named != planned:
        scope = (f"Note: you asked about GW{named}, but this plans **GW{planned}** — the weekly plan always "
                 f"covers the next gameweek. For chip timing further out, ask \"which chip should I use?\".")
        facts = {"scope": scope, **facts}

    detail = render_gameweek_plan(plan, squad_name, horizon=horizon, explanation=explanation)
    return {
        # ADR-174 — the plan travels with the rendered text, so an edge that offers "apply this transfer"
        # applies **the move on screen**. Recomputing it at the surface would be a second search that could
        # legitimately return something else, and then the button and the sentence above it would disagree.
        "plan": plan,
        "detail": f"{scope}\n\n{detail}" if scope else detail,
        "headline": f"This week ({scope_label(squad_name)}): captain "
                    f"{cap['web_name'] if cap else '—'}",
        "facts": facts,
        "subjects": subjects,
        "task": "give a brief 'this week' recommendation in 3-4 short sentences — who to captain, any "
                "lineup change, one transfer to consider, and any injury/doubt flags — using ONLY the facts",
    }


def price_a_rebuild(owned, players, xp_by_id, squad):
    """`rebuild_value` for this squad, or **None** when it cannot be priced (ADR-185).

    The budget a wildcard has is the squad's selling value plus the bank. A player row without a `price` —
    a hand-built fixture, a partial snapshot — makes that unanswerable, and the right response is to skip
    the valuation rather than fail the whole chip answer: `chip_advisor` treats `rebuild=None` as "say only
    when", which is exactly the advice that shipped before this ADR. **The enhancement degrades; the answer
    does not.**
    """
    try:
        budget = round(sum(p["price"] for p in owned) + (squad.get("bank") or 0.0), 1)
    except (KeyError, IndexError, TypeError):
        return None
    return rebuild_value(owned, players, xp_by_id, budget=budget)


def _chip_state_answer(chip_status, squad_name: str, lens: str, question: str) -> dict:
    """The two questions that are **facts about your season**, not recommendations (ADR-317 A).

    ⚠️⚠️ **Without a manager id there is no honest answer here**, and the engine says so rather than
    guessing — ⭐ *this is the one place where "I do not know" is the whole truth, and inventing a chip list
    would be the worst failure this file could have.*
    """
    known = chip_status and any(v.get("available") is not None for v in chip_status.values())
    if not known:
        return {"message": ("I cannot see which chips you have played — that needs your FPL manager id. "
                            "Ask me *which chip should I use?* and I will still tell you when each is best.")}

    played = [(CHIP_NAMES[k], v["played_in"]) for k, v in chip_status.items() if v.get("played_in")]
    held = [CHIP_NAMES[k] for k, v in chip_status.items() if v.get("available")]

    # ⭐⭐ **Naming a chip asks a yes/no, whichever way the question was phrased.** *"Have I used my
    # wildcard?"* reads as a `played` question and wants one word, not a list of four — ⚠️ *the lens says
    # what kind of question it is; the named chip says how narrow the answer should be.*
    named = _chip_named(question)
    if named:
        state = chip_status.get(named) or {}
        gone = state.get("played_in")
        # ⭐ The answer first, then the evidence — *a yes/no question answered with a paragraph has not
        # been answered.*
        head = (f"No — you played your {CHIP_NAMES[named]} in GW{gone}."
                if gone else f"Yes — your {CHIP_NAMES[named]} is still available.")
        return {
            "headline": f"{head} ({squad_name})",
            "detail": _chip_state_detail(played, held),
            "facts": {"chip": CHIP_NAMES[named],
                      "available": "no" if gone else "yes",
                      "played_in": f"GW{gone}" if gone else "not played"},
            "subjects": [],
            "task": f"answer in one short sentence whether the {CHIP_NAMES[named]} is still available, "
                    "using ONLY the facts",
        }

    # ⭐ `played`, or a `holding` question that named no chip — both want the same list.
    head = (", ".join(f"{name} (GW{gw})" for name, gw in played) if played
            else "none yet — all four are still in hand")
    return {
        "headline": f"Chips played ({squad_name}): {head}",
        "detail": _chip_state_detail(played, held),
        "facts": {"played": head, "still_available": ", ".join(held) or "none"},
        "subjects": [],
        "task": "say in one short sentence which chips are gone and which are left, using ONLY the facts",
    }


def _chip_state_detail(played, held) -> str:
    lines = ["Your chips", ""]
    if played:
        lines.append("  Played:     " + ", ".join(f"{n} (GW{g})" for n, g in played))
    else:
        lines.append("  Played:     none yet")
    lines += [f"  Still have: {', '.join(held)}"] if held else ["  Still have: none"]
    # ⚠️ Availability is per HALF, not per season (ADR-234) — a wildcard spent in GW4 leaves the
    # second-half one untouched, and a reader who does not know that reads "played" as "gone for good".
    lines += ["", "  Chips reset at the halfway point, so a chip used in the first half does not",
              "  spend the second half's."]
    return "\n".join(lines)


def _decide_chips(store: Storage, squad_name: str | None, active_squad=None,
                  *, horizon=_HORIZON, chip_status=None, lens=None, question="") -> dict | None:
    """Analytics DECIDE when to play each chip (ADR-082): Triple Captain · Bench Boost · Free Hit · Wildcard.

    An assembly of the per-GW xP (`chip_advisor` over `by_gameweek`), humanised for narration and
    verified — the LLM never decides anything. Reuses `_squad_xp` so the horizon xP is the same the
    transfer/analyse/gameweek tools use (no drift). `horizon` (ADR-077) drives the window.
    """
    # ⭐⭐ **A question about your season, not about the fixtures** (ADR-317 A). *"What have I played?"* and
    # *"can I still play X?"* are answered from the chip status alone — ⚠️ *running a five-gameweek
    # optimisation to answer "yes" is how four questions came to share one answer.*
    if lens in {"played", "holding"}:
        return _chip_state_answer(chip_status, squad_name or "yours", lens, question)

    data = _squad_xp(store, squad_name, active_squad, horizon=horizon)
    if data is None:
        return None
    squad, players, owned, xp_by_id, by_gameweek_by_id, gameweeks, _weight = data
    if not owned:
        return None

    # ADR-185 — price the rebuild, so the wildcard can answer *whether* and not only *when*. The budget is
    # what this squad is actually worth: its selling value plus the bank, which is what a wildcard has to
    # spend. One extra solve (~0.08s, ADR-183).
    rebuild = price_a_rebuild(owned, players, xp_by_id, squad)
    advice = chip_advisor(owned, by_gameweek_by_id, gameweeks, rebuild=rebuild)
    if advice is None:
        return None
    confidences = explain_chips(advice)   # a per-chip confidence (ADR-089) — Low preseason (near-flat weeks)
    tc = advice["triple_captain"]
    # subjects = the named TC player (the prose may name them), so verify_grounding (ADR-037) doesn't flag it.
    subjects = [tc["player"]["web_name"]] if tc["player"] else []
    facts = _chips_facts(advice)
    facts["confidence"] = "; ".join(f"{c.replace('_', ' ')} {v['confidence']}/100 ({v['band']})"
                                    for c, v in confidences.items())
    # ⭐⭐ **"Before they expire" is the same recommendation over a shorter list**, so it changes the
    # heading and not the arithmetic — ⚠️ *a lens that recomputed the answer would be a second engine, and
    # two engines for one question is how a number starts disagreeing with itself.*
    expiry_note, expiry_lead = "", ""
    if lens == "expiry":
        last = chip_deadline(gameweeks[0] if gameweeks else None)
        held = [CHIP_NAMES[k] for k, v in (chip_status or {}).items() if v.get("available")]
        expiry_note = (f" — {', '.join(held)} expire after GW{last}" if held
                       else f" — this half's chips expire after GW{last}")
        # ⚠️⚠️ **The heading is not the answer.** A lens that changed only the headline left the body
        # identical to the plain strategy question — ⭐ *which is the complaint this ADR exists for, made
        # by my own fix.* The deadline and what is still in hand belong in the block a reader reads.
        expiry_lead = (
            f"Expiring after GW{last}: {', '.join(held)}\n\n" if held
            else f"Nothing left to use — this half's chips expire after GW{last}.\n\n"
        )

    return {
        "detail": expiry_lead + render_chip_advice(advice, squad_name, horizon=horizon,
                                                   confidences=confidences, status=chip_status),
        "headline": f"Chip strategy ({scope_label(squad_name)}){expiry_note}: "
                    f"Triple Captain GW{tc['gameweek']}, Bench Boost GW{advice['bench_boost']['gameweek']}",
        "facts": facts,
        "subjects": subjects,
        "task": "in 3-4 short sentences, say which gameweek to play each chip (Triple Captain, Bench Boost, "
                "Free Hit, Wildcard) and why, using ONLY the facts; note it sharpens in-season",
    }


def _decide_rules(question: str) -> dict | None:
    """Analytics-free but GROUNDED: answer an FPL-rules question from the curated KB (ADR-085).

    `match_rules` selects the authoritative facts the question is about; the LLM narrates ONLY those and is
    verified (✓, ADR-037) — it never sources rules from its own memory. A rules-shaped question that matches
    no specific topic gets a "here's what I can explain" message (US-260 replaces this with a free-form
    answer). Not squad-scoped."""
    matched = match_rules(question)
    if not matched:
        # a rules-shaped question we have no curated fact for → the labelled free-form tail (US-260)
        return {"free_form": True, "question": question}
    return {
        "detail": render_rules(matched),                       # the curated facts — the truth, LLM or not
        "facts": {topic: fact for topic, fact in matched},
        "subjects": [],
        "task": "answer the user's FPL rules question in 2-4 short sentences using ONLY these official rules "
                "facts; do not state any rule that isn't given here",
    }


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
    # Explainability (ADR-089): grounded Why/Risk/Confidence for the build, above the squad table.
    explanation = explain_squad(picks, xp_by_id, weight_by_id, budget=budget, xi_ids=xi_ids, horizon=_HORIZON)
    if explanation is not None:
        facts["confidence"] = f"{explanation.confidence}/100 ({explanation.band})"
        facts["why"] = "; ".join(explanation.reasons)
        facts["risk"] = "; ".join(explanation.risks) or "none noted"
    detail = "\n".join([render_explanation(explanation), "",
                        render_squad(result, budget=budget, objective="xp", full=True, xi_ids=xi_ids,
                                     bench_boost=bench_boost), "", MODEL_NOTE])
    return {
        "detail": detail,
        "facts": facts,
        "subjects": [p["web_name"] for p in picks],
        "task": "in 2-3 short sentences, state the starting XI's projected points, name a couple of standout "
                "picks, and reflect the confidence + any ⚠ risk — using ONLY the facts",
        # ADR-062: the built 15 in SquadStore shape, so a web edge can offer "Use this squad →".
        "squad": {
            "name": "My squad",
            "player_ids": [p["id"] for p in picks],
            "player_names": [p["web_name"] for p in picks],
            "bench_ids": [p["id"] for p in picks if p["id"] not in xi_ids],
            "cost": result["total_cost"],
        },
    }
_SHORTLIST_N = 8   # how many players a shortlist shows


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
    lead = None
    if differential:
        facts["filter"] = f"differentials only (≤{DIFFERENTIAL_OWN:.0f}% owned)"
        facts["top_players"] = [
            f"{r['web_name']} ({r['position']}, £{r['price']}m, {r['selected_by']}% owned, xP {r['xp']})"
            for r in rows[:3]]
        # Why a differential (US-288, tester feedback) — the rank-lever benefit + the variance trade-off.
        lead = (f"Why a differential? Few managers own a ≤{DIFFERENTIAL_OWN:.0f}%-owned player, so if they "
                "haul you gain rank on the template — and a blank costs you little relative rank. The "
                "trade-off is variance: play them for upside, not safety. Ranked by xP; standout signals below.")
    return {
        "detail": render_shortlist(rows, title, show_own=differential, rationale=lead),
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


def _decide_history(store: Storage, question: str) -> dict | None:
    """A single player's season record (US-296, ADR-027/060) — past seasons + this-season per-GW, GROUNDED.

    Reuses `player_history` + `render_player_history`; the facts carry the last season's points/minutes/xGI so a
    narrated number verifies (✓). Degrades on an ambiguous / absent player, or one with no backfilled history.
    """
    players = store.get_players()
    if not players:
        return None
    matched = _match_players(question, players)
    ambiguous = [wn for wn, ps in matched.items() if len(ps) > 1]
    if ambiguous:
        return {"message": f"More than one player called '{ambiguous[0]}' — name the team too."}
    if not matched:
        return {"message": 'Name a player, e.g. ask "Haaland\'s history".'}

    target = next(iter(matched.values()))[0]
    hist = player_history(target, store.get_history_past(target["code"]), store.get_history(target["code"]))
    seasons = hist["seasons"]
    if not seasons and not hist["gameweeks"]:
        return {"message": f"No history stored for {target['web_name']} yet — run `history --backfill` first "
                           "(past-season data; per-GW form fills once the season starts)."}
    facts = {"player": f"{target['web_name']} ({target['team']}, {target['position']})",
             "seasons_on_record": len(seasons)}
    if seasons:
        last = seasons[-1]
        xgi = f", {last['xgi']} xGI" if last["xgi"] is not None else ""
        facts["last_season"] = f"{last['season']}: {last['points']} pts over {last['minutes']} mins{xgi}"
    return {
        "detail": render_player_history(hist),
        "facts": facts,
        "subjects": [target["web_name"]],
        "task": "in 1-2 short sentences, summarise this player's recent seasons (points + minutes), using ONLY "
                "the facts — do not invent any number",
    }


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
    headline = (f"{target['web_name']} (£{target['price']}m): {verdict} — {tval:.2f} xP/£m, "
                f"{rank_str} by value; {pos} median {median:.2f}")
    # Explainability (ADR-089, US-284): grounded Why/Risk/Confidence for *why* it's worth it — computed from
    # the data, closed by the shared Model note; so the answer explains itself even without Ollama.
    explanation = explain_worth(target, value=tval, median=median, rank=rank, n_peers=len(peers),
                                xp=xp_by_id.get(target["id"], 0), horizon=_HORIZON)
    facts = {
        "player": f"{target['web_name']} ({target['team']}, {pos}, £{target['price']}m)",
        "expected_points": f"xP {xp_by_id.get(target['id'], 0)} over the next {_HORIZON} GW",
        "value": f"{tval:.2f} xP per £m",
        "position_rank_by_value": rank_str,
        "position_median_value": f"{median:.2f} xP per £m",
        "verdict": verdict,
    }
    if explanation is not None:
        facts["confidence"] = f"{explanation.confidence}/100 ({explanation.band})"
        facts["why"] = "; ".join(explanation.reasons) or "none"
        facts["risk"] = "; ".join(explanation.risks) or "none noted"
    detail = "\n".join([headline, "", render_explanation(explanation), "", MODEL_NOTE])
    return {
        "detail": detail,          # the verdict + Confidence·Why·Risk block — the truth, with or without prose
        "headline": headline,
        "facts": facts,
        "subjects": [target["web_name"]],
        "task": f"in 2-3 short sentences, say whether {target['web_name']} is worth the money, citing the "
                "value + rank and reflecting the confidence and the ✓ reasons / ⚠ risks — using ONLY the facts",
    }


# ---- trends intent (Sprint 067, ADR-057) — community "trending" from free FPL crowd data -----------

_TREND_N = 8   # how many players a trending board shows


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
        return {"message": 'No transfer or form movement to report this gameweek. '
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


_PRICE_N = 5   # how many likely risers / fallers to name


def _decide_price(store: Storage, question: str) -> dict | None:
    """Who's likely to rise/fall in price next — the directional predictor (ADR-092), a lens (never xP).

    Net transfers per 1% ownership → a rise/fall flag. **0 on flat preseason data** → a clear 'live at GW1'
    message; it lights up when transfers flow in-season.
    """
    players = store.get_players()
    if not players:
        return None
    pool = [p for p in players if not is_unavailable(p)]
    # ⚠️ Bound to the WHOLE board, then applied to the available pool. ADR-215: a percentile taken over the
    # filtered list would manufacture a top 2% inside that filter — here, among the fit players only, which
    # is a different question from "who is rising".
    predict = price_detector(players)
    risers = sorted((p for p in pool if predict(p) == "rise"),
                    key=lambda p: price_pressure(p) or 0, reverse=True)[:_PRICE_N]
    fallers = sorted((p for p in pool if predict(p) == "fall"),
                     key=lambda p: price_pressure(p) or 0)[:_PRICE_N]
    if not risers and not fallers:
        # ⚠️ This used to promise the predictor *"lights up at GW1 (2026-08-21)"* — a date a month past, for
        # a feature that was in fact dead behind an unreachable threshold (ADR-215). ⭐ *A message that
        # explains why there is nothing to show is a claim, and it expires like any other.*
        return {"message": f"No clear price moves right now — nobody is far enough into the top or bottom of "
                           f"the transfer-pressure board to call it. The predictor flags likely risers "
                           f"{PRICE_UP} / fallers {PRICE_DOWN} when they appear."}

    def _disp(p):
        return {"web_name": p["web_name"], "team": p["team"], "position": p["position"],
                "selected_by": p["selected_by"], "pressure": price_pressure(p)}

    riser_rows, faller_rows = [_disp(p) for p in risers], [_disp(p) for p in fallers]
    return {
        "detail": render_price_movers(riser_rows, faller_rows),
        "facts": {
            "likely_risers": [f"{r['web_name']} ({r['position']})" for r in riser_rows[:3]] or ["none"],
            "likely_fallers": [f"{r['web_name']} ({r['position']})" for r in faller_rows[:3]] or ["none"],
            "basis": "net transfers per 1% ownership — a directional flag, not the exact price/timing",
        },
        "subjects": [r["web_name"] for r in riser_rows + faller_rows],
        "task": "in 2 short sentences, say who's likely to rise or fall in price from the facts — it's a "
                "directional flag (not the exact price/timing) and it sharpens in-season",
    }


# ---- fixtures / FDR intent (ADR-048) ----------------------------------------

_FIXTURES_N = 8   # how many teams the league FDR ranking shows
_HARDEST_WORDS = ("hard", "tough", "difficult", "avoid", "worst", "nightmare")


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
    horizon = fixture_horizon(question)
    hardest = any(w in question.lower() for w in _HARDEST_WORDS)
    match = match_team(question, store.get_teams())

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


def _dispatch(intent: str, store: Storage, question: str, squad: str | None,
              *, count: int = 1, rank: int = 0, active_squad=None, horizon=_HORIZON,
              free: int = 1, bank: float = 0.0, chip_status=None) -> dict | None:
    """Run the decision engine for `intent` (shared by `answer` and `converse`).

    `count`/`rank` are threaded so a conversational follow-up can ask for an N-transfer plan or
    the Nth-best pick (ADR-047); the intents that don't rank ignore them. `active_squad` is the
    session squad so squad-scoped intents see the loaded team, not only saved squads (Sprint 066).
    `horizon` (ADR-077) is consumed by the gameweek intent; the others keep the `_HORIZON` default.
    """
    if intent == "transfer":
        return _decide_transfer(store, squad, count, rank=rank, active_squad=active_squad)
    if intent == "captain":
        # ⭐ The question, not just the intent: *"vice"*, *"safest"*, *"differential"* and *"rotation"*
        # all route here, and until ADR-308 all four returned the same pick.
        return _decide_captain(store, squad, rank=rank, active_squad=active_squad,
                               lens=captain_lens(question), question=question)
    if intent == "start_bench":
        return _decide_start_bench(store, squad, active_squad=active_squad)
    if intent == "gameweek":
        return decide_gameweek(store, squad, active_squad=active_squad, horizon=horizon,
                                question=question, free=free, bank=bank)
    if intent == "chips":
        return _decide_chips(store, squad, active_squad=active_squad, horizon=horizon,
                             chip_status=chip_status, lens=chip_lens(question), question=question)
    if intent == "rules":
        return _decide_rules(question)
    if intent == "compare":
        return _decide_compare(store, question)
    if intent == "build_squad":
        return _decide_build_squad(store, question)
    if intent == "shortlist":
        return _decide_shortlist(store, question, rank=rank)
    if intent == "worth":
        return _decide_worth(store, question)
    if intent == "history":
        return _decide_history(store, question)
    if intent == "trends":
        return _decide_trends(store, question)
    if intent == "price":
        return _decide_price(store, question)
    if intent == "fixtures":
        return _decide_fixtures(store, question, squad, active_squad=active_squad)
    return _decide_analyse(store, squad, active_squad=active_squad)
