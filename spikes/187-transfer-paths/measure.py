"""ADR-187 — does a planned 2-3 move SEQUENCE beat the greedy move repeated?

The measurement that ADR-187 gates on. ADR-132 declined a multi-gameweek transfer-path planner in August on
a prototype that found *"one beneficial move — a tree with one branch"*; that was measured preseason, on an
xP model ADR-172 and ADR-173 have since corrected across 186 players. This re-runs the question that
actually decides it, which is **not** "how many branches are there" but ADR-132's own finding:

> *"the gain moves; the DECISION does not."*

Both strategies get the same budget: **one free transfer per gameweek, no hits, money carried between
moves**. The only difference is foresight.

  greedy   — each gameweek, take the best single move for the remaining horizon, then move on.
  planned  — choose up to N moves AND their timing together, to maximise total points over the window.

If planned does not beat greedy by a margin worth acting on, ADR-132's decline stands on current data and
ADR-187 closes.
"""
import itertools
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")

from src.analytics import available_players, decision_xp  # noqa: E402
from src.analytics.optimizer import MAX_PER_CLUB, XI_FLEX, best_legal_xi  # noqa: E402
from src.storage import Storage  # noqa: E402

HORIZON = 6
SHORTLIST = 10        # candidate (out, in) pairs carried into the sequence search


def load():
    store = Storage()
    try:
        players = store.get_players()
        ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                             horizon=HORIZON, gw_history_by_code=store.get_gw_history_by_code())
    finally:
        store.close()
    gws = ranked[0]["gameweeks"]
    per_gw = {r["id"]: r["by_gameweek"] for r in ranked}
    return players, per_gw, gws


# ⚠️ A local XI picker, because `best_legal_xi` runs a PuLP solve (~0.08s) and this measurement needs tens of
# thousands of them. The XI problem is tiny and exactly solvable by enumeration: one GK, then the best DEF/MID/
# FWD counts over the handful of legal shapes. `check_xi_picker()` asserts it agrees with the real one — a
# faster stand-in that quietly disagreed would invalidate the whole result.
_SHAPES = [(d, m, f)
           for d in range(XI_FLEX["DEF"][0], XI_FLEX["DEF"][1] + 1)
           for m in range(XI_FLEX["MID"][0], XI_FLEX["MID"][1] + 1)
           for f in range(XI_FLEX["FWD"][0], XI_FLEX["FWD"][1] + 1)
           if d + m + f == 10]


def xi_points(squad, per_gw, gw):
    """The best legal XI's points in one gameweek — the thing both strategies are maximising."""
    pts = {p["id"]: per_gw.get(p["id"], {}).get(gw, 0.0) for p in squad}
    by_pos = defaultdict(list)
    for p in squad:
        by_pos[p["position"]].append(pts[p["id"]])
    for v in by_pos.values():
        v.sort(reverse=True)
    gk = by_pos["GK"][0] if by_pos["GK"] else 0.0
    best = 0.0
    for d, m, f in _SHAPES:
        if len(by_pos["DEF"]) < d or len(by_pos["MID"]) < m or len(by_pos["FWD"]) < f:
            continue
        total = gk + sum(by_pos["DEF"][:d]) + sum(by_pos["MID"][:m]) + sum(by_pos["FWD"][:f])
        best = max(best, total)
    return best


def check_xi_picker(squad, per_gw, gws):
    """The fast picker must agree with `best_legal_xi` — asserted before any measurement is reported."""
    for gw in gws[:2]:
        pts = {p["id"]: per_gw.get(p["id"], {}).get(gw, 0.0) for p in squad}
        exact = sum(pts[i] for i in best_legal_xi(squad, pts))
        assert abs(exact - xi_points(squad, per_gw, gw)) < 0.05, (
            f"the fast XI picker disagrees with best_legal_xi: {exact} vs {xi_points(squad, per_gw, gw)}")


def season(squad, per_gw, gws, moves):
    """Total XI points across `gws`, applying `moves` = {gameweek: (out_id, in_player)}."""
    cur, total = list(squad), 0.0
    for gw in gws:
        if gw in moves:
            out_id, incoming = moves[gw]
            cur = [p for p in cur if p["id"] != out_id] + [incoming]
        total += xi_points(cur, per_gw, gw)
    return round(total, 1)


def legal(squad, out, incoming, bank):
    if incoming["id"] in {p["id"] for p in squad}:
        return False
    if incoming["position"] != out["position"]:
        return False
    if incoming["price"] > out["price"] + bank + 1e-9:
        return False
    clubs = Counter(p["team"] for p in squad if p["id"] != out["id"])
    return clubs[incoming["team"]] < MAX_PER_CLUB


def candidates(squad, market, per_gw, gws, bank, limit=SHORTLIST):
    """Top (out, in) pairs by gain over the whole window — the pool both strategies draw from."""
    rest = gws
    def horizon_xp(pid):
        return sum(per_gw.get(pid, {}).get(g, 0.0) for g in rest)
    out = []
    for o in squad:
        for c in market:
            if legal(squad, o, c, bank):
                gain = horizon_xp(c["id"]) - horizon_xp(o["id"])
                if gain > 0:
                    out.append((gain, o, c))
    out.sort(key=lambda t: -t[0])
    return out[:limit]


