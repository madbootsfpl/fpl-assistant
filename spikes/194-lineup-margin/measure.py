"""How big is a start/bench call, really? (ADR-194)

The lineup advice says *"Start Thomas over Konsa (higher projected xP: 2.7 vs 2.6)"* and has **no threshold**:
any gap above zero is stated as an instruction. Every other surface has one — captain `WHISKER 0.3`/`CLEAR
1.3` (ADR-144), transfers `TIE_NOISE 2.0` (ADR-189), chips a 15% relative margin.

This measures the distribution the threshold has to come from: for random legal squads with a random legal
declared XI, the xP gap of each swap the plan would actually print. ⚠️ Two seeds, because one sample of a
random process is not a measurement (ADR-183).

    venv/bin/python spikes/194-lineup-margin/measure.py
"""
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.optimizer import best_legal_xi, is_unavailable   # noqa: E402
from src.analytics.xp import decision_xp                            # noqa: E402
from src.storage import Storage                                     # noqa: E402

MAX_PER_CLUB, N = 3, 250
SHAPES = [(d, m, f) for d in range(3, 6) for m in range(2, 6) for f in range(1, 4) if d + m + f == 10]


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
    return squad if cost <= 100.0 else None


def declared_xi(squad, rng):
    """A legal but arbitrary XI — what a manager who has not optimised is fielding."""
    by = {}
    for p in squad:
        by.setdefault(p["position"], []).append(p)
    d, m, f = rng.choice(SHAPES)
    return {rng.choice(by["GK"])["id"], *[p["id"] for p in rng.sample(by["DEF"], d)],
            *[p["id"] for p in rng.sample(by["MID"], m)], *[p["id"] for p in rng.sample(by["FWD"], f)]}


def main():
    store = Storage()
    try:
        players = store.get_players()
        ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                             horizon=1, gw_history_by_code=store.get_gw_history_by_code())
    finally:
        store.close()
    xp = {r["id"]: r["xp"] for r in ranked}
    by_pos = {}
    for p in players:
        if not is_unavailable(p):
            by_pos.setdefault(p["position"], []).append(p)

    print(f"{N} random squads per seed, each with an arbitrary legal declared XI · next-GW xP\n")
    print(f"{'seed':>5} | {'swaps':>6} {'p25':>6} {'median':>7} {'p75':>6} {'p90':>6} {'max':>6}"
          f" | {'≤0.1':>6} {'≤0.3':>6} {'≤0.5':>6}")
    for seed in (3, 17):
        rng = random.Random(seed)
        gaps, made = [], 0
        while made < N:
            squad = random_squad(by_pos, rng)
            if squad is None:
                continue
            made += 1
            declared = declared_xi(squad, rng)
            optimal = best_legal_xi(squad, xp)
            bring = sorted((p for p in squad if p["id"] in optimal - declared), key=lambda p: -xp.get(p["id"], 0))
            drop = sorted((p for p in squad if p["id"] in declared - optimal), key=lambda p: -xp.get(p["id"], 0))
            gaps += [round(xp.get(b["id"], 0) - xp.get(d["id"], 0), 2) for b, d in zip(bring, drop)]
        share = lambda t: f"{100 * sum(1 for g in gaps if g <= t) / len(gaps):.0f}%"   # noqa: E731
        print(f"{seed:>5} | {len(gaps):>6} {pct(gaps,.25):>6.2f} {pct(gaps,.50):>7.2f} {pct(gaps,.75):>6.2f}"
              f" {pct(gaps,.90):>6.2f} {max(gaps):>6.2f} | {share(0.1):>6} {share(0.3):>6} {share(0.5):>6}")
    print("\n  Per-player weekly sd is 3.51 (ADR-161), so a swap's own spread is wider still — roughly 5.0.")


if __name__ == "__main__":
    main()
