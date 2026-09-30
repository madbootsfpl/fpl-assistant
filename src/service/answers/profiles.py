"""The player and club profiles

⚠️ **Named `profiles`, not `player`, for the reason `mini_leagues` is not `league`** (ADR-324): `player()` is
a handler here, and it would shadow the module.

The player answers — one player, a board of them, and the two DNA lenses.

`player` · `players` · `compare` · `player_dna` · `team_dna`.
"""


from src.analytics import (
    is_unavailable,
    player_summary,
    team_dna_all,
    team_insights,
    team_schedule,
)
from src.analytics.compare import compare_rows, stat_rows
from src.analytics.gw_form import team_form
from src.analytics.last_season import last_season_name, last_season_rows
from src.analytics.player_dna import player_dna as analytics_player_dna
from src.analytics.player_dna import player_insights
from src.analytics.team_dna import key_players_this_or_last
from src.kits import photo_url
from src.service.inputs import load, opened
from src.service.requests import (
    CompareRequest,
    PlayerDnaRequest,
    PlayerRequest,
    PlayersRequest,
    TeamDnaRequest,
)
from src.storage import Storage


def _badges(row) -> list[dict]:
    """The display lenses a player card carries — ownership tier and set-piece duty.

    ⚠️ **Glyph and word kept apart**, not the `"🟦 template"` string the tables use. ⭐ *A client that has
    to split a string to lay it out will one day split it differently* — and the phone draws the two at
    different sizes.

    ⭐ Built from `crowd`'s **public** helpers, so the duty rules and the ownership boundaries have one
    definition. ⚠️ *A second copy of "who takes the corners" is a second answer to it.*

    Never xP. These are lenses over facts already inside the projection (ADR-081): a penalty taker's
    penalties are in his points before any badge says so.
    """
    from src.analytics.crowd import ownership_tier, set_piece_flags

    def split(flag: str) -> dict:
        glyph, _, label = flag.partition(" ")
        return {"glyph": glyph, "label": label}

    tier = ownership_tier(row)
    return [*([split(tier)] if tier else []), *(split(f) for f in set_piece_flags(row))]


def _recent_rows(rows, club_by_id) -> list[dict]:
    """The last few appearances — points, minutes, **and who it was against** (ADR-242).

    ⭐⭐ **"Last 5 should maybe indicate who they played"** (tester feedback item 5), and the data was
    already in the row: `player_history` has stored `opponent_team` and `was_home` since ADR-201. A run of
    bare numbers cannot distinguish a quiet week from a hard one — ⚠️ *two blanks against City and Arsenal
    say something completely different from two blanks against the bottom two, and the column that made
    them different was being dropped on the way out.*

    ⚠️ `opponent` is **null, never a guess**, when the club id is unknown — an away trip to "???" is worse
    than an away trip to nothing.
    """
    out = []
    for r in rows:
        row = dict(r)
        out.append({
            "gameweek": row.get("round"),
            "points": row.get("total_points"),
            "minutes": row.get("minutes"),
            "opponent": club_by_id.get(row.get("opponent_team")),
            "home": bool(row.get("was_home")),
        })
    return out


