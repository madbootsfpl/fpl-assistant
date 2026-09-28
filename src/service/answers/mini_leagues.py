"""The mini-league answers

⚠️ **Named `mini_leagues`, not `league`, because `league()` is one of the handlers it holds** (ADR-324).
A submodule whose name a re-exported function also uses gets shadowed in the package namespace — `answers.league`
would be the function, and `answers.league.something` an AttributeError. ⭐ *A name that resolves to two
different objects depending on import order is a trap, not a convenience.*

The league answers — a table, a manager's week, and two managers side by side.

`leagues` · `league` · `gameweek_result` · `head_to_head`, with the pick-fetching and award helpers they
share and nothing else uses.
"""


from src.analytics import (
    player_summary,
)
from src.fpl_rules import (
    rank_movement,
)
from src.kits import shirt_url

# ⭐⭐ **Imported as a module, not as names** (ADR-324). `common`'s helpers are shared by more than one
# answer family, and a test that fakes one — `_chip_status` is faked in three suites — must be able to
# reach every consumer from one place. ⚠️ *Binding a shared function into each module's globals gives it
# as many patch points as there are importers*, which is how a fake silently applies to one caller and
# not the next.
from src.service.answers import common
from src.service.inputs import load, opened
from src.service.requests import (
    GameweekResultRequest,
    HeadToHeadRequest,
    LeagueRequest,
    LeaguesRequest,
)
from src.storage import Storage


def leagues(request: LeaguesRequest) -> dict:
    """The classic leagues a manager is in (ADR-141/267).

    ⭐⭐ **Nobody knows their league id.** It appears in a URL you have to go and find, which made the
    first cut of the web page unusable for the thing it was built for. The manager id is the handle people
    actually have, and the entry payload already carries every league behind it.

    ⚠️ **Private leagues lead.** FPL mixes the mini-league you joined with your friends in among automatic
    ones — your club, your region, "Gameweek 1", Overall — and by size the automatic ones always win.
    ⭐ *Sorting by size would bury the only leagues anyone means.*
    """
    request.validate()
    from src.analytics.league import my_leagues
    from src.api.client import FplApiError, FplClient

    try:
        entry = FplClient().get_entry(request.manager_id)
    except FplApiError as exc:
        # ⭐ The client's own words: it distinguishes a bad id from an unreachable API, and a caller
        # cannot tell those apart from a 400 alone.
        raise ValueError(str(exc)) from exc

    return {
        "manager_id": request.manager_id,
        "name": entry.get("player_first_name", "") + " " + entry.get("player_last_name", ""),
        "leagues": my_leagues(entry),
    }


def _picks_for(entries, gameweek, client):
    """Each manager's picks for a finished gameweek, best-effort.

    ⚠️ **A manager whose fetch fails is simply absent.** ⭐ *A partial league still gives a usable split,
    and an exception here would throw away forty-nine good fetches because of one bad id* — so the caller
    reports how many it is standing on rather than pretending it read them all.
    """
    from src.api.client import FplApiError

    out = {}
    for entry in entries:
        try:
            out[entry] = client.get_entry_picks(entry, gameweek)
        except FplApiError:
            continue
    return out


def _manager_rows(picks: dict, rows: list) -> list[dict]:
    """One row per manager read, from the picks payload the captain split already fetched.

    ⚠️ **Only the managers whose fetch succeeded**, like the captain split — ⭐ *a partial read must never
    present itself as the whole league* (ADR-215), and `captains_from` already says how many.
    """
    named = {r["entry"]: r for r in rows if r.get("entry")}
    out = []
    for entry, payload in picks.items():
        history = payload.get("entry_history") or {}
        row = named.get(entry) or {}
        out.append({
            "entry": entry,
            "manager": row.get("manager"),
            "team": row.get("team"),
            "points": history.get("points"),
            # ⭐ The one number a league table cannot show you: where you are **in the world**, not just
            # among the eleven people you know.
            "overall_rank": history.get("overall_rank"),
            "transfers": history.get("event_transfers"),
            # ⚠️ Positive in FPL's payload and positive here. ⭐ *A cost stored as a negative number gets
            # added somewhere by accident exactly once.*
            "hit": history.get("event_transfers_cost"),
            "bench_points": history.get("points_on_bench"),
            # `None` when no chip was played — ⚠️ not `""`, which a client would render as a blank chip.
            "chip": payload.get("active_chip"),
        })
    return sorted(out, key=lambda m: -(m["points"] or 0))


