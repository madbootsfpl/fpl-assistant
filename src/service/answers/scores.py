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


def _yours(rows, squad, by_code, players, benched) -> list:
    """The manager's players who featured in one fixture, with what they did.

    ⚠️ **Points come from `player_history`, never computed here.** FPL settles bonus after full time, and
    ⭐ *a total this app worked out itself would disagree with the one FPL shows, which is worse than
    showing none.*

    ⭐⭐ **The player stays a full `player_summary` here, and that is a compatibility decision, not a
    design one** (ADR-360). Making him an id into `people` would describe each man once — eleven travel
    twice today — but 🔴 **build 45 parses this field as an object** (`json['player'] as Map`), Render
    deploys on push, and the nine would have had a broken Scores screen the moment the server moved,
    before any of them could update. ⚠️⚠️ *An additive change reaches old clients harmlessly; a changed
    field does not*, and the ~2 KB is the price of not breaking a shipped build.

    📌 So `events` and `bonus_race` reference `people` by id and `yours` does not. The inconsistency is
    deliberate and paid for; it can go the next time this field changes shape for another reason.
    """
    out = []
    for code, player_id in squad:
        for r in by_code.get(code, ()):
            if r["fixture"] in rows:
                row = players.get(player_id)
                if row is None:
                    continue
                out.append({
                    "player": player_summary(row, {}, {}, {}),
                    "minutes": r["minutes"],
                    "goals": r["goals_scored"],
                    "assists": r["assists"],
                    "points": r["total_points"],
                    "bonus": r["bonus"],
                    # ⭐⭐ **Did his points count?** (ADR-365) A benched man's do not, unless an automatic
                    # substitution brought him on — which `multiplier` already accounts for.
                    # ⚠️ `None` where no manager id could be asked: *unknown and benched are not the same.*
                    "benched": (player_id in benched) if benched is not None else None,
                })
    return out


#: How many of a match's players the bonus race names. ⭐ Three bonus points are awarded, and the two or
#: three behind them are the ones that can still overtake while the award is provisional (ADR-356).
BONUS_RACE = 5


def _events(rows, by_code, named) -> dict:
    """Goals, assists and cards for one match — **everyone's, not just the manager's** (ADR-360).

    ⚠️⚠️ **Goals and assists are two lists, and FPL links them to nothing.** A scorer is never paired with
    an assister here. Brentford 1-2 Liverpool: Brentford's pair is forced (one goal, one assist) and
    Liverpool's is not — Wirtz and Barcola each set up one of Munoz and Isak and the data cannot say which.
    ⭐⭐ *Pairing two sorted lists is the ADR-351 mistake*, and the first mockup of this card made it.
    """
    out = {"goals": [], "assists": [], "cards": []}
    for r in rows:
        player = by_code.get(r["element_code"])
        if player is None:
            continue
        # ⚠️⚠️ **Named only when he is actually referenced.** The first version added every player with a
        # history row — all twenty-two, then all 667 across a gameweek, for a sidecar of **126 KB**.
        # ⭐ *That is the ADR-227 payload sin committed inside the fix that cites it*, and it was invisible
        # until the bytes were counted.
        if r["goals_scored"]:
            named.add(player["id"])
            out["goals"].append({"player": player["id"], "count": r["goals_scored"]})
        if r["assists"]:
            named.add(player["id"])
            out["assists"].append({"player": player["id"], "count": r["assists"]})
        # ⭐ Red first: a player sent off for a second yellow has both, and the red is the fact.
        if r["red_cards"]:
            named.add(player["id"])
            out["cards"].append({"player": player["id"], "colour": "red"})
        elif r["yellow_cards"]:
            named.add(player["id"])
            out["cards"].append({"player": player["id"], "colour": "yellow"})
    return out


