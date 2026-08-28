"""What a league is doing — effective ownership, captains, chips, movers (ADR-141).

**The number this exists for is effective ownership**, and one measurement justifies the whole module. Across
the top 20 managers in the world in GW1, Palmer sat at **90% EO** while his *global* ownership was **11.9%**.
Every other surface in this app reads that 11.9% and calls him a differential; among the people actually
winning, he was template. Those are opposite decisions, and global ownership — the only ownership number the
app had before this — cannot tell them apart.

EO counts the captain twice, because that is what it costs you: if a player you do not own is captained by
half your league, you lose double to half your league. Ownership alone understates the damage.

Pure and offline: these take already-fetched payloads and return numbers. The fetching, throttling and
caching live at the edge, where the network belongs.
"""

from collections import Counter

_BENCH_FROM = 12          # picks 1-11 start, 12-15 are the bench (same convention as `manager.py`)


def _get(row, key, default=None):
    try:
        v = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if v is None else v


def standings_rows(payload) -> list[dict]:
    """The league table from a standings payload — rank, movement, points. Empty-safe.

    `movement` is last rank minus current, so **positive means climbing**. A `last_rank` of 0 means the
    manager had no previous rank (the league's first gameweek, or a new entry), which is *not* a rise of 400
    places — it returns `None`, and the caller shows "new".
    """
    results = _get(_get(payload, "standings", {}), "results", []) or []
    rows = []
    for r in results:
        last = _get(r, "last_rank", 0) or 0
        rank = _get(r, "rank", 0) or 0
        rows.append({
            "entry": _get(r, "entry"),
            "manager": _get(r, "player_name", ""),
            "team": _get(r, "entry_name", ""),
            "rank": rank,
            "movement": (last - rank) if last else None,
            "gw_points": _get(r, "event_total", 0) or 0,
            "total": _get(r, "total", 0) or 0,
        })
    return rows


def league_name(payload) -> str:
    return _get(_get(payload, "league", {}), "name", "") or ""


def effective_ownership(picks_by_entry) -> dict:
    """`{player_id: EO%}` over the managers whose picks we have.

    EO = (starters owning + captains) ÷ managers × 100, so a player owned and captained by everyone reads
    **200%** and one owned by everyone but captained by nobody reads 100%. Bench players are excluded: a
    benched player scores you nothing (bar an auto-sub), so counting them would overstate exposure.

    `picks_by_entry` maps entry id → a `/entry/{id}/event/{gw}/picks/` payload. Managers whose fetch failed
    are simply absent, and the divisor is what we actually have — a partial league still gives a usable EO,
    which is why a partial fetch degrades rather than raises.
    """
    if not picks_by_entry:
        return {}
    owned, capped = Counter(), Counter()
    for payload in picks_by_entry.values():
        for pk in _get(payload, "picks", []) or []:
            pid = _get(pk, "element")
            if pid is None:
                continue
            if (_get(pk, "position", 99) or 99) < _BENCH_FROM:
                owned[pid] += 1
            if _get(pk, "is_captain"):
                capped[pid] += 1
    n = len(picks_by_entry)
    return {pid: round((c + capped[pid]) / n * 100, 1) for pid, c in owned.items()}


def captain_split(picks_by_entry) -> list[tuple]:
    """`[(player_id, count)]`, most-captained first — the spread, not just the winner.

    A 6/5/4 split across three players is a completely different week from 18/1/1, and only the shape says so.
    """
    counts = Counter()
    for payload in picks_by_entry.values():
        for pk in _get(payload, "picks", []) or []:
            if _get(pk, "is_captain") and _get(pk, "element") is not None:
                counts[_get(pk, "element")] += 1
    return counts.most_common()


def chip_usage(picks_by_entry) -> list[tuple]:
    """`[(chip, count)]` for the gameweek, most-played first. Managers playing no chip are counted as `none`.

    Free from the same payloads the EO comes from — `active_chip` is on every picks response. On the live GW1
    data, 18 of the top 20 played Bench Boost, which is the kind of consensus worth seeing as one number.
    """
    counts = Counter(_get(p, "active_chip") or "none" for p in picks_by_entry.values())
    return counts.most_common()


def ownership_gaps(eo_by_id, players, *, limit: int = 12) -> list[dict]:
    """The league's EO against **global** ownership, biggest gap first — the differential-or-template call.

    A positive gap means the league is *more* exposed than the wider game: owning that player is keeping up,
    not getting ahead. A negative gap is where a differential actually exists.

    Players missing from `players` (a stale id) are skipped rather than guessed at.
    """
    by_id = {p["id"]: p for p in players}
    out = []
    for pid, eo in eo_by_id.items():
        p = by_id.get(pid)
        if p is None:
            continue
        glob = float(_get(p, "selected_by", 0.0) or 0.0)
        out.append({"id": pid, "player": p, "eo": eo, "global": round(glob, 1), "gap": round(eo - glob, 1)})
    return sorted(out, key=lambda r: -abs(r["gap"]))[:limit]


def last_completed_gameweek(upcoming) -> int | None:
    """The most recent gameweek whose picks are final, or None before any has been played.

    Derived from `get_upcoming_fixtures`, which cuts on the **gameweek deadline** (ADR-123): its first event
    is the next gameweek you can still act on, so the one before it is the last that is done. Reusing that
    rule rather than inventing a second one is deliberate — the two must not be able to disagree about where
    "now" is.

    This matters more here than elsewhere: it is what makes the picks cache safe to keep forever. Ask for the
    in-flight gameweek and the answer would still be changing underneath the cache.
    """
    events = sorted({e for f in upcoming or [] if (e := _get(f, "event")) is not None})
    if not events or events[0] <= 1:
        return None
    return events[0] - 1


