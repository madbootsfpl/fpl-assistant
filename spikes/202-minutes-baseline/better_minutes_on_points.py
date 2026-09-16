"""Would a BETTER minutes forecaster produce a better points ranking? (the Phase 1 premise)

`xmins_on_points.py` showed the weight is worth **+0.117 ρ (2.9 SE)** against having no weight at all. That
settles *whether to weight*. It does not settle the ML roadmap's actual premise, which is stronger:

> **a more accurate minutes model produces a better points ranking.**

That is an assumption, and it is testable **today**, without training anything — because the minutes baseline
already found a forecaster that is measurably more accurate than the live one on owned players ("last GW",
MAE 20.5 vs 24.0). Swap it in as the weight and re-score the ranking.

⭐ *If a strictly better minutes forecaster does not produce a better ranking, Phase 1 is not a small model
away from paying — its premise is wrong, and no amount of LightGBM fixes that.* Cheaper to find out now.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod
from src.analytics.minutes import chance_factor  # noqa: E402
from src.storage import Storage  # noqa: E402

FULL_GAME = 90


def make_weight_factory(kind, real_factory):
    """Return a drop-in replacement for `minutes_weight_from_history`.

    ⚠️ It keeps the **chance factor** in every variant. Availability news is real information the naive
    forecasters lack, and dropping it would make this a test of two things at once.
    """
    def factory(history_by_code, gw_history_by_code=None):
        if kind == "live":
            return real_factory(history_by_code, gw_history_by_code)

        def weight(player):
            rows = (gw_history_by_code or {}).get(player["code"]) or []
            cf = chance_factor(player)
            if not rows:
                # No in-season evidence: fall back to the live model so GW1 is not a different experiment.
                return real_factory(history_by_code, gw_history_by_code)(player)
            if kind == "last":
                mins = max(rows, key=lambda r: r["round"])["minutes"] or 0
            else:                                   # "mean"
                mins = sum((r["minutes"] or 0) for r in rows) / len(rows)
            return cf * min(1.0, mins / FULL_GAME)
        return weight
    return factory


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_factory = xp_mod.minutes_weight_from_history

    def predict_with(kind):
        def predict(before, n):
            upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
            xp_mod.minutes_weight_from_history = make_weight_factory(kind, real_factory)
            try:
                ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1,
                                            gw_history_by_code=before)
            finally:
                xp_mod.minutes_weight_from_history = real_factory
            return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
        return predict

    rounds = backtest.rounds_with_actuals(gw_history)
    print(f"rounds: {rounds}\n")
    print(f"  {'weight from':<24} {'ρ (mean GW)':>12} {'MAE':>7} {'hit@20':>8}   per-round ρ")
    base = None
    for kind, label in (("live", "xMins v0 (the app)"), ("last", "last GW's minutes"), ("mean", "mean minutes so far")):
        triples = backtest.pairs(gw_history, predict_with(kind))
        rho = backtest.mean_gw_spearman(triples)
        by_gw = {}
        for pred, actual, rnd in triples:
            by_gw.setdefault(rnd, []).append((pred, actual))
        cells = " ".join(
            f"{backtest.spearman([p for p, _ in by_gw[r]], [a for _, a in by_gw[r]]):>7.3f}" for r in rounds)
        if base is None:
            base = rho
        print(f"  {label:<24} {rho:>12.3f} {backtest.mae(triples):>7.2f} "
              f"{backtest.hit_rate(triples, 20):>8.2f}   {cells}"
              + ("" if kind == "live" else f"   Δ {rho - base:+.3f}"))
    se = backtest.spearman_se(backtest.eligible_n(backtest.pairs(gw_history, predict_with("live"))))
    print(f"\n  1 SE = {se:.3f}")
    store.close()


if __name__ == "__main__":
    main()