#: Where a match's **fantasy** points stand, which is not where the football stands (ADR-363).
#:
#: ⭐⭐ *A finished match does not mean finished fantasy points.* The owner's framing, and the whole reason
#: this is a field of its own rather than something read off `finished`.
#:
#: Measured on GW6 and GW7 rather than assumed:
#:
#: * `finished_provisional` flips at the **whistle** — 13:37 for Everton–Chelsea, ADR-356.
#: * the **bonus** block fills per match, hours later, while `finished` is still false: 32 hours after
#:   GW7's first kick-off every match had its 3-2-1 and not one was `finished`.
#: * `finished` flips with the **gameweek**: GW6 had `data_checked = true` and ten finished fixtures;
#:   GW7 had neither. ⭐ So it stands in for the lock, and no `bootstrap-static` call is needed for it.
BONUS_LIVE = "live"              # the match is on; BPS moves with it
BONUS_PENDING = "pending"        # full time, and the 3-2-1 has not been awarded
BONUS_PROVISIONAL = "provisional"  # awarded, and still open to a post-match correction
BONUS_FINAL = "final"            # the gameweek is locked


_live_elements_cache: dict[int, tuple[float, dict]] = {}


def _live_elements(gameweek: int, *, client=None, now=time.monotonic) -> dict:
    """`{player id: element}` from FPL's own live gameweek endpoint, cached like the fixtures (ADR-364).

    ⭐⭐ **This is where the week's points live before the backfill stores them.** `event/{gw}/live/`
    carries every player's `total_points` and an `explain` block per fixture — FPL's own attribution,
    the thing ADR-299 added this endpoint for.

    ⚠️ One call for all 659 players, so a fifteen-man squad costs one request, not fifteen.
    ⚠️⚠️ Never fatal: an upstream failure yields nothing and `yours` simply stays empty, which
    `yours_known` already describes honestly.
    """
    hit = _live_elements_cache.get(gameweek)
    if hit and now() - hit[0] < LIVE_CACHE_SECONDS:
        return hit[1]
    try:
        from src.api.client import FplClient
        payload = (client or FplClient()).get_event_live(gameweek)
        found = {e["id"]: e for e in (payload.get("elements") or []) if e.get("id")}
    except Exception:          # noqa: BLE001 - every upstream failure degrades the same way
        return hit[1] if hit else {}
    _live_elements_cache[gameweek] = (now(), found)
    return found


def forget_live_elements() -> None:
    """Drop the live-points cache. ⚠️ For tests — production lets the TTL do it."""
    _live_elements_cache.clear()


def _yours_live(fixture_id, squad_ids, elements, players, named, benched) -> list:
    """The manager's players in one fixture, from FPL's live attribution (ADR-364).

    🔴 **The agreed card had a YOUR PLAYERS block and the week being played had none.** `yours` is built
    from `player_history`, which the backfill does not reach until a gameweek completes (ADR-361) — so
    the block that makes this *"not a livescore app"* was missing on the only week anybody was watching.

    ⭐⭐ **The points are FPL's, not this app's.** `explain` carries a per-stat breakdown per fixture —
    `minutes 90 → 2`, `bonus 3 → 3` — and summing those is reading FPL's arithmetic, not applying the
    scoring rules here. ⚠️⚠️ *A hand-rolled table starts disagreeing the moment the game changes without
    telling us* (ADR-299), which is why there is not one.

    ⭐ Per **fixture**, not per week: a double gameweek has two `explain` blocks, and `total_points` cannot
    say which match earned what.
    """
    out = []
    for pid in squad_ids:
        element = elements.get(pid)
        if element is None or pid not in players:
            continue
        for block in element.get("explain") or ():
            if block.get("fixture") != fixture_id:
                continue
            stats = {row.get("identifier"): row for row in (block.get("stats") or ())}
            named.add(pid)
            out.append({
                "player": player_summary(players[pid], {}, {}, {}),
                "minutes": (stats.get("minutes") or {}).get("value", 0),
                "goals": (stats.get("goals_scored") or {}).get("value", 0),
                "assists": (stats.get("assists") or {}).get("value", 0),
                "points": sum(row.get("points") or 0 for row in (block.get("stats") or ())),
                "bonus": (stats.get("bonus") or {}).get("value", 0),
                "benched": (pid in benched) if benched is not None else None,
            })
    return out


def _bonus_status(f, stats) -> str:
    """Which of the four states this match's bonus is in.

    ⚠️⚠️ **Deliberately independent of the scoreline's state.** A match can read *Full time* for a day
    and a half while its points are still open — that gap is the thing this field exists to show, and
    folding it into `finished` is what hid it.
    """
    if not _started(f):
        return BONUS_PENDING
    # ⭐ The gameweek lock, read from the fixture rather than from `bootstrap-static` — see the note above.
    if f["finished"]:
        return BONUS_FINAL
    if not _over(f):
        return BONUS_LIVE
    awarded = any(
        (block.get("h") or block.get("a"))
        for block in (stats or ())
        if block.get("identifier") == "bonus"
    )
    return BONUS_PROVISIONAL if awarded else BONUS_PENDING


