"""A one-gameweek plan for a squad (ADR-070) — captain · lineup · a transfer · flags.

An **assembler**, not new analytics: it orchestrates the existing decision primitives so the weekly
answer can't diverge from the standalone tools. Captain uses its own next-GW xP (`captain_picks`,
horizon 1); the lineup and the transfer use the caller's multi-GW `xp_by_id` (`best_legal_xi`,
`suggest_transfers`) — the horizon each decision actually wants. Pure given its inputs (no I/O), so
it's unit-tested with a fake squad offline. The `ask` layer humanises + verifies it (ADR-034/037).
"""

from datetime import UTC, datetime

from src.analytics.captain import captain_picks
from src.analytics.headlines import event_phrase, leavers, reported_leaving
from src.analytics.optimizer import best_legal_xi, is_unavailable
from src.analytics.transfer import TIE_NOISE_WINDOW, replace_dead, suggest_transfer_plan, suggest_transfers
from src.analytics.transfer_timing import affordability_cliff, bank_or_use

# FPL status codes → a human word for a flag (mirrors the CLI's availability messages, ADR-023).
# "d" (doubtful) is handled separately — it's a warning, not an unavailability.
_STATUS_WORD = {"i": "injured", "s": "suspended", "u": "unavailable", "n": "unavailable"}


def auto_sub_cover(player, bench, xp_by_id):
    """Who actually comes on if `player` blanks, and what he is worth (ADR-208).

    ⭐ **The advice *"bench or replace him"* assumes a bench worth using**, and never checked. FPL
    auto-substitutes a starter who plays 0 minutes with the first legal bench player, so a flagged starter's
    real exposure is not his own doubt — it is **the doubt times the drop to whoever replaces him**.

    On the owner's own squad the answer was **0.2 xP**: a doubtful forward covered by a forward who projects
    nothing, so *"bench him"* was advice to field a blank. ⭐ *An instruction is only as good as the option it
    assumes you have.*

    ⚠️ Same position only, because FPL's auto-sub must keep the formation legal and an XI needs at least one
    forward and a goalkeeper. A midfielder on the bench is not cover for a forward, however good he is.

    Returns `{"name", "xp"}` for the best same-position bench player, or **None when there is nobody** — which
    is a different sentence from a poor option and must not be flattened into one.
    """
    def pos(row):
        """A row's position, or None — a `sqlite3.Row` has no `.get`, and a thin row must not crash a plan."""
        try:
            return row["position"]
        except (KeyError, IndexError):
            return None

    if (want := pos(player)) is None:
        return None            # ⚠️ unknown position → say nothing. Matching None to None would make every
                               # bench player "cover", which is worse than silence.
    # ⚠️ **Cover must be able to play.** FPL's auto-sub skips a bench player who also records 0 minutes, so
    # an injured or suspended substitute is not cover — he is a second hole. Found by the first smoke run on
    # the owner's real squad, which reported *"benching E.Le Fée fields Foden (0.0 xP)"* about a **suspended**
    # player. ⭐ *A fallback that shares the failure it is covering for is not a fallback.*
    same = [p for p in bench if pos(p) == want and not is_unavailable(p)]
    if not same:
        return None
    best = max(same, key=lambda p: xp_by_id.get(p["id"], 0.0))
    return {"name": best["web_name"], "xp": round(xp_by_id.get(best["id"], 0.0), 1)}


