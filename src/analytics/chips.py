"""Chip-strategy guidance (ADR-082) — WHEN to play each chip, from a squad's per-GW xP + fixture run.

An **assembler**, not new analytics (the `gameweek_plan` shape, ADR-070): it reduces the per-GW xP the caller
already computed (`by_gameweek`, ADR-032) into one recommendation per chip, so the chip answer can't drift from
the standalone tools. Pure given its inputs (the only I/O is `best_legal_xi`'s in-memory solve); the `ask` layer
humanises + verifies it (ADR-034/037). Fixture-run + xP based — double/blank gameweeks and mini-league position
sharpen it in-season / at GW1 (a caption says so).
"""

from src.analytics.optimizer import best_legal_xi

# The chips, in the order we present them (ceiling first, then the whole-squad and reset chips).
CHIP_NAMES = ("Triple Captain", "Bench Boost", "Free Hit", "Wildcard")

_WILDCARD_WINDOW = 3        # the rolling stretch (GWs) a wildcard resets for; clamped to the horizon


def _points(by_gameweek_by_id, owned, gw) -> dict:
    """Each owned player's xP in gameweek `gw` (id → xP), 0 where absent. Empty-safe."""
    return {p["id"]: (by_gameweek_by_id.get(p["id"], {}) or {}).get(gw, 0.0) for p in owned}


def _gap(values, *, largest) -> float:
    """The separation between the best and the next-best value (US-272) — how clearly the recommended
    gameweek/window wins. `largest=True` when the best is the max (TC/BB), False when it's the min (FH/WC).
    0.0 when there's nothing to compare against."""
    if len(values) < 2:
        return 0.0
    ordered = sorted(values, reverse=largest)
    return round(abs(ordered[0] - ordered[1]), 1)


def _rank(gameweeks, values, *, largest):
    """Gameweeks ordered best-first for one chip, as `[(gameweek, value)]` — the fallbacks if its first
    choice is taken by another chip."""
    return sorted(zip(gameweeks, values), key=lambda t: t[1], reverse=largest)


def _relative_gap(options) -> float:
    """How much a chip loses by dropping to its second choice, **as a share of its own best value**.

    Dimensionless on purpose. The absolute margins are not comparable between chips: Triple Captain's is a
    single player's ceiling, Bench Boost's is a whole-squad total, Free Hit's is a bad week's XI. Comparing
    those raw picks the chip with the biggest *numbers*, not the chip with the most at stake — and Bench Boost
    always has the biggest numbers, because its total includes the very spike that made Triple Captain want
    that week in the first place. (Measured: a squad where TC's margin read 24.1 and BB's 29.4 off the *same*
    player, so the raw comparison moved the wrong chip.)

    A share of its own scale is comparable: *"this chip gives up 80% of what it came for"* means the same
    thing for all three.
    """
    if len(options) < 2:
        return 0.0
    best, second = options[0][1], options[1][1]
    return abs(best - second) / max(abs(best), 1e-9)


def _one_per_gameweek(*chips, ranks) -> None:
    """Force the chips onto **distinct** gameweeks, in place. FPL allows one chip per gameweek.

    **Which chip moves: the one with the least at stake**, measured by `_relative_gap` — the share of its own
    value it gives up by dropping to its next choice. Deliberately *not* "maximise total xP across the chips":
    Triple Captain's value is extra captain points, Bench Boost's is bench points and Free Hit's is a bad week
    avoided. Those are three different currencies, and adding them would look rigorous while meaning nothing.

    Each moved chip records `moved_from` and `cost` — what the move actually gives up, in that chip's own
    units. On live data that cost is **0.0 xP at the median and 0.6 at the worst** over eight gameweeks, which
    is why the surfaces state it: the point is that the app stops advising something illegal, not that it
    found you points.
    """
    keys = {id(c): k for k, c in zip(("triple_captain", "bench_boost", "free_hit"), chips)}
    taken = set()
    # Most at stake first — that chip keeps the week it wants, and the others work around it.
    for chip in sorted(chips, key=lambda c: -_relative_gap(ranks[keys[id(c)]])):
        options = ranks[keys[id(chip)]]
        first = chip["gameweek"]
        if first not in taken:
            taken.add(first)
            continue
        alternative = next(((gw, val) for gw, val in options if gw not in taken), None)
        if alternative is None:                          # fewer gameweeks than chips — leave it where it is
            continue
        original = next((val for gw, val in options if gw == first), None)
        chip["moved_from"] = first
        chip["gameweek"] = alternative[0]
        chip["cost"] = abs(round(original - alternative[1], 1)) if original is not None else 0.0
        taken.add(alternative[0])


