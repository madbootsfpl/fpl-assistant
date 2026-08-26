"""How much of a gameweek rides on one match (ADR-145) — the honest version of "player clashes".

**The Roadmap's premise did not survive being checked.** It asked for *"your own players meeting = point
cannibalisation"*: flag your attacker facing your defender, because a goal kills the clean sheet. Two
measurements on live data killed that framing.

**1. Clashes are universal, so a list of them is noise.** Across 300 random legal squads over five gameweeks,
**100%** had at least one, averaging **26 clashing pairs**. Narrowed to the starting XI *and* to the only
combination that actually conflicts — a defensive asset against an attacker — it is still **7.4 per squad**.
Nobody can act on that, and a warning that fires for everyone every week is wallpaper.

**2. A clash does not cost expected points, which is the part the premise gets wrong.** `decision_xp` already
prices each player's own fixture (ADR-006/032): a defender facing a strong attack is already discounted, and
so is an attacker facing a strong defence. Summing them does not double-count. What a clash changes is the
**joint** distribution — the two outcomes become anti-correlated — not either marginal. Your expected score is
unchanged; your *variance* falls.

And lower variance is not automatically bad. Chasing a rival wants variance; protecting a lead wants less of
it. That is the same logic as league effective ownership (ADR-141), and it means "cannibalisation" is the
wrong word for a thing that is sometimes exactly what you want.

**So this measures the real, actionable quantity instead: concentration.** How much of one gameweek's XI
projection depends on a single match. On live data that is **29% at the median, 40% at p90 and 64% at worst** —
which is a fact about a squad a manager can do something about, and it *subsumes* clashes: a clash is simply a
concentration whose players sit on opposite sides of the same fixture.
"""

from collections import defaultdict

# The thresholds are the measured quartiles of the distribution above, not round numbers — the same
# calibrate-against-your-own-spread idiom as ADR-144's captain margin and ADR-138's price peers.
CONCENTRATED = 0.35      # ≈ p75: about a quarter of squad-gameweeks
HEAVY = 0.45             # above p90: rare enough that saying so means something


def _get(row, key, default=None):
    try:
        v = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if v is None else v


def _fixtures_by_event(upcoming) -> dict:
    """`{event: [(home, away)]}` — the matches in each gameweek."""
    out = defaultdict(list)
    for f in upcoming or []:
        event = _get(f, "event")
        if event is not None:
            out[event].append((_get(f, "home"), _get(f, "away")))
    return out


def match_concentration(owned, upcoming, by_gameweek_by_id, *, horizon: int = 6) -> list[dict]:
    """Per gameweek, the single match carrying the largest share of the squad's projection.

    `owned` should be the **starting XI**, not the 15 — a benched player scores nothing, so counting them
    would dilute the share with points that were never at risk.

    Each row is ``{event, share, xp, total, home, away, players, opposed}``:

    * `share` — that match's xP as a fraction of the gameweek's total.
    * `opposed` — True when the squad has players on **both** sides. This is the clash the Roadmap asked
      about, kept as a *qualifier* rather than a warning: those players' returns partly cancel, so the week is
      even less spread than the share alone suggests.

    Empty when there is nothing to measure. A gameweek whose projection totals zero is skipped rather than
    divided by — an undefined share is not a share of zero.
    """
    fixtures = _fixtures_by_event(upcoming)
    events = sorted(fixtures)[:horizon]
    by_gw = by_gameweek_by_id or {}
    rows = []
    for event in events:
        total = sum(by_gw.get(_get(p, "id"), {}).get(event, 0.0) for p in owned)
        if total <= 0:
            continue
        best = None
        for home, away in fixtures[event]:
            involved = [p for p in owned if _get(p, "team") in (home, away)]
            if not involved:
                continue
            value = sum(by_gw.get(_get(p, "id"), {}).get(event, 0.0) for p in involved)
            if best is None or value > best["xp"]:
                sides = {_get(p, "team") for p in involved}
                best = {
                    "event": event, "xp": round(value, 1), "total": round(total, 1),
                    "share": value / total, "home": home, "away": away,
                    "players": [_get(p, "web_name") for p in involved],
                    "opposed": len(sides) > 1,
                }
        if best:
            rows.append(best)
    return rows


def concentration_note(row) -> str | None:
    """One sentence for a gameweek that is genuinely concentrated, or `None` when it is ordinary.

    Returning `None` for the common case is the whole discipline here. The naive feature fired for every
    squad every week; this speaks only above the measured 75th percentile, so when it does say something a
    manager has reason to look.
    """
    if not row or row["share"] < CONCENTRATED:
        return None
    pct = round(row["share"] * 100)
    who = ", ".join(row["players"][:4]) + ("…" if len(row["players"]) > 4 else "")
    weight = "Over " if row["share"] >= HEAVY else ""
    note = (f"{weight}{pct}% of your GW{row['event']} rides on {row['home']} v {row['away']} "
            f"({len(row['players'])} players: {who}).")
    if row["opposed"]:
        # The Roadmap's "clash", stated as what it actually is: not a loss of expected points, a further
        # narrowing of the outcomes.
        note += (" You have players on **both** sides, so their returns partly cancel — the week is even "
                 "less spread than that.")
    return note
