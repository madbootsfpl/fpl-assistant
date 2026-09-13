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


def _selection_xp(xp_by_id, reported_out):
    """A **local copy** of the xP map with reported leavers zeroed — ADR-154's rule, reused (ADR-156).

    Same reasoning as the lineup: FPL still rates a player with an agreed move abroad, so ranking on his stored
    xP asks *"how much better is his replacement than the points he will score?"* when the honest question is
    *"…than nothing?"*. `decision_xp` is untouched; this map exists for the length of one ranking.
    """
    if not reported_out:
        return xp_by_id
    return {k: (0.0 if k in reported_out else v) for k, v in xp_by_id.items()}


def _club_ok(out, candidate, club_counts, max_per_club) -> bool:
    """Would bringing `candidate` in (and `out` out) keep ≤ max_per_club from any club?

    Only `candidate`'s club can breach the cap. Selling a same-club player frees a slot,
    so a same-club swap is always fine; otherwise the candidate's club must currently
    hold fewer than the cap.
    """
    same_club = candidate["team"] == out["team"]
    final = club_counts.get(candidate["team"], 0) - (1 if same_club else 0) + 1
    return final <= max_per_club


# ADR-189 — how close two gains must be before the tie-break may speak. ADR-161 measured **one starter's
# single-gameweek points at sd 3.51**, so a gap of a few tenths per week is a coin flip dressed as a ranking.
# 2.0 over a five-gameweek window is 0.4 a week — comfortably inside that noise, and deliberately small
# enough that the tie-break can never overturn a difference worth having.
TIE_NOISE = 2.0

# Positions whose points depend on their club keeping a clean sheet, so two of them from one club succeed and
# fail together.
_DEFENSIVE = ("DEF", "GK")


def _correlated_after(out, incoming, owned) -> int:
    """How many **other** defensive assets from the incoming player's club you would hold after the swap.

    Two defenders at one club are not two bets, they are one bet twice: the clean sheet arrives for both or
    neither. Measured (ADR-189) that correlation **never moves expected points** — it multiplies the spread
    of that component by exactly √2, worth ~1.2 points at worst — which is why this is a tie-break and not a
    warning or a weight. It speaks only when the xP difference is already noise.
    """
    if incoming["position"] not in _DEFENSIVE:
        return 0
    return sum(1 for p in owned
               if p["id"] != out["id"]
               and p["position"] in _DEFENSIVE
               and p["team"] == incoming["team"])


def suggest_transfers(
    owned, players, xp_by_id, *,
    bench_ids=(), bank: float = 0.0, limit: int = 5, max_per_club: int = MAX_PER_CLUB,
    xi_aware: bool = True, reported_out=None,
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

    `reported_out` (id → event, ADR-153/154) values a player reported to be leaving the league at **zero** for
    this ranking, and keeps one out of the incoming shortlist. Without it the ranking compares a replacement
    against points the outgoing player will never score, and a bench leaver moves the XI by nothing — so the
    single most urgent transfer in the squad never appears (ADR-156).
    """
    owned_ids = {p["id"] for p in owned}
    bench = set(bench_ids)
    reported_out = reported_out or {}
    rank_xp = _selection_xp(xp_by_id, reported_out)
    base_xi = best_xi_points(owned, rank_xp) if xi_aware else 0.0

    club_counts: dict = {}
    for p in owned:
        club_counts[p["team"]] = club_counts.get(p["team"], 0) + 1

    # Every positive-gain (out → in) pair; the shortlist is then a disjoint pick from these.
    pairs = []
    for out in owned:
        budget = out["price"] + bank
        out_sum = _summary(out, rank_xp)
        out_sum["leaving"] = reported_out.get(out["id"])
        for c in players:
            if (c["position"] == out["position"]
                    and c["id"] not in owned_ids
                    and not is_unavailable(c)
                    and c["id"] not in reported_out      # never buy someone on his way out (ADR-156)
                    and c["price"] <= budget
                    and _club_ok(out, c, club_counts, max_per_club)):
                in_sum = _summary(c, xp_by_id)
                if xi_aware:   # how much the swap lifts the best legal XI (ADR-046)
                    after = best_xi_points([p for p in owned if p["id"] != out["id"]] + [c], rank_xp)
                    gain = round(after - base_xi, 1)
                else:
                    gain = round(in_sum["xp"] - out_sum["xp"], 1)
                if gain > 0:
                    pairs.append((gain, out, out_sum, c, in_sum))

    pairs.sort(key=lambda t: t[0], reverse=True)

    used_out: set = set()
    used_in: set = set()
    suggestions = []
    while len(suggestions) < limit:
        eligible = [t for t in pairs if t[1]["id"] not in used_out and t[3]["id"] not in used_in]
        if not eligible:
            break
        # ADR-189 — among moves the model cannot tell apart, prefer the one leaving less correlated defence.
        #
        # The owner, on a suggestion to sell his Arsenal defender for a Sunderland one while already holding
        # a Sunderland defender: *"he would be a better option to transfer to Ballard maybe."* He was right,
        # and the model had chosen on **1.7 xP over five gameweeks** — 0.34 a week against a per-player
        # weekly sd of 3.51 (ADR-161). A coin flip presented as a ranking.
        #
        # ⚠️ **A band around the leader, not a bucket.** This shipped first as `round(gain / TIE_NOISE)` in a
        # sort key, and **it did not work**: 11.4 and 9.7 are 1.7 apart — inside the band — yet round to 6 and
        # 5, so the tie-break never engaged. **Quantising is not the same as "within noise of each other"**;
        # bucket edges fall where they fall, and two near-equal values can land either side of one. Comparing
        # each candidate against the current leader has no edges.
        #
        # Still never overrides a real difference: only moves within `TIE_NOISE` of the best are considered.
        best_gain = eligible[0][0]
        close = [t for t in eligible if best_gain - t[0] <= TIE_NOISE]
        gain, out, out_sum, c, in_sum = min(close, key=lambda t: (_correlated_after(t[1], t[3], owned), -t[0]))
        used_out.add(out["id"])
        used_in.add(c["id"])
        suggestions.append({
            "position": out["position"],
            "out": out_sum,
            "in": in_sum,
            "gain": gain,
            "out_on_bench": out["id"] in bench,
        })
    return suggestions


def suggest_transfer_plan(
    owned, players, xp_by_id, *,
    bench_ids=(), bank: float = 0.0, count: int = 1, max_per_club: int = MAX_PER_CLUB,
    xi_aware: bool = True, reported_out=None,
) -> list[dict]:
    """A coordinated, greedy plan of up to `count` transfers (ADR-035).

    Repeatedly takes the **best legal single transfer given the running state** and applies
    it: the shared **bank threads** (a later move can spend what an earlier sale freed), club
    counts and ownership update, and no player is bought twice or a sold one re-bought. Reuses
    `suggest_transfers` on the evolving state, so every single-transfer rule holds across the
    plan. Returns the ordered moves, each annotated with `bank_after`; stops early when no
    positive-gain move remains. `reported_out` threads through to every step (ADR-156), so a departing player
    is worth zero on move 3 for the same reason he is on move 1.
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
            limit=1, max_per_club=max_per_club, xi_aware=xi_aware, reported_out=reported_out,
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