def chip_advisor(owned, by_gameweek_by_id, gameweeks) -> dict | None:
    """Recommend the best gameweek (or window) for each chip, from the squad's per-GW xP.

    `owned` are the squad's 15 player rows; `by_gameweek_by_id` is `{id → {gw → xP}}` (from
    `decision_xp`, ADR-032); `gameweeks` the horizon's GW numbers in order. Returns
    ``{triple_captain, bench_boost, free_hit, wildcard}`` (each a dict), or None if there's nothing to
    reduce (no players / no gameweeks). Each reduction is a decomposition of `by_gameweek` + the best
    legal XI that GW — so it agrees with the lineup/captain tools by construction.
    """
    if not owned or not gameweeks:
        return None

    by_id = {p["id"]: p for p in owned}
    # Per GW: the per-player xP, the best legal XI (ids), that XI's total, and the whole-15 total.
    per_gw = {}
    for gw in gameweeks:
        pts = _points(by_gameweek_by_id, owned, gw)
        xi = best_legal_xi(owned, pts)
        per_gw[gw] = {
            "pts": pts,
            "xi": xi,
            "xi_total": round(sum(pts[i] for i in xi), 1),
            "squad_total": round(sum(pts.values()), 1),
        }

    # The `margin` on each chip is how clearly the recommended gameweek/window beats the next-best — the
    # separation the explainability layer turns into a confidence (small margin = a preseason-flat, low-confidence
    # call). ADR-089.
    tc_ceilings = [max((per_gw[gw]["pts"][i] for i in per_gw[gw]["xi"]), default=0.0) for gw in gameweeks]
    bb_totals = [per_gw[gw]["squad_total"] for gw in gameweeks]
    xi_totals = [per_gw[gw]["xi_total"] for gw in gameweeks]

    # Triple Captain — the single starter with the highest ceiling in any GW (a TC only lifts a starter).
    tc_gw, tc_id, tc_val = None, None, -1.0
    for gw in gameweeks:
        g = per_gw[gw]
        for i in g["xi"]:
            if g["pts"][i] > tc_val:
                tc_gw, tc_id, tc_val = gw, i, g["pts"][i]
    tc_player = by_id.get(tc_id)
    triple_captain = {
        "gameweek": tc_gw,
        "player": tc_player,
        "player_xp": round(tc_val, 1),
        "extra_points": round(tc_val, 1),   # TC = ×3 vs a ×2 captain → an extra ×1 of the player's GW xP
        "margin": _gap(tc_ceilings, largest=True),
    }

    # Bench Boost — the GW where all 15 score most (the bench's points count this week).
    bb_gw = max(gameweeks, key=lambda gw: per_gw[gw]["squad_total"])
    bb = per_gw[bb_gw]
    bench_boost = {
        "gameweek": bb_gw,
        "squad_total": bb["squad_total"],
        "bench_points": round(bb["squad_total"] - bb["xi_total"], 1),
        "margin": _gap(bb_totals, largest=True),
    }

    # Free Hit — the squad's weakest single week (lowest best-XI xP): a one-off to cover a bad GW.
    fh_gw = min(gameweeks, key=lambda gw: per_gw[gw]["xi_total"])
    free_hit = {
        "gameweek": fh_gw,
        "xi_total": per_gw[fh_gw]["xi_total"],
        "margin": _gap(xi_totals, largest=False),   # how much lower the worst week is than the next-worst
    }

    # Wildcard — the weakest sustained stretch (lowest rolling window of best-XI xP): reset before it.
    window = min(_WILDCARD_WINDOW, len(gameweeks))
    starts = range(len(gameweeks) - window + 1)
    win_avgs = [round(sum(per_gw[gameweeks[s + k]]["xi_total"] for k in range(window)) / window, 1)
                for s in starts]
    best_start = min(starts, key=lambda s: win_avgs[s])
    win_gws = gameweeks[best_start:best_start + window]
    wildcard = {
        "window": (win_gws[0], win_gws[-1]),
        "gameweeks": list(win_gws),
        "avg_xi": win_avgs[best_start],
        "margin": _gap(win_avgs, largest=False),
    }

    # **One chip per gameweek** (ADR-143). Each chip above was chosen independently, so nothing stopped two of
    # them naming the same week — measured at **28% of squads** over an 8-GW horizon, and the app was then
    # advising a move FPL forbids, contradicting its own rules base ("You can play only one chip per
    # gameweek", `fpl_rules`). Resolved here rather than at a surface, so every caller inherits legal advice.
    _one_per_gameweek(triple_captain, bench_boost, free_hit,
                      ranks={"triple_captain": _rank(gameweeks, tc_ceilings, largest=True),
                             "bench_boost": _rank(gameweeks, bb_totals, largest=True),
                             "free_hit": _rank(gameweeks, xi_totals, largest=False)})

    return {
        "triple_captain": triple_captain,
        "bench_boost": bench_boost,
        "free_hit": free_hit,
        "wildcard": wildcard,
    }