def gameweek_plan(owned, market, upcoming, xp_by_id, *,
                  baseline_by_code=None, minutes_weight=None, history_by_code=None,
                  bench_ids=(), bank: float = 0.0, horizon: int = 5, today=None, events_by_id=None,
                  free: int = 1, horizon_xp=None, exodus_for=None) -> dict:
    """Assemble this gameweek's plan for a squad from the existing primitives.

    `owned` are the squad's player rows; `market` is the whole player pool (for the transfer);
    `upcoming` the fixtures; `xp_by_id` the multi-GW xP the caller already computed (id → xP). The
    captain hooks (`baseline_by_code`/`minutes_weight`/`history_by_code`) feed `captain_picks` its
    own next-GW xP. `bench_ids` is the squad's declared bench (drives the lineup change); `bank` the
    money available for the transfer.

    Returns ``{captain, lineup, transfer, flags}``:
    - **captain** — the top next-GW pick (a `captain_picks` dict), or None if none is eligible.
    - **lineup** — ``{start, bench, bring_in, drop, has_declared_bench}``: the best legal XI (rows)
      and its bench, plus who to bring in / drop vs the declared XI (empty when already optimal).
    - **transfer** — the first recommended move (a `suggest_transfer_plan` dict), or None. Kept as its own
      key because every existing consumer reads it.
    - **transfers** — the week's actual advice: **as many moves as `free` transfers held**, each priced
      against the squad and the bank the previous one leaves, so **the gains add up** (ADR-191). At `free=1`
      this is `[transfer]` and nothing downstream changes.
    - **free** — how many free transfers the plan assumed. Stated rather than implied: the count is
      manager-entered, and a stated assumption can be corrected where a silent one cannot.
    - **timing** — `bank_or_use`'s verdict (ADR-132/173): spend the free transfer now, or bank it because a
      second move worth having is coming. Always present, so a caller cannot forget the alternative exists.
    - **cliff** — a materially better transfer just out of budget (`affordability_cliff`, ADR-186), or None.
      Answers *"bank the money?"* where `timing` answers *"bank the transfer?"* — two different questions
      that shared one word. **Priced over `horizon_xp`'s wider window when one is supplied**: waiting a
      fortnight is a multi-week question and a one-week gain is the wrong yardstick for it.
    - **horizon_gain** — the same swap's gain over `horizon_xp`'s wider window, or None when not supplied.
      A one-week number reads as a season verdict when it stands alone (ADR-173).
    - **replacements** — one move per **dead slot**: a squad place that cannot score for the whole horizon
      (ADR-136). Deliberately a separate key rather than folded into `transfer`, because its `gain` answers a
      different question — what the slot is throwing away, not what the swap adds to your XI — and a
      differently-meaning number in an existing field is how consumers start lying. Surfaces that care opt in.
    - **flags** — owned players who can't (or might not) play: ``{web_name, team, reason, chance}``.
    """
    # ADR-153/154 — work out who is on his way out of the league **first**, because it changes three of the
    # answers below: the captain, the lineup, and the transfer. A transfer headline plus a heavy unexplained
    # sell-off, and only while a window is open — outside one he cannot go anywhere, so a story about a
    # January move must change nothing about this gameweek.
    events_by_id = events_by_id or {}
    as_of = today or datetime.now(UTC).date()
    # ADR-210 — `exodus_for` is bound to the whole board by the caller (`crowd.exodus_detector`), because the
    # threshold is a percentile of the live league and this function only ever sees fifteen players.
    # ⭐ **No detector means no exodus flag, never a stale one.** The old module-level default was a constant
    # measured in one hour of GW1, and a caller that forgot it got that hour applied to today.
    exodus_for = exodus_for or (lambda _p: None)
    reported_out = leavers(owned, events_by_id, exodus_for, today=as_of)

    # Captain — the next-GW pick from the owned, XI-eligible players (ADR-029). `limit=3` so the runner-up is
    # available for the captain explanation's lead-margin (ADR-089); the pick is still picks[0].
    # A leaving player must not be captained either — the same reasoning, and a worse outcome if it happened.
    captain_pool = [p for p in owned if p["id"] not in reported_out] or owned
    picks = captain_picks(captain_pool, upcoming, baseline_by_code=baseline_by_code, limit=3,
                          minutes_weight=minutes_weight, history_by_code=history_by_code)
    captain = picks[0] if picks else None

    # Lineup — the best legal XI on the horizon xP vs the declared bench (ADR-039/040).
    # ADR-154: a player who is leaving is ranked as if he scores nothing, **for selection only**. His
    # `decision_xp` is untouched and every other surface still shows it; this is the one place where letting
    # a fiction win would put him in your XI. Scoped as tightly as it can be — reported-leaving players, an
    # open window, and a local copy of the map that goes no further than this call.
    lineup_xp = dict(xp_by_id)
    for pid in reported_out:
        lineup_xp[pid] = 0.0
    optimal = best_legal_xi(owned, lineup_xp)
    declared_bench = set(bench_ids)
    declared_xi = ({p["id"] for p in owned if p["id"] not in declared_bench}
                   if declared_bench else optimal)
    by_id = {p["id"]: p for p in owned}
    lineup = {
        "start": [by_id[i] for i in optimal if i in by_id],
        "bench": [p for p in owned if p["id"] not in optimal],
        "bring_in": [by_id[i] for i in optimal - declared_xi if i in by_id],
        "drop": [by_id[i] for i in declared_xi - optimal if i in by_id],
        "has_declared_bench": bool(declared_bench),
    }

    # Transfer — the single best positive-gain, self-funding upgrade (ADR-030/046).
    # ADR-173 — **two moves, not one.** The second is never shown; it exists so `bank_or_use` can answer the
    # question the owner asked ("is there value in letting transfers build up?"), which turns entirely on
    # whether a *second* move worth having exists. Asking for one move made that unanswerable here, which is
    # why the arithmetic has lived on the Transfer tab since ADR-132 and never reached the week's answer.
    # ⚠️ **ADR-191 — a PLAN, not a menu.** This used to call `suggest_transfers(limit=2)`, which returns two
    # *disjoint alternatives*, each priced against the **same** squad and the **same** bank. That is right for
    # a shortlist and wrong here: their gains do not add, because the second is not priced on the squad or the
    # money the first one leaves.
    #
    # `suggest_transfer_plan` has done this correctly since ADR-035 — the bank threads, the squad evolves, and
    # each move's gain is its true marginal lift. The CLI, `ask` and the Transfer tab all use it. **The week's
    # answer was the one caller that did not**, so the surface a manager actually reads was the one getting
    # the menu. The fix is to call the function that already existed.
    #
    # `count` is at least 2 whatever the manager holds: move 2 is the *recommendation* when he holds two
    # transfers, and the *value of banking* when he holds one (ADR-132's arithmetic). Same number, two uses.
    # ⚠️ **`free` is reported as given and planned as at-least-one.** Holding zero free transfers is a real
    # position — every move then costs a 4-point hit — so the best move is still worth naming, but the plan
    # must not silently claim he holds one. `held` drives the search; the returned `free` is the truth.
    held = max(int(free if free is not None else 1), 1)
    # ADR-209 — the plan knows both things `suggest_transfers` cannot: how wide `xp_by_id` is, and what the
    # wider map says. Without them the tie-break sizes its band for five gameweeks whatever it was handed,
    # and the longer view it already prints is never allowed to choose.
    moves = suggest_transfer_plan(owned, market, xp_by_id, window=horizon, horizon_xp=horizon_xp,
                                  bench_ids=bench_ids, bank=bank,
                                  count=max(held, 2), reported_out=reported_out)
    # What we actually advise him to do this week: as many moves as he holds transfers for.
    transfers = moves[:held]
    transfer = transfers[0] if transfers else None

    # Bank or use it (ADR-132, surfaced here by ADR-173). Banking buys a second free transfer next week,
    # which is worth only the hit it saves — and costs the gain skipped by waiting a week.
    timing = bank_or_use(moves, transfer["gain"] if transfer else None, free=free)

    # ADR-186 — a materially better move just out of budget. `bank_or_use` above answers *"bank the
    # transfer?"*; this answers *"bank the money?"*, which nothing did. Measured on the owner's squad:
    # Watkins → Havertz +7.4 today, Watkins → Isak **+13.8** with £1.5m more.
    # ⚠️ **Priced over the WIDE window, not the page's horizon.** Shipped first against `xp_by_id`, which on
    # My Squad is a single gameweek since ADR-179 — and a one-week gain can essentially never clear the
    # threshold, so the line never appeared (owner-reported the day it shipped). The thresholds were sized
    # against a five-gameweek measurement and rendered on a one-gameweek page: **I tuned against one window
    # and shipped onto another.**
    #
    # The window is the fix, not the threshold. *"Is it worth waiting a fortnight for a better player?"* is a
    # question about several gameweeks, so it must be measured over several — the same `horizon_xp` ADR-173
    # already computes for the *Longer view* line, so the two numbers answer the same span.
    cliff = affordability_cliff(owned, market, horizon_xp or xp_by_id, bank=bank, suggest=suggest_transfers)

    # ⚠️ **ADR-191 — the cliff has to COMPETE, not merely coexist.** It answers *"is a better player one
    # price-rise away?"*; a second free transfer answers *"is there another move worth making today?"* Both
    # were computed and **neither was compared to the other**, so the reader got whichever happened to render.
    # On the owner's squad *"save £1.0m for +3.3"* was being shown while a second transfer he already held was
    # worth several times that. Two correct answers to competing questions, and no argument between them.
    #
    # ⚠️ **Compared over the cliff's own window, never the page's.** The cliff is priced on `horizon_xp` (five
    # gameweeks) while `xp_by_id` on My Squad is a single one (ADR-179). Comparing those two numbers would
    # repeat ADR-186's original mistake exactly — a threshold sized against one window applied to another —
    # so the rival move is re-priced over the same map before the two are weighed.
    if cliff and held >= 2:
        wide = horizon_xp or xp_by_id
        # ⭐ **Stated, because here the default is right by coincidence** (ADR-220). This branch only runs
        # when `horizon_xp` exists, and it ranks on that map — so the window is the wider one, and there is
        # no *further* view left to break a tie with. ⚠️ `gameweek_plan` is handed `horizon_xp` without being
        # told how wide it is; every caller builds it at five, which is `TIE_NOISE_WINDOW`. That assumption
        # was already load-bearing and unwritten.
        rival = (suggest_transfer_plan(owned, market, wide, bench_ids=bench_ids, bank=bank,
                                       count=2, reported_out=reported_out,
                                       window=TIE_NOISE_WINDOW, horizon_xp=None)
                 if horizon_xp else moves)
        second = rival[1]["gain"] if len(rival) > 1 else 0.0
        if second >= (cliff.get("uplift") or 0.0):
            cliff = None            # you do not need to save up for it — you can move twice today

    # The same swap over a longer window (ADR-173). A one-week gain reads as a verdict when it stands alone;
    # the owner rejected a transfer that was right for next week and wrong for his season. `horizon_xp` is an
    # xP map over a wider horizon — the *same* players, priced over more gameweeks — so this compares like
    # with like rather than re-running the search and possibly naming a different move.
    horizon_gain = None
    if transfer and horizon_xp:
        horizon_gain = round(horizon_xp.get(transfer["in"]["id"], 0)
                             - horizon_xp.get(transfer["out"]["id"], 0), 1)
    # ⚠️ **ADR-191 — EVERY move gets the longer view, not just the first.**
    #
    # ADR-173 added the *Longer view* line because a one-week number reads as a season verdict when it stands
    # alone, and the owner had rejected a transfer that was right for next week and wrong for his season. I
    # then shipped a second move with **no longer view at all** — on My Squad, whose window is a single
    # gameweek (ADR-179).
    #
    # That matters most for exactly the move it was reported on. A **+1.4 one-week** XI gain sits against a
    # per-player weekly sd of **3.51** (ADR-161) — a swap's week-to-week spread is wider still — so a second
    # move can be presented as a plan step on a margin smaller than its own noise. The five-gameweek number is
    # what says whether it is a decision or a coin flip, and it was missing from the only place a manager
    # could have used it.
    if horizon_xp:
        for m in transfers:
            m["horizon_gain"] = round(horizon_xp.get(m["in"]["id"], 0)
                                      - horizon_xp.get(m["out"]["id"], 0), 1)

    # Replacements — the slots that cannot score at all (ADR-136). A dead player on the bench is invisible to
    # the XI-gain ranking above (it moves the XI by zero), so "hold" was the advice on a squad with a hole in
    # it. This asks the other question. `today` is injected so the horizon arithmetic is testable.
    # ADR-153 — a player the press says is leaving, whom the crowd is dumping, is a dead slot FPL has not
    # caught up with yet. `reported_out` is how that reaches ADR-136's machinery, so the recommendation
    # ("replace him") arrives through the path that already exists rather than a new one.
    replacements = replace_dead(owned, market, xp_by_id, upcoming, bench_ids=bench_ids, bank=bank,
                                horizon=horizon, today=as_of, reported_out=reported_out)

    # Flags — owned players who are unavailable, or doubtful (a warning, kept in the XI). ADR-023.
    # ADR-146 adds a third: a heavy sell-off our own data cannot explain. The first two are facts FPL told us;
    # this one is an inference from behaviour, and it is the app's only route to news the feed does not carry
    # (a transfer abroad, a row, a press conference). Ordered last in the `elif` so a real status always wins —
    # if FPL says he is injured, say *that*, not "the crowd is nervous".
    flags = []
    for p in owned:
        exodus = exodus_for(p)
        if is_unavailable(p):
            reason = _STATUS_WORD.get(p["status"], "unavailable")
        elif p["status"] == "d":
            reason = "doubtful"
        elif exodus:
            # ADR-153: say WHY when we know why. The flag used to assert "nothing in the data says why" even
            # after the headlines had been read — the one place the cause was available and unused.
            found = reported_leaving(events_by_id.get(p["id"]), exodus)
            because = (f"{event_phrase(found)}" if found
                       else "nothing in the data says why")
            flags.append({"web_name": p["web_name"], "team": p["team"],
                          "reason": f"{abs(exodus['net']):,} sold him this week — {because}",
                          "chance": None,
                          "cover": (auto_sub_cover(p, lineup["bench"], lineup_xp)
                                    if p["id"] in optimal else None),
                          "starting": p["id"] in optimal})
            continue
        else:
            continue
        # ADR-208 — what benching him actually gets you. Only for a starter: a flagged player already on
        # the bench costs the XI nothing, so "your cover is…" would be answering a question nobody has.
        flags.append({"web_name": p["web_name"], "team": p["team"],
                      "reason": reason, "chance": p["chance"],
                      "cover": (auto_sub_cover(p, lineup["bench"], lineup_xp)
                                if p["id"] in optimal else None),
                      "starting": p["id"] in optimal})

    return {"captain": captain, "captain_ranked": picks, "lineup": lineup,
            "transfer": transfer, "transfers": transfers, "free": int(free if free is not None else 1), "bank": bank,
            "replacements": replacements, "flags": flags,
            "timing": timing, "horizon_gain": horizon_gain, "cliff": cliff}