def players(request: PlayersRequest, *, store: Storage | None = None) -> dict:
    """Every available player, ranked by xP over the horizon (ADR-230).

    ⚠️ **§4.1 prefers a client that reads the published board straight from Supabase**, which is what
    ADR-213 publishes it for — and spike 018 proved it (667 players, 162 KB, 511 ms). This endpoint exists
    because **that path is not testable today**: staging predates the board, and production credentials are
    not something to hand a browse screen in order to try it. ⭐ *Shipping a path nobody has run is how
    this session's bugs were made.* Revisit when the app carries Supabase config for a real device.

    ⭐ **Unavailable players are excluded, not flagged.** A browse list is for finding someone to buy; a
    player who cannot play is not a candidate, and leaving him in makes the reader do the filtering the
    app exists to do. ⚠️ *Doubtful* players stay — a doubt is a probability, not a verdict (ADR-206).
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load([], request.horizon, store)
    finally:
        if ours:
            store.close()

    by_id = {p["id"]: p for p in data.players}

    # ⭐⭐ **Bound over `data.players` — every player, not the rows being returned** (ADR-215). A percentile
    # taken over the list on screen manufactures a top 5% *inside every filter*, so filtering to one club
    # would find a riser at that club every week of the season. ⚠️ *The population is a decision, and it is
    # made once, here.*
    from src.analytics import price_detector
    predict = price_detector(data.players)

    rows = []
    for r in data.ranked:
        if r["id"] not in by_id or is_unavailable(by_id[r["id"]]):
            continue
        rows.append(player_summary(by_id[r["id"]], data.xp_by_id,
                                   {r["id"]: r["by_gameweek"] for r in data.ranked},
                                   {r["id"]: r["minutes_weight"] for r in data.ranked}))
    shown = rows[:request.limit]
    return {
        "horizon": request.horizon,
        "gameweeks": data.ranked[0]["gameweeks"] if data.ranked else [],
        # ⭐ Stated so a client can say "667 of 720" rather than implying the list is everyone.
        "total": len(rows),
        "players": shown,
        # ⚠️⚠️ **A sidecar map, not a field on the player** — and the first attempt was the field.
        # `tests/test_player_shape.py` caught it: ADR-227 says every player in every answer is the same
        # shape, built by `player_summary`, because four shapes once drifted far enough that one of them
        # shipped 45 database columns to a phone. ⭐ *A rule about "every call site" only stays true if
        # adding a field to one of them fails.*
        #
        # ⭐ my-team had already solved this the same way, in `prices`. Two answers, one habit.
        "price_directions": {str(r["id"]): predict(by_id[r["id"]]) for r in shown},
    }

#: ⭐ Six fixtures on the DNA page, where the pitch card shows three (`RUN`). A club's *run* is a longer
#: question than a player's next card — ⚠️ *and they are separate constants because they answer separate
#: questions, not because one of them was forgotten.*
DNA_RUN = 6


def player_dna(request: PlayerDnaRequest, *, store: Storage | None = None) -> dict:
    """One player's fingerprint, ranked **within his position** (ADR-250).

    ⭐⭐ **Within position, not across the league.** A defender's attacking threat and a forward's are not
    the same question — ranked together, every defender would look poor at a thing defenders are not asked
    to do. ⚠️ *A single scale across incomparable roles is a ranking that flatters and punishes by
    position.*

    ⭐ **`pool_size` and `low_minutes` travel with it**, and the client shows both. A percentile is only as
    meaningful as the field it was measured in: *"84th of 31 midfielders"* is a fact, *"84th"* alone is an
    invitation to over-read it — and a player below the minutes floor is ranked anyway, with a caption,
    rather than silently excluded (ADR-118).
    """
    request.validate()
    store, ours = opened(store)
    try:
        players = store.get_players()
        target = next((p for p in players if p["id"] == request.player_id), None)
        if target is None:
            raise ValueError(f"no player with id {request.player_id}")
        dna = analytics_player_dna(target, players)
        insights = player_insights(target, dna) if dna else []
        data = load([request.player_id], request.horizon, store, need_history=True)
        summary = player_summary(target, data.xp_by_id,
                                 {r["id"]: r["by_gameweek"] for r in data.ranked},
                                 reported_out=data.leaving)
        club_by_id = {t["id"]: t["short_name"] for t in store.get_teams()}
        recent = list((data.gw_history or {}).get(target["code"]) or [])[-RECENT:]
    finally:
        if ours:
            store.close()

    if dna is None:
        # ⚠️ A player with no position cannot be ranked. ⭐ Saying so beats an empty radar, which reads as
        # "this player is bad at everything".
        return {"player": summary, "photo": photo_url(target["code"]), "axes": [], "insights": [],
                "pool_size": 0,
                "low_minutes": True, "min_minutes": 0, "recent": _recent_rows(recent, club_by_id),
                "unranked": "no position on record"}

    return {
        "player": summary,
        # ⭐ Same rule as the card: a face belongs where a name already is.
        "photo": photo_url(target["code"]),
        "axes": [{"label": a.label, "sublabel": a.sublabel, "value": a.value,
                  "percentile": a.percentile} for a in dna.axes],
        "insights": [{"kind": i.kind, "text": i.text} for i in insights],
        # ⭐ The field he was ranked in, not just his place in it.
        "pool_size": dna.pool_size,
        "low_minutes": dna.low_minutes,
        "min_minutes": dna.min_minutes,
        "recent": _recent_rows(recent, club_by_id),
        "unranked": None,
    }


def team_dna(request: TeamDnaRequest, *, store: Storage | None = None) -> dict:
    """Every club's fingerprint, ranked across the league (ADR-247).

    ⭐⭐ **Team DNA, not player DNA, and that is the choice.** A player's fingerprint answers *what kind of
    player is he?* — a question the app already answers twice, on the expanding card (ADR-237) and in Boot
    Battle (ADR-236). A club's answers *is this attack actually any good?*, which is what you need when
    choosing between two players from different sides, and the app could not answer it at all.

    ⭐ **Eight axes as percentiles**, so "74" means the same thing on Attacking Threat as on Squad Depth.
    The web draws them as a radar; ⚠️ *a radar needs width a phone does not have*, so the client draws bars
    — the same numbers, a shape that survives the screen.

    ⭐ `player_ids` marks which clubs you hold players from. ⚠️ It **filters nothing**: a league table you
    can see yourself in is a different object from a league table of the clubs you already own.
    """
    request.validate()
    store, ours = opened(store)
    try:
        players = store.get_players()
        teams = store.get_teams()
        upcoming = store.get_upcoming_fixtures()
        names = {t["short_name"]: t["name"] for t in teams}
        all_dna = team_dna_all(players, upcoming, team_names=names)
        mine = {p["team"] for p in players if p["id"] in set(request.player_ids)}
        gw_history = store.get_gw_history_by_code()
        past = store.get_history_by_code()
        # ⚠️⚠️ **Last season, when this one cannot rank anybody yet** (ADR-126). The ranking needs ~900
        # minutes and it is September — ⭐ *an empty table reads as "this club has no good players", which
        # is a claim nobody made*, so the fallback answers and the label says which season it answered for.
        last_rows = last_season_rows(players, past)
        last_name = last_season_name(past)
        schedule = {club: [{"gameweek": c.get("event"), "opponent": c["opponent"],
                            "venue": c["venue"], "difficulty": c.get("difficulty")}
                           for c in (team_schedule(upcoming, club) or [])[:DNA_RUN]]
                    for club in all_dna}
        form = {club: [{"gameweek": gw, "result": result}
                       for gw, result in (team_form(gw_history, players, club) or [])]
                for club in all_dna}
        key_players = {}
        for club in all_dna:
            rows_, season = key_players_this_or_last(players, club, last_rows=last_rows,
                                                    season_name=last_name)
            key_players[club] = {"season": season, "players": rows_}
    finally:
        if ours:
            store.close()

    rows = []
    for dna in all_dna.values():
        rows.append({
            "team": dna.team,
            "name": dna.name,
            "grade": dna.grade,
            "score": dna.grade_score,
            "yours": dna.team in mine,
            "axes": [{"label": a.label, "sublabel": a.sublabel, "value": a.value,
                      "percentile": a.percentile} for a in dna.axes],
            "insights": [{"kind": i.kind, "text": i.text} for i in team_insights(dna)],
            # ⭐ The three things the web page carries beside the fingerprint, and the reason a manager
            # opens it: where the club is going, how it has been going, and who to buy.
            "fixtures": schedule.get(dna.team, []),
            "form": form.get(dna.team, []),
            "key_players": key_players.get(dna.team, {"season": None, "players": []}),
        })
    # ⭐ Best first. ⚠️ Ties broken by name rather than left to dict order, so two runs of the same data
    # cannot disagree about the table — *an unstable sort is a diff that appears from nowhere.*
    rows.sort(key=lambda r: (-r["score"], r["name"]))
    return {"teams": rows, "yours": sorted(mine)}


#: How many recent gameweeks a comparison shows. ⭐ Five, because that is the window a manager means by
#: "form" and the one FPL's own `form` field averages over.
RECENT = 5


def compare(request: CompareRequest, *, store: Storage | None = None) -> dict:
    """Two players, side by side — **Boot Battle** (ADR-110/236).

    ⭐⭐ **Offered here so the comparison can sit where the decision is.** The web app has had this since
    ADR-110, on the Players page, as a destination you navigate to. A transfer screen that suggests
    `Groß → Belloumi` and cannot show you the two of them side by side is sending you to another room to
    answer the question it just raised.

    Three things, because the Hub's version showed two we lacked:

    * **the stat grid** — ours already, with the better value marked per row
    * **recent form** — the last five gameweeks, points and minutes
    * **the projected run** — per-gameweek xP for both, so the lines can be drawn against each other

    ⚠️ Same-position only. `compare_rows` orders the stats by what matters for a position, so comparing a
    keeper with a midfielder would produce rows that are individually true and jointly meaningless.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load([request.a_id, request.b_id], request.horizon, store, need_history=True)
        gw_history = data.gw_history or {}
        club_by_id = {t["id"]: t["short_name"] for t in store.get_teams()}
    finally:
        if ours:
            store.close()

    a, b = data.by_id[request.a_id], data.by_id[request.b_id]
    if a["position"] != b["position"]:
        raise ValueError(f"{a['web_name']} is a {a['position']} and {b['web_name']} is a {b['position']} — "
                         f"a comparison across positions ranks them on stats that do not mean the same thing")

    by_gameweek = {r["id"]: r["by_gameweek"] for r in data.ranked}

    def side(player):
        # ⭐ Keyed by the player's **code**, not id: `code` is stable across seasons, which is why the
        # history is stored under it (FPL restarts element ids each August).
        rows = list(gw_history.get(player["code"]) or [])[-RECENT:]
        return {
            **player_summary(player, data.xp_by_id, by_gameweek, reported_out=data.leaving),
            # ⭐ The face, as the web's compare header has had since ADR-110 — a named card, which is where
            # ADR-255 says a mugshot belongs.
            "photo": photo_url(player["code"]),
            "recent": _recent_rows(rows, club_by_id),
        }

    return {
        "horizon": request.horizon,
        "gameweeks": data.ranked[0]["gameweeks"] if data.ranked else [],
        "a": side(a),
        "b": side(b),
        # ⭐ `(label, a, b, winner)` — the winner decided by `_BETTER`, which knows that a lower expected
        # goals-conceded is the better number. ⚠️ A naive `max()` would crown the worse defence.
        "rows": [
            {"label": label, "a": fa, "b": fb, "winner": winner}
            for label, fa, fb, winner in compare_rows(a, b)
        ],
    }


