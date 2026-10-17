"""Match scores for a gameweek, and which of your players were in them (ADR-346).

⭐⭐ **The join is the feature.** A scoreline is a commodity — every livescore site has one. What nobody
else can print is *"CHE 5-1 BOU — your João Pedro scored twice"*, and the data for that is already here:
`player_history` carries each player's week keyed by fixture, and the squad arrives with the request.

🔴 **A finished match is a fact; a match in progress is a feed.** They are fetched differently on purpose:

* **Finished** — read from `fixtures`, which the pipeline fills. A played score never changes, so one
  successful fetch is enough, ever (ADR-298's economics, applied to matches instead of weeks).
* **In progress** — fetched live from FPL on request, behind a short cache. ⚠️ *The scheduled pipeline
  fires at roughly a fifth of its declared cadence with an 08:00–16:00 hole, so a "live" score behind it
  would be a lie in the product.* The live path does not go near it.

⚠️⚠️ **`0-0` is a real result and `None` is not.** Nothing here defaults a score to zero: a fixture that
has not kicked off reports `started: false` and null scores, and the one screen built to tell those apart
must not be handed a number that cannot.
"""

import time

from src.analytics import player_summary
from src.kits import badge_url
from src.service.inputs import opened
from src.service.requests import GameweekScoresRequest
from src.storage import Storage

#: How long a live scoreline may be served from memory. ⭐ The real control on upstream load — a rate limit
#: bounds one caller, this bounds *everyone*: nine testers refreshing during a 15:00 kick-off become one
#: request a minute against an undocumented API that can block a noisy client.
LIVE_CACHE_SECONDS = 60

#: How long after kick-off a match may still be treated as in progress (ADR-354).
#:
#: ⭐⭐ Generous on purpose, because it has to outlast **the pipeline**, not the match. A game is over
#: ~2h after kick-off, but `finished` in the database only flips when the refresh next runs — and the
#: observed gaps reach five hours. ⚠️ *Closing this window before the pipeline catches up would replace a
#: live score with "not started"*, which is worse than either truth. Inside it, FPL's own `finished` is
#: read live and the screen says Full time regardless.
LIVE_WINDOW_HOURS = 24

_live_cache: dict[int, tuple[float, list]] = {}


def _live_fixtures(gameweek: int, *, client=None, now=time.monotonic) -> list:
    """FPL's current `/fixtures/` for one gameweek, cached for `LIVE_CACHE_SECONDS`.

    ⚠️ **Never fatal.** A live fetch that fails returns nothing and the caller falls back to the stored
    score — ⭐ *a screen showing a half-hour-old score is working; a screen showing an error is not.*
    """
    hit = _live_cache.get(gameweek)
    if hit and now() - hit[0] < LIVE_CACHE_SECONDS:
        return hit[1]
    try:
        from src.api.client import FplClient
        rows = [f for f in (client or FplClient()).get_fixtures()
                if f.get("event") == gameweek]
    except Exception:          # noqa: BLE001 - every upstream failure degrades the same way
        return hit[1] if hit else []
    _live_cache[gameweek] = (now(), rows)
    return rows


def forget_live() -> None:
    """Drop the live cache. ⚠️ For tests — production lets the TTL do it."""
    _live_cache.clear()


def _started(f) -> bool:
    """Has this match kicked off?

    ⚠️⚠️ **`finished` implies `started`, and the database cannot be trusted to say so.** `started` arrived
    with ADR-346; every fixture stored before it has the column as NULL while `finished` is already 1 —
    so a played match read as *"not started but finished"*, and `_which_gameweek` could find no played
    week at all. ⭐ *A derived truth is cheaper than a backfill and cannot drift out of date.*
    """
    return bool(f["started"]) or bool(f["finished"])


def _over(f) -> bool:
    """Is the football finished? (ADR-356)

    ⚠️⚠️ **FPL has two "finished" flags and they mean different things.** `finished_provisional` is the
    referee: it flips at the whistle. `finished` is the accountant: it waits until **bonus points are
    confirmed** for the whole gameweek, which is hours later and sometimes the next day.

    🔴 Reading only `finished`, a match that ended at 13:20 still reported `minutes = 90` and printed
    **"90'"** all afternoon — ⭐ *a match that is over, captioned as if it were still being played.*

    ⭐ The project already knew this. ADR-123 refuses `finished` for the fixture horizon for exactly this
    reason — *"FPL holds that flag back until a gameweek's bonus points are confirmed"* — and that
    reasoning sat in one module and never reached the card.
    """
    return bool(f["finished"]) or bool(_get(f, "finished_provisional"))


def _get(f, key):
    """⚠️ Rows arrive as `sqlite3.Row` (no `.get`) and as dicts, and this key is on neither when it has not
    been merged — so the lookup has to tolerate all three. ⭐ The `kits._get` convention."""
    try:
        return f[key]
    except (KeyError, IndexError, TypeError):
        return None


