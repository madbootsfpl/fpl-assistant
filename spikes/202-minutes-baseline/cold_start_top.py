"""Does demoting the unknown case change the TOP of the board? (ADR-192's actual complaint)

⚠️ **This is a diagnosis, not a third criterion.** The rank correlation declines at every value, on the whole
board and on the cold population alike, and whole-board `hit@20` is **flat at 0.17 across the entire sweep** —
the §B0 verdict is already in. ⭐ *Reaching for a new metric after two have declined is how you choose the
answer* (ADR-190). What this adds is *why*: the complaint that started ADR-192 was not about a correlation, it
was one player in one recommendation — Affengruber, no career, projected above a seven-season defender.

So: at each value, how many of the board's top 20 have no history at all, and what did they actually score?
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics import backtest  # noqa: E402
from src.analytics import minutes as min_mod
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402

VALUES = [1.0, 0.8, 0.6, 0.4]
TOP = 20


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_aw = min_mod.availability_weight
    cold = {p["code"] for p in players if not history.get(p["code"])}

    def rank_at(value, before, n):
        upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))

        def patched(player, hist_rows):
            if not hist_rows:
                return min_mod.chance_factor(player) * value
            return real_aw(player, hist_rows)

        min_mod.availability_weight = patched
        try:
            ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1, gw_history_by_code=before)
        finally:
            min_mod.availability_weight = real_aw
        return [(code_by_id[r["id"]], r["xp"]) for r in ranked if r["id"] in code_by_id]

    print(f"  {'value':>6} {'cold in top20':>14} {'their mean pts':>15} {'top20 mean pts':>15}")
    for v in VALUES:
        n_cold, cold_pts, all_pts = 0, [], []
        for n in backtest.rounds_with_actuals(gw_history):
            before = {c: [r for r in rows if r["round"] < n] for c, rows in gw_history.items()}
            top = sorted(rank_at(v, before, n), key=lambda t: -t[1])[:TOP]
            for code, _ in top:
                actual = next((r["total_points"] for r in (gw_history.get(code) or [])
                               if r["round"] == n and r["total_points"] is not None), None)
                if actual is None:
                    continue
                all_pts.append(actual)
                if code in cold:
                    n_cold += 1
                    cold_pts.append(actual)
        print(f"  {v:>6.2f} {n_cold:>14} "
              f"{(f'{statistics.mean(cold_pts):.2f}' if cold_pts else '-'):>15} "
              f"{statistics.mean(all_pts):>15.2f}")
    store.close()


if __name__ == "__main__":
    main()
