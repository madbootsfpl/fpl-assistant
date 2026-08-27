"""Transfer suggestions (ADR-030) — best single legal upgrades for a squad.

Two different questions live here. `suggest_transfers` answers *"what would improve my starting XI?"*.
`replace_dead` answers *"what in my 15 cannot play at all?"* — a question an XI-gain ranking cannot see, because
a dead player on the bench moves the XI by zero (ADR-136). They are kept apart on purpose: their `gain` fields
mean different things, and merging them would quietly make one of the numbers lie.

Pure: given a squad, the transfer market, and each player's xP over a horizon, it
returns the best legal, affordable, available same-position replacement per owned
player, ranked by xP gain. No I/O — the caller loads the squad, computes xP, and
formats the result. It respects FPL's rules (same position, ≤3/club, budget) so a
suggestion is always a move you could actually make.
"""

from src.analytics.dead_slot import dead_slots
from src.analytics.optimizer import MAX_PER_CLUB, best_xi_points, is_unavailable


def _summary(player, xp_by_id) -> dict:
    """The display fields for one player + their xP over the horizon."""
    return {
        "id": player["id"],
        "web_name": player["web_name"],
        "team": player["team"],
        "price": player["price"],
        "xp": round(xp_by_id.get(player["id"], 0), 1),
    }


def _club_ok(out, candidate, club_counts, max_per_club) -> bool:
    """Would bringing `candidate` in (and `out` out) keep ≤ max_per_club from any club?

    Only `candidate`'s club can breach the cap. Selling a same-club player frees a slot,
    so a same-club swap is always fine; otherwise the candidate's club must currently
    hold fewer than the cap.
    """
    same_club = candidate["team"] == out["team"]
    final = club_counts.get(candidate["team"], 0) - (1 if same_club else 0) + 1
    return final <= max_per_club


def suggest_transfers(
    owned, players, xp_by_id, *,
    bench_ids=(), bank: float = 0.0, limit: int = 5, max_per_club: int = MAX_PER_CLUB,
    xi_aware: bool = True,
) -> list[dict]:
    """Rank the best single transfers for a squad (ADR-030/046).

    `owned` are the squad's player rows; `players` is the whole market; `xp_by_id`
    maps player id → xP over the chosen horizon (the caller computes it). For each owned
    player, a legal replacement is: same position, not already owned, available
    (`is_unavailable`), affordable (`price ≤ out.price + bank`), and ≤ `max_per_club` per
    club after the swap. Only **positive-gain** moves are returned, highest gain first,
    capped at `limit`. Each result flags whether the outgoing player is on the bench
    (`bench_ids`) — a bench upgrade helps the weekly score less.

    `xi_aware` (default, ADR-046) ranks by the swap's effect on the best legal **starting XI**
    (`best_xi_points` after − before), so a bench-only swap (XI-gain 0) drops out; `xi_aware=False`
    (the `--raw` view) ranks by the raw player xP gain (`in.xp − out.xp`).

    The shortlist is a menu of *alternative* single swaps, so each is taken greedily and
    disjoint (ADR-040): no incoming player is suggested twice, and no outgoing player twice —
    a sell whose best target is already taken gets its next-best available one.
    """
    owned_ids = {p["id"] for p in owned}
    bench = set(bench_ids)
    base_xi = best_xi_points(owned, xp_by_id) if xi_aware else 0.0

    club_counts: dict = {}
    for p in owned:
        club_counts[p["team"]] = club_counts.get(p["team"], 0) + 1

    # Every positive-gain (out → in) pair; the shortlist is then a disjoint pick from these.
    pairs = []
    for out in owned:
        budget = out["price"] + bank
        out_sum = _summary(out, xp_by_id)
        for c in players:
            if (c["position"] == out["position"]
                    and c["id"] not in owned_ids
                    and not is_unavailable(c)
                    and c["price"] <= budget
                    and _club_ok(out, c, club_counts, max_per_club)):
                in_sum = _summary(c, xp_by_id)
                if xi_aware:   # how much the swap lifts the best legal XI (ADR-046)
                    after = best_xi_points([p for p in owned if p["id"] != out["id"]] + [c], xp_by_id)
                    gain = round(after - base_xi, 1)
                else:
                    gain = round(in_sum["xp"] - out_sum["xp"], 1)
                if gain > 0:
                    pairs.append((gain, out, out_sum, c, in_sum))

    pairs.sort(key=lambda t: t[0], reverse=True)

    used_out: set = set()
    used_in: set = set()
    suggestions = []
    for gain, out, out_sum, c, in_sum in pairs:
        if out["id"] in used_out or c["id"] in used_in:   # each sell + each buy at most once
            continue
        used_out.add(out["id"])
        used_in.add(c["id"])
        suggestions.append({
            "position": out["position"],
            "out": out_sum,
            "in": in_sum,
            "gain": gain,
            "out_on_bench": out["id"] in bench,
        })
        if len(suggestions) >= limit:
            break
    return suggestions


