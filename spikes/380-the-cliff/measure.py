"""ADR-372 removed the ratchet and left a cliff. Does capping the fallback cost anything?

🔴 **More evidence of decline produces a better forecast.** Konsa, if Saliba's return costs him minutes:

    plays every week        share 1.000  ->  xMins 90
    benched ONCE in five    share 0.800  ->  xMins 72    (window answers, one miss forgiven)
    benched TWICE in five   REFUSED      ->  xMins 79    <-- falls back to history

The second benching **raises** him, because two misses breach the tolerance, `in_season_share` refuses, and
`availability_weight` hands back his historical share — **0.879, earned at Aston Villa.** ⭐⭐ *ADR-372 took
away the ratchet and the cliff simply moved: the rule no longer gets stricter every week, but the moment it
gives up it reaches for a stale, higher number.*

**The candidate is a one-sided cap, not a new estimate.** On a breach, the fallback may not exceed what the
(distrusted) window evidence would have said:

    weight = min(historical_weight, chance_factor * window_share_anyway)

⚠️ *"We do not trust it enough to use, but we trust it enough to cap"* sounds like having it both ways, and
is not: the claim is **monotonicity**, not a point estimate. Evidence of decline must never improve a
forecast. ⭐ Using a distrusted number only where being wrong about it is cheap is the same asymmetry the
ADR-376 sell guard rests on.

Scored board-wide **and** on the population that actually breaches (ADR-190's rule).
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "192-defender-only-calibration"))

from measure import score, triples_for  # noqa: E402

from src.analytics import backtest  # noqa: E402
from src.analytics import minutes as m  # noqa: E402
from src.analytics import xp as xp_mod  # noqa: E402
from src.storage import Storage  # noqa: E402

FULL = 90


def window_share(player, gw_history_by_code, completed):
    """What the rolling window would say if nothing were refused — the cap, and only ever the cap."""
    recent = sorted(completed)[-m._WINDOW_GAMEWEEKS:]
    rows = {r["round"]: r for r in ((gw_history_by_code or {}).get(player["code"]) or [])}
    played = [rows[g] for g in recent if g in rows and (rows[g]["minutes"] or 0) > 0]
    if not played:
        return None
    return min(1.0, sum(r["minutes"] or 0 for r in played) / (len(recent) * FULL))


def capped_factory(history_by_code, gw_history_by_code=None):
    completed = m.completed_gameweeks(gw_history_by_code) if gw_history_by_code else set()

    def weight(player):
        share = m.in_season_share(player, gw_history_by_code, completed) if completed else None
        if share is not None:
            return m.chance_factor(player) * share
        rows = history_by_code.get(player["code"], [])
        hist = m.availability_weight(player, rows)
        if not completed:
            return hist
        # 🔴🔴 **Cap only where the historical weight is EVIDENCE.** The first version of this capped
        # everyone and lowered 118 of 167 breachers by a mean of 44.5 xMins — because a player with no past
        # seasons gets `availability_weight` = **1.0 by default** (ADR-038), and a 2-minute window share then
        # crushes him to zero. ⭐⭐ *That is not fixing a cliff, it is re-deciding the cold-start default* —
        # ADR-192's proposal, already declined by ADR-202, arriving by the back door.
        if m.minutes_share(rows) is None:
            return hist                      # no past seasons: the 1.0 is a default, not a measurement
        floor = window_share(player, gw_history_by_code, completed)
        if floor is None:
            return hist                      # never played at all — nothing to cap with
        return min(hist, m.chance_factor(player) * floor)
    return weight


def breachers(players, gw_history_by_code, completed):
    """Players the window refuses but who HAVE played — the ones the cliff can move."""
    out = set()
    for p in players:
        if not ((gw_history_by_code or {}).get(p["code"]) or []):
            continue
        if m.in_season_share(p, gw_history_by_code, completed) is None \
                and window_share(p, gw_history_by_code, completed) is not None:
            out.add(p["code"])
    return out


def main():
    store = Storage()
    try:
        players = store.get_players()
        history = store.get_history_by_code()
        gw_history = store.get_gw_history_by_code()
        code_by_id = store.get_player_codes()
        fixtures: dict = {}
        real = xp_mod.minutes_weight_from_history

        # ── how big is the cliff, and which way does it point?
        completed = m.completed_gameweeks(gw_history)
        hit = breachers(players, gw_history, completed)
        live = m.minutes_weight_from_history(history, gw_history)
        capped = capped_factory(history, gw_history)
        moves = [(p, live(p), capped(p)) for p in players if p["code"] in hit]
        lowered = [t for t in moves if t[2] < t[1] - 1e-9]
        print(f"players the window refuses but who have played: {len(hit)}")
        print(f"  the cap lowers {len(lowered)} of them; it can never raise one (it is a min)")
        if lowered:
            d = [t[1] - t[2] for t in lowered]
            print(f"  mean drop {statistics.mean(d):.3f} weight ({statistics.mean(d)*90:.1f} xMins)"
                  f"   max {max(d):.3f} ({max(d)*90:.0f} xMins)")
            print(f"\n  {'player':<14} {'today':>7} {'capped':>7} {'xMins':>12}")
            for p, a, b in sorted(lowered, key=lambda t: t[2] - t[1])[:8]:
                print(f"  {p['web_name'][:14]:<14} {a:>7.3f} {b:>7.3f} {round(a*90):>5} -> {round(b*90):<4}")

        # ── and what it costs
        def make_predict(factory):
            def predict(before, n):
                upcoming = fixtures.setdefault(n, store.get_fixtures_by_event(n))
                if factory is not None:
                    xp_mod.minutes_weight_from_history = factory
                try:
                    ranked = xp_mod.decision_xp(players, upcoming, history, horizon=1,
                                                gw_history_by_code=before)
                finally:
                    xp_mod.minutes_weight_from_history = real
                return {code_by_id[r["id"]]: r["xp"] for r in ranked if r["id"] in code_by_id}
            return predict

        gws = len(backtest.rounds_with_actuals(gw_history))
        print(f"\nscored over {gws} gameweeks\n")
        print(f"  {'variant':<12} {'ALL: ρ':>8} {'MAE':>6} {'hit@20':>7} {'1 SE':>7}"
              f" | {'BREACHERS: ρ':>13} {'MAE':>6} {'hit@10':>7} {'n':>4}")
        base_all = base_hit = None
        for label, factory in (("today", None), ("capped", capped_factory)):
            pred = make_predict(factory)
            a = score(triples_for(gw_history, pred), 20)
            b = score(triples_for(gw_history, pred, keep_codes=hit), 10)
            if base_all is None:
                base_all, base_hit = a["rho"], b["rho"]
            print(f"  {label:<12} {a['rho']:>8.4f} {a['mae']:>6.2f} {a['hit']:>7.2f} {a['se']:>7.4f}"
                  f" | {b['rho']:>13.4f} {b['mae']:>6.2f} {b['hit']:>7.2f} {b['n']:>4}")
        print("\n  §B0's bar is for accuracy BIDS. This is a monotonicity fix, so the question is "
              "'does it cost anything',\n  not 'does it gain +1 SE'.")
    finally:
        store.close()


if __name__ == "__main__":
    main()
