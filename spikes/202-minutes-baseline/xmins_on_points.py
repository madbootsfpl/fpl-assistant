"""Does the xMins weight improve the POINTS ranking, or only look like it should? (0b follow-up)

The minutes baseline found that on owned players the model is beaten by "same as last week", and above 3%
ownership by the **constant 90** — which is exactly what `--no-xmins` does. That raises a question the minutes
measurement cannot answer:

⚠️ **MAE on minutes is not the question the app asks.** A constant forecaster has **zero variance**, so it can
win MAE and still be useless for a decision — it cannot rank two players at all. ⭐ *A forecaster that cannot
discriminate can still be well calibrated, and calibration is not what a recommendation needs.* ADR-190's
lesson, in a new place: check that the metric can see what the term is for.

So this scores the thing the app actually does — rank players by decision xP — with the weight ON and OFF,
walk-forward on real returns, using ADR-101's existing harness unchanged.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics import backtest  # noqa: E402
from src.analytics.xp import decision_xp  # noqa: E402
from src.storage import Storage  # noqa: E402


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}

    def make_predict(minutes_weighted):
        def predict(before, n):
            upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
            ranked = decision_xp(players, upcoming, history, horizon=1,
                                 minutes_weighted=minutes_weighted, gw_history_by_code=before)
            return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
        return predict

    print(f"rounds with actuals: {backtest.rounds_with_actuals(gw_history)}")
    print(f"\n  {'xMins':<8} {'ρ (mean GW)':>12} {'1 SE':>7} {'MAE':>7} {'hit@20':>8} {'n':>7}")
    out = {}
    for label, on in (("ON", True), ("OFF", False)):
        triples = backtest.pairs(gw_history, make_predict(on))
        n = backtest.eligible_n(triples)
        out[label] = {
            "rho": backtest.mean_gw_spearman(triples),
            "se": backtest.spearman_se(n),
            "mae": backtest.mae(triples),
            "hit": backtest.hit_rate(triples, 20),
            "n": n,
        }
        r = out[label]
        print(f"  {label:<8} {r['rho']:>12.3f} {r['se']:>7.3f} {r['mae']:>7.2f} {r['hit']:>8.2f} {r['n']:>7}")

    d = out["ON"]["rho"] - out["OFF"]["rho"]
    print(f"\n  Δρ (ON − OFF) = {d:+.3f}   against 1 SE = {out['ON']['se']:.3f}"
          f"   → {abs(d) / out['ON']['se']:.1f} SE")

    # Per round, because a mean over 4 numbers hides which way each one went (ADR-183).
    rounds = backtest.rounds_with_actuals(gw_history)
    print(f"\n  per round ρ:  {'':<6}" + " ".join(f"{'GW' + str(n):>8}" for n in rounds))
    for label, on in (("ON", True), ("OFF", False)):
        triples = backtest.pairs(gw_history, make_predict(on))
        by_gw = {}
        for pred, actual, rnd in triples:
            by_gw.setdefault(rnd, []).append((pred, actual))
        cells = []
        for rnd in rounds:
            got = by_gw.get(rnd, [])
            rho = backtest.spearman([p for p, _ in got], [a for _, a in got]) if len(got) > 2 else None
            cells.append(f"{rho:>8.3f}" if rho is not None else f"{'-':>8}")
        print(f"  {label:<12}" + " ".join(cells))

    store.close()


if __name__ == "__main__":
    main()
