"""Which owned players are a **dead slot** — a squad place that cannot score (ADR-136).

The gap this fills: `suggest_transfers` ranks by the swap's effect on the best legal starting XI (ADR-046), so
a dead player sitting on the *bench* moves that number by exactly zero and the advice reads *"no positive-gain
upgrade — hold"*. The ranking is correct about what it measures. It just isn't the only thing a squad slot is
for: a dead slot is a permanent zero **with no auto-sub cover**, which costs nothing on the sheet and
everything on the week a starter is knocked.

**Why the news string, of all things.** 94 of 610 players are currently unavailable and `decision_xp` scores
every one of them at 0.00 — it cannot separate them, because `chance_of_playing_next_round` is 0 for all of
them by definition. *Next round* is the only thing that field knows. Yet a player who has joined Konyaspor
permanently and a £7.5m winger back from a calf strain in two weeks are opposite advice. The **only** signal
that distinguishes them lives in FPL's free-text `news`. So we parse it — narrowly, and with the failure
direction chosen on purpose (below).

**The failure direction is the important design decision here.** A date we cannot parse means the player is
**not** dead, and the advice stays exactly as it is today. Missing a dead slot leaves the manager where they
already are; inventing one costs them a transfer. So every uncertainty resolves toward silence.
"""

import re
from datetime import date, datetime

from src.analytics.optimizer import is_unavailable

# FPL writes two dated forms, and both end in `<D Mon>`: "Ankle injury - Expected back 14 Sep" and
# "Suspended until 19 Sep". Everything else in the live data is either "... - Unknown return date" or a
# departure ("Has joined ... permanently", "has returned to Getafe CF") — neither of which carries a date.
_DATED = re.compile(r"(?:expected back|suspended until)\s+(\d{1,2})\s+([A-Za-z]{3})", re.I)
_MONTHS = {m: i for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), start=1)}


def _get(row, key):
    """Row/dict safe read — these functions take sqlite3.Row in the app and dicts in tests."""
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        return None


def _is_gone(player) -> bool:
    """Has he left the league entirely? Status `u` is FPL's marker for it and is unambiguous.

    Worth separating from an injury even though both score zero: "has joined Inter" is a permanent fact, and
    it is also the sentence that actually makes a manager act.
    """
    return _get(player, "status") == "u"


def return_date(player, *, today: date):
    """The date this player is expected back, or `None` when the news gives no date.

    `None` is the common case and covers three different situations — a departure, an "Unknown return date"
    injury, and news we could not parse — which callers deliberately treat the same way: no date to wait for.

    **Year inference.** FPL writes "14 Sep" with no year, and an FPL season runs August → May, so a month
    *earlier* than today's belongs to next year. In August, "5 Sep" is this year and "10 Jan" is next; in
    January, "5 Sep" would be this year's September, eight months out — still correctly "a long way off",
    which is all any caller asks of it.
    """
    m = _DATED.search(_get(player, "news") or "")
    if not m:
        return None
    day, month = int(m.group(1)), _MONTHS.get(m.group(2).lower())
    if month is None:
        return None
    year = today.year + 1 if month < today.month else today.year
    try:
        return date(year, month, day)
    except ValueError:                       # "31 Feb" and friends — unparseable is not-dead, by design
        return None


def _kickoff(fixture):
    """A fixture's kickoff as a date, or None if it has none (FPL leaves TBC fixtures without one)."""
    raw = _get(fixture, "kickoff_time")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date()
    except ValueError:
        return None


def gameweeks_missed(player, upcoming, *, today: date, horizon: int = 5) -> tuple[int, int]:
    """`(missed, total)` — how many of his team's next `horizon` gameweeks this player misses.

    `total` counts only the gameweeks his team actually **plays** in, so a blank gameweek is not scored
    against him; there was nothing to miss. A gameweek counts as missed when **every** one of his team's
    fixtures in it kicks off before he is back — so in a double gameweek where he returns for the second
    match, he has not missed the week.

    With no return date, he misses all of them. That is the whole point of turning a string into this number:
    *"out until 28 Nov"* and *"has joined Inter"* both come out as 5-of-5, while *"back 5 Sep"* comes out as
    2-of-5 and stops being advice to sell.
    """
    team = _get(player, "team")
    events = sorted({f["event"] for f in upcoming if _get(f, "event") is not None})[:horizon]
    back = return_date(player, today=today)

    missed = total = 0
    for gw in events:
        kicks = [_kickoff(f) for f in upcoming
                 if _get(f, "event") == gw and team in (_get(f, "home"), _get(f, "away"))]
        if not kicks:                                    # blank gameweek — nothing to miss
            continue
        total += 1
        if back is None or all(k is None or k < back for k in kicks):
            missed += 1
    return missed, total


def _reported_reason(event) -> str:
    """Just the attribution — *"per Romano"* — because the caller's sentence already carries the claim.

    Kept short on purpose: the renderer says *"X is reported to be leaving — …"*, so a reason of "reported
    leaving" made that read *"is reported to be leaving — reported leaving — Romano"*. Naming **who** says it
    is the part that adds anything, since it is what lets a reader weigh the source.
    """
    source = event.get("source")
    return f"per {source}" if source else "per the press"


def dead_slots(owned, upcoming, *, today: date, horizon: int = 5, reported_out=None) -> list[dict]:
    """The owned players who cannot score for the whole horizon — the slots worth a transfer.

    Each entry is ``{player, reason, until, missed, total}``. `reason` is the honest word for *why*, because
    naming it is most of the value: *"Spence has joined Inter"* is a different sentence from *"Spence is a
    low-xP defender"*, and only one of them makes anyone act.

    A player is a dead slot only when he misses **every** gameweek in the horizon. A dated return inside it
    (Doku, back 5 Sep, 2 of the next 5) is not a dead slot — selling a premium to fill a two-week hole is
    worse advice than the "hold" this exists to fix.

    `reported_out` maps player id → the headline event showing he is **leaving the league** (ADR-153). FPL's
    `status` is the usual evidence, but it lags the news by days: Watkins read `a` — fully available — while
    Romano reported an agreed move to Al-Hilal and 167,825 managers sold him. **A confirmed departure is the
    same dead slot ADR-136 already handles; we simply know before FPL does.**
    """
    reported_out = reported_out or {}
    out = []
    for p in owned:
        event = reported_out.get(_get(p, "id"))
        if event is not None and not is_unavailable(p):
            # The press and the crowd both say he is going, and FPL has not caught up. Treated as missing the
            # whole horizon, because a player at a Saudi club scores nothing here ever again.
            out.append({"player": p, "reason": _reported_reason(event), "until": None,
                        "missed": horizon, "total": horizon, "event": event})
            continue
        if not is_unavailable(p):
            continue
        missed, total = gameweeks_missed(p, upcoming, today=today, horizon=horizon)
        if total == 0 or missed < total:                 # plays at some point in the horizon — not dead
            continue
        back = return_date(p, today=today)
        if _is_gone(p):
            reason = "gone"
        elif back is not None:
            reason = f"out until {back.strftime('%-d %b')}"
        else:
            reason = "no return date"
        out.append({"player": p, "reason": reason, "until": back, "missed": missed, "total": total})
    return out
