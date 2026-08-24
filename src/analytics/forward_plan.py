"""The weeks ahead — what's coming for a squad, and when to act (ADR-131).

The Risk Monitor (ADR-130) asks *"who needs attention now?"*. This asks *"what's coming, and when?"*.

**It leads with fixture exposure, not projected points, and that was decided by measurement.** A prototype on a
real squad put six gameweeks inside a 3.9-point range on a 55.8 average — **±3%** — because the fixture
multiplier is ±20% at its extremes (ADR-006) and averaging fifteen players smooths most of that away. Naming a
"problem week" out of that spread would be presenting noise as a finding. Over the same six weeks the number of
players facing a hard match swung **2 → 7**; that is the signal worth a chart.

The real headline is a **blank** or a **double**, because those change a week in kind rather than by degree — a
blanked player scores nothing at all. Those do not exist yet (FPL publishes a full 10-fixture schedule; cup
rounds displace fixtures later), so this must be able to say *nothing stands out* without inventing drama.

Pure and reuse-only: `decision_xp`'s `by_gameweek` (ADR-032), `team_schedule` and FDR difficulties.
"""

from src.analytics.fdr import team_schedule

HARD_DIFFICULTY = 4      # FPL's own scale: 4 and 5 are the hard end
HARD_MARGIN = 2          # a week is "tough" only this far above the window's median — see `_flag`
_FLAT_SHARE = 0.10       # an xP spread under a tenth of the average reads as flat, because it is


def _get(row, key):
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _median(values):
    vals = sorted(values)
    if not vals:
        return 0
    mid = len(vals) // 2
    return vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2


def week_rows(owned, upcoming, by_gameweek_by_id=None, *, horizon: int = 6) -> list[dict]:
    """One row per upcoming gameweek: the squad's exposure, and who it falls on.

    `blank` is a player whose club has **no** fixture that week, `double` one whose club has two, and `hard` one
    facing difficulty ≥ `HARD_DIFFICULTY` (the worse of the two in a double — a double is only as easy as its
    harder half). Names are carried alongside the counts: the count says there is a problem, the names say what
    to do about it.
    """
    events = sorted({f["event"] for f in upcoming if f["event"] is not None})[:horizon]
    schedules = {t: team_schedule(upcoming, t) for t in {_get(p, "team") for p in owned}}
    rows = []
    for event in events:
        hard, blank, double = [], [], []
        for p in owned:
            name = _get(p, "web_name")
            fx = [s for s in schedules.get(_get(p, "team"), []) if s["event"] == event]
            if not fx:
                blank.append(name)
                continue
            if len(fx) > 1:
                double.append(name)
            if max((s.get("difficulty") or 3) for s in fx) >= HARD_DIFFICULTY:
                hard.append(name)
        rows.append({
            "event": event,
            "xp": round(sum((by_gameweek_by_id or {}).get(_get(p, "id"), {}).get(event, 0.0) for p in owned), 1),
            "hard": hard, "blank": blank, "double": double,
        })
    return rows


def _flag(row, hard_median) -> str | None:
    """Why this week is worth calling out, or None if it isn't.

    Blanks and doubles always count — they change a week **in kind**. A hard run only counts when it is well
    clear of the window's median, because a fifteen-man squad's exposure wobbles by a player or two every week
    and calling that a problem would be the noise-as-finding trap this whole module is shaped around.
    """
    if row["blank"]:
        return "blank"
    if row["double"]:
        return "double"
    if len(row["hard"]) >= hard_median + HARD_MARGIN:
        return "hard"
    return None


def forward_plan(owned, upcoming, by_gameweek_by_id=None, *, horizon: int = 6) -> dict:
    """The weeks ahead: per-gameweek exposure, any weeks worth acting on, and an honest headline.

    Returns `{"weeks", "headline", "xp": {"avg", "min", "max", "flat"}}`. `flat` is True when the projected
    points barely move across the window — which is the *usual* case and worth saying, so a reader doesn't
    read a 3% wobble as a forecast.
    """
    rows = week_rows(owned, upcoming, by_gameweek_by_id, horizon=horizon)
    if not rows:
        return {"weeks": [], "headline": "No fixtures to look at yet.", "xp": None}

    hard_median = _median([len(r["hard"]) for r in rows])
    for r in rows:
        r["flag"] = _flag(r, hard_median)

    xps = [r["xp"] for r in rows]
    avg = sum(xps) / len(xps)
    xp = {"avg": round(avg, 1), "min": min(xps), "max": max(xps),
          "flat": (max(xps) - min(xps)) < _FLAT_SHARE * avg if avg else True}

    return {"weeks": rows, "headline": _headline(rows, len(rows)), "xp": xp}


def _headline(rows, span) -> str:
    """One line naming the week to act on — or saying plainly that there isn't one.

    "No standout week" is a real answer, not a failure to find something. A planner that always names a worst
    week teaches its reader to distrust it.
    """
    blanks = [r for r in rows if r["blank"]]
    if blanks:
        w = max(blanks, key=lambda r: len(r["blank"]))
        return (f"GW{w['event']} is the one to plan for — **{len(w['blank'])} of your players blank**"
                f" ({', '.join(w['blank'][:3])}{'…' if len(w['blank']) > 3 else ''}).")
    doubles = [r for r in rows if r["double"]]
    if doubles:
        w = max(doubles, key=lambda r: len(r["double"]))
        return (f"GW{w['event']} is a **double** for {len(w['double'])} of your players"
                f" ({', '.join(w['double'][:3])}{'…' if len(w['double']) > 3 else ''}) — a week to load up on.")
    tough = [r for r in rows if r["flag"] == "hard"]
    if tough:
        w = max(tough, key=lambda r: len(r["hard"]))
        return (f"GW{w['event']} is your toughest — **{len(w['hard'])} players face a hard fixture**"
                f" ({', '.join(w['hard'][:3])}{'…' if len(w['hard']) > 3 else ''}).")
    return f"No standout week in the next {span} — your fixtures are even. Nothing to plan around yet."
