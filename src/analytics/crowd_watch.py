"""What the crowd is doing that a single leaderboard can't show (ADR-170).

Trending carries four boards — most owned · most transferred in · most transferred out · in form. Each is a
ranking of one number, and the useful signals live **between** them: a player can top none of the four and
still be the most interesting name on the page.

The owner, after Scout: *"For Trending I'd like an overview like you did for Scout, as it's a fab way of
directing people's attention to the more notable items."*

**Three patterns, each a different action, each needing two boards at once:**

* **In form, still under-owned** — the crowd has not caught up. The one nobody can see today, and the most
  valuable: it is a differential *with evidence*, rather than a differential because nobody has heard of him.
* **A bandwagon forming** — bought heavily, not yet template. Says whether you are early or late.
* **The template breaking up** — widely owned and being sold. Changes what "safe" means, which is the whole
  reason to track ownership at all.

**Two rules this module keeps.**

**1. Every threshold is one that already exists.** `FORM_MIN`, `TRENDING_NET`, `DIFFERENTIAL_OWN` and
`TEMPLATE_OWN` are all calibrated constants from `crowd.py` — inventing a fourth cut-off to make a nicer
shortlist would be a number with no population behind it.

**2. It says what the crowd is DOING, never why.** Trending and Signals are split on exactly that axis
(ADR-149/150): what people *do*, in numbers, versus what is being *said*. If a sell-off has a headline behind
it, Signals' exodus banner is where that belongs — repeating it here would collapse the distinction the two
pages exist on, and put an unsourced guess next to a measured fact.

Crowd data is a **lens** and never enters xP. So the claim is *worth noticing*, never *worth points*.
"""

from src.analytics.crowd import (
    DIFFERENTIAL_OWN,
    FORM_MIN,
    TEMPLATE_OWN,
    TRENDING_NET,
    _get,
    net_transfers,
)

# The order patterns are reported in — most actionable first. "Under-owned and in form" leads because it is
# the only one that tells you something before the crowd does; the other two describe a move already under way.
PATTERNS = ("undervalued", "bandwagon", "template_breaking")

_LABEL = {
    "undervalued": "In form, still under-owned",
    "bandwagon": "A bandwagon forming",
    "template_breaking": "The template breaking up",
}


def _form(player) -> float:
    try:
        return float(_get(player, "form") or 0.0)
    except (TypeError, ValueError):
        return 0.0


def classify(player) -> str | None:
    """Which pattern a player shows, or `None` — the whole rule set, in one readable place.

    Checked in order, and a player reports **one** pattern: the shortlist answers *"what should I notice?"*,
    and a name appearing three times with three framings is a worse answer than a name appearing once.
    """
    own, net, form = _get(player, "selected_by"), net_transfers(player), _form(player)
    if own is None:
        return None
    if form >= FORM_MIN and own <= DIFFERENTIAL_OWN:
        return "undervalued"
    if net is not None and net >= TRENDING_NET and own < TEMPLATE_OWN:
        return "bandwagon"
    if net is not None and net <= -TRENDING_NET and own >= TEMPLATE_OWN:
        return "template_breaking"
    return None


def reason(player, pattern: str) -> str:
    """The evidence, in the crowd's own units — never an explanation of *why* (that is Signals')."""
    own, net, form = _get(player, "selected_by"), net_transfers(player), _form(player)
    if pattern == "undervalued":
        return f"form {form:.1f} on just {own:.1f}% owned"
    if pattern == "bandwagon":
        return f"{net:+,} transfers this gameweek, still {own:.1f}% owned"
    return f"{net:+,} transfers this gameweek, off {own:.1f}% owned"


def worth_noticing(players, *, per_pattern: int = 4) -> list[dict]:
    """`[{pattern, label, players: [{id, web_name, team, position, price, reason}]}]`, most actionable first.

    Capped `per_pattern` because this is a *pointer*, not a fifth board — the boards are directly below it, and
    a shortlist long enough to need scrolling has stopped directing attention and started competing for it.
    Groups with nothing to report are dropped rather than shown empty.
    """
    found: dict = {p: [] for p in PATTERNS}
    for player in players or []:
        pattern = classify(player)
        if pattern is None:
            continue
        found[pattern].append({
            "id": _get(player, "id"), "web_name": _get(player, "web_name"),
            "team": _get(player, "team"), "position": _get(player, "position"),
            "price": _get(player, "price"), "selected_by": _get(player, "selected_by"),
            "reason": reason(player, pattern),
        })

    out = []
    for pattern in PATTERNS:
        rows = found[pattern]
        if not rows:
            continue
        # Within a group, rank by the number that *defines* it — form for the undervalued, the size of the
        # move for the other two. Across groups the order is fixed (see PATTERNS): mixing them would need a
        # score comparing "form" with "transfers", which are not on the same scale and never will be.
        key = (lambda r: -(r["selected_by"] or 0)) if pattern == "undervalued" else \
              (lambda r: -abs(int(r["reason"].split()[0].replace(",", "").replace("+", ""))))
        out.append({"pattern": pattern, "label": _LABEL[pattern], "players": sorted(rows, key=key)[:per_pattern]})
    return out


def watch_note(groups) -> str:
    """One sentence framing the shortlist — or explaining an empty one, which is a real answer in a quiet week."""
    if not groups:
        return ("Nothing unusual in the crowd numbers this gameweek — no under-owned player in form, no "
                "bandwagon, no template pick being dumped. A quiet week is a finding, not a gap.")
    n = sum(len(g["players"]) for g in groups)
    return (f"**{n} players** the four boards below only show *between* them. This is what other managers are "
            "**doing** — not a points projection, and not a reason: for *why* a player is moving, see "
            "📡 **Signals**.")