def player(request: PlayerRequest, *, store: Storage | None = None) -> dict:
    """One player in full — the card behind a row (ADR-109/237).

    ⭐ **The stats are ordered by POSITION, not by a fixed list.** A defender leads with expected goals
    conceded and DefCon; a forward with goals and xG involvement. ⚠️ *The same twelve numbers in the same
    order for everyone is a table, not a card* — and it buries the one a reader opened the row for.

    Three blocks, matching what a comparison shows for two: the season stats, the last five gameweeks with
    minutes, and the projected run with its fixtures.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load([request.player_id], request.horizon, store, need_history=True)
        gw_history = data.gw_history or {}
        upcoming = data.upcoming
        # ⭐ Read inside the `try`, because it needs the store — see `_recent_rows`.
        club_by_id = {t["id"]: t["short_name"] for t in store.get_teams()}
    finally:
        if ours:
            store.close()

    row = data.by_id[request.player_id]
    by_gameweek = {r["id"]: r["by_gameweek"] for r in data.ranked}
    recent = list(gw_history.get(row["code"]) or [])[-RECENT:]

    return {
        "horizon": request.horizon,
        "player": player_summary(row, data.xp_by_id, by_gameweek, reported_out=data.leaving),
        # ⭐⭐ **On a named card, never on the pitch** (ADR-255). ADR-084 chose the club kit there on
        # purpose: FPL's photo CDN lags a transfer by weeks while the kit graphic updates instantly, so a
        # just-transferred player would sit on the pitch wearing his old club's face. ⚠️ *On a card his
        # name is beside him and the staleness is a curiosity; on the pitch it is the app being visibly
        # wrong about your team.*
        "photo": photo_url(row["code"]),
        "stats": [{"label": label, "value": value} for label, value in stat_rows(row)],
        # ⭐⭐ **Already computed, and the phone could not see them** (ADR-286). The web card has carried
        # set-piece duty and the ownership tier since ADR-081/US-289; the mobile card showed neither,
        # because this endpoint never sent them. ⚠️ *A lens the engine already applies, withheld from one
        # client, is not a missing feature — it is the same product disagreeing with itself.*
        #
        # ⭐ Ownership first, then the duties, which is the order they answer in: *how many people own
        # him* frames *what he does for them*.
        "badges": _badges(row),
        "recent": _recent_rows(recent, club_by_id),
        # ⭐ The run **with difficulty**, so a reader can see whether a high projection is a good player or
        # an easy month — which is the question a card is opened to answer.
        "fixtures": [
            {"gameweek": cell.get("event"), "opponent": cell["opponent"],
             "venue": cell["venue"], "difficulty": cell.get("difficulty")}
            for cell in (team_schedule(upcoming, row["team"]) or [])[:request.horizon]
        ],
    }
