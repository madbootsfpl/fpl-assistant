"""Transfer suggestions (ADR-030) — best single legal upgrades for a squad.

Pure: given a squad, the transfer market, and each player's xP over a horizon, it
returns the best legal, affordable, available same-position replacement per owned
player, ranked by xP gain. No I/O — the caller loads the squad, computes xP, and
formats the result. It respects FPL's rules (same position, ≤3/club, budget) so a
suggestion is always a move you could actually make.
"""

from src.analytics.optimizer import MAX_PER_CLUB, is_unavailable


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
) -> list[dict]:
    """Rank the best single transfers for a squad by xP gain (ADR-030).

    `owned` are the squad's player rows; `players` is the whole market; `xp_by_id`
    maps player id → xP over the chosen horizon (the caller computes it). For each owned
    player, the best legal replacement is: same position, not already owned, available
    (`is_unavailable`), affordable (`price ≤ out.price + bank`), and ≤ `max_per_club` per
    club after the swap. Only **positive-gain** moves are returned, highest gain first,
    capped at `limit`. Each result flags whether the outgoing player is on the bench
    (`bench_ids`) — a bench upgrade helps the weekly score less.
    """
    owned_ids = {p["id"] for p in owned}
    bench = set(bench_ids)

    club_counts: dict = {}
    for p in owned:
        club_counts[p["team"]] = club_counts.get(p["team"], 0) + 1

    suggestions = []
    for out in owned:
        budget = out["price"] + bank
        candidates = [
            c for c in players
            if c["position"] == out["position"]
            and c["id"] not in owned_ids
            and not is_unavailable(c)
            and c["price"] <= budget
            and _club_ok(out, c, club_counts, max_per_club)
        ]
        if not candidates:
            continue

        best = max(candidates, key=lambda c: xp_by_id.get(c["id"], 0))
        out_sum, in_sum = _summary(out, xp_by_id), _summary(best, xp_by_id)
        gain = round(in_sum["xp"] - out_sum["xp"], 1)
        if gain <= 0:
            continue

        suggestions.append({
            "position": out["position"],
            "out": out_sum,
            "in": in_sum,
            "gain": gain,
            "out_on_bench": out["id"] in bench,
        })

    suggestions.sort(key=lambda s: s["gain"], reverse=True)
    return suggestions[:limit]


def suggest_transfer_plan(
    owned, players, xp_by_id, *,
    bench_ids=(), bank: float = 0.0, count: int = 1, max_per_club: int = MAX_PER_CLUB,
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
            limit=1, max_per_club=max_per_club,
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
