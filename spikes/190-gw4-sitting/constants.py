"""Re-measure the single-GW constants at the GW4 sitting (GW1_RUNBOOK §B0, "Also in this sitting").

`WHISKER`/`CLEAR` (ADR-144) and `CONCENTRATED`/`HEAVY` (ADR-145) are quartiles of a distribution over
**random legal squads**, so re-measuring them is a resampling, not a re-reading. ⚠️ Run at two seeds and
compare: ADR-183's lesson is that one sample of a random process is not a measurement.

    venv/bin/python spikes/190-gw4-sitting/constants.py
"""
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.xp import decision_xp                      # noqa: E402
from src.storage import Storage                               # noqa: E402

MAX_PER_CLUB, N_SQUADS = 3, 300


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


def measure(seed, players, xp_by_id, by_pos):
    rng = random.Random(seed)
    margins, concentrations = [], []
    made = 0
    while made < N_SQUADS:
        squad = random_squad(by_pos, rng)
        if squad is None:
            continue
        made += 1
        # captain margin: the top two by xP in the squad (ADR-144)
        top = sorted((xp_by_id.get(p["id"], 0.0) for p in squad), reverse=True)[:2]
        if len(top) == 2:
            margins.append(round(top[0] - top[1], 2))
        # concentration: the largest share of one club in the squad (ADR-145)
        clubs = Counter(p["team"] for p in squad)
        concentrations.append(max(clubs.values()) / len(squad))
    return margins, concentrations


def main():
    store = Storage()
    try:
        players = store.get_players()
        ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                             horizon=1, gw_history_by_code=store.get_gw_history_by_code())
    finally:
        store.close()
    xp_by_id = {r["id"]: r["xp"] for r in ranked}
    by_pos = {}
    for p in players:
        if p["status"] != "u":
            by_pos.setdefault(p["position"], []).append(p)

    print(f"{N_SQUADS} random legal squads per seed, live GW4 data\n")
    print(f"{'seed':>5} | {'captain margin p25':>18} {'median':>7} {'p75':>6} {'max':>6}"
          f" | {'concentration p75':>17} {'p90':>6}")
    for seed in (3, 17):
        m, c = measure(seed, players, xp_by_id, by_pos)
        print(f"{seed:>5} | {pct(m,.25):>18.2f} {pct(m,.50):>7.2f} {pct(m,.75):>6.2f} {max(m):>6.2f}"
              f" | {pct(c,.75):>17.3f} {pct(c,.90):>6.3f}")
    print("\nADR-144 (GW1): captain margin p25 0.20 · median 0.60 · p75 1.00 · max 2.80  -> WHISKER 0.3, CLEAR 1.0")
    print("ADR-145 (GW1): concentration p75 ~0.35 (CONCENTRATED) · p90 ~0.45 (HEAVY)")


if __name__ == "__main__":
    main()
