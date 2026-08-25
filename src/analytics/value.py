"""Value analytics — the project's first derived metric, and the frontier built on it.

Points-per-£m answers a simple question: "how many points does each £1m of a
player's price buy?" It's the first number the app calculates rather than reads.

`value_frontier` (ADR-138) asks the sharper version of the same question: **at your price, who is actually
worth buying?** Measured on live data, choosing well *within* a price bracket is worth about as much as moving
up one — the best £4.5 player is 11.9 xP clear of the median £4.5 player over five gameweeks — and no ranked
list in the app puts those two decisions side by side. The frontier is also not the same set as "the best
players": only 4 of the 8 players on it are in the top 8 by raw xP. The other half is the whole point.
"""

from statistics import median


def points_per_million(total_points, price):
    """Points per £1m of price.

    Returns None when the value is *undefined* — price missing or <= 0 — rather
    than inventing a number. A 0-price player isn't genuinely "worth zero", and
    dividing by zero has no answer, so we say "undefined" and let the caller show
    a dash and sort it last.
    """
    if total_points is None or not price or price <= 0:
        return None
    return total_points / price


def rank_players(rows, sort_by: str = "points") -> list[dict]:
    """Attach a `value` (points-per-£m) to each row, then sort.

    `rows` is a sequence of mappings (e.g. from Storage.get_players()). Returns a
    list of plain dicts. With sort_by="value", best value ranks first and
    undefined values sort to the bottom; otherwise rows are ranked by total points.
    """
    enriched = []
    for row in rows:
        data = dict(row)
        data["value"] = points_per_million(data.get("total_points"), data.get("price"))
        enriched.append(data)

    if sort_by == "value":
        # (has-value, value): the first element pushes None values to the bottom.
        enriched.sort(
            key=lambda d: (d["value"] is not None, d["value"] or 0.0),
            reverse=True,
        )
    else:
        enriched.sort(key=lambda d: d.get("total_points") or 0, reverse=True)

    return enriched


def _get(row, key, default=None):
    """Row/dict safe read — these take sqlite3.Row in the app and plain dicts in tests."""
    try:
        v = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if v is None else v