def _status(f) -> str:
    """What to print under the score. ⚠️ Never invents a time it does not have."""
    if _over(f):
        return "Full time"
    if _started(f):
        return f"{f['minutes']}'" if f["minutes"] is not None else "Live"
    return ""


def _kicked_off(f, now=None) -> bool:
    """Has this match's kick-off time passed? (ADR-354)

    🔴🔴 **The live path was gated on a flag the hourly pipeline writes.** `started` only becomes 1 when
    the refresh next runs, so at 15:00 on a Saturday the database still said *not started*, `in_flight`
    was False, and the screen served **last week** — ⭐⭐ *the fetch did not depend on the pipeline and the
    decision to fetch did.*

    ⚠️⚠️ The kick-off time is **already stored, weeks in advance**: the fixture is known before the match
    and only its score evolves. ⭐ *A clock we already have beats a flag somebody has to write.*

    ⚠️ **Bounded at the far end, and the first version was not.** Kick-off alone made every old fixture
    the feed never finished — a postponement, an abandonment — count as in progress for ever, polling FPL
    and holding the screen on a dead week. 🔴 Caught by two tests going red against the seed, whose
    fixtures are months past; ⭐ *an unbounded "since" is a condition that becomes permanently true.*
    """
    from datetime import UTC, datetime, timedelta
    ko = f.get("kickoff_time") if hasattr(f, "get") else f["kickoff_time"]
    if not ko:
        return False
    try:
        when = datetime.fromisoformat(str(ko).replace("Z", "+00:00"))
    except ValueError:
        return False
    return when <= (now or datetime.now(UTC)) < when + timedelta(hours=LIVE_WINDOW_HOURS)


def _playing(f, now=None) -> bool:
    """A match this gameweek is in progress — by the clock, or because the feed already said so."""
    return (_started(f) or _kicked_off(f, now)) and not f["finished"]


def _which_gameweek(fixtures: list, now=None) -> int | None:
    """The gameweek worth showing: one with a match in progress, else the most recently played.

    ⭐ *"Current or last"* was the tester's own phrasing, and it is two questions with one answer — the
    live week while there is one, the finished week the rest of the time.
    """
    live = [f["event"] for f in fixtures if f["event"] and _playing(f, now)]
    if live:
        return min(live)
    played = [f["event"] for f in fixtures if f["event"] and _started(f)]
    return max(played) if played else None


def _yours(rows, squad, by_code, players) -> list:
    """The manager's players who featured in one fixture, with what they did.

    ⚠️ **Points come from `player_history`, never computed here.** FPL settles bonus after full time, and
    ⭐ *a total this app worked out itself would disagree with the one FPL shows, which is worse than
    showing none.*
    """
    out = []
    for code, player_id in squad:
        for r in by_code.get(code, ()):
            if r["fixture"] in rows:
                row = players.get(player_id)
                out.append({
                    # ⭐⭐ **The player is a `player_summary`, and the week sits beside him** (ADR-227).
                    # ⚠️ The first version of this was a flat dict of `id` + stats — a *second* player
                    # shape, which is the exact mistake `gameweek_result` records making and
                    # `test_player_shape.py` caught here within minutes, as it did there.
                    "player": player_summary(row, {}, {}, {}) if row else None,
                    "minutes": r["minutes"],
                    "goals": r["goals_scored"],
                    "assists": r["assists"],
                    "points": r["total_points"],
                    "bonus": r["bonus"],
                })
    return out


def _squad_that_week(request, gameweek: int, played: bool, players, *, client=None):
    """The ids that were actually in this manager's team **that** gameweek.

    🔴🔴 **The squad a caller holds today is not the squad that played last week**, and joining one to the
    other invents a past. The owner saw *Calafiori* and *Haaland* credited with points in GW6, a week he
    held *Gabriel* and *Calvert-Lewin* — ⚠️⚠️ *and the card totalled them, so the number looked
    authoritative and was fiction.*

    ⭐ For a **played** week only FPL knows, so it is asked — one request per manager per gameweek, and a
    played week never changes, so the answer can be cached for ever (ADR-298's economics).

    ⚠️⚠️ **A failed fetch returns nothing, never the current squad.** ⭐ *A wrong attribution is worse
    than none*, and falling back would restore the exact bug this exists to fix, silently.

    For a week still in play the caller's own squad is right: FPL locks picks at the deadline and
    `my-team` returns that locked side.
    """
    if not played:
        return [i for i in request.player_ids if i in players]
    if not request.manager_id:
        return []
    try:
        from src.api.client import FplApiError, FplClient
        picks = (client or FplClient()).get_entry_picks(request.manager_id, gameweek)
    except (FplApiError, Exception):   # noqa: B014 - every failure degrades the same way
        return []
    return [p["element"] for p in (picks.get("picks") or []) if p.get("element") in players]


