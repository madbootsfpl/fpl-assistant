"""Which players are worth a look, and why — convergence across the stat boards (ADR-167).

The Players tab carried five leaderboards of the same shape: set pieces, over/under, DefCon, clean sheets,
xG·xA. Each is true and none is a decision. The owner, reading them: *"I am getting weary as I tab through…
could we call out a recommendation rather than just showing multiple tables of fact which none will use."*

**The claim this module makes is deliberately narrow: `worth a look`, not `worth points`.** Two of the signals
it reads — set-piece duty and DefCon — are ones the engine has explicitly decided *not* to price yet
(`SET_PIECE_WEIGHT` and `DEFCON_MAGNIFIER_WEIGHT` are both **0**, pending the GW4-6 calibration). Ranking
players on them as though they were points would be the app asserting confidence it has withheld, and would
put a second opinion beside `decision_xp` — which is the one thing ADR-041 exists to prevent.

**What a single board cannot say is that two boards agree.** A first-choice penalty taker who *also* clears
the DefCon threshold is a different proposition from either fact alone, and convergence is cheap, honest, and
genuinely new information. So this returns players who stand out on **two or more** signals, each with the
evidence that put them there — never a score, never an ordering that competes with xP.

⚠️ **Most of the evidence is last season's, and every reason says so.** Over/under, DefCon and clean sheets
need **900 minutes** to mean anything; the most any player has played this season is 180. Those boards run on
ADR-126's last-season fallback until about GW10, and a reason that did not carry its own vintage would be the
most misleading kind of true statement.
"""

from src.analytics.cleansheet import defensive_solidity
from src.analytics.defcon import defcon_reliability
from src.analytics.overperf import over_under

# How far down each board still counts as "standing out". Not tuned — there is nothing to tune it on while
# three of the four boards are last season's. It is a **display** cut-off for a shortlist, and it is stated
# rather than hidden, because a threshold with no population behind it is a number pretending to be a finding.
TOP_N = 25

# …and how many signals must agree. Two is the whole point: one board is a fact, two boards are a reason.
MIN_SIGNALS = 2


def _get(row, key, default=None):
    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if value is None else value


def _vintage(season):
    """` (2025/26)` for a last-season fact, `""` for a current one — appended to every reason it applies to."""
    return f" ({season})" if season else ""


def set_piece_reason(player) -> str | None:
    """The one signal that is **current**: it reads a duty, not a rate, so it needs no minutes at all."""
    pens, corners = _get(player, "penalties_order"), _get(player, "corners_order")
    if pens == 1:
        return "first-choice penalties"
    if corners == 1:
        return "first-choice corners"
    if pens and pens <= 2:
        return f"penalties (order {int(pens)})"
    return None


def worth_a_look(players, *, rows=None, season=None, top_n: int = TOP_N,
                 min_signals: int = MIN_SIGNALS, limit: int = 8) -> list[dict]:
    """Players standing out on ≥ `min_signals` boards — `[{id, web_name, team, position, reasons}]`.

    `rows` is the pool the *rate* boards read (this season's players, or `last_season_rows` while nobody has
    900 minutes); `season` names it, and is carried into every reason drawn from it. `players` is always the
    current pool — set-piece duty and the display fields come from there.

    Ordered by how many signals agree, then by name. **Deliberately not ordered by any of the underlying
    numbers**: they are on different scales measuring different things, and picking one to sort by would smuggle
    in a ranking this module has no basis for.
    """
    current = {_get(p, "id"): p for p in players or []}
    reasons: dict = {}

    def add(pid, text):
        if pid in current:
            reasons.setdefault(pid, []).append(text)

    for p in players or []:
        if (why := set_piece_reason(p)):
            add(_get(p, "id"), why)

    pool = list(rows or [])
    tag = _vintage(season)
    for r in defcon_reliability(pool)[:top_n]:
        add(_get(r, "id"), f"DefCon +{_get(r, 'margin', 0):.1f}/90 over the bar{tag}")
    for r in defensive_solidity(pool)[:top_n]:
        add(_get(r, "id"), f"concedes {_get(r, 'xgc90', 0):.2f} xGC/90{tag}")
    # Under-performers only. An over-performer is a **warning** — points ahead of the underlying numbers tend
    # to regress — so counting them as a reason to look would invert the signal.
    for r in sorted(over_under(pool), key=lambda x: _get(x, "diff", 0))[:top_n]:
        if _get(r, "diff", 0) < 0:
            add(_get(r, "id"), f"{abs(_get(r, 'diff', 0)):.0f} pts below expected — due a bounce{tag}")

    out = []
    for pid, why in reasons.items():
        if len(why) < min_signals:
            continue
        p = current[pid]
        out.append({"id": pid, "web_name": _get(p, "web_name", ""), "team": _get(p, "team", ""),
                    "position": _get(p, "position", ""), "price": _get(p, "price"),
                    "selected_by": _get(p, "selected_by"), "reasons": why})
    out.sort(key=lambda r: (-len(r["reasons"]), r["web_name"] or ""))
    return out[:limit]


def scout_note(found, *, season=None) -> str:
    """One sentence framing the list — or explaining an empty one, which is a real answer here.

    Named for what it must not become: a recommendation to buy. It says how many players two or more boards
    agree on, and where that evidence came from.
    """
    if not found:
        return ("No player stands out on more than one of these boards right now — which is the honest "
                "answer, not a gap. One board agreeing with itself is just a leaderboard.")
    n = len(found)
    who = "player" if n == 1 else "players"
    src = (f" Most of the evidence is **{season}** — the rate boards need ~900 minutes, so they read last "
           "season until around GW10." if season else "")
    return (f"**{n} {who}** stand out on two or more of these boards at once. That is a reason to look, "
           f"**not a points projection** — set-piece and DefCon value is not in xP yet.{src}")
