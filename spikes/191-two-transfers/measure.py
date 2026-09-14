"""Does the single-move recommendation leave points on the table when you hold 2 free transfers?

Owner, 2026-09-14, on a "Worth saving for: £1.0m more makes this M.Sangaré → Rayan" line:

    "I have £1.0m in the bank, I have 2 free transfers for the next gameweek, so is this advice the best
     or most effective? Should we not be triangulating number of available transfers, spending the money
     on the starting 11, looking at budget and then making a decision?"

Three strategies, same squad, same bank, same 5-GW xP map, all scored as the lift to the **best legal XI**:

  A  ONE    — the app's current answer: the single best move (what `suggest_transfers` returns first).
  B  GREEDY — take A, then the best move from the *resulting* squad with the *remaining* bank. Two moves,
              chosen one at a time. This is what a manager does if they follow the app twice.
  C  JOINT  — the best **pair** of moves chosen together, sharing one budget. Two moves, chosen as a plan.

C − B is the value of *planning* two moves instead of taking two greedy ones.
B − A is the value of the second transfer at all — the number the app never shows.

    venv/bin/python spikes/191-two-transfers/measure.py [n_squads] [bank]
"""
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.optimizer import best_xi_points, is_unavailable   # noqa: E402
from src.analytics.xp import decision_xp                    # noqa: E402
from src.storage import Storage                             # noqa: E402

MAX_PER_CLUB, HORIZON, TOP_K = 3, 5, 6


def load():
    store = Storage()
    try:
        players = store.get_players()
        ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                             horizon=HORIZON, gw_history_by_code=store.get_gw_history_by_code())
    finally:
        store.close()
    return players, {r["id"]: r["xp"] for r in ranked}


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


def club_ok(out, cand, squad):
    counts = Counter(p["team"] for p in squad if p["id"] != out["id"])
    return counts[cand["team"]] + 1 <= MAX_PER_CLUB


def moves_for(squad, market, xp, bank):
    """Every (out, in) this squad can legally make, keeping only the top-K incoming by xP per outgoing —
    the shortlist keeps the pair search tractable without changing which single move wins."""
    owned = {p["id"] for p in squad}
    out_moves = []
    for out in squad:
        budget = out["price"] + bank
        cands = [c for c in market
                 if c["position"] == out["position"] and c["id"] not in owned
                 and not is_unavailable(c) and c["price"] <= budget and club_ok(out, c, squad)]
        cands.sort(key=lambda c: -xp.get(c["id"], 0.0))
        out_moves += [(out, c) for c in cands[:TOP_K]]
    return out_moves


def apply(squad, out, cand):
    return [p for p in squad if p["id"] != out["id"]] + [cand]


def main(n_squads=30, bank=1.0, seed=5):
    market, xp = load()
    by_pos = {}
    for p in market:
        if not is_unavailable(p):
            by_pos.setdefault(p["position"], []).append(p)

    rng = random.Random(seed)
    rows = []
    while len(rows) < n_squads:
        squad = random_squad(by_pos, rng)
        if squad is None:
            continue
        base = best_xi_points(squad, xp)

        singles = moves_for(squad, market, xp, bank)
        if not singles:
            continue
        scored = sorted(((best_xi_points(apply(squad, o, c), xp) - base, o, c) for o, c in singles),
                        key=lambda t: -t[0])
        a_gain, a_out, a_in = scored[0]

        # B — greedy: take A, then the best move from what is left, with what is left of the money.
        s2 = apply(squad, a_out, a_in)
        bank2 = bank + a_out["price"] - a_in["price"]
        base2 = best_xi_points(s2, xp)
        second = sorted(((best_xi_points(apply(s2, o, c), xp) - base2, o, c)
                         for o, c in moves_for(s2, market, xp, bank2)), key=lambda t: -t[0])
        b_gain = a_gain + (second[0][0] if second and second[0][0] > 0 else 0.0)

        # C — joint: the best PAIR, chosen together, sharing one budget.
        c_gain, c_pair = a_gain, (a_out, a_in, None, None)
        for g1, o1, c1 in scored[:12]:                      # the pair's first leg is one of the best singles
            s_mid = apply(squad, o1, c1)
            bank_mid = bank + o1["price"] - c1["price"]
            mid = best_xi_points(s_mid, xp)
            for o2, c2 in moves_for(s_mid, market, xp, bank_mid):
                if o2["id"] == c1["id"]:
                    continue                                 # don't sell what you just bought
                total = best_xi_points(apply(s_mid, o2, c2), xp) - base
                if total > c_gain:
                    c_gain, c_pair = total, (o1, c1, o2, c2)
        rows.append({"a": a_gain, "b": b_gain, "c": c_gain, "pair": c_pair,
                     "a_move": (a_out["web_name"], a_in["web_name"])})

    def mean(k):
        return sum(r[k] for r in rows) / len(rows)

    print(f"{len(rows)} random legal squads · bank £{bank:.1f}m · {HORIZON}-GW XI xP · seed {seed}\n")
    print(f"  A  one move (what the app says)   mean +{mean('a'):.1f}")
    print(f"  B  two moves, taken greedily      mean +{mean('b'):.1f}   (+{mean('b')-mean('a'):.1f} vs A)")
    print(f"  C  two moves, planned together    mean +{mean('c'):.1f}   (+{mean('c')-mean('b'):.1f} vs B)")
    diff = [r for r in rows if r["c"] - r["b"] > 0.05]
    print(f"\n  squads where planning the pair beats taking two greedily: {len(diff)}/{len(rows)}")
    if diff:
        worst = max(diff, key=lambda r: r["c"] - r["b"])
        o1, c1, o2, c2 = worst["pair"]
        print(f"  biggest gap +{worst['c']-worst['b']:.1f}: greedy starts {worst['a_move'][0]} → "
              f"{worst['a_move'][1]}; the plan is {o1['web_name']} → {c1['web_name']}"
              + (f" + {o2['web_name']} → {c2['web_name']}" if o2 else ""))
    # where does the money land?
    print(f"\n  A's incoming player makes the XI in: "
          f"{sum(1 for r in rows if r['a'] > 0)}/{len(rows)} squads (a positive XI gain means he starts)")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    b = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    sd = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    main(n, b, sd)