def gameweek_scores(request: GameweekScoresRequest, *, store: Storage | None = None,
                    client=None, now=None) -> dict:
    """Every match of a gameweek, with the manager's own players beside each one.

    ⚠️ `now` is injectable because this answer became **clock-dependent** when the live gate moved off a
    stored flag (ADR-354). ⭐ *A test that reads the real clock passes on the day it was written* — this
    repo has watched that happen (`test_xp_board` pinned to "from GW6" went red the week GW6 was played).
    """
    request.validate()
    store, ours = opened(store)
    try:
        teams = list(store.get_teams())
        clubs = {t["id"]: t["short_name"] for t in teams}
        # ⭐ A **sidecar map**, not a field repeated on every match — the same shape `my-team` uses for
        # `kits` (ADR-227). Twenty clubs, each named once, however many matches reference them.
        club_rows = {t["short_name"]: {"name": t["name"], "badge": badge_url(t["code"])}
                     for t in teams}
        all_fixtures = [dict(f) for f in store.get_all_fixtures()]
        gameweek = request.gameweek or _which_gameweek(all_fixtures, now)
        if gameweek is None:
            # ⭐ A season that has not started is a fact, not a failure.
            return {"gameweek": None, "live": False, "yours_known": False,
                "clubs": {}, "matches": []}

        stored = {f["id"]: f for f in all_fixtures if f["event"] == gameweek}

        # ⭐ Only reach upstream when something is actually in flight. A finished week is served entirely
        # from the database, which is the whole point of storing it.
        # ⚠️ By the clock, not by a stored flag — see `_kicked_off`. ⭐ A week whose matches are all over
        # still makes **no** upstream call, which is the economy this gate was for.
        in_flight = any(_playing(f, now) for f in stored.values())
        if in_flight:
            for raw in _live_fixtures(gameweek, client=client):
                if raw.get("id") in stored:
                    stored[raw["id"]] |= {
                        "team_h_score": raw.get("team_h_score"),
                        "team_a_score": raw.get("team_a_score"),
                        "minutes": raw.get("minutes"),
                        "started": raw.get("started"),
                        "finished": raw.get("finished"),
                        # ⭐ The referee's flag, read live and **not stored** (ADR-356). A column would be a
                        # schema migration — the step that has bitten twice — to buy a better degrade in a
                        # case that already degrades to exactly today's behaviour.
                        "finished_provisional": raw.get("finished_provisional"),
                    }

        players = {p["id"]: p for p in store.get_players()}
        # ⭐ "Played" means every match of the week is over — the point at which the caller's current
        # squad stops being the one that earned these points.
        played = bool(stored) and all(f["finished"] for f in stored.values())
        ids = _squad_that_week(request, gameweek, played, players, client=client)
        squad = {(players[i]["code"], i) for i in ids}
        by_code = store.get_gw_history_by_code() if squad else {}

        # ⚠️⚠️ **Scores arrive before the player history does, and an empty `yours` lies about it.**
        # `fixtures` is filled by the refresh; `player_history` by the separate backfill — so for a window
        # after full time the score is known and nobody's week is. ⭐ *"None of your players were in this
        # match" and "we do not know yet" look identical in an empty list and mean opposite things*, which
        # is the shape of mistake ADR-298 and ADR-146 are both about.
        # 🔴 Found by running this against the real database, where GW6 had ten scores and no history.
        # ⚠️ Also false when the week is played and the squad could not be established — ⭐ *an empty
        # `yours` that claims to be known is the lie this whole helper exists to stop.*
        yours_known = bool(squad) and any(
            r["round"] == gameweek for rows in by_code.values() for r in rows
        )

        matches = []
        for f in sorted(stored.values(), key=lambda r: (r["kickoff_time"] or "", r["id"])):
            matches.append({
                "fixture": f["id"],
                "home": clubs.get(f["team_h"]),
                "away": clubs.get(f["team_a"]),
                "home_score": f["team_h_score"],
                "away_score": f["team_a_score"],
                "minutes": f["minutes"],
                "started": _started(f),
                "finished": bool(f["finished"]),
                "kickoff_time": f["kickoff_time"],
                # ⭐ Decided here, not in each client: "Full time" / "63'" / a kick-off time is the same
                # judgement every surface has to make, and ⚠️ *three clients making it separately is three
                # chances to disagree about whether a match is over.*
                "status": _status(f),
                # ⭐ The club's own highlights video when one has been matched to **this** scoreline
                # (ADR-347), null otherwise. ⚠️ *Null is the normal case for a match that has just
                # finished* — the clubs take hours — so a client must draw the card without it.
                "highlights": f["highlights_url"],
                "yours": _yours({f["id"]}, squad, by_code, players),
            })
        # ⭐ `yours_known` is about the gameweek, not one match: history lands for the whole week at once.
        return {"gameweek": gameweek, "live": in_flight, "yours_known": yours_known,
                "clubs": club_rows, "matches": matches}
    finally:
        if ours:
            store.close()