def suggest_transfer_plan(
    owned, players, xp_by_id, *,
    bench_ids=(), bank: float = 0.0, count: int = 1, max_per_club: int = MAX_PER_CLUB,
    xi_aware: bool = True,
) -> list[dict]:
    """A coordinated, greedy plan of up to `count` transfers (ADR-035).

    Repeatedly takes the **best legal single transfer given the running state** and applies
    it: the shared **bank threads** (a later move can spend what an earlier sale freed), club
    counts and ownership update, and no player is bought twice or a sold one re-bought. Reuses
    `suggest_transfers` on the evolving state, so every single-transfer rule holds across the
    plan. Returns the ordered moves, each annotated with `bank_after`; stops early when no
    positive-gain move remains.
    """
    by_id = {p["id"]: p for p in players}
    owned = list(owned)
    sold: set = set()
    running_bank = bank
    plan = []

    for _ in range(count):
        market = [p for p in players if p["id"] not in sold]   # a sold player can't return
        moves = suggest_transfers(
            owned, market, xp_by_id, bench_ids=bench_ids, bank=running_bank,
            limit=1, max_per_club=max_per_club, xi_aware=xi_aware,
        )
        if not moves:
            break
        move = moves[0]
        out_id, in_id = move["out"]["id"], move["in"]["id"]
        # Bank after: the sale frees the out price, the buy spends the in price.
        running_bank = round(running_bank + move["out"]["price"] - move["in"]["price"], 1)
        owned = [p for p in owned if p["id"] != out_id] + [by_id[in_id]]  # buy → owned (no re-buy)
        sold.add(out_id)
        plan.append({**move, "bank_after": running_bank})

    return plan


def replace_dead(
    owned, players, xp_by_id, upcoming, *,
    today, bench_ids=(), bank: float = 0.0, horizon: int = 5, max_per_club: int = MAX_PER_CLUB,
    reported_out=None,
) -> list[dict]:
    """One replacement for each **dead slot** in the squad — a place that cannot score (ADR-136).

    A dead slot is a permanent zero with no auto-sub cover, so this is not an upgrade ranking and does not
    pretend to be one: `gain` here is `in.xp − out.xp` (the out is 0.00 by construction), which is what the
    slot is throwing away, **not** what the swap adds to your XI. `suggest_transfers` answers that other
    question and is left exactly as it is.

    The replacement chosen is the **highest-xP** legal, affordable, available, same-position player — not the
    cheapest body that can kick a ball. *"Any playing £4.5m body is pure upside"* describes the floor; if the
    best affordable replacement is worth 16.9 xP over the horizon, that is the one worth naming.

    Legality is the same as a normal transfer (same position, not owned, available, affordable, ≤3/club) and
    reuses the same helpers, so a suggestion here is always a move you could actually make. Multiple dead slots
    get disjoint incoming players, biggest recovery first.

    Each entry carries `reason` (*"gone"*, *"no return date"*, *"out until 28 Nov"*) and `missed`/`total`, so a
    surface can state its evidence rather than asserting a verdict.
    """
    slots = dead_slots(owned, upcoming, today=today, horizon=horizon, reported_out=reported_out)
    if not slots:
        return []

    owned_ids = {p["id"] for p in owned}
    bench = set(bench_ids)
    club_counts: dict = {}
    for p in owned:
        club_counts[p["team"]] = club_counts.get(p["team"], 0) + 1

    # Best-first across all dead slots, so two dead players can't be offered the same replacement.
    ranked = []
    for slot in slots:
        out = slot["player"]
        budget = out["price"] + bank
        cands = [c for c in players
                 if c["position"] == out["position"]
                 and c["id"] not in owned_ids
                 and not is_unavailable(c)
                 and c["price"] <= budget
                 and _club_ok(out, c, club_counts, max_per_club)]
        cands.sort(key=lambda c: xp_by_id.get(c["id"], 0), reverse=True)
        ranked.append((slot, cands))
    ranked.sort(key=lambda t: xp_by_id.get(t[1][0]["id"], 0) if t[1] else 0, reverse=True)

    used_in: set = set()
    out_rows = []
    for slot, cands in ranked:
        c = next((c for c in cands if c["id"] not in used_in), None)
        if c is None:                                    # nothing legal and affordable — say nothing
            continue
        used_in.add(c["id"])
        out, out_sum, in_sum = slot["player"], _summary(slot["player"], xp_by_id), _summary(c, xp_by_id)
        # ADR-153 — for a player the press and the crowd both say is leaving, his projected xP is **fiction**:
        # FPL still calls him available, so `decision_xp` still credits him a full horizon of points he will
        # not be here to score. Comparing a replacement against that produced *"recovers −8.6 xP"* — a
        # negative recovery, which is not a sentence about anything.
        #
        # So the baseline is 0, exactly as it already is for a player FPL has marked `u`. This changes no
        # analytics: `decision_xp` is untouched, and only this slot's arithmetic uses the number that will
        # actually happen.
        leaving = slot.get("event") is not None
        baseline = 0.0 if leaving else out_sum["xp"]
        out_rows.append({
            "position": out["position"],
            "out": {**out_sum, **({"xp": 0.0} if leaving else {})},
            "in": in_sum,
            "gain": round(in_sum["xp"] - baseline, 1),
            "out_on_bench": out["id"] in bench,
            "reason": slot["reason"],
            "missed": slot["missed"],
            "total": slot["total"],
            "reported": leaving,
        })
    return out_rows
