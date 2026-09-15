"""Score the clean-sheet weight on the population it applies to (ADR-190 Option 3 → ADR-188).

ADR-188's term adds `4 × (team_rate − league_rate)` to **DEF and GK only**. Its GW4 sweep scored it the way
every weight is scored — mean-GW Spearman across **all** ~626 players with actuals — and the curve declined,
so the weight stayed at 0.

ADR-190 then found that a whole-board rank metric **cannot see a term scoped to a sub-population**, and closed
`SET_PIECE_WEIGHT` on exactly that reasoning (9 eligible players of 657). Clean sheet is a milder case — it
moves ~170 players and genuinely re-ranks the board (ρ(rank₀, rank_w) = 0.981) — which is why ADR-190 classed
it as *measurable* and took its decline at face value.

But "measurable" is not "measured on the right population". Roughly three quarters of the players in that
statistic can never be touched by the term, and they dilute it. This re-scores the identical sweep restricted
to **DEF/GK**, and prints both so the dilution is visible rather than argued.

Deterministic: `decision_xp` is arithmetic, no solver, no sampling — the same inputs give the same curve.

    venv/bin/python spikes/192-defender-only-calibration/measure.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src import config                                                    # noqa: E402
from src.analytics import backtest                                        # noqa: E402
from src.analytics.xp import decision_xp                                  # noqa: E402
from src.storage import Storage                                           # noqa: E402

WEIGHTS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]
ATTR = "CLEAN_SHEET_WEIGHT"


def triples_for(gw_history, predict, keep_codes=None):
    """`backtest.pairs`, but able to keep only a sub-population.

    Reimplemented rather than filtered afterwards because `pairs` returns `(pred, actual, round)` and drops
    the code — there is nothing left to filter on, which is itself why the whole-board score was the only one
    anybody could compute.
    """
    out = []
    for n in backtest.rounds_with_actuals(gw_history):
        before = {c: [r for r in rows if r["round"] < n] for c, rows in gw_history.items()}
        preds = predict(before, n) or {}
        for code, rows in gw_history.items():
            if keep_codes is not None and code not in keep_codes:
                continue
            actual = next((r["total_points"] for r in rows
                           if r["round"] == n and r["total_points"] is not None), None)
            if actual is not None and code in preds:
                out.append((preds[code], actual, n))
    return out


def score(triples, top_n):
    n = backtest.eligible_n(triples)
    return {"rho": backtest.mean_gw_spearman(triples), "mae": backtest.mae(triples),
            "hit": backtest.hit_rate(triples, top_n), "n": n, "se": backtest.spearman_se(n)}


def main():
    store = Storage()
    try:
        players = store.get_players()
        history = store.get_history_by_code()
        gw_history = store.get_gw_history_by_code()
        code_by_id = store.get_player_codes()
        fixtures = {}

        pos_by_code = {}
        for p in players:
            code = code_by_id.get(p["id"])
            if code is not None:
                pos_by_code[code] = p["position"]
        back = {c for c, pos in pos_by_code.items() if pos in ("DEF", "GK")}

        def make_predict(value):
            def predict(before, n):
                upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
                old = getattr(config, ATTR)
                setattr(config, ATTR, value)
                try:
                    ranked = decision_xp(players, upcoming, history, horizon=1, gw_history_by_code=before)
                finally:
                    setattr(config, ATTR, old)
                return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
            return predict

        gws = len(backtest.rounds_with_actuals(gw_history))
        print(f"CLEAN_SHEET_WEIGHT over {gws} gameweeks — whole board vs the population the term applies to\n")
        print(f"{'weight':>7} | {'ALL: ρ':>7} {'MAE':>5} {'hit':>5} {'n':>5}"
              f" | {'DEF/GK: ρ':>10} {'MAE':>5} {'hit':>5} {'n':>4} {'±1 SE':>6}")
        print("-" * 78)
        base_all = base_def = None
        for w in WEIGHTS:
            predict = make_predict(w)
            a = score(triples_for(gw_history, predict), 20)
            d = score(triples_for(gw_history, predict, keep_codes=back), 10)
            if base_all is None:
                base_all, base_def = a["rho"], d["rho"]
            print(f"{w:>7.2f} | {a['rho']:>7.3f} {a['mae']:>5.2f} {a['hit']:>5.2f} {a['n']:>5}"
                  f" | {d['rho']:>10.3f} {d['mae']:>5.2f} {d['hit']:>5.2f} {d['n']:>4} {d['se']:>6.3f}")
        print(f"\n  whole-board baseline ρ {base_all:.3f} · DEF/GK baseline ρ {base_def:.3f}")
        print("  §B0 criterion 1 asks for ≥ 1 SE of improvement over the weight-0 row, in the column that "
              "matches\n  the term's scope.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
