"""Score the shipped price predictor against what actually happened (ADR-092, recalibrated ADR-215).

⭐⭐ **It imports the real functions.** A backtest that reimplements the rule measures the
reimplementation — and the whole reason this is worth running is that nobody has ever checked whether
the shipped one works.

Two pairings, and the difference between them is the point:

* **Same week (a ceiling).** The signal for GW N against the price change that happened during GW N's
  window. The counters are the END of that window, so they include transfers made *after* the price
  already moved — this is the rule marking its own homework with hindsight. ⚠️ *If it cannot separate
  movers from non-movers here, it cannot possibly forecast.*
* **Next week (the honest test).** The signal for GW N against the change in GW N+1's window. No
  hindsight, and this is the claim the ▲ actually makes to a reader.
"""

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from src.analytics.price import price_prediction, price_thresholds  # noqa: E402

TOTAL_MANAGERS = 11_000_809   # ⚠️ today's figure used for every week; see "Caveats" in the report


def load():
    rows = json.loads((pathlib.Path(__file__).parent / "history.json").read_text())
    by_round = {}
    for r in rows:
        by_round.setdefault(r["round"], {})[r["id"]] = r
    return by_round


def as_player(row):
    """The shape the shipped rule reads."""
    return {
        "id": row["id"],
        "web_name": row["name"],
        "selected_by": row["selected"] / TOTAL_MANAGERS * 100,
        "transfers_in_event": row["in"],
        "transfers_out_event": row["out"],
    }


def outcome(prev, cur):
    """What the price actually did, in tenths."""
    if prev is None or cur is None:
        return None
    d = cur["value"] - prev["value"]
    return "rise" if d > 0 else "fall" if d < 0 else "stable"


def score(by_round, offset: int):
    """offset 0 = same week (ceiling) · offset 1 = next week (forecast)."""
    rounds = sorted(by_round)
    tally = {}
    for rnd in rounds:
        board = [as_player(r) for r in by_round[rnd].values()]
        cuts = price_thresholds(board)
        if cuts.rise is None and cuts.fall is None:
            continue
        for p in board:
            call = price_prediction(p, cuts)
            a, b = rnd + offset - 1, rnd + offset
            actual = outcome(by_round.get(a, {}).get(p["id"]), by_round.get(b, {}).get(p["id"]))
            if actual is None:
                continue
            tally[(call, actual)] = tally.get((call, actual), 0) + 1
    return tally


def report(name, tally):
    calls = ("rise", "fall", "stable")
    print(f"\n  {name}")
    print(f"    {'called':<8}" + "".join(f"{'actually ' + a:>18}" for a in calls) + f"{'n':>8}")
    for c in calls:
        n = sum(tally.get((c, a), 0) for a in calls)
        row = "".join(f"{tally.get((c, a), 0):>18,}" for a in calls)
        print(f"    {c:<8}{row}{n:>8,}")
    print()
    for d in ("rise", "fall"):
        called = sum(tally.get((d, a), 0) for a in calls)
        right = tally.get((d, d), 0)
        happened = sum(tally.get((c, d), 0) for c in calls)
        prec = right / called * 100 if called else 0
        rec = right / happened * 100 if happened else 0
        base = happened / max(sum(tally.values()), 1) * 100
        print(f"    {d.upper():<5} precision {prec:5.1f}%  ({right:,}/{called:,})"
              f"   recall {rec:5.1f}%  ({right:,}/{happened:,})"
              f"   base rate {base:4.1f}%   lift {prec / base if base else 0:.1f}x")


if __name__ == "__main__":
    data = load()
    print(f"  {sum(len(v) for v in data.values()):,} player-gameweeks, rounds {min(data)}..{max(data)}")
    report("SAME WEEK — the ceiling (signal sees the whole window, including after the change)",
           score(data, 0))
    report("NEXT WEEK — the honest forecast (what the ▲ actually claims)", score(data, 1))