def value_frontier(rows, xp_by_id, *, price_step: float = 0.1, unproven=()) -> list[dict]:
    """Position every player against price, and mark the efficient frontier (ADR-138).

    Returns one dict per player: the row itself, `xp`, `peer_median` (the median xP of everyone at the **same
    price**), `edge` (how far above or below those peers they are), and `frontier` — True when **nobody
    cheaper scores more**.

    The frontier is the honest reading of "good value", and it is deliberately not points-per-£m: a ratio
    flatters cheap players who score a little (a £4.0 player on 4 xP beats Haaland on that measure and is not
    a better pick). *Nobody cheaper scores more* has no such failure mode — it is a statement you can act on.

    `peer_median` is what turns a dot into a sentence. "16.9 xP" means nothing until you know the median £4.5
    player manages 5.0, and then it means everything.

    `price_step` groups the peers, since FPL prices land on 0.1 boundaries and float equality is not something
    to trust. Players with no xP entry are scored 0.0 — they are real squad options that happen to be worth
    nothing, and hiding them would flatter the pool.

    `unproven` is the set of player ids whose xP has **no minutes behind it this season** (`minutes.yet_to_play`)
    — their team has played and they did not. They are **excluded from the frontier but keep their entry**, and
    that split is the whole point:

    * *Off the frontier*, because "nobody cheaper scores more" is a claim about who to buy, and it must not be
      made on behalf of a player with evidence he does not start. The owner caught this immediately on a £4.0
      backup keeper whose 9.9 xP rested on 35 starts at a former club, while the keeper who actually played
      that gameweek scored 2.3. The frontier's cheap end is exactly where the xMins model is weakest (the
      in-season minutes share is deferred to ~GW4-6, ADR-125), so it is where the claim needs the most care.
    * *Still plotted and still scored*, because the number itself is not wrong — it is unsupported. Deleting
      him would hide a player some managers own; silently discounting him would invent a minutes correction
      the calibration has not earned. Marking is the honest middle.

    They remain in the **peer median**: an unproven player is still someone you could buy at that price, and
    leaving him in makes every edge slightly smaller — the conservative direction.
    """
    scored = [{"player": p, "price": float(_get(p, "price", 0.0) or 0.0),
               "xp": float(xp_by_id.get(_get(p, "id"), 0.0) or 0.0)}
              for p in rows]
    scored = [s for s in scored if s["price"] > 0]
    if not scored:
        return []

    # Peers = everyone at the same price. Keyed on an integer number of steps so 4.5 and 4.5 always agree.
    peers: dict = {}
    for s in scored:
        peers.setdefault(round(s["price"] / price_step), []).append(s["xp"])
    peer_median = {k: median(v) for k, v in peers.items()}

    # The frontier: walk cheapest-first and keep anyone who beats every cheaper player. Ties at one price are
    # ordered best-first so the strict `>` admits the best of them and correctly rejects the rest.
    # Unproven players are skipped entirely — they cannot claim the frontier, and they must not raise the bar
    # for anyone dearer either. A backup keeper on last season's form should not be able to knock the best
    # *playing* £4.5 player off the frontier by standing in front of him.
    unproven_ids = set(unproven)
    best_so_far = float("-inf")
    on_frontier = set()
    for s in sorted(scored, key=lambda s: (s["price"], -s["xp"])):
        if _get(s["player"], "id") in unproven_ids:
            continue
        if s["xp"] > best_so_far:
            best_so_far = s["xp"]
            on_frontier.add(id(s))

    out = []
    for s in scored:
        key = round(s["price"] / price_step)
        med = peer_median[key]
        out.append({
            "player": s["player"],
            "price": s["price"],
            "xp": round(s["xp"], 1),
            "peer_median": round(med, 1),
            "edge": round(s["xp"] - med, 1),
            # How many players share this price — including them. At the top of the market a player can be
            # the *only* one at his price, and "exactly the median for £15.5" is then a fact about a group of
            # one. The caller needs to know that to avoid saying something vacuous.
            "peers": len(peers[key]),
            "unproven": _get(s["player"], "id") in unproven_ids,
            "frontier": id(s) in on_frontier,
        })
    return out


def frontier_verdict(entry, *, horizon: int = 5) -> str:
    """The sentence a hover should show — a finding, not a coordinate (ADR-138).

    A dot at (4.5, 16.9) is a fact. *"11.9 xP more than the median £4.5 player, and nobody cheaper scores
    more"* is the thing that makes someone act, and it is computed here rather than in the view so it can be
    tested like any other claim the app makes.
    """
    p = entry["player"]
    window = f"{horizon} GW" if horizon != 1 else "next GW"
    lines = [f"{_get(p, 'web_name', '?')} · £{entry['price']:.1f} {_get(p, 'position', '')} — "
             f"{entry['xp']:.1f} xP over {window}"]
    if entry.get("peers", 0) <= 1:
        # He is the only player at his price — there are no peers to be above or below, so say nothing rather
        # than "exactly the median", which is true of a group of one and tells you nothing.
        lines.append(f"the only player at £{entry['price']:.1f}")
    elif entry["edge"] > 0:
        lines.append(f"+{entry['edge']:.1f} xP vs the median £{entry['price']:.1f} player")
    elif entry["edge"] < 0:
        lines.append(f"{entry['edge']:.1f} xP vs the median £{entry['price']:.1f} player")
    else:
        lines.append(f"exactly the median for £{entry['price']:.1f}")
    if entry["frontier"]:
        lines.append("On the value frontier — nobody cheaper scores more")
    if entry.get("unproven"):
        # Last, and unmissable. This is the caveat that stops the chart's best-looking cheap picks from being
        # its least trustworthy ones — the owner spotted it immediately on a backup keeper (ADR-138).
        lines.append("⚠ has not played a minute this season — this rests entirely on last season")
    return " · ".join(lines)