def _by_identifier(stats) -> dict:
    """FPL's `stats` list → `{identifier: {player_id: value}}`, both sides merged.

    ⭐ The fixture payload keys these by player **id**, where `player_history` keys by **code** — the one
    difference between the two sources of the same facts.
    """
    out: dict[str, dict[int, int]] = {}
    for block in stats or ():
        name = block.get("identifier")
        if not name:
            continue
        merged = out.setdefault(name, {})
        for side in ("h", "a"):
            for row in block.get(side) or ():
                merged[row.get("element")] = row.get("value") or 0
    return out


def _events_from_stats(stats, players, named) -> dict:
    """The same card, built from the **live fixture payload** instead of stored history (ADR-361).

    🔴🔴 **The current gameweek had no history at all.** `backfill_due` fetches a round only once every
    one of its fixtures is complete — one request per player makes it deliberately rare (ADR-211 2d) — so
    GW7's Saturday matches carried no goals, no cards and no bonus race until the **Monday night match**
    settled the week. ⚠️⚠️ *The week people care most about was the one week the card was blank.*

    ⭐⭐ And the data was already in hand: `/fixtures/` carries a `stats` block per match, and this module
    already fetches it. The fix is to read what was being thrown away.
    """
    by_id = _by_identifier(stats)
    out = {"goals": [], "assists": [], "cards": []}
    for key, bucket in (("goals_scored", "goals"), ("assists", "assists")):
        for pid, value in (by_id.get(key) or {}).items():
            if value and pid in players:
                named.add(pid)
                out[bucket].append({"player": pid, "count": value})
    reds = by_id.get("red_cards") or {}
    for pid, value in reds.items():
        if value and pid in players:
            named.add(pid)
            out["cards"].append({"player": pid, "colour": "red"})
    for pid, value in (by_id.get("yellow_cards") or {}).items():
        # ⭐ Red wins: a second yellow is recorded as both, and the dismissal is the fact.
        if value and pid in players and not reds.get(pid):
            named.add(pid)
            out["cards"].append({"player": pid, "colour": "yellow"})
    return out


def _bonus_race_from_stats(stats, players, named) -> list:
    """The bonus race from the live payload — same shape, same ordering by BPS."""
    by_id = _by_identifier(stats)
    bps = by_id.get("bps") or {}
    bonus = by_id.get("bonus") or {}
    ranked = sorted(bps.items(), key=lambda kv: kv[1], reverse=True)[:BONUS_RACE]
    out = []
    for pid, value in ranked:
        if pid not in players:
            continue
        named.add(pid)
        out.append({"player": pid, "bonus": bonus.get(pid, 0), "bps": value})
    return out


def _bonus_race(rows, by_code, named) -> list:
    """The top `BONUS_RACE` by BPS, with the bonus each has been awarded so far.

    ⭐⭐ **The one thing no livescore app carries.** BPS decides the 3/2/1, and ADR-356 measured the award
    staying provisional for ninety-six minutes after the whistle — ⚠️ *which is exactly the window in which
    knowing who is winning it matters, and exactly when it can still change.*
    """
    ranked = sorted(rows, key=lambda r: (r["bps"] or 0), reverse=True)[:BONUS_RACE]
    out = []
    for r in ranked:
        player = by_code.get(r["element_code"])
        if player is None:
            continue
        named.add(player["id"])
        out.append({"player": player["id"], "bonus": r["bonus"] or 0, "bps": r["bps"] or 0})
    return out


def _lining_up(fixture, squad_ids, players, benched) -> list:
    """Which of the manager's players are in a fixture that has **not been played** (ADR-360).

    ⭐ `yours` is built from `player_history`, which does not exist before a match — so a forward week
    would show every card empty. ⚠️ Team membership answers it instead: this is *who is involved*, never
    who will start, and it carries no points because there are none.
    """
    out = []
    for pid in squad_ids:
        row = players.get(pid)
        if row is None:
            continue
        if row["team_id"] in (fixture["team_h"], fixture["team_a"]):
            out.append({"player": player_summary(row, {}, {}, {}), "minutes": None, "goals": None,
                        "assists": None, "points": None, "bonus": None,
                        "benched": (pid in benched) if benched is not None else None})
    return out


