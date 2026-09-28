"""Decision in, the grounded facts out.

⭐ The narrator is never trusted with a number (ADR-181): these shape what the model is allowed to say, and
`verify_grounding` checks the answer back against them. ⚠️ *A fact this layer does not extract is a fact the
answer cannot legitimately contain.*
"""




def _captain_facts(pick: dict, lens: str | None = None) -> dict:
    """Pre-humanised, self-describing facts for one captain pick — nothing to decode."""
    venue = "home against" if pick["venue"] == "H" else "away against"
    facts = {
        "player": f"{pick['web_name']} ({pick['team']})",
        "expected_points_next_gameweek": pick["xp"],
        "fixture": f"{venue} {pick['opponent']}",
        "is_penalty_taker": pick["penalty_taker"],
    }
    # ⭐⭐ **A question about minutes has to be answered with minutes.** Naming the lens in the heading and
    # then handing back the same four facts would be *the same failure in nicer clothing* — the reader
    # asked whether his captain might be rested and would still be reading expected points.
    if lens in {"rotation", "safest"}:
        facts["expected_minutes_share"] = _minutes_phrase(pick)
        facts["is_flagged_doubtful"] = bool(pick.get("doubtful"))
        if pick.get("chance") is not None:
            facts["fpl_chance_of_playing"] = f"{pick['chance']}%"
    return facts


def _minutes_phrase(pick: dict) -> str:
    """xMins as a sentence — ⚠️ *0.82 is a number the model produced, not a thing a person can act on.*

    ⭐ The bands are the ones the pitch already uses for a doubt (ADR-206): a flagged player is a
    different kind of risk from a rotated one, and they must not read the same.
    """
    weight = pick.get("minutes_weight")
    if weight is None:
        return "not known"
    if pick.get("doubtful"):
        return f"{round(weight * 100)}% of a full game, and FPL has him flagged"
    if weight >= 0.9:
        return f"{round(weight * 100)}% of a full game — he starts"
    if weight >= 0.7:
        return f"{round(weight * 100)}% of a full game — usually starts"
    return f"{round(weight * 100)}% of a full game — rotated"


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

    # ADR-136 — a dead slot is stated as its own fact, never merged into the line above. The two answer
    # different questions, and the whole reason this exists is that "none — no positive-gain upgrade" was
    # being said over a squad with a player who had left the league.
    reps = plan.get("replacements") or []
    dead = ("none — every player in your 15 can play" if not reps else
            f"{len(reps)}: " + "; ".join(
                f"{r['out']['web_name']} cannot play ({r['reason']}) — replace with "
                f"{r['in']['web_name']} (£{r['in']['price']}, xP {r['in']['xp']} over the horizon)"
                for r in reps))

    flags = ("none" if not plan["flags"] else
             f"{len(plan['flags'])}: " + ", ".join(
                 f"{f['web_name']} ({f['reason']}"
                 f"{'' if f['chance'] is None else f', {f['chance']}%'})"
                 for f in plan["flags"]))

    return {
        "captain": captain,
        "lineup_change": lineup,
        "dead_slots_to_replace": dead,
        "transfer_to_consider": transfer,
        "flagged_players": flags,
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
