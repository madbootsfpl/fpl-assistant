"""Pull every player's per-gameweek price, ownership and transfer counters.

⭐ `element-summary/{id}/` carries exactly the three things a price backtest needs — `value`,
`selected`, `transfers_in/out` — per gameweek, per player. Public, no key.

⚠️ Throttled on purpose. 667 requests is not a crawl, but FPL rate-limits and a tool that gets the
project blocked is worse than no tool.
"""

import json
import pathlib
import sys
import time
import urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120 Safari/537.36"
OUT = pathlib.Path(__file__).parent / "history.json"
DELAY = 0.25


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    boot = get("https://fantasy.premierleague.com/api/bootstrap-static/")
    elements = boot["elements"]
    rows = []
    for i, el in enumerate(elements, 1):
        try:
            hist = get(f"https://fantasy.premierleague.com/api/element-summary/{el['id']}/")["history"]
        except Exception as exc:                      # a missing player must not lose the other 666
            print(f"  ! {el['id']} {el['web_name']}: {exc}", file=sys.stderr)
            continue
        for h in hist:
            rows.append({
                "id": el["id"],
                "name": el["web_name"],
                "round": h["round"],
                "value": h["value"],
                "selected": h["selected"],
                "in": h["transfers_in"],
                "out": h["transfers_out"],
            })
        if i % 100 == 0:
            print(f"  {i}/{len(elements)}  ({len(rows):,} rows)", flush=True)
        time.sleep(DELAY)
    OUT.write_text(json.dumps(rows))
    print(f"  wrote {len(rows):,} rows for {len({r['id'] for r in rows})} players -> {OUT}")


if __name__ == "__main__":
    main()
