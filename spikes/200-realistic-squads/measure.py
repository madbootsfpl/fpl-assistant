"""The two thresholds ADR-199 gated, measured across squad quality instead of on random squads.

⭐ **The point is the gradient, not a number.** ADR-199 could not set `_CLEAR_GAIN` or `_CLEAR_REBUILD`
because both had been measured on random squads, which are so bad that any improvement looks enormous. The
fix is not "measure on realistic squads" as though that were one thing — it is to measure **as a function of
squad quality** and then read off the value where the app's users actually are.

    venv/bin/python spikes/200-realistic-squads/measure.py
"""
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from population import BUDGET, MAX_PER_CLUB, ladder                      # noqa: E402

from src.analytics.chips import rebuild_value                            # noqa: E402
from src.analytics.optimizer import best_xi_points, is_unavailable       # noqa: E402
from src.analytics.transfer import suggest_transfers                     # noqa: E402
from src.analytics.xp import decision_xp                                 # noqa: E402
from src.storage import Storage                                          # noqa: E402


def pct(v, q):
    v = sorted(v)
    i = (len(v) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (i - lo)


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
    return squad if cost <= BUDGET else None


def main(seed=3):
    store = Storage()
    try:
        players = store.get_players()
        r1 = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                         horizon=1, gw_history_by_code=store.get_gw_history_by_code())
        r5 = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                         horizon=5, gw_history_by_code=store.get_gw_history_by_code())
    finally:
        store.close()
    xp1 = {r["id"]: r["xp"] for r in r1}
    xp5 = {r["id"]: r["xp"] for r in r5}
    by_id = {p["id"]: p for p in players}

    rng = random.Random(seed)
    by_pos = {}
    for p in players:
        if not is_unavailable(p):
            by_pos.setdefault(p["position"], []).append(p)

    groups = {}
    rnd = [s for s in (random_squad(by_pos, rng) for _ in range(20)) if s]
    if rnd:
        groups["random"] = rnd
    groups.update(ladder(players, xp5, seed=seed, per_step=14))
    # The owner's own squads — the only observed point on the whole chart.
    real = []
    for v in json.load(open("data/squads.json")).values():
        sq = [by_id[i] for i in v["player_ids"] if i in by_id]
        if len(sq) == 15:
            real.append(sq)
    if real:
        groups["REAL"] = real

    print(f"seed {seed} · transfer gain over ONE gameweek (what the app scores) and wildcard gain "
          f"as a share of the squad's own projection\n")
    print(f"  {'population':>11} {'n':>3} {'XI xP':>7} | {'transfer p50':>12} {'p75':>6} | "
          f"{'wildcard p50':>12} {'p75':>6}")
    print("  " + "-" * 74)
    for name, squads in groups.items():
        gains, rel = [], []
        for sq in squads:
            mv = suggest_transfers(sq, players, xp1, bank=0.0, limit=1)
            if mv:
                gains.append(mv[0]["gain"])
            rb = rebuild_value(sq, players, xp5, budget=round(sum(p["price"] for p in sq), 1))
            if rb and rb.get("current"):
                rel.append(max(0.0, rb["gain"]) / rb["current"])
        q = sum(best_xi_points(s, xp5) for s in squads) / len(squads)
        g = f"{pct(gains,.50):>12.2f} {pct(gains,.75):>6.2f}" if gains else f"{'—':>12} {'—':>6}"
        w = f"{pct(rel,.50):>12.2f} {pct(rel,.75):>6.2f}" if rel else f"{'—':>12} {'—':>6}"
        print(f"  {str(name):>11} {len(squads):>3} {q:>7.1f} | {g} | {w}")
    print("\n  chosen today: _CLEAR_GAIN 3.0 · _CLEAR_REBUILD 0.25")


if __name__ == "__main__":
    main()
