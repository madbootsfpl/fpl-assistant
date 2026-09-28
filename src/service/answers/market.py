"""The market answers — what is moving, and what is worth being told about.

`trending` · `ticker` · `signals`, and the evidence tiers that order them.
"""


from src.analytics import (
    player_summary,
)
from src.kits import photo_url

# ⭐⭐ **Imported as a module, not as names** (ADR-324). `common`'s helpers are shared by more than one
# answer family, and a test that fakes one — `_chip_status` is faked in three suites — must be able to
# reach every consumer from one place. ⚠️ *Binding a shared function into each module's globals gives it
# as many patch points as there are importers*, which is how a fake silently applies to one caller and
# not the next.
from src.service.answers import common
from src.service.inputs import load, opened
from src.service.requests import (
    DEFAULT_HORIZON,
    SignalsRequest,
    TickerRequest,
    TrendingRequest,
)
from src.storage import Storage


def _worth_noticing(request: TrendingRequest, data) -> dict:
    """What the crowd is doing that a single leaderboard cannot show (ADR-170/271).

    ⭐⭐ **Three patterns, each needing two boards at once**: *in form, still under-owned* · *a bandwagon
    forming* · *the template breaking up*. ⚠️ *A player can top none of the four boards and still be the
    most interesting name on the page* — which is exactly what a ranking of one number cannot say.

    ⚠️⚠️ **It says what the crowd is DOING, never why.** Trending and Signals split on that axis
    (ADR-149/150): what people *do*, in numbers, versus what is being *said*. ⭐ *Repeating a headline
    here would put an unsourced guess next to a measured fact.*

    ⭐ **Rows carry a `group`, rather than this being a third answer shape.** The client renders a heading
    when the group changes — ⚠️ *a second row shape would be a second renderer, and the two would drift.*
    """
    from src.analytics.crowd import ownership_label
    from src.analytics.crowd_watch import watch_note, worth_noticing

    groups = worth_noticing(data.players, per_pattern=4)
    by_id = {p["id"]: p for p in data.players}
    ranked_by_id = {r["id"]: r for r in data.ranked}
    owned_ids = set(request.player_ids)

    rows = []
    for group in groups:
        for row in group["players"]:
            raw = by_id.get(row["id"])
            if raw is None:
                continue
            ranked = ranked_by_id.get(row["id"], {})
            rows.append({
                "player": player_summary(raw, data.xp_by_id,
                                         {row["id"]: ranked.get("by_gameweek", {})},
                                         {row["id"]: ranked.get("minutes_weight", 1.0)}),
                "photo": photo_url(raw["code"]),
                # ⭐ The heading this row sits under. Carried per row so the order cannot come apart from
                # the grouping — ⚠️ *two lists that have to be zipped are two lists that will be.*
                "group": group["label"],
                # ⚠️ **No ranking number.** These rows are sentences, and ⭐ *a number in the corner would
                # invite a reader to sort by it* — there is nothing here to sort by.
                "value": 0.0,
                "owned_by": raw.get("selected_by"),
                "tier": ownership_label(raw),
                "owned": row["id"] in owned_ids,
                "reasons": [row["reason"]],
            })

    return {
        "by": "watch",
        "label": "worth noticing",
        # ⭐ Empty on purpose: the client shows no value column when there is no number to head.
        "column": "",
        # ⚠️ The engine's sentence says *"the four boards below"* — true of a page that stacks them and
        # ⭐ **false on a phone, where they are a tap away**. Reworded here rather than in the engine,
        # because the Streamlit page it was written for still stacks them: *a sentence about a layout
        # belongs to the layout.*
        "caveat": common.plain(watch_note(groups).replace("the four boards below only show *between* them",
                                                   "the other boards only show *between* them")),
        "rows": rows,
    }


