"""ADR-192's constant, swept on real returns under §B0's pre-registered criteria.

ADR-192 established the **direction** (a player with no history is currently modelled as a nailed 90-minute
starter, because `minutes_share` returns None and None is read as 1.0) and deliberately did **not** choose the
number. The minutes baseline sized the error: on the 130 players with no past seasons the live model runs
**+39.1 minutes optimistic** and calls start/bench at **49.2% — a coin flip**.

This sweeps the value the unknown case should take, scored the way every other weight in this project is:
walk-forward rank correlation against real points (ADR-101), against §B0's bar of **+1 SE**.

⚠️ Scored on the **whole board and on the affected players separately** — ADR-190: a whole-board metric cannot
evaluate a term scoped to a sub-population, and a flat whole-board curve may mean the term is unreachable
rather than useless.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics import backtest  # noqa: E402
from src.analytics import minutes as min_mod
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402

VALUES = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4]


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_aw = min_mod.availability_weight
    cold_codes = {p["code"] for p in players if not history.get(p["code"])}

    def patched(value):
        def availability_weight(player, hist_rows):
            if not hist_rows:                       # the unknown case — the whole of ADR-192
                return min_mod.chance_factor(player) * value
            return real_aw(player, hist_rows)
        return availability_weight

    def predict_with(value):
        def predict(before, n):
            upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
            min_mod.availability_weight = patched(value)
            try:
                ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1,
                                            gw_history_by_code=before)
            finally:
                min_mod.availability_weight = real_aw
            return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
        return predict

    def pairs_with_code(predict):
        """`backtest.pairs` drops the player code, and a sub-population cannot be cut without it."""
        out = []
        for n in backtest.rounds_with_actuals(gw_history):
            before = {c: [r for r in rows if r["round"] < n] for c, rows in gw_history.items()}
            preds = predict(before, n) or {}
            for code, rows in gw_history.items():
                actual = next((r["total_points"] for r in rows
                               if r["round"] == n and r["total_points"] is not None), None)
                if actual is not None and code in preds:
                    out.append((preds[code], actual, n, code))
        return out

    def mean_gw_rho(quads):
        rhos = []
        for n in sorted({q[2] for q in quads}):
            got = [q for q in quads if q[2] == n]
            if len(got) > 2:
                r = backtest.spearman([g[0] for g in got], [g[1] for g in got])
                if r is not None:
                    rhos.append(r)
        return sum(rhos) / len(rhos) if rhos else None

    print(f"cold-start players (no past seasons): {len(cold_codes)}\n")
    print(f"  {'value':>6} {'rho board':>10} {'MAE':>7} {'hit@20':>8} | {'rho cold':>9} {'n cold':>7} {'MAE cold':>9}")
    ranks = {}
    for v in VALUES:
        quads = pairs_with_code(predict_with(v))
        cold = [q for q in quads if q[3] in cold_codes]
        ranks[v] = {q[3]: q[0] for q in quads if q[2] == max(q2[2] for q2 in quads)}
        rho_cold = mean_gw_rho(cold)
        mae_cold = sum(abs(q[0] - q[1]) for q in cold) / len(cold) if cold else None
        print(f"  {v:>6.2f} {mean_gw_rho(quads):>10.3f} "
              f"{backtest.mae([(q[0], q[1], q[2]) for q in quads]):>7.2f} "
              f"{backtest.hit_rate([(q[0], q[1], q[2]) for q in quads], 20):>8.2f} | "
              f"{rho_cold:>9.3f} {len(cold):>7} {mae_cold:>9.2f}")

    se_all = backtest.spearman_se(len(pairs_with_code(predict_with(1.0))))
    n_cold = len([q for q in pairs_with_code(predict_with(1.0)) if q[3] in cold_codes])
    print(f"\n  1 SE whole board = {se_all:.3f}   |   1 SE on the cold population (n={n_cold}) = "
          f"{backtest.spearman_se(n_cold):.3f}")

    # ⚠️ ADR-190's check: is the term even LIVE? A flat curve means nothing if the value cannot
    # re-rank the board — the bar would be unreachable rather than unmet.
    a, b = ranks[1.0], ranks[0.4]
    common = sorted(set(a) & set(b))
    rho_self = backtest.spearman([a[c] for c in common], [b[c] for c in common])
    cold_common = [c for c in common if c in cold_codes]
    rho_self_cold = backtest.spearman([a[c] for c in cold_common], [b[c] for c in cold_common])
    print(f"  reachability: rho(ranking at 1.0, ranking at 0.4) = {rho_self:.5f} whole board, "
          f"{rho_self_cold:.5f} on the cold population")
    print("  (ADR-190: a ranking ~0.9999 correlated with the baseline cannot move rho against reality by 0.040)")

    store.close()


if __name__ == "__main__":
    main()