def greedy(squad, market, per_gw, gws, bank, max_moves=3):
    """One transfer a gameweek, each chosen for the remaining horizon. No foresight.

    ⚠️ **Capped at the same `max_moves` as `planned`.** The first run of this measurement let greedy make one
    move per gameweek (six) while planned was limited to three, and reported planned losing by 12 points a
    squad. That was not a finding about foresight — it was a finding about **six transfers beating three**.
    A comparison in which the two strategies get different budgets measures the budget.
    """
    cur, cash, moves = list(squad), bank, {}
    for i, gw in enumerate(gws):
        if len(moves) >= max_moves:
            break
        rest = gws[i:]
        def hz(pid, rest=rest):
            return sum(per_gw.get(pid, {}).get(g, 0.0) for g in rest)
        best = None
        for o in cur:
            for c in market:
                if legal(cur, o, c, cash):
                    g = hz(c["id"]) - hz(o["id"])
                    if g > 0 and (best is None or g > best[0]):
                        best = (g, o, c)
        if not best:
            continue
        _, o, c = best
        moves[gw] = (o["id"], c)
        cash = round(cash + o["price"] - c["price"], 1)
        cur = [p for p in cur if p["id"] != o["id"]] + [c]
    return moves


def planned(squad, market, per_gw, gws, bank, max_moves=3, seed_moves=None):
    """Choose up to `max_moves` moves AND their gameweeks together — the thing ADR-132 declined.

    ⚠️ **Seeded with greedy's own answer, so planned can never lose.** Without that it did, by up to 13
    points — not because foresight hurt, but because this search draws from a shortlist computed **once**
    against the opening squad, while greedy re-scans the whole market after every move. That measures
    shortlist size, not planning.

    Seeded, `planned ≥ greedy` holds by construction and the reported gain is exactly what it should be:
    **what foresight adds on top of greedy**, which is the question ADR-187 asks.
    """
    pool = candidates(squad, market, per_gw, gws, bank)
    best = ({}, season(squad, per_gw, gws, {}))
    if seed_moves:
        best = (seed_moves, season(squad, per_gw, gws, seed_moves))
    for k in range(1, max_moves + 1):
        for combo in itertools.combinations(pool, k):
            outs = {o["id"] for _, o, _ in combo}
            ins = {c["id"] for _, _, c in combo}
            if len(outs) < k or len(ins) < k:
                continue                                   # one sell / one buy each
            for slots in itertools.combinations(gws, k):    # earliest-first timing
                cur, cash, moves, ok = list(squad), bank, {}, True
                for (_, o, c), gw in zip(combo, slots):
                    if not legal(cur, o, c, cash):
                        ok = False
                        break
                    moves[gw] = (o["id"], c)
                    cash = round(cash + o["price"] - c["price"], 1)
                    cur = [p for p in cur if p["id"] != o["id"]] + [c]
                if not ok:
                    continue
                total = season(squad, per_gw, gws, moves)
                if total > best[1]:
                    best = (moves, total)
    return best


def random_squad(by_pos, rng):
    squad, clubs, cost = [], Counter(), 0.0
    for pos, k in (("GK", 2), ("DEF", 5), ("MID", 5), ("FWD", 3)):
        picks = []
        for p in rng.sample(by_pos[pos], min(len(by_pos[pos]), 60)):
            if len(picks) == k:
                break
            if clubs[p["team"]] < MAX_PER_CLUB:
                picks.append(p)
                clubs[p["team"]] += 1
                cost += p["price"]
        if len(picks) < k:
            return None
        squad += picks
    return squad if cost <= 100.0 else None


def main(n_squads=24, seed=3):
    players, per_gw, gws = load()
    market = [p for p in available_players(players, keep_ids=set())[0]
              if sum(per_gw.get(p["id"], {}).values()) > 0]
    by_pos = defaultdict(list)
    for p in market:
        by_pos[p["position"]].append(p)

    rng = random.Random(seed)
    print(f"ADR-187 — planned sequence vs greedy, {HORIZON} gameweeks {gws}, 1 free transfer/week\n")
    print(f"{'squad':>6} {'do nothing':>11} {'greedy':>9} {'planned':>9} {'gain':>7} {'moves':>6}")
    diffs = []
    done = 0
    while done < n_squads:
        squad = random_squad(by_pos, rng)
        if not squad:
            continue
        done += 1
        if done == 1:
            check_xi_picker(squad, per_gw, gws)
        base = season(squad, per_gw, gws, {})
        g_moves = greedy(squad, market, per_gw, gws, 0.0)
        g_total = season(squad, per_gw, gws, g_moves)
        p_moves, p_total = planned(squad, market, per_gw, gws, 0.0, seed_moves=g_moves)
        diffs.append(p_total - g_total)
        print(f"{done:>6} {base:>11.1f} {g_total:>9.1f} {p_total:>9.1f} "
              f"{p_total - g_total:>+7.1f} {len(p_moves):>6}")

    diffs.sort()
    mid = diffs[len(diffs) // 2]
    print(f"\n  planned beats greedy by: median {mid:+.1f} · best {max(diffs):+.1f} · worst {min(diffs):+.1f}")
    print(f"  over {HORIZON} gameweeks, i.e. {mid / HORIZON:+.2f} points per gameweek at the median")


if __name__ == "__main__":
    main()