def _match_events(f, per_fixture, live_rows, by_code, players, named) -> dict:
    """Events for one match, from history where it exists and from the live payload where it does not."""
    if not _started(f):
        return {"goals": [], "assists": [], "cards": []}
    rows = per_fixture.get(f["id"])
    if rows:
        return _events(rows, by_code, named)
    raw = live_rows.get(f["id"])
    return (_events_from_stats(raw.get("stats"), players, named) if raw
            else {"goals": [], "assists": [], "cards": []})


def _match_yours(f, per_fixture, squad, by_code, elements, ids, players, named, benched) -> list:
    """Your players in one match, from whichever source can honestly describe them."""
    if not _started(f):
        return _lining_up(f, ids, players, benched)
    if per_fixture.get(f["id"]):
        return _yours({f["id"]}, squad, by_code, players, benched)
    return _yours_live(f["id"], ids, elements, players, named, benched)


def _match_bonus(f, per_fixture, live_rows, by_code, players, named) -> list:
    """The bonus race for one match, from whichever source has it."""
    if not _started(f):
        return []
    rows = per_fixture.get(f["id"])
    if rows:
        return _bonus_race(rows, by_code, named)
    raw = live_rows.get(f["id"])
    return _bonus_race_from_stats(raw.get("stats"), players, named) if raw else []