def _worth_a_look(request: TrendingRequest, data, store) -> dict:
    """ADR-167's convergence board, on a phone (ADR-269).

    ⭐⭐ **The claim is deliberately narrow: *worth a look*, not *worth points*.** Two of the signals it
    reads — set-piece duty and DefCon — are ones the engine has explicitly decided **not** to price, so
    ⚠️ *ranking players on them as though they were points would be the app asserting confidence it has
    withheld*, and would put a second opinion beside xP.

    ⭐ **What a single board cannot say is that two boards agree.** A first-choice penalty taker who also
    clears the DefCon bar is a different proposition from either fact alone, and that convergence is the
    only new information here.

    ⚠️⚠️ **Most of the evidence is last season's, and every reason says so.** The rate boards need 900
    minutes; ⭐ *a reason that did not carry its own vintage would be the most misleading kind of true
    statement.*
    """
    from src.analytics.crowd import ownership_label
    from src.analytics.last_season import last_season_name, last_season_rows
    from src.analytics.scout import scout_note, worth_a_look

    # ⚠️⚠️ **`get_history_by_code`, not `get_gw_history_by_code`.** The first holds PAST SEASONS; the
    # second holds this season's gameweeks. Reading the wrong one returned 667 codes and **zero** last-
    # season rows, so the rate boards ran on five gameweeks of minutes, cleared nothing, and the board
    # came back empty — ⭐ *a wrong source that returns plenty of data fails as an empty answer, not as an
    # error*, and "nobody stands out" is a sentence this board is designed to say truthfully.
    past = store.get_history_by_code()
    season = last_season_name(past)
    rows = last_season_rows(data.players, past)
    found = worth_a_look(data.players, rows=rows or data.players, season=season,
                         limit=request.limit)

    by_id = {p["id"]: p for p in data.players}
    ranked_by_id = {r["id"]: r for r in data.ranked}
    owned_ids = set(request.player_ids)
    out = []
    for row in found:
        raw = by_id.get(row["id"])
        if raw is None:
            continue
        ranked = ranked_by_id.get(row["id"], {})
        out.append({
            "player": player_summary(raw, data.xp_by_id,
                                     {row["id"]: ranked.get("by_gameweek", {})},
                                     {row["id"]: ranked.get("minutes_weight", 1.0)}),
            "photo": photo_url(raw["code"]),
            # ⚠️ **The count of agreeing signals, not a score.** ⭐ *A number that looked like a rating
            # would compete with xP*, which is the one thing this board must not do.
            "value": float(len(row["reasons"])),
            "owned_by": raw.get("selected_by"),
            "tier": ownership_label(raw),
            "owned": row["id"] in owned_ids,
            # ⭐ The evidence itself, each line carrying its own vintage.
            "reasons": row["reasons"],
        })

    return {
        "by": "look",
        "label": "worth a look",
        "column": "signals",
        # ⭐ The engine's own sentence — including for an **empty** list, which is a real answer here and
        # not a failure to load.
        "caveat": common.plain(scout_note(found, season=season if rows else None)),
        "rows": out,
    }


def trending(request: TrendingRequest, *, store: Storage | None = None) -> dict:
    """The crowd's four leaderboards — most bought, most sold, most owned, in form (ADR-266).

    ⚠️⚠️ **This is the weakest evidence the app carries, and it says so.** ADR-150 ranks the signal tiers
    by evidentiary strength and puts `trending` **last, deliberately** — ⭐ *it is a fact about other
    managers, not about the player.* Presenting it beside FPL's own injury news without that framing is
    the failure this endpoint is built to avoid, so every board carries its own `caveat`.

    ⭐ **Ownership is the number that makes the others readable.** *"200k bought him"* means something
    different at 4% ownership than at 40%, so each row carries `owned_by` and its tier whichever board
    you are on.
    """
    request.validate()
    from src.analytics.crowd import TREND_BYS, ownership_label
    from src.analytics.crowd import trending as rank_trending

    store, ours = opened(store)
    try:
        data = load(list(request.player_ids), DEFAULT_HORIZON, store)
        if request.by == "look":
            return _worth_a_look(request, data, store)
        if request.by == "watch":
            return _worth_noticing(request, data)
    finally:
        if ours:
            store.close()

    by_id = {p["id"]: p for p in data.players}
    ranked_by_id = {r["id"]: r for r in data.ranked}
    owned_ids = set(request.player_ids)

    label, column = TREND_BYS[request.by]
    rows = []
    for row in rank_trending(data.players, by=request.by, limit=request.limit):
        raw = by_id.get(row["id"])
        if raw is None:
            continue
        ranked = ranked_by_id.get(row["id"], {})
        rows.append({
            "player": player_summary(raw, data.xp_by_id,
                                     {row["id"]: ranked.get("by_gameweek", {})},
                                     {row["id"]: ranked.get("minutes_weight", 1.0)}),
            # ⭐ A named card, so the photo is right here (ADR-084's rule) — ⚠️ *never the pitch*, where
            # the CDN lags a transfer by weeks and a just-moved player would wear his old club's face.
            "photo": photo_url(raw["code"]),
            # ⚠️ The board's own number, named by the board — `trend` alone would be four different
            # quantities sharing one key, and a client would have to know which board it asked for.
            "value": row["trend"],
            "owned_by": raw.get("selected_by"),
            "tier": ownership_label(raw),
            "owned": row["id"] in owned_ids,
        })

    return {
        "by": request.by,
        "label": label,
        "column": column,
        # ⭐ Carried with the answer rather than written into the app, so the warning cannot drift from
        # the numbers it is about.
        "caveat": "What other managers are doing. It is the weakest evidence here — a reason a template "
                  "forms, not on its own a reason to join one.",
        "rows": rows,
    }