def _awards(picks: dict, rows: list) -> list[dict]:
    """The two the owner picked: who won the gameweek, and who wasted the most on their bench.

    ⚠️ **Structured, not worded.** The server sends *who* and *how much*; the client supplies the title
    and the emoji — ⭐ the same split as a player card's badges (ADR-286), and for the same reason: *a
    client that has to take a sentence apart to lay it out will one day take it apart differently.*
    """
    managers = _manager_rows(picks, rows)
    if not managers:
        return []

    def best(field: str) -> dict | None:
        # ⚠️ `max` is stable, so a tie resolves to the highest-placed manager in the table rather than to
        # whichever order a dict happened to iterate in — ⭐ *an award that changes hands on a refresh is
        # an award nobody believes.*
        ranked = [m for m in managers if m.get(field) is not None]
        return max(ranked, key=lambda m: m[field]) if ranked else None

    out = []
    if winner := best("points"):
        out.append({"kind": "gameweek_winner", **_award_of(winner, "points")})
    # ⭐ Omitted when nobody left anything behind. *An award for wasting nothing is not an award*, and a
    # row reading "0 pts left on the bench" invites the reader to work out whether that is good.
    if (bench := best("bench_points")) and bench["bench_points"]:
        out.append({"kind": "worst_bench", **_award_of(bench, "bench_points")})
    return out


def _award_of(manager: dict, field: str) -> dict:
    return {
        "entry": manager["entry"],
        "manager": manager["manager"],
        "team": manager["team"],
        "value": manager[field],
    }


def league(request: LeagueRequest, *, store: Storage | None = None) -> dict:
    """One classic league — the table, and optionally what everybody captained (ADR-267).

    ⚠️⚠️ **The captain split is opt-in and capped**, because it costs one FPL request per manager where
    the table costs one in total. ⭐ *A screen that quietly spends fifty requests to draw a second panel is
    a screen that will be blamed for being slow.*

    ⚠️ **Only a finished gameweek.** Picks are public **after** a deadline; asking for the one in flight
    returns 404 for everybody, and a split built from nothing would read as *"nobody captained anyone"*.
    """
    request.validate()
    from src.analytics.league import (
        captain_split,
        effective_ownership,
        last_completed_gameweek,
        league_name,
        standings_rows,
    )
    from src.api.client import FplApiError, FplClient

    client = FplClient()
    try:
        payload = client.get_league_standings(request.league_id)
    except FplApiError as exc:
        raise ValueError(str(exc)) from exc

    rows = standings_rows(payload)
    store, ours = opened(store)
    try:
        players = store.get_players()
        gameweek = request.gameweek or last_completed_gameweek(store.get_upcoming_fixtures())
        captains, checked, picks = [], 0, {}
        if request.with_captains and gameweek:
            entries = [r["entry"] for r in rows[:request.limit] if r["entry"]]
            picks = _picks_for(entries, gameweek, client)
            checked = len(picks)
            by_id = {p["id"]: p for p in players}
            eo = effective_ownership(picks)
            captains = [
                {
                    "player": player_summary(by_id[pid], {}, {}, {}) if pid in by_id else None,
                    "count": count,
                    # ⭐ The share, not just the count — *"9 of 12"* is a different fact from *"9"*, and
                    # the reader is deciding whether to differ from a crowd.
                    "share": round(100 * count / checked, 1) if checked else 0.0,
                    "effective_ownership": round(eo.get(pid, 0.0), 1),
                }
                for pid, count in captain_split(picks)
                if pid in by_id
            ]
    finally:
        if ours:
            store.close()

    return {
        "league_id": request.league_id,
        "name": league_name(payload),
        "gameweek": gameweek,
        "rows": rows,
        # ⚠️ Stated, so a partial read never presents itself as the whole league (ADR-215's rule).
        "captains_from": checked,
        "captains": captains,
        # ⭐⭐ **Free riders on a fetch already being made** (ADR-287). `with_captains` spends one request
        # per manager, and the payload it gets back carries `active_chip` and an `entry_history` with the
        # overall rank, the transfer count, the hit and the bench points. ⚠️ *Four sub-tabs were parked as
        # unbuilt when three of them were already paid for* — the data was arriving and being discarded.
        "managers": _manager_rows(picks, rows),
        "awards": _awards(picks, rows),
    }


