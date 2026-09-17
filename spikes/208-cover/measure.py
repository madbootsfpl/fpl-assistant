"""Is a BACKUP worth more than the marginal upgrade? (owner's report, 2026-09-17)

> *"We are picking up that João Pedro is a Doubt, we are not suggesting a transfer for him — that's as
> designed, so good. BUT where we have a gap is that the other 2 fwds are zero to low scoring, we should be
> getting a backup recommendation in there. I would suspect that is a better option than Fée to Hall."*

**The mechanism, before any measurement.** `best_xi_points` takes **one** score per player and maximises over
legal formations. The doubt is folded into João Pedro's score *first* (0.75 x his rate, ADR-206) and the XI is
chosen *after*. So the model computes **max of the expectation**, when what a manager actually experiences is
the **expectation of the max**: two different worlds — he plays, or he doesn't and the bench auto-subs in —
each with its own best XI.

⭐ `max(E[x])` and `E[max(x)]` are not the same number, and they diverge exactly when a *starter* is doubtful,
because that is when the bench stops being decoration and becomes a coin-flip starter.

⚠️ And `xi_aware` ranking (ADR-046) makes it invisible in the other direction too: a bench player contributes
**nothing** to the best XI, so upgrading him scores **+0.0** and never reaches the shortlist. That is correct
when the XI is safe. Third sighting of this family, after ADR-136 (*a slot that cannot score is invisible to
an XI-gain ranking*) and ADR-156 (*a bench leaver moves the XI by nothing*).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.minutes import chance_factor  # noqa: E402
from src.analytics.optimizer import MAX_PER_CLUB, best_xi_points  # noqa: E402
from src.analytics.transfer import suggest_transfers  # noqa: E402
from src.analytics.xp import decision_xp  # noqa: E402
from src.storage import Storage  # noqa: E402


def expected_xi(owned, xp_by_id, doubtful, chance):
    """E[max]: the best XI in each world, weighted by the chance the doubtful player features.

    This is what a manager actually gets, because FPL auto-substitutes a starter who plays 0 minutes.
    """
    full = dict(xp_by_id)
    full[doubtful["id"]] = xp_by_id[doubtful["id"]] / chance if chance else 0.0   # undo the discount
    blank = dict(xp_by_id)
    blank[doubtful["id"]] = 0.0
    return chance * best_xi_points(owned, full) + (1 - chance) * best_xi_points(owned, blank)


def main():
    db = Storage()
    players = db.get_players()
    hist, gw, up = db.get_history_by_code(), db.get_gw_history_by_code(), db.get_upcoming_fixtures()
    xp_by_id = {r["id"]: r["xp"] for r in decision_xp(players, up, hist, horizon=1, gw_history_by_code=gw)}
    by_name = {p["web_name"]: p for p in players}

    # The owner's shape: a doubtful star forward, and two forwards who are not scoring.
    jp = by_name["João Pedro"]
    weak = sorted((p for p in players if p["position"] == "FWD" and p["status"] == "a"
                   and 4.0 <= (p["price"] or 0) <= 5.6),
                  key=lambda p: xp_by_id.get(p["id"], 0))[:2]
    squad = [jp] + weak
    used = {p["team"] for p in squad}
    for pos, n in (("GK", 2), ("DEF", 5), ("MID", 5)):
        pool = sorted((p for p in players if p["position"] == pos and p["status"] == "a"),
                      key=lambda p: -xp_by_id.get(p["id"], 0))
        picked = []
        for p in pool:
            if sum(1 for q in squad + picked if q["team"] == p["team"]) < MAX_PER_CLUB:
                picked.append(p)
            if len(picked) == n:
                break
        squad += picked
    chance = chance_factor(jp)

    print(f"squad: {len(squad)} · forwards = " + " · ".join(
        f"{p['web_name']} (xP {xp_by_id.get(p['id'])}{', ' + str(jp['chance']) + '%' if p is jp else ''})"
        for p in squad if p["position"] == "FWD"))
    base_naive = best_xi_points(squad, xp_by_id)
    base_true = expected_xi(squad, xp_by_id, jp, chance)
    print(f"\n  XI as the app scores it (max of the expectation): {base_naive:.2f}")
    print(f"  XI as the manager experiences it (expectation of the max): {base_true:.2f}")
    print(f"  the model is understating the squad by {base_true - base_naive:+.2f} — the bench cover it "
          f"cannot see\n")

    # Now: rank candidate transfers both ways.
    print(f"  {'move':<40} {'app gain':>9} {'true gain':>10} {'delta':>7}")
    by_id = {p["id"]: p for p in players}
    shortlist = suggest_transfers(squad, players, xp_by_id, bank=1.2, limit=4)
    rows = []
    for m in shortlist:
        rows.append((f"{m['out']['web_name']} -> {m['in']['web_name']}", m["gain"],
                     by_id[m["out"]["id"]], by_id[m["in"]["id"]]))
    # …plus the move the owner is asking about: upgrade a weak forward.
    for w in weak:
        best_fwd = max((c for c in players if c["position"] == "FWD" and c["status"] == "a"
                        and c["price"] <= w["price"] + 1.2
                        and c["id"] not in {p["id"] for p in squad}),
                       key=lambda c: xp_by_id.get(c["id"], 0), default=None)
        if best_fwd:
            after = [p for p in squad if p["id"] != w["id"]] + [best_fwd]
            rows.append((f"{w['web_name']} -> {best_fwd['web_name']} (cover)",
                         round(best_xi_points(after, xp_by_id) - base_naive, 2), w, best_fwd))
    for label, app_gain, out, inc in rows:
        after = [p for p in squad if p["id"] != out["id"]] + [inc]
        true_gain = expected_xi(after, xp_by_id, jp, chance) - base_true
        print(f"  {label:<40} {app_gain:>9.2f} {true_gain:>10.2f} {true_gain - app_gain:>+7.2f}")
    db.close()


if __name__ == "__main__":
    main()