def _squad_that_week(request, gameweek: int, played: bool, players, *, client=None) -> tuple:
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
    if request.manager_id:
        # ⭐⭐ **Picks are public once the deadline passes**, not only once the week is over — so a week in
        # play has them too, and with them the one thing the caller's flat list cannot carry: who was on
        # the **bench** (ADR-365).
        try:
            from src.api.client import FplApiError, FplClient
            picks = (client or FplClient()).get_entry_picks(request.manager_id, gameweek)
        except (FplApiError, Exception):   # noqa: B014 - every failure degrades the same way
            picks = None
        if picks:
            rows = [p for p in (picks.get("picks") or []) if p.get("element") in players]
            # ⭐⭐ **`multiplier`, never `position`** — and the reason is **Bench Boost**, not automatic
            # substitutions. 🔴 *The first version of this comment said otherwise and a mutation proved it
            # wrong*: on an autosub FPL **swaps the positions**, so the man brought on reads
            # `position 5, multiplier 1` and the two fields agree. They diverge under the chip, where all
            # fifteen play and the bench keeps `position 12-15` with `multiplier 1`.
            # ⚠️⚠️ *Reading the position there would bench four players whose points counted.*
            return ([p["element"] for p in rows],
                    {p["element"] for p in rows if not p.get("multiplier")})
    if played:
        # ⚠️⚠️ **A played week never falls back** (ADR-350). ⭐ *A wrong attribution is worse than none*,
        # and the current squad is a different fifteen.
        return [], None
    # ⚠️ `None`, not an empty set: with no picks to read, who was benched is **unknown** — ⭐ *and an
    # empty set would quietly tell every card that nobody was, which is a claim and not an absence.*
    return [i for i in request.player_ids if i in players], None


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
                    "clubs": {}, "people": {}, "squad": [], "matches": []}

        stored = {f["id"]: f for f in all_fixtures if f["event"] == gameweek}

        # ⭐ Only reach upstream when something is actually in flight. A finished week is served entirely
        # from the database, which is the whole point of storing it.
        # ⚠️ By the clock, not by a stored flag — see `_kicked_off`. ⭐ A week whose matches are all over
        # still makes **no** upstream call, which is the economy this gate was for.
        in_flight = any(_playing(f, now) for f in stored.values())
        live_rows: dict[int, dict] = {}
        if in_flight:
            for raw in _live_fixtures(gameweek, client=client):
                if raw.get("id") in stored:
                    live_rows[raw["id"]] = raw
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
        by_code_player = {p["code"]: p for p in players.values()}

        # ⭐⭐ **One local query for the whole week's events** (ADR-360). `player_history` already holds
        # goals, assists, cards, saves, bonus and BPS keyed by fixture, so a card for GW1 costs nothing
        # upstream and needs no column that is not already there.
        per_fixture: dict[int, list] = {}
        for row in store.history_for_fixtures(stored):
            per_fixture.setdefault(row["fixture"], []).append(row)

        # 🔴🔴 **A played fixture with no stored history is the CURRENT gameweek** (ADR-361): the backfill
        # waits for every fixture of a round to finish before spending one request per player (ADR-211 2d),
        # so until the Monday night match settles the week, Saturday's cards carry nothing at all.
        # ⚠️⚠️ *The week people care most about was the one week the card was blank.*
        #
        # ⭐ The fixture payload already carries a `stats` block per match and this module already fetches
        # it when something is in flight. Fetch it here too when a played match has no history — a week
        # that HAS its history (every past gameweek) asks for nothing.
        starved = [f for f in stored.values() if _started(f) and not per_fixture.get(f["id"])]
        if starved and not live_rows:
            for raw in _live_fixtures(gameweek, client=client):
                if raw.get("id") in stored:
                    live_rows[raw["id"]] = raw
        # ⭐ And the week's points, for the same reason and on the same condition (ADR-364). A week whose
        # history is stored never asks.
        elements = _live_elements(gameweek, client=client) if starved else {}

        # ⭐ Every player named anywhere in the answer, once — the sidecar `clubs` already uses (ADR-227).
        # ⚠️ *A scorer, an assister and a bonus-race entry are often the same man*, and repeating his
        # summary three times per match is the payload mistake that ADR made a rule about.
        named: set[int] = set()
        # ⭐ "Played" means every match of the week is over — the point at which the caller's current
        # squad stops being the one that earned these points.
        played = bool(stored) and all(f["finished"] for f in stored.values())
        ids, benched = _squad_that_week(request, gameweek, played, players, client=client)
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
        # ⚠️⚠️ **Either source counts** (ADR-364). This asked only the stored history, so the week being
        # played said *"your players not in yet"* on a card that was, by then, showing them — ⭐ *a
        # caption contradicting the thing underneath it is worse than the gap it was written for.*
        yours_known = bool(squad) and (
            any(r["round"] == gameweek for rows in by_code.values() for r in rows)
            or any(i in elements for i in ids)
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
                # ⭐ Everyone's events, so the card can say what happened rather than only what *you* got.
                # ⚠️ An unplayed fixture has rows (ADR-125) but no football: the match gates them, not the
                # rows, so a future week reports nothing rather than eleven nil returns.
                # ⭐ Stored history first — it is local, complete and never moves. The live payload is
                # the fallback for the week the backfill has not reached.
                "events": _match_events(f, per_fixture, live_rows, by_code_player, players, named),
                "bonus_race": _match_bonus(f, per_fixture, live_rows, by_code_player, players, named),
                # ⭐⭐ Where the **points** stand, which is not where the football stands (ADR-363).
                "bonus_status": _bonus_status(f, (live_rows.get(f["id"]) or {}).get("stats")),
                # ⭐ Played: what your players did. Not yet played: which of them are involved (ADR-360).
                # ⭐ Stored history, then FPL's live attribution, then who is merely involved — each a
                # weaker claim than the one before, and ⚠️ *never a points total this app worked out.*
                "yours": _match_yours(f, per_fixture, squad, by_code, elements, ids, players, named,
                                      benched),
            })
        # ⭐ `yours_known` is about the gameweek, not one match: history lands for the whole week at once.
        return {"gameweek": gameweek, "live": in_flight, "yours_known": yours_known,
                "clubs": club_rows,
                # ⭐⭐ **Whose team it was THAT week** (ADR-362), so the card can mark a scorer as yours
                # before `player_history` lands and `yours` can be built. 🔴 Without it GW7 showed no
                # dots at all: the dots were derived from `yours`, which waits for the backfill.
                # ⚠️⚠️ Not the caller's squad echoed back — for a played week this is FPL's own answer
                # (ADR-350), because *the squad held today did not play last Saturday.*
                "squad": sorted(ids),
                # ⚠️ Keys are strings because JSON has no integer keys — the client looks up by `str(id)`.
                "people": {str(i): player_summary(players[i], {}, {}, {})
                           for i in sorted(named) if i in players},
                "matches": matches}
    finally:
        if ours:
            store.close()
