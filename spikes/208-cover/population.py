"""How often does the cover blind spot change the recommendation, and by how much? (ADR-200's discipline)

One constructed squad showed the app pricing a cover move at +0.30 against a true +1.35. ⭐ *One squad is a
mechanism, not a rate* — and ADR-200 is explicit that a measurement on an unrealistic population produces a
confident wrong number. So: realistic squads, and two questions.

1. **How much is the app understating cover** behind a doubtful starter?
2. **Does it change the decision** — would the true ranking put a cover move above the app's top pick?
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "200-realistic-squads"))

from population import perturbed, template  # noqa: E402

from src.analytics.minutes import chance_factor  # noqa: E402
from src.analytics.optimizer import best_legal_xi, best_xi_points  # noqa: E402
from src.analytics.transfer import suggest_transfers  # noqa: E402
from src.analytics.xp import decision_xp  # noqa: E402
from src.storage import Storage  # noqa: E402

import random  # noqa: E402


def expected_xi(owned, xp, doubts):
    """E[max] over every combination of doubtful starters playing or blanking.

    ⚠️ 2^k branches, but k is the number of DOUBTFUL players in one squad — 0, 1 or 2 in practice.
    """
    if not doubts:
        return best_xi_points(owned, xp)
    total = 0.0
    for mask in range(1 << len(doubts)):
        prob, scores = 1.0, dict(xp)
        for i, (p, c) in enumerate(doubts):
            if mask >> i & 1:                       # he plays
                prob *= c
                scores[p["id"]] = xp[p["id"]] / c if c else 0.0
            else:                                   # he blanks; the bench auto-subs
                prob *= (1 - c)
                scores[p["id"]] = 0.0
        total += prob * best_xi_points(owned, scores)
    return total


def main():
    db = Storage()
    players = db.get_players()
    hist, gw, up = db.get_history_by_code(), db.get_gw_history_by_code(), db.get_upcoming_fixtures()
    xp = {r["id"]: r["xp"] for r in decision_xp(players, up, hist, horizon=1, gw_history_by_code=gw)}
    by_id = {p["id"]: p for p in players}
    base = template(players)

    gaps, flipped, n_with_doubt, n = [], 0, 0, 0
    rows = []
    for seed in (1, 2):
        rng = random.Random(seed)
        for k in (2, 4, 6, 8):
            for _ in range(8):
                squad = perturbed(base, players, k, rng)
                if squad is None or len(squad) != 15:
                    continue
                n += 1
                xi = best_legal_xi(squad, xp)
                doubts = [(p, chance_factor(p)) for p in squad
                          if p["status"] == "d" and p["id"] in xi]
                if not doubts:
                    continue
                n_with_doubt += 1
                naive0, true0 = best_xi_points(squad, xp), expected_xi(squad, xp, doubts)

                shortlist = suggest_transfers(squad, players, xp, bank=1.0, limit=5)
                if not shortlist:
                    continue
                best_app = max(shortlist, key=lambda m: m["gain"])
                cands = []
                for m in shortlist:
                    after = [p for p in squad if p["id"] != m["out"]["id"]] + [by_id[m["in"]["id"]]]
                    d2 = [(p, c) for p, c in doubts if p["id"] != m["out"]["id"]]
                    cands.append((m, m["gain"], expected_xi(after, xp, d2) - true0))
                # the best COVER move: upgrade a bench player in a doubtful starter's position
                for p_out in squad:
                    if p_out["id"] in xi:
                        continue
                    if p_out["position"] not in {p["position"] for p, _ in doubts}:
                        continue
                    pool = [c for c in players if c["position"] == p_out["position"]
                            and c["status"] == "a" and c["price"] <= p_out["price"] + 1.0
                            and c["id"] not in {q["id"] for q in squad}]
                    if not pool:
                        continue
                    inc = max(pool, key=lambda c: xp.get(c["id"], 0))
                    after = [q for q in squad if q["id"] != p_out["id"]] + [inc]
                    cands.append((None, round(best_xi_points(after, xp) - naive0, 2),
                                  expected_xi(after, xp, doubts) - true0))
                app_pick = max(cands, key=lambda c: c[1])
                true_pick = max(cands, key=lambda c: c[2])
                gaps.append(true_pick[2] - app_pick[2])
                covers = [c for c in cands if c[0] is None]
                rows.append({"best_app": app_pick[1],
                             "cover_app": max((c[1] for c in covers), default=None),
                             "cover_true": max((c[2] for c in covers), default=None),
                             "gap": true_pick[2] - app_pick[2]})
                if app_pick is not true_pick and true_pick[0] is None and app_pick[0] is not None:
                    flipped += 1
                _ = best_app
    print(f"squads: {n}   with a DOUBTFUL player in the best XI: {n_with_doubt}")
    if gaps:
        print(f"\n  points the app leaves on the table by ranking on max(E) instead of E(max):")
        print(f"    mean {statistics.mean(gaps):+.2f} · median {statistics.median(gaps):+.2f} · "
              f"max {max(gaps):+.2f}  (per gameweek, XI xP)")
        print(f"  squads where the TRUE best move is a COVER move the app did not pick: "
              f"{flipped} of {len(gaps)} ({flipped / len(gaps):.0%})")

    # ⚠️ The two results disagree, so find what separates them: does the blind spot matter only when the
    # best ordinary upgrade is SMALL? A squad with a +3.0 move available never needs the contingency.
    band = {}
    for r in rows:
        if r["cover_true"] is None:
            continue
        key = "best move < 1.5" if r["best_app"] < 1.5 else ("1.5-3.0" if r["best_app"] < 3.0 else ">= 3.0")
        band.setdefault(key, []).append(r)
    print(f"\n  {'app-best move':<16} {'n':>4} {'cover: app says':>16} {'cover: true':>12} "
          f"{'understated by':>15} {'flips?':>7}")
    for key in ("best move < 1.5", "1.5-3.0", ">= 3.0"):
        rs = band.get(key) or []
        if not rs:
            continue
        ca = statistics.mean(r["cover_app"] for r in rs)
        ct = statistics.mean(r["cover_true"] for r in rs)
        flips = sum(1 for r in rs if r["cover_true"] > r["best_app"])
        print(f"  {key:<16} {len(rs):>4} {ca:>16.2f} {ct:>12.2f} {ct - ca:>+15.2f} "
              f"{f'{flips}/{len(rs)}':>7}")
    db.close()


if __name__ == "__main__":
    main()