def my_leagues(entry_payload) -> list[dict]:
    """The classic leagues a manager is in, from their `/entry/{id}/` payload (ADR-141 rev).

    **Nobody knows their league id.** It appears in a URL you have to go and find, which made the first cut of
    this page unusable for the thing it was built for — the owner had the page open, his own manager id to
    hand, and no way in. The manager id is the handle people actually have, and this payload already carries
    every league behind it, so the lookup costs one call that the app was making anyway.

    **Private leagues lead.** FPL mixes the mini-league you joined with your friends in among automatic ones —
    your club, your region, "Gameweek 1", Overall — and by `rank_count` the automatic ones are always bigger.
    Sorting by size would bury the only leagues anyone means. `league_type` separates them: `x` is a league
    somebody created, `s` is one FPL put you in. Private first, each group smallest-first, because a small
    league is a more personal one.

    Returns `{id, name, size, rank, private}` per league; empty for a manager with none, or a bad payload.
    """
    classic = _get(_get(entry_payload, "leagues", {}), "classic", []) or []
    out = []
    for lg in classic:
        lid = _get(lg, "id")
        if lid is None:
            continue
        out.append({
            "id": lid,
            "name": _get(lg, "name", "") or f"League #{lid}",
            "size": _get(lg, "rank_count", 0) or 0,
            "rank": _get(lg, "entry_rank"),
            "private": _get(lg, "league_type") == "x",
        })
    return sorted(out, key=lambda r: (not r["private"], r["size"]))


def manager_name(entry_payload) -> str:
    """A manager's team name, for confirming the id resolved to who they expected."""
    return _get(entry_payload, "name", "") or ""


# ---- Transfer flow (ADR-162) ----------------------------------------------------------------------
#
# Two halves with very different costs, kept apart for that reason. **The activity half is free**: FPL puts
# `entry_history` on every picks payload the league view has already fetched, and it carries how many
# transfers a manager made, what the hits cost and what they left on the bench. **The identity half is not**:
# which players moved needs `/entry/{id}/transfers/`, one more call per manager — the second N-call step on a
# page whose first one already spent N.

def transfer_activity(picks_by_entry) -> dict:
    """What the league *did* about its transfers — free, from the picks payloads already in hand.

    Returns `{"managers", "movers", "transfers", "hits", "hit_points", "bench_points", "bank"}`. `movers` is
    how many managers made at least one transfer, which is the number that says whether a gameweek was quiet
    or frantic; a total alone hides one manager taking a −12 among thirty who did nothing.
    """
    n = movers = transfers = hits = hit_points = bench = 0
    banks = []
    for payload in (picks_by_entry or {}).values():
        h = _get(payload, "entry_history", {}) or {}
        n += 1
        made = _get(h, "event_transfers", 0) or 0
        cost = _get(h, "event_transfers_cost", 0) or 0
        transfers += made
        movers += 1 if made else 0
        hits += 1 if cost else 0
        hit_points += cost
        bench += _get(h, "points_on_bench", 0) or 0
        bank_val = _get(h, "bank")
        if bank_val is not None:
            banks.append(bank_val / 10.0)
    return {
        "managers": n,
        "movers": movers,
        "transfers": transfers,
        "hits": hits,
        "hit_points": hit_points,
        "bench_points": bench,
        "bank": round(sum(banks) / len(banks), 1) if banks else None,
    }


def transfer_flow(transfers_by_entry, gameweek) -> dict:
    """Who the league moved in and out **in one gameweek** — `{"in": [(id, n)], "out": [(id, n)], "net": {}}`.

    `transfers_by_entry` maps entry id → that manager's whole-season transfer list; the gameweek filter is
    applied here because the endpoint has no per-gameweek form.

    `net` is in-count minus out-count per player, which is the number worth reading: a player with 6 in and 5
    out is not "popular", he is **churning**, and two separate top-tens would have shown him twice and said
    neither.
    """
    ins, outs = Counter(), Counter()
    for rows in (transfers_by_entry or {}).values():
        for t in rows or []:
            if _get(t, "event") != gameweek:
                continue
            if _get(t, "element_in") is not None:
                ins[_get(t, "element_in")] += 1
            if _get(t, "element_out") is not None:
                outs[_get(t, "element_out")] += 1
    net = {pid: ins[pid] - outs.get(pid, 0) for pid in set(ins) | set(outs)}
    return {"in": ins.most_common(), "out": outs.most_common(), "net": net}


def flow_rows(flow, players, *, limit: int = 10) -> list[dict]:
    """The flow as one ranked table — biggest **net** move first, in or out.

    One table rather than two, because a manager comparing a buy against a sell should not have to hold two
    lists in their head; the sign does that work.
    """
    index = {p["id"]: p for p in players or []}
    rows = []
    for pid, net in (flow or {}).get("net", {}).items():
        p = index.get(pid)
        ins = dict(flow["in"]).get(pid, 0)
        outs = dict(flow["out"]).get(pid, 0)
        rows.append({
            "id": pid,
            "player": p["web_name"] if p is not None else f"#{pid}",
            "team": p["team"] if p is not None else "",
            "position": p["position"] if p is not None else "",
            "in": ins, "out": outs, "net": net,
        })
    rows.sort(key=lambda r: (-abs(r["net"]), -r["in"]))
    return rows[:limit]