def ticker(request: TickerRequest, *, store: Storage | None = None) -> dict:
    """The fixture-difficulty grid: every club, their next few gameweeks, easiest run first (ADR-265).

    ⭐⭐ **The engine already did all of this.** `fixture_ticker` has handled doubles and blank gameweeks
    since Sprint 062; what was missing was a way for a phone to ask. ⚠️ *A capability with no transport is
    invisible to every surface that does not share a process.*

    ⭐ **A blank gameweek is `null`, not a gap.** The cell is present and empty, because *"they do not
    play"* is the single most valuable thing a ticker says and a missing key reads as missing data.

    ⚠️ **A double shows both matches** and is shaded by its **harder** half — a double is only as easy as
    its worse fixture, and shading it by the first would make the view built for spotting doubles the one
    that misrepresents them.
    """
    request.validate()
    from src.analytics.fdr import fixture_ticker

    store, ours = opened(store)
    try:
        grid = fixture_ticker(store.get_upcoming_fixtures(), next_n=request.next_n,
                              source=request.source)
    finally:
        if ours:
            store.close()

    return {
        "gameweeks": grid["gameweeks"],
        "rows": [
            {
                "team": row["team"],
                "avg_difficulty": row["avg_difficulty"],
                # ⚠️ Keys are stringified: JSON has no integer object keys, and a client sorting text
                # would put "10" before "6" (ADR-219). The gameweek order lives in `gameweeks`.
                "cells": {
                    str(ev): None if cell is None else {
                        "opponent": cell["opponent"],
                        "venue": cell["venue"],
                        "difficulty": cell["difficulty"],
                        "opponents": [f["opponent"] for f in cell["fixtures"]],
                        "venues": [f["venue"] for f in cell["fixtures"]],
                    }
                    for ev, cell in row["cells"].items()
                },
            }
            for row in grid["rows"]
        ],
    }


#: ⭐⭐ **The ordering IS the design** (ADR-150). These sources are not equally reliable, and putting them in
#: one list without saying so would present a Reddit rumour beside an injury FPL confirmed. So they descend
#: by **evidentiary strength**, and each says what it is.
_TIERS = {
    "official": 1,     # FPL's own `news`. A fact — it drives `status`, and therefore every xP in the app.
    "departure": 2,    # the press and the crowd agreeing a player is leaving the league (ADR-153/155).
    "exodus": 3,       # our own inference: a sell-off our fields cannot explain (ADR-146).
    "headline": 4,     # reported by a named outlet (ADR-093).
    # ⚠️ Last, and deliberately: what the crowd is **buying** is the weakest evidence here. It is a fact
    # about other managers, not about the player — ⭐ *"lots of people did this" is the reason a template
    # forms, and it is not on its own a reason to join one.*
    "trending": 5,
}

#: ⭐⭐ **The share of the board that anyone actually considers**, read from the live distribution rather
#: than typed (ADR-210/215). Measured on 2026-09-22: ownership has a **median of 0.2%**, so a plain sweep
#: of the market surfaced **194 news items**, nearly all of them about players almost nobody holds.
#:
#: ⚠️ At the 75th percentile (**1.2% owned**) the same sweep gives **22 signals** — a list a person reads.
#: The number is not a judgement about 1.2%; it is *"the quarter of the board most managers consider"*, and
#: it moves when the league does.
GLOBAL_OWNERSHIP_PERCENTILE = 75


