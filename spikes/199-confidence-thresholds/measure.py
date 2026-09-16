"""Measure the four *chosen* confidence thresholds (ADR-199).

Owner, on the "Why 73?" explainer: *"is this more of a discussion rather than an empirical result… they're
more like hunches or punts — tell me if I'm wrong."* He was right about the layer, wrong about the level.
The **formulas** invert exactly; the **constants they invert over** were mostly picked:

    measured  WHISKER 0.3 / CLEAR 1.3   captain margin   (ADR-144, re-measured ADR-190)
    measured  LINEUP_TOO_CLOSE / CLEAR  start-bench gap  (ADR-194)
    CHOSEN    _CLEAR_LEAD        0.8    captain lead → clearness saturates here
    CHOSEN    _CLEAR_GAIN        3.0    transfer XI-xP gain
    CHOSEN    _CLEAR_CHIP_MARGIN 0.15   chip week vs next-best, relative
    CHOSEN    _CLEAR_REBUILD     0.25   wildcard gain vs your own projection ("Provisional" in its comment)

And one of them demonstrably disagrees with a measurement that already exists: **42–47% of captain calls sit
at or above `_CLEAR_LEAD`**, so a lead of 0.8 and the measured p75 of 1.30 score identically — confidence
stops distinguishing exactly where real leads start being clear.

⭐ **The house rule, used twice already: "clear" is the p75 of the real distribution.** This measures each
distribution so the constants can be set that way rather than chosen.

⚠️ Two seeds throughout (ADR-183). The wildcard runs an optimiser solve per squad, so its N is smaller and
said so rather than quietly.

    venv/bin/python spikes/199-confidence-thresholds/measure.py
"""
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.chips import chip_advisor, rebuild_value              # noqa: E402
from src.analytics.optimizer import best_xi_points, is_unavailable       # noqa: E402
from src.analytics.transfer import suggest_transfers                     # noqa: E402
from src.analytics.xp import decision_xp                                 # noqa: E402
from src.storage import Storage                                          # noqa: E402

MAX_PER_CLUB, HORIZON = 3, 5


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


def report(name, const, values, n_label=""):
    if not values:
        print(f"  {name:<22} — no data")
        return
    print(f"  {name:<22} n={len(values):<5} p25 {pct(values,.25):>6.2f}  median {pct(values,.50):>6.2f}  "
          f"p75 {pct(values,.75):>6.2f}  p90 {pct(values,.90):>6.2f}   [chosen: {const}] {n_label}")


def main(n=200, n_wildcard=40):
    store = Storage()
    try:
        players = store.get_players()
        ranked = decision_xp(players, store.get_upcoming_fixtures(), store.get_history_by_code(),
                             horizon=HORIZON, gw_history_by_code=store.get_gw_history_by_code())
    finally:
        store.close()
    xp = {r["id"]: r["xp"] for r in ranked}
    per_gw = {r["id"]: r["by_gameweek"] for r in ranked}
    gws = ranked[0]["gameweeks"]
    # Next-GW xP is what the captain pick actually uses (horizon 1 in the app).
    near = {r["id"]: (list(r["by_gameweek"].values()) or [0])[0] for r in ranked}
    by_pos = {}
    for p in players:
        if not is_unavailable(p):
            by_pos.setdefault(p["position"], []).append(p)

    for seed in (3, 17):
        rng = random.Random(seed)
        leads, gains, chip_rel, wc_rel = [], [], [], []
        made = 0
        while made < n:
            squad = random_squad(by_pos, rng)
            if squad is None:
                continue
            made += 1
            top = sorted((near.get(p["id"], 0.0) for p in squad), reverse=True)[:2]
            if len(top) == 2:
                leads.append(round(top[0] - top[1], 2))                       # _CLEAR_LEAD
            moves = suggest_transfers(squad, players, xp, bank=0.0, limit=1)
            if moves:
                gains.append(moves[0]["gain"])                                # _CLEAR_GAIN
            advice = chip_advisor(squad, per_gw, gws)
            if advice:
                for chip, key in (("triple_captain", "player_xp"), ("bench_boost", "squad_total"),
                                  ("free_hit", "xi_total")):
                    a = advice.get(chip) or {}
                    val, margin = a.get(key), a.get("margin")
                    if val and margin is not None:
                        chip_rel.append(abs(margin) / val)                    # _CLEAR_CHIP_MARGIN
            if made <= n_wildcard:
                rb = rebuild_value(squad, players, xp, budget=0.0)
                cur = (rb or {}).get("current")
                if rb and cur:
                    wc_rel.append(max(0.0, rb["gain"]) / cur)                 # _CLEAR_REBUILD

        print(f"\nseed {seed} · {n} squads")
        report("_CLEAR_LEAD (captain)", 0.8, leads)
        report("_CLEAR_GAIN (transfer)", 3.0, gains)
        report("_CLEAR_CHIP_MARGIN", 0.15, chip_rel)
        report("_CLEAR_REBUILD", 0.25, wc_rel, f"(n={n_wildcard} squads — one optimiser solve each)")
    print("\n  House rule (ADR-144, ADR-194): 'clear' = the p75 of the real distribution.")


if __name__ == "__main__":
    main()
