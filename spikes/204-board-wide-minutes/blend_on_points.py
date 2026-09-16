"""Does the board-wide-better forecaster produce a better points ranking? (the Phase 1 gate, scored)

`blend.py` cleared the gate ADR-202 set: the shrinkage blend is **better board-wide** (24.5 -> 20.9 MAE,
start calls 73.5% -> 78.8%), which the first premise test's substitute never was.

⚠️ **It is also WORSE on owned players** (24.0 -> 25.0). Neither candidate dominates, and that is worth
saying before the ranking number arrives: ⭐ *"more accurate" is a claim about a population, and two
forecasters can each be more accurate than the other.*

⚠️ **`k` was chosen by board MAE on four gameweeks**, which is selection on the same data this then scores.
So every `k` that cleared the gate is reported, not just the winner — a result that only exists at one value
of a swept parameter is a result about the sweep (ADR-101's `_FLAT_EPS` guard exists for this).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from blend import blended_factory  # noqa: E402

from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_factory = xp_mod.minutes_weight_from_history

    def predict_with(k):
        def predict(before, n):
            upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
            if k is not None:
                xp_mod.minutes_weight_from_history = (
                    lambda h, gw=None, _k=k: blended_factory(_k, h, gw))
            try:
                ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1,
                                            gw_history_by_code=before)
            finally:
                xp_mod.minutes_weight_from_history = real_factory
            return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
        return predict

    rounds = backtest.rounds_with_actuals(gw_history)
    se = backtest.spearman_se(backtest.eligible_n(backtest.pairs(gw_history, predict_with(None))))
    print(f"  {'weight':<24} {'rho':>8} {'MAE':>7} {'hit@20':>8}   per-round rho{'':>10}   vs live")
    base = None
    for k, label in ((None, "xMins v0 (the app)"), (1, "blend, k=1"), (2, "blend, k=2"), (3, "blend, k=3")):
        triples = backtest.pairs(gw_history, predict_with(k))
        by_gw = {}
        for pred, actual, rnd in triples:
            by_gw.setdefault(rnd, []).append((pred, actual))
        cells = " ".join(
            f"{backtest.spearman([p for p, _ in by_gw[r]], [a for _, a in by_gw[r]]):>6.3f}" for r in rounds)
        rho = backtest.mean_gw_spearman(triples)
        if base is None:
            base = rho
        delta = "" if k is None else f"   {rho - base:+.3f}  = {(rho - base) / se:+.1f} SE"
        print(f"  {label:<24} {rho:>8.3f} {backtest.mae(triples):>7.2f} "
              f"{backtest.hit_rate(triples, 20):>8.2f}   {cells}{delta}")

    print(f"\n  1 SE = {se:.3f}   §B0 bar: a gain of +1 SE, across >=2 adjacent values, MAE and hit@20 not falling")
    print("  ADR-202's ceiling for reference: perfect minutes = +0.206 (5.1 SE), of which "
          "+0.061 (1.5 SE) is information rather than appearance-point arithmetic")
    store.close()


if __name__ == "__main__":
    main()
