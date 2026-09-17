"""§3 of ADR-191, designed: *"what would it take to field X?"* — verified on a real squad before building.

The app asks a **squad-driven** question — *for each player I own, what is the best replacement?* The owner
keeps asking a **target-driven** one:

> *"Is Haaland a better option than Bruno and figure the moves needed to select him."*  (2026-09-14)
> *"I would use my transfers to see if I can get another forward in that is scoring."*  (2026-09-17)

Two unprompted requests for the same missing shape. Nothing in the codebase answers it: `suggest_transfers`
iterates **outgoing** players and picks the best incoming, so a named incoming player can only be reached by
luck.

⭐ **The inversion is the whole feature.** Fix the incoming player; search the *route* — which of my fifteen
to sell. ADR-191 §2 already showed the route matters: on RoboTS the best pair routed **the same incoming
player through a different sale**, because that is the sale that leaves enough money for the second move.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "200-realistic-squads"))

from population import template  # noqa: E402

from src.analytics.optimizer import MAX_PER_CLUB, best_xi_points, is_unavailable  # noqa: E402
from src.analytics.xp import decision_xp  # noqa: E402
from src.storage import Storage  # noqa: E402


def route_to(target, owned, xp_by_id, *, bank=0.0, max_per_club=MAX_PER_CLUB):
    """Every legal one-transfer route to owning `target`, best first, plus what blocks the rest.

    A route is *which of my fifteen I sell*. FPL transfers are one-for-one and same-position, so the
    candidates are my players in the target's position — and they differ in two ways that matter: what they
    were contributing, and what selling them leaves in the bank.

    ⭐ **Ranked by the XI effect, never by cheapness.** The obvious implementation sells whoever frees enough
    money; that is how ADR-191 §2's RoboTS case went wrong in the other direction.
    """
    if any(p["id"] == target["id"] for p in owned):
        return {"owned": True, "routes": [], "shortfall": None}

    club_counts: dict = {}
    for p in owned:
        club_counts[p["team"]] = club_counts.get(p["team"], 0) + 1

    base = best_xi_points(owned, xp_by_id)
    routes, blocked = [], []
    for out in owned:
        if out["position"] != target["position"]:
            continue
        # Club limit AFTER the swap: selling a clubmate of the target frees a slot, so this is not a
        # property of the squad today.
        after = dict(club_counts)
        after[out["team"]] = after[out["team"]] - 1
        if after.get(target["team"], 0) + 1 > max_per_club:
            continue
        budget = out["price"] + bank
        if budget < target["price"]:
            # ⭐ A blocked route is INFORMATION, not an absence. "Sell him and you are £0.6m short" is
            # exactly ADR-186's "worth saving for", and dropping it silently is how the reader learns
            # only about the route that happened to clear.
            blocked.append({"out": out["web_name"], "out_price": out["price"],
                            "short_by": round(target["price"] - budget, 1)})
            continue
        new_squad = [p for p in owned if p["id"] != out["id"]] + [target]
        routes.append({
            "out": out["web_name"], "out_price": out["price"], "out_xp": xp_by_id.get(out["id"], 0.0),
            "gain": round(best_xi_points(new_squad, xp_by_id) - base, 1),
            "bank_after": round(budget - target["price"], 1),
        })
    routes.sort(key=lambda r: -r["gain"])
    blocked.sort(key=lambda b: b["short_by"])
    return {"owned": False, "routes": routes, "blocked": blocked,
            "shortfall": blocked[0]["short_by"] if blocked else None}


def main():
    db = Storage()
    players, hist, gw = db.get_players(), db.get_history_by_code(), db.get_gw_history_by_code()
    up = db.get_upcoming_fixtures()
    ranked = decision_xp(players, up, hist, horizon=5, gw_history_by_code=gw)
    xp_by_id = {r["id"]: r["xp"] for r in ranked}

    squad = template(players)
    spend = sum(p["price"] for p in squad)
    bank = round(100.0 - spend, 1)
    print(f"squad: {len(squad)} players, £{spend:.1f}m spent, £{bank:.1f}m bank, "
          f"XI xP over 5 GWs = {best_xi_points(squad, xp_by_id):.1f}")
    print("  FWDs owned: " + " · ".join(f"{p['web_name']} £{p['price']}" for p in squad
                                        if p["position"] == "FWD"))

    for name in ("Haaland", "Isak", "Emersonn", "João Pedro"):
        target = next((p for p in players if p["web_name"] == name), None)
        if target is None or is_unavailable(target):
            print(f"\n{name}: not a valid target")
            continue
        res = route_to(target, squad, xp_by_id, bank=bank)
        print(f"\n▸ What would it take to field {name} (£{target['price']}m, {target['team']}, "
              f"xP {xp_by_id.get(target['id'])})?")
        if res["owned"]:
            print("    you already own him")
        elif not res["routes"]:
            print(f"    ✗ no single transfer affords him — short by £{res['shortfall']}m")
        else:
            for r in res["routes"][:3]:
                print(f"    sell {r['out']:<16} £{r['out_price']:<5} (xP {r['out_xp']:>5})  "
                      f"→  {r['gain']:>+6} XI xP · £{r['bank_after']}m left")
        for b in res.get("blocked", [])[:2]:
            print(f"    ✗ sell {b['out']:<14} £{b['out_price']:<5} — short by £{b['short_by']}m")
    db.close()


if __name__ == "__main__":
    main()
