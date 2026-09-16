"""Is hit@20's jump bigger than hit@20's own noise?

The blend moved hit@20 from **0.17 to 0.26** while rho moved only +0.4 SE. ⭐ *A secondary criterion that
moves a long way deserves an error bar before it is allowed to mean anything* — otherwise it is just the
loudest number in the table, and ADR-190 is explicit that reaching for one of those after the primary
fails is how you choose the answer.

hit@20 is a proportion over `rounds x 20` slots, so it has a standard error the rho SE does not describe:
sqrt(p(1-p)/n). With four rounds that is 80 slots, and 80 is not many.

⚠️ It also reports the **paired** difference, which is the right test: the two forecasters are scored on the
same rounds and the same actuals, so a per-round paired comparison removes the round-to-round variance that
dominates an unpaired one.
"""

import math
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from blend import blended_factory  # noqa: E402

from src.analytics import backtest  # noqa: E402
from src.analytics import xp as xp_mod
from src.storage import Storage  # noqa: E402

TOP = 20


def main():
    store = Storage()
    gw_history = store.get_gw_history_by_code()
    players = store.get_players()
    history = store.get_history_by_code()
    code_by_id = store.get_player_codes()
    fixtures: dict[int, list] = {}
    real_factory = xp_mod.minutes_weight_from_history

    def triples_for(k):
        def predict(before, n):
            upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
            if k is not None:
                xp_mod.minutes_weight_from_history = lambda h, gw=None, _k=k: blended_factory(_k, h, gw)
            try:
                ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1, gw_history_by_code=before)
            finally:
                xp_mod.minutes_weight_from_history = real_factory
            return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
        return backtest.pairs(gw_history, predict)

    rounds = backtest.rounds_with_actuals(gw_history)

    def per_round_hits(triples):
        """Hits in the predicted top-20 per round — the raw counts the rate is made of."""
        out = {}
        for rnd in rounds:
            got = [(p, a) for p, a, r in triples if r == rnd]
            if len(got) < TOP:
                continue
            top_pred = {i for i, _ in sorted(enumerate(got), key=lambda t: -t[1][0])[:TOP]}
            top_actual = {i for i, _ in sorted(enumerate(got), key=lambda t: -t[1][1])[:TOP]}
            out[rnd] = len(top_pred & top_actual)
        return out

    live, blend = per_round_hits(triples_for(None)), per_round_hits(triples_for(1))
    n_slots = len(live) * TOP
    p_live = sum(live.values()) / n_slots
    p_blend = sum(blend.values()) / n_slots

    print(f"  slots = {len(live)} rounds x {TOP} = {n_slots}")
    print(f"  {'round':>6} {'live':>6} {'blend':>7} {'diff':>6}")
    for rnd in rounds:
        if rnd in live:
            print(f"  {rnd:>6} {live[rnd]:>6} {blend[rnd]:>7} {blend[rnd] - live[rnd]:>+6}")
    print(f"  {'TOTAL':>6} {sum(live.values()):>6} {sum(blend.values()):>7} "
          f"{sum(blend.values()) - sum(live.values()):>+6}")

    se_live = math.sqrt(p_live * (1 - p_live) / n_slots)
    diffs = [blend[r] - live[r] for r in live]
    print(f"\n  hit@20: {p_live:.3f} -> {p_blend:.3f}   (+{p_blend - p_live:.3f})")
    print(f"  1 SE on a proportion of {n_slots} slots = {se_live:.3f}  ->  the gain is "
          f"{(p_blend - p_live) / se_live:.1f} SE unpaired")
    if len(diffs) > 1 and statistics.stdev(diffs) > 0:
        se_paired = statistics.stdev(diffs) / math.sqrt(len(diffs))
        print(f"  paired across {len(diffs)} rounds: mean +{statistics.mean(diffs):.1f} hits/round, "
              f"SE {se_paired:.1f}  ->  {statistics.mean(diffs) / se_paired:.1f} SE")
        print(f"  every round improved: {all(d > 0 for d in diffs)}")
    store.close()


if __name__ == "__main__":
    main()
