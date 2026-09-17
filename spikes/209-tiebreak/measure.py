"""What does the longer-view tie-break actually trade? (ADR-209)

It only ever chooses between moves the primary metric **cannot tell apart** — within `tie_noise(window)` of
the leader. So the question is not *"is it better"* but *"what does it give up, and how often does it speak"*.

⚠️ And one thing it must be checked for: the horizon map carries **ADR-192's cold-start inflation** (a player
with one appearance projecting 22.4 xP over five gameweeks). A tie-break on that number will preferentially
pick those players. ⭐ *A tie-break inherits the bias of whatever number it breaks the tie on.*
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "200-realistic-squads"))

import random  # noqa: E402

from population import perturbed, template  # noqa: E402

from src.analytics.transfer import suggest_transfers  # noqa: E402
from src.analytics.xp import decision_xp  # noqa: E402
from src.storage import Storage  # noqa: E402


def main():
    db = Storage()
    players = db.get_players()
    hist, gw, up = db.get_history_by_code(), db.get_gw_history_by_code(), db.get_upcoming_fixtures()
    r1 = decision_xp(players, up, hist, horizon=1, gw_history_by_code=gw)
    r5 = decision_xp(players, up, hist, horizon=5, gw_history_by_code=gw)
    x1 = {r["id"]: r["xp"] for r in r1}
    x5 = {r["id"]: r["xp"] for r in r5}
    tier = {r["id"]: r["rate_source"] for r in r5}
    base = template(players)

    fired = 0
    d_now, d_wide = [], []
    cold_before = cold_after = 0
    n = 0
    for seed in (1, 2, 3):
        rng = random.Random(seed)
        for k in (2, 4, 6, 8):
            for _ in range(8):
                squad = perturbed(base, players, k, rng)
                if squad is None or len(squad) != 15:
                    continue
                n += 1
                old = suggest_transfers(squad, players, x1, bank=1.0, limit=1, window=5)
                new = suggest_transfers(squad, players, x1, bank=1.0, limit=1,
                                        window=1, horizon_xp=x5)
                if not old or not new:
                    continue
                cold_before += tier.get(old[0]["in"]["id"]) == "cold_start"
                cold_after += tier.get(new[0]["in"]["id"]) == "cold_start"
                if old[0]["in"]["id"] == new[0]["in"]["id"] and old[0]["out"]["id"] == new[0]["out"]["id"]:
                    continue
                fired += 1
                d_now.append(new[0]["gain"] - old[0]["gain"])
                w_old = x5.get(old[0]["in"]["id"], 0) - x5.get(old[0]["out"]["id"], 0)
                w_new = x5.get(new[0]["in"]["id"], 0) - x5.get(new[0]["out"]["id"], 0)
                d_wide.append(w_new - w_old)

    print(f"squads: {n}   the tie-break changed the top move on {fired} ({fired / n:.0%})")
    if fired:
        print(f"\n  what it gives up next GW : mean {statistics.mean(d_now):+.2f} · "
              f"worst {min(d_now):+.2f}  (band at window=1 is 0.89)")
        print(f"  what it gains over 5 GWs : mean {statistics.mean(d_wide):+.2f} · "
              f"best {max(d_wide):+.2f} · worst {min(d_wide):+.2f}")
        print(f"  trades that LOSE over 5 GWs too: "
              f"{sum(1 for d in d_wide if d < 0)} of {len(d_wide)}")
    print(f"\n  ⚠️ ADR-192 interaction — top move is a cold_start player: "
          f"{cold_before} before → {cold_after} after")
    db.close()


if __name__ == "__main__":
    main()
