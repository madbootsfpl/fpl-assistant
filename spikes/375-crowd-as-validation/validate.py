"""The crowd as a validation set, not an input (ADR-377).

⭐⭐ The sentiment signal cannot yet be **backtested as a feature**: `player_transfer_flow` holds too few
phase-comparable readings (ADR-377). But it can be used for free in the one way that needs no history —
**as a second opinion on a correction we have already derived independently.**

ADR-375 claims `clean_sheet_delta` under-credits defenders who moved to a better defence. If that is true,
the players it under-credits should be the ones **the crowd is buying** — two unrelated methods pointing the
same way. ⚠️ Agreement is corroboration, not proof: the crowd could be wrong in the same direction we are.

⭐ Ownership is used rather than the transfer counters **because it is a stock, not a flow.** The counters
reset at each deadline and climb all week, so a reading 0.6 h out and one 4.9 h out are not comparable
(GW7 vs GW8, ADR-377). `selected_by` is a level: it does not reset, so a few hours of phase drift barely
moves it. *The phase defect blocks the flows and leaves the stock usable.*
"""

import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.analytics.backtest import spearman  # noqa: E402
from src.analytics.cleansheet import unpriced_defence_by_id  # noqa: E402
from src.storage import Storage  # noqa: E402


def main():
    db = Storage()
    players = db.get_players()
    doubt = unpriced_defence_by_id(players, db.get_history_by_code(), db.get_all_fixtures())

    flow = db.transfer_flow()
    events = sorted({r["event"] for r in flow})
    print(f"crowd readings held: {events}")
    phases = {e: min(r["hours_to_deadline"] for r in flow
                     if r["event"] == e and r["hours_to_deadline"] is not None) for e in events}
    print("  phase of each (hours before deadline): "
          + "  ".join(f"GW{e} @ {phases[e]:.0f}h" for e in events))
    if len(events) < 2:
        print("\n  ⚠️ fewer than two readings — nothing to difference. Re-run once the capture has more.")
        db.close()
        return
    first, last = events[0], events[-1]
    print(f"  ⚠️ phases differ by {abs(phases[last] - phases[first]):.0f}h, so the COUNTERS are not"
          " comparable across these two readings — only ownership is used below.\n")

    owned = {e: {r["element_code"]: r["selected_by"] for r in flow if r["event"] == e} for e in events}
    pairs = []
    for p in players:
        if p["position"] not in ("DEF", "GK"):
            continue
        a, b = owned[first].get(p["code"]), owned[last].get(p["code"])
        if a is None or b is None:
            continue
        pairs.append((p, doubt.get(p["id"], 0.0), b - a, a))

    print(f"DEF/GK present in both readings: {len(pairs)}\n")

    # @@ **Ownership change is FLOOR-LIMITED and the first run of this ignored it.** A player at 0.0%
    # cannot lose ownership and will not gain any, so the un-owned tail contributes near-zero movement
    # carrying no information - and it dominated the correlation (rho = 0.021 across all 290). The crowd
    # has no opinion about a player nobody owns, and reading its silence as disagreement is a sampling
    # error, not a finding.
    print(f"  {'ownership floor':>16} {'n':>5} {'rho':>8} {'under-rated':>14} {'rest':>11}")
    for floor in (0.0, 0.5, 1.0, 3.0, 5.0):
        sub = [t for t in pairs if t[3] >= floor]
        rho = spearman([d for _, d, _, _ in sub], [m for _, _, m, _ in sub])
        flagged = [t for t in sub if t[1] > 0]
        rest = [t for t in sub if t[1] == 0]
        mf = statistics.mean(m for _, _, m, _ in flagged) if flagged else float("nan")
        mr = statistics.mean(m for _, _, m, _ in rest) if rest else float("nan")
        shown = f"{rho:.3f}" if rho is not None else "n/a"
        print(f"  {'>= ' + str(floor) + '%':>16} {len(sub):>5} {shown:>8} "
              f"{mf:>+13.3f}pp {mr:>+10.3f}pp  (flagged {len(flagged)})")
    print("\n  rho rising with the floor is what corroboration looks like: the crowd's view carries more"
          "\n  information where the crowd actually holds one. @@ It is ALSO what a measurement-quality"
          "\n  effect looks like - ownership change is simply measured better among owned players - and two"
          "\n  readings cannot tell those apart. Reported as support for ADR-375's gate, not as a result.")

    print(f"\n  the ones we under-rate most, among players at least 3% owned:")
    print(f"    {'player':<14} {'team':>5} {'unpriced':>9} {'owned ' + str(first):>9} "
          f"{'owned ' + str(last):>9} {'change':>8}")
    for p, d, m, a in sorted((t for t in pairs if t[3] >= 3.0), key=lambda t: -t[1])[:10]:
        print(f"    {p['web_name'][:14]:<14} {p['team']:>5} {d:>+9.2f} "
              f"{a:>9.1f} {owned[last][p['code']]:>9.1f} {m:>+8.2f}")
    db.close()


if __name__ == "__main__":
    main()
