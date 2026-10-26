"""ADR-320 option A, scored on the POINTS RANKING against §B0's bar.

`rolling.py` found the ratchet is real (49% -> 78% refused, GW2 -> GW8) and that **almost every window
variant is worse on minutes than the rule it replaces**. ⚠️ That is not the decision: ADR-204's blend was
*better* on minutes and still declined, because MAE and the ranking do not move together. So the candidate
gets the same treatment every other one has had.

§B0's bar: ρ gain >= +1 SE, across >= 2 **adjacent** values, with MAE and hit@20 not falling.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rolling import rolling_factory  # noqa: E402

from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402

# Adjacency runs down the `tolerance` column at a fixed window — "forgive one miss in the last five" is the
# knob option A proposed, so that is the axis a gain has to hold across.
GRID = [(None, None, None, "ADR-173 (the app)")]
for _w in (3, 4, 5, 6, 8):
    for _t in (0, 1, 2, 3):
        if _t < _w:
            GRID.append((_w, _t, "available", f"last {_w}, forgive {_t}"))


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_factory = xp_mod.minutes_weight_from_history

    def predict_with(window, tolerance, denom):
        def predict(before, n):
            upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
            if window is not None:
                xp_mod.minutes_weight_from_history = (
                    lambda h, gw=None, _a=(window, tolerance, denom): rolling_factory(*_a, h, gw))
            try:
                ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1,
                                            gw_history_by_code=before)
            finally:
                xp_mod.minutes_weight_from_history = real_factory
            return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
        return predict

    rounds = backtest.rounds_with_actuals(gw_history)
    se = backtest.spearman_se(backtest.eligible_n(backtest.pairs(gw_history, predict_with(None, None, None))))
    print(f"  {'guard':<24} {'rho':>8} {'MAE':>7} {'hit@20':>8}   per-round rho{'':>12}   vs live")
    base = None
    for window, tolerance, denom, label in GRID:
        triples = backtest.pairs(gw_history, predict_with(window, tolerance, denom))
        by_gw: dict[int, list] = {}
        for pred, actual, rnd in triples:
            by_gw.setdefault(rnd, []).append((pred, actual))
        cells = " ".join(
            f"{backtest.spearman([p for p, _ in by_gw[r]], [a for _, a in by_gw[r]]):>6.3f}" for r in rounds)
        rho = backtest.mean_gw_spearman(triples)
        if base is None:
            base = rho
        # Four decimals on the SE — at GW8 the decision lived in the third (ADR-369).
        delta = "" if window is None else f"   {rho - base:+.5f}  = {(rho - base) / se:+.4f} SE"
        print(f"  {label:<24} {rho:>8.3f} {backtest.mae(triples):>7.2f} "
              f"{backtest.hit_rate(triples, 20):>8.2f}   {cells}{delta}")

    print(f"\n  1 SE = {se:.6f}   §B0 bar: +1 SE on rho, across >=2 adjacent values, MAE and hit@20 not falling")
    print("  for reference: ADR-204's blend reached +0.9 SE and was declined; perfect minutes = +5.1 SE")
    store.close()


if __name__ == "__main__":
    main()