def signals(request: SignalsRequest, *, store: Storage | None = None) -> dict:
    """What a manager should know about his own fifteen, strongest evidence first (ADR-232).

    ⭐ **Squad-scoped, which is the whole difference from the web page.** That browses the market; this
    answers *"what should I know?"* about the players you actually hold — the question a manager opens a
    phone to ask before a deadline.

    ⚠️ **Each signal says what kind of thing it is**, because they are not equally reliable. An FPL `news`
    string is a fact; an unexplained exodus is *"the crowd knows something and we do not"*; a headline is
    one outlet's reporting. ⭐ *Presenting them as one undifferentiated list would be the page ADR-150 was
    written to replace.*

    ⭐ **Every signal carries a stable `key`**, so a client can remember which it has already shown. The
    app cannot ask the server *what changed since I last looked* — the server has no idea when that was —
    but it can be told what each thing **is**, and work the rest out itself.
    """
    request.validate()
    store, ours = opened(store)
    try:
        data = load(request.player_ids, request.horizon, store, need_events=True)
        events = data.events or {}
    finally:
        if ours:
            store.close()

    from src.analytics.crowd import exodus_detector, trending

    # ⚠️ Bound to the whole board, never the fifteen — ADR-210: a tenth of fifteen flags somebody weekly.
    exodus_for = exodus_detector(data.players)

    owned_ids = {p["id"] for p in data.owned}
    if request.scope == "global":
        subjects, cut = _market_subjects(data.players)
    else:
        subjects, cut = list(data.owned), None

    # ⭐ Only in global, and only for players the reader does not already hold: *"lots of managers are
    # buying him"* is news about the market. About your own player it is not news at all.
    buying = {}
    if request.scope == "global":
        for row in trending(subjects, by="in", limit=8):
            if row["id"] not in owned_ids:
                buying[row["id"]] = row["trend"]

    found = []
    for player in subjects:
        summary = player_summary(player, data.xp_by_id, reported_out=data.leaving)
        news = (player["news"] or "").strip() if "news" in player.keys() else ""

        if news:
            found.append({"kind": "official", "key": f"official:{player['id']}:{hash(news) & 0xffff}",
                          "player": summary, "headline": news,
                          "detail": "FPL's own news. It drives his status, and therefore his projection."})

        if leaving := data.leaving.get(player["id"]):
            found.append({"kind": "departure", "key": f"departure:{player['id']}",
                          "player": summary,
                          "headline": leaving.get("title") or "Reported to be leaving the league",
                          "detail": f"Reported by {leaving.get('source') or 'the press'}. "
                                    f"FPL still lists him as available."})

        if exodus := exodus_for(player):
            found.append({"kind": "exodus", "key": f"exodus:{player['id']}",
                          "player": summary,
                          # ⚠️ `net` is negative by construction — it is transfers *out* minus in. "-2,762 managers
                          # sold him" reads as nonsense, and the sign is already carried by the
                          # word "sold".
                          "headline": f"{abs(exodus['net']):,} managers sold him this week",
                          # ⭐ Deliberately says nothing about *what* the news is. It reports that the crowd
                          # knows something and we do not — true, checkable, and the most the data supports.
                          "detail": "Nothing in his status or news explains it."})

        if (net_in := buying.get(player["id"])) is not None:
            found.append({"kind": "trending", "key": f"trending:{player['id']}",
                          "player": summary,
                          "headline": f"{abs(int(net_in)):,} managers bought him this week",
                          # ⭐ Says what it is and stops. The app does not know *why* they bought him, and
                          # a confident guess would be the thing ADR-150 was written to remove.
                          "detail": "A crowd movement, not a projection. He may already be priced in."})

        for event in events.get(player["id"], []):
            row = dict(event)
            found.append({"kind": "headline", "key": f"headline:{player['id']}:{row.get('seen_at')}",
                          "player": summary, "headline": row.get("title") or "",
                          "detail": f"Reported by {row.get('source') or 'an outlet'}.",
                          "at": row.get("seen_at")})

    found.sort(key=lambda s: (_TIERS[s["kind"]], s["player"]["web_name"]))
    for signal in found:
        # ⭐ So a global list can say *"you own him"* without the client holding a second copy of the squad.
        signal["owned"] = signal["player"]["id"] in owned_ids
    return {
        "signals": found,
        "scope": request.scope,
        # ⭐ So a quiet week reads as *"nothing to report"* rather than as a screen that failed to load.
        "checked": len(subjects),
        # ⚠️ **What "global" actually means, stated.** A market view that silently drops four fifths of the
        # board is a view that lies by omission — ⭐ *a filter the reader cannot see is a filter he will
        # eventually be surprised by* (ADR-215).
        "ownership_floor": cut,
    }


def _market_subjects(players):
    """The slice of the board worth sweeping, and the cut that produced it (ADR-245).

    ⭐⭐ **Read from the live distribution, never typed.** Measured on the real board: ownership has a
    **median of 0.2%**, so an unbounded market sweep returned **194 news items**, nearly all about players
    almost nobody holds — ⚠️ *a list that long is not more information, it is a screen a person stops
    reading.* At the 75th percentile the same sweep gives about **22**.
    """
    rows = [dict(p) for p in players]
    shares = sorted((p.get("selected_by") or 0) for p in rows)
    if not shares:
        return [], None
    cut = shares[min(len(shares) - 1, int(len(shares) * GLOBAL_OWNERSHIP_PERCENTILE / 100))]
    return [p for p in rows if (p.get("selected_by") or 0) >= cut], round(cut, 1)