def gameweek_result(request: GameweekResultRequest, *, store: Storage | None = None) -> dict:
    """A gameweek that has been **played** — the squad as it was, and what each player actually scored.

    ⭐⭐ **Almost all of this is already on the server** (ADR-298). The per-player week — points, goals,
    assists, bonus, saves, minutes, cards — is in `player_history`, kept current by the pipeline. The one
    thing FPL alone knows is *whose team he was in that week*, which costs one request.

    ⚠️⚠️ **A played gameweek never changes**, so a caller may cache this forever. That is the whole
    economics of the feature: one request per manager per gameweek, ever.

    ⚠️ Degrades rather than raises, like `my_team` — a gameweek FPL has not published yet returns
    `played: false` and an empty squad, because ⭐ *a screen that can be swiped into before the data
    exists must have something true to draw.*
    """
    from src.api.client import FplApiError, FplClient

    request.validate()
    client = FplClient()
    try:
        payload = client.get_entry_picks(request.manager_id, request.gameweek)
    except FplApiError:
        # ⭐ Not an error: swiping to a gameweek that has not happened is a normal gesture.
        return {"gameweek": request.gameweek, "played": False, "squad": [], "kits": {}, "summary": {}}

    store, ours = opened(store)
    try:
        players = {p["id"]: p for p in store.get_players()}
        by_code = store.get_gw_history_by_code()
        # ⚠️ Keyed by the **round**, not the fixture: a double gameweek gives a player two rows, and the
        # week's story is their sum — ⭐ *showing one of two matches is worse than showing neither,
        # because it looks complete.*
        week = {}
        for code, rows in by_code.items():
            played = [r for r in rows if r["round"] == request.gameweek]
            if played:
                week[code] = played

        history = payload.get("entry_history") or {}
        subs = {s.get("element_out"): s.get("element_in")
                for s in (payload.get("automatic_subs") or [])}

        # ⭐⭐ **The player is a `player_summary`, and the week sits beside him** (ADR-227). The first
        # version of this invented a flat dict with `web_name` and `points` on one level — a *second*
        # player shape, which `test_player_shape.py` refused within minutes of it being written.
        # ⚠️ *A past week's facts are not properties of a player; they are properties of a player in a
        # week*, and flattening them makes every other endpoint's shape a little less true.
        # ⭐⭐⭐ **FPL's own points attribution, fetched once for the whole gameweek** (ADR-299). The
        # owner asked for the breakdown his competitor shows — *minutes 80' → 2, goals 1 → 4, yellow 1 →
        # -1* — and 🔴 **the obvious implementation is the wrong one**: a scoring table is twenty lines and
        # is already wrong, because FPL added `defensive_contribution` this season and it is in real rows
        # now. ⚠️ *A breakdown that disagrees with the total printed above it is worse than no breakdown.*
        #
        # ⚠️⚠️ **Never fatal.** One request per gameweek, and if it fails the page still draws everything
        # it drew before — ⭐ *a detail that did not load must not take the screen that was working with
        # it.*
        # ⭐ Club ids → short names, for the scoreline line. ⚠️ Missing ids stay **null, never a guess**
        # — the rule `_recent_rows` already follows: *an away trip to "???" is worse than to nothing.*
        clubs = {tm["id"]: tm["short_name"] for tm in store.get_teams()}

        explain = {}
        try:
            live = client.get_event_live(request.gameweek)
        except (FplApiError, KeyError, TypeError, AttributeError):
            # ⚠️ **`AttributeError` too, and it is not defensive padding.** Three test doubles in this
            # repo implement only the calls their subject used to make, and a client injected by any
            # future caller may do the same — ⭐ *an optional decoration that hard-requires a method turns
            # every partial client into a crash*, which is the opposite of what this `try` is for.
            live = None
        for element in ((live or {}).get("elements") or []):
            lines = [
                {"stat": stat.get("identifier"), "value": stat.get("value"),
                 "points": stat.get("points")}
                for fixture in (element.get("explain") or [])
                for stat in (fixture.get("stats") or [])
                # ⚠️ Zero-point lines dropped: FPL emits `minutes 0 → 0` for a man who never came on, and
                # ⭐ *a breakdown listing what did not happen is longer and says less.*
                if stat.get("points")
            ]
            if lines:
                explain[element.get("id")] = lines

        squad = []
        def total(rows, key):
            return sum((r[key] or 0) for r in rows)

        # ⚠️ **`sqlite3.Row` indexes by name but has no `.get`**, and a psycopg row is a dict — so one
        # accessor for both, tolerant of a column an older database has not migrated yet. ⭐ *A detail
        # line that throws takes down the whole played week it was decorating.*
        def cell(row, key):
            try:
                return row[key]
            except (KeyError, IndexError):
                return None
        for pick in payload.get("picks") or []:
            pid = pick.get("element")
            player = players.get(pid)
            if player is None:
                continue
            rows = week.get(player["code"], [])
            squad.append({
                # ⚠️ Empty projection maps: a played week has results, not forecasts — the same call the
                # league captain split makes.
                "player": player_summary(player, {}, {}, {}),
                "result": {
                    # ⚠️ FPL's own total, **not** ours: it already includes bonus, and recomputing a
                    # settled fact is offering a second opinion on it.
                    "points": total(rows, "total_points"),
                    "minutes": total(rows, "minutes"),
                    "goals": total(rows, "goals_scored"),
                    "assists": total(rows, "assists"),
                    "bonus": total(rows, "bonus"),
                    "saves": total(rows, "saves"),
                    "clean_sheet": any(r["clean_sheets"] for r in rows),
                    "yellow_cards": total(rows, "yellow_cards"),
                    "red_cards": total(rows, "red_cards"),
                    # ⚠️ Distinguishes *"zero points"* from *"no match"* — ⭐ a blank gameweek and a bad
                    # performance are different weeks and must not draw the same.
                    "played": bool(rows),
                    # ⭐ **How the points were earned, in FPL's words** (ADR-299). Empty for a blank week,
                    # which the client draws as "did not play" rather than as a table of zeroes.
                    "breakdown": explain.get(pid, []),
                    # ⭐ The scoreline, already stored — *"BOU 0-1 LIV" is the context a bare total lacks.*
                    # ⚠️ A list because a double gameweek is two matches, and showing one of two is worse
                    # than showing neither.
                    "matches": [
                        {"opponent": clubs.get(cell(r, "opponent_team")),
                         "home": bool(cell(r, "was_home")),
                         "scored": cell(r, "team_h_score") if cell(r, "was_home")
                                   else cell(r, "team_a_score"),
                         "conceded": cell(r, "team_a_score") if cell(r, "was_home")
                                     else cell(r, "team_h_score")}
                        for r in rows
                    ],
                },
                "pick": {
                    "multiplier": pick.get("multiplier"),
                    "is_captain": bool(pick.get("is_captain")),
                    "is_vice_captain": bool(pick.get("is_vice_captain")),
                    # ⭐ The bench as it was **set**; `came_on` is what the game then did.
                    "benched": (pick.get("position") or 0) > 11,
                    "came_on": pid in set(subs.values()),
                    "went_off": pid in subs,
                },
            })

        # ⚠️⚠️ **The kits of the clubs you owned THEN, not the ones you own now.** The past week is drawn
        # on the pitch (feedback on ADR-298's first build) and the live `my-team` kit map covers only the
        # current squad's clubs — ⭐ *a player you have since sold would be shirtless in the week he
        # scored*, which is exactly the week you swiped back to look at.
        past_clubs = {p["player"]["team"] for p in squad if p["player"].get("team")}
        teams = store.get_teams()
        code_by_club = {tm["short_name"]: tm["code"] for tm in teams}
        kits = {
            club: {"outfield": shirt_url(code_by_club.get(club)),
                   "gk": shirt_url(code_by_club.get(club), "GK")}
            for club in past_clubs
        }

        return {
            "gameweek": request.gameweek,
            "played": True,
            "squad": squad,
            "kits": kits,
            "summary": {
                "points": history.get("points"),
                "overall_rank": history.get("overall_rank"),
                "rank": history.get("rank"),
                "transfers": history.get("event_transfers"),
                "hit": history.get("event_transfers_cost"),
                "bench_points": history.get("points_on_bench"),
                # ⭐⭐ **Places climbed (+) or dropped (−)**, computed here and not in the client.
                # ⚠️⚠️ *A rank of 167,946 is better than 292,349, so a falling number is a rising
                # position* — doing that arithmetic on each surface is repeating the trap on each surface.
                # ⚠️ None for GW1, and None when the lookup failed: *"we could not check" is not "no
                # movement".*
                "overall_rank_moved": rank_movement(
                    (common._entry_history(request.manager_id).get("current") or []), request.gameweek),
                "chip": payload.get("active_chip"),
            },
        }
    finally:
        if ours:
            store.close()


def head_to_head(request: HeadToHeadRequest, *, store: Storage | None = None) -> dict:
    """You against one rival, decomposed (ADR-161/267).

    ⭐⭐ **The shared players are reported and then set aside.** They are usually the large majority of
    both totals and the part you can do nothing about — ⚠️ *printing the shared total is what makes the
    small gap believable rather than looking like a rounding error on two big numbers.*

    ⭐ **It leads with the differentials, not the totals**, because *a reader told "52.1 vs 49.8" learns
    far less than one told "three players separate you, and their captain is worth 4.2 more than yours."*
    """
    request.validate()
    from src.analytics.h2h import catch_up_note, h2h_gap
    from src.analytics.league import last_completed_gameweek
    from src.api.client import FplApiError, FplClient

    store, ours = opened(store)
    try:
        players = store.get_players()
        data = load([], request.horizon, store)
        # ⚠️⚠️ **The last FINISHED gameweek, and the same rule the league table uses.** A rival's picks
        # are public only after a deadline, so the gameweek in flight cannot be read for anybody. ⭐ *Two
        # places deciding separately where "now" is would eventually disagree*, which is exactly why
        # `last_completed_gameweek` is derived from the fixtures cut rather than invented again here.
        gameweek = last_completed_gameweek(store.get_upcoming_fixtures())
        if gameweek is None:
            raise ValueError("no gameweek has finished yet — a head-to-head needs both squads to be public")
        client = FplClient()
        try:
            mine = client.get_entry_picks(request.manager_id, gameweek)
            theirs = client.get_entry_picks(request.rival_id, gameweek)
        except FplApiError as exc:
            raise ValueError(str(exc)) from exc
        gap = h2h_gap(mine, theirs, data.xp_by_id, players)
    finally:
        if ours:
            store.close()

    by_id = {pl["id"]: pl for pl in players}

    def edges(rows):
        """The engine's differential rows, re-dressed in **the one player shape** (ADR-227).

        ⚠️⚠️ **Found by the shape sweep, and it was a real defect, not a formality.** The engine's row
        carries `{id, web_name, team, position, multiplier, xp}` — no `status` — so ⭐ *a differential who
        is doubtful could not be flagged as one*, which is precisely ADR-226's bug: **a doubt hidden is a
        doubt priced at certainty.** The differentials are the players the whole screen is about, and they
        were the ones it could not warn you on.

        ⚠️ The engine is left alone: this is the transport's job, and the Streamlit page reads the same
        function. ⭐ *A shape the API owes its clients is not a reason to change what the engine computes.*
        """
        out = []
        for row in rows:
            raw = by_id.get(row["id"])
            if raw is None:
                continue
            out.append({
                "player": player_summary(raw, data.xp_by_id, {}, {}),
                # ⭐ 2 means he is their captain. Kept beside the player rather than folded into `xp`,
                # because *"his captain"* and *"a good player"* are different reasons to be behind.
                "multiplier": row["multiplier"],
                # ⚠️ Already multiplied — what this differential is actually worth to that side.
                "xp": row["xp"],
            })
        return out

    return {
        "gameweek": gameweek,
        **gap,
        "my_edge": edges(gap["my_edge"]),
        "their_edge": edges(gap["their_edge"]),
        # ⭐ One sentence saying where this actually sits, built from the same numbers — so the headline
        # and the rows can never disagree. ⚠️ Built from the **engine's** rows, before re-dressing, so the
        # sentence and the list cannot come from two different sets.
        "note": catch_up_note(gap),
    }
