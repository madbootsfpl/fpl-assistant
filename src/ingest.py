"""Ingestion — fetch FPL data, map it, and store it.

This coordinates three layers (client → mapping → storage) into the single
"refresh" operation. It is the only path in the app that reaches the network.
Keeping it in one module (rather than inside the CLI handler) honours ADR-003:
the CLI dispatches, the ingestion does the work.
"""

import time
from datetime import datetime, timezone

from src import config
from src.analytics.deadline import next_deadline
from src.api.client import FplApiError, FplClient
from src.api.clubelo import (
    ClubEloError,
    EloClient,
    map_elo_to_teams,
    parse_english_elo,
)
from src.models import Fixture, Player, PlayerGameweek, PlayerSeason, Team
from src.storage import Storage

# ── Validation ────────────────────────────────────────────────────────────────────────────────────────────
#
# ⚠️ **These are a smoke alarm, not a thermostat, and that is the whole of their provenance** (ADR-199 asks
# where a threshold comes from, and the honest answer here is *declared, not measured*). They exist to catch a
# catastrophic payload — an empty response, a truncated one, a wholesale zeroing — **not** to police ordinary
# movement. Every bound below is therefore deliberately loose: a check that fires on a real January transfer
# window would block good data, which is worse than storing slightly odd data.
#
# 📅 Re-visit if one ever fires on a payload that turns out to have been fine — that, not a calendar date, is
# the evidence that a bound is wrong.
MIN_PLAYERS = 300               # a real Premier League season carries ~600-700; half that is a broken fetch
EXPECTED_TEAMS = 20             # not a guess — the competition has twenty clubs
MIN_SHARE_OF_PREVIOUS = 0.70    # windows add and remove players; losing a third in one fetch is not a window
MIN_SHARE_PRICED = 0.90         # every listed player has a price; a mass of zeros is a mangled payload


class PayloadRejected(Exception):
    """FPL's response did not pass validation, so **nothing was stored** and the last good data still stands.

    ⭐ Raised rather than returned, and raised *before* the first write, because the alternative — checking
    after storing — is not a check at all once storing is publishing.
    """

    def __init__(self, reasons):
        self.reasons = list(reasons)
        super().__init__("; ".join(self.reasons))


def validate(players, teams, fixtures, *, previous_players: int | None = None) -> list[str]:
    """Reasons to refuse this payload — empty when it is safe to publish.

    ⭐ **Checks what FPL sent, not what we stored.** The failure this guards against is a bad *response*, and
    by the time it is in the database the last good copy is already gone.

    `previous_players` is how many the database currently holds, so a collapse can be seen; `None` (a first
    run) skips that one comparison rather than inventing a baseline.
    """
    reasons = []
    if len(players) < MIN_PLAYERS:
        reasons.append(f"only {len(players)} players (expected at least {MIN_PLAYERS})")
    if len(teams) != EXPECTED_TEAMS:
        reasons.append(f"{len(teams)} teams (expected {EXPECTED_TEAMS})")
    if not fixtures:
        reasons.append("no fixtures at all")
    if previous_players and len(players) < previous_players * MIN_SHARE_OF_PREVIOUS:
        reasons.append(
            f"player count collapsed {previous_players} → {len(players)} "
            f"(below {MIN_SHARE_OF_PREVIOUS:.0%} of the last good fetch)")
    if players:
        priced = sum(1 for p in players if (getattr(p, "price", 0) or 0) > 0)
        if priced < len(players) * MIN_SHARE_PRICED:
            reasons.append(f"only {priced} of {len(players)} players carry a price")
    return reasons


def _record_transfer_flow(store: Storage, players, fixtures, stamped: str) -> int:
    """Log this refresh's transfer counters against the gameweek they are accumulating toward (ADR-210).

    ⭐ **The same fault as ADR-203, in the one other place it was still happening.** `transfers_in_event` /
    `transfers_out_event` / `selected_by` are *now* fields on the mutable `players` row: FPL resets the
    counters at every deadline, publishes no history for them, and every refresh overwrote the only copy of
    last week's answer. ADR-190 found this by instruction-failure — its own rule, *"re-measure the exodus
    threshold on ≥4 gameweeks"*, had nothing to run on and quietly produced a second one-week sample instead.

    ⭐ Stamped with the event it climbs toward **and how far off that deadline was**, because the counter is an
    *accumulation*: one week's reading is not comparable with another's unless both sit at the same point in
    the cycle. That is the column ADR-190's attempted re-measurement did not have and could not reconstruct.

    ⚠️ `next_deadline` indexes its rows (`f["event"]`) because every other caller hands it `sqlite3.Row`s;
    `refresh` holds `Fixture` **dataclasses**, which are not subscriptable. So they are converted here rather
    than loosening a helper six other call sites depend on.

    Returns rows written — 0 when there is no next deadline (season over, nothing to key a reading on).
    """
    when = datetime.fromisoformat(stamped)
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)      # a naive stamp is UTC here; `next_deadline` needs aware
    upcoming = next_deadline([{"event": f.event, "kickoff_time": f.kickoff_time} for f in fixtures], when)
    if upcoming is None:
        return 0
    gameweek, deadline = upcoming
    return store.save_transfer_flow(
        players, gameweek, stamped,
        hours_to_deadline=(deadline - when).total_seconds() / 3600.0)


def refresh(
    store: Storage,
    client: FplClient | None = None,
    elo_client: EloClient | None = None,
    now: str | None = None,
) -> tuple[int, int, int, int]:
    """Fetch the latest data and store it locally.

    Returns (players, teams, fixtures, elo_ratings). FPL is required (raises
    FplApiError on failure); ClubElo is best-effort (a failure is non-fatal — see
    _refresh_elo). Both clients are injectable so tests can supply fakes.
    """
    client = client or FplClient()
    data = client.get_bootstrap_static()
    fixtures_raw = client.get_fixtures()

    teams = [Team.from_api(t) for t in data.get("teams", [])]
    players = [Player.from_api(e) for e in data.get("elements", [])]
    fixtures = [Fixture.from_api(f) for f in fixtures_raw]

    # ⭐⭐ **Check before the first write, and for every caller** (ADR-211 2c). Once storing *is* publishing,
    # a check that runs afterwards is not a check — the last good copy is already gone. And it is deliberately
    # **not** an optional argument: an opt-out on a shared helper is how one call site ends up behaving
    # differently from every other (ADR-181), and the call site that forgot would be the manual refresh, run
    # by a person, on the database everything else reads.
    #
    # ⚠️ Locally the blast radius of a bad payload is one laptop. Server-side it is every user at once, which
    # is what makes this worth raising rather than warning about.
    if reasons := validate(players, teams, fixtures, previous_players=store.count_players()):
        raise PayloadRejected(reasons)

    # Teams first: both players and fixtures reference them (FK enforcement is on).
    store.save_teams(teams)
    store.save_players(players)
    store.save_fixtures(fixtures)
    # ADR-203 — `players` holds only the CURRENT status/chance/news, so every refresh overwrites the last
    # answer to "was he fit that week?". The observation has to be recorded as it passes or it is not
    # recoverable: FPL serves availability as a *now* field and keeps no history of it. ADR-201's lesson,
    # in the one other place the app was letting data expire.
    store.save_availability(players, now or datetime.now(timezone.utc).isoformat(timespec="seconds"))

    # ADR-210 — the other *now* field. See `_record_transfer_flow`: FPL resets the transfer counters at
    # every deadline and keeps no history, so a reading not recorded as it passes is gone.
    _record_transfer_flow(store, players, fixtures,
                          now or datetime.now(timezone.utc).isoformat(timespec="seconds"))

    n_elo = _refresh_elo(store, data.get("teams", []), elo_client)

    return len(players), len(teams), len(fixtures), n_elo


def backfill_history(
    store: Storage,
    client: FplClient | None = None,
    ids: list[int] | None = None,
    sleep_between: float = config.HISTORY_THROTTLE,
    sleep=time.sleep,
    progress=None,
) -> tuple[int, int, int, int]:
    """Fetch each player's past-season **and** per-GW summaries and store them (ADR-027/060).

    One `element-summary` call per player, **throttled** (`sleep_between`) to respect
    rate limits and kept out of `refresh`. The single payload carries both `history_past`
    (past-season aggregates, ADR-027) and `history` (this-season per-GW, ADR-060) — so the
    per-GW ingest **rides the same walk** (no second pass). Per-GW is **empty preseason** and
    lights up at GW1. **Idempotent** (past: upsert on code+season; per-GW: on code+round, so an
    interrupted run resumes) and **per-player degrading** — one player's FplApiError is logged
    and skipped, never aborting the run. `ids` defaults to every stored player; pass a subset to
    backfill a slice. `progress(i, total)` is called after each player.

    Returns (players_processed, seasons_stored, gameweeks_stored, failures).
    """
    client = client or FplClient()
    if ids is None:
        ids = store.get_player_ids()
    # The per-GW `history` row carries `element` (the season id), not the stable code — so map it.
    code_by_id = store.get_player_codes()

    processed = seasons_stored = gameweeks_stored = failures = 0
    total = len(ids)
    for i, element_id in enumerate(ids, start=1):
        try:
            summary = client.get_element_summary(element_id)
        except FplApiError as exc:
            failures += 1
            print(f"  history: player {element_id} failed — skipped ({exc}).")
        else:
            rows = [PlayerSeason.from_api(s) for s in summary.get("history_past", [])]
            if rows:
                store.save_history_past(rows)
                seasons_stored += len(rows)
            # Per-GW (ADR-060) — empty preseason, live at GW1; needs the stable code to key by.
            code = code_by_id.get(element_id)
            if code is not None:
                gw_rows = [PlayerGameweek.from_api(h, code) for h in summary.get("history", [])]
                if gw_rows:
                    store.save_history(gw_rows)
                    gameweeks_stored += len(gw_rows)
            processed += 1

        if progress:
            progress(i, total)
        # Throttle between calls (not after the last one).
        if sleep_between and i < total:
            sleep(sleep_between)

    return processed, seasons_stored, gameweeks_stored, failures


def _refresh_elo(store: Storage, raw_teams, elo_client: EloClient | None) -> int:
    """Best-effort: fetch ClubElo and store team Elo. Returns the count stored.

    A ClubElo failure is *non-fatal* — it's logged and the last-known Elo is kept
    (we simply don't write). Unmapped clubs are reported loudly but don't stop the
    ones that did map from being stored.
    """
    elo_client = elo_client or EloClient()
    try:
        elo_by_club = parse_english_elo(elo_client.get_elo_csv())
    except ClubEloError as exc:
        print(f"ClubElo unavailable — keeping last-known Elo ({exc}).")
        return 0

    elo_by_team, unmapped = map_elo_to_teams(elo_by_club, raw_teams)
    if unmapped:
        print(f"ClubElo: {len(unmapped)} club(s) not mapped: {', '.join(unmapped)}.")

    store.save_team_elo(elo_by_team)
    return len(elo_by_team)


def enrich_headlines(store, players=None, *, ask=None, feeds=None,
                     budget_seconds: float = config.EXTRACT_BUDGET_SECONDS) -> tuple[int, str]:
    """Read events out of the current headlines and store them (ADR-151). `(count, message)`.

    **Runs at refresh, not per page view**, and that is a deployment fact rather than a preference: extraction
    needs a language model, Streamlit Cloud has none, and the committed snapshot (ADR-056) is how every other
    number reaches the app. A snapshot built without a model simply carries no events, and every surface
    degrades to exactly what it said before.

    Never raises. A missing Ollama, an unreachable feed or a rate-limited Reddit each cost the enrichment,
    not the refresh — the player data is the point of `refresh`, and this is a bonus on top.
    """
    from datetime import UTC, datetime

    from src.analytics.headlines import extract as extract_events
    from src.llm import extract as ask_model

    ask = ask or ask_model
    players = players if players is not None else store.get_players()
    if not players:
        return 0, "no players to resolve against"

    titles = []
    try:
        titles += [t for t in (feeds() if feeds else _headline_titles())]
    except Exception as exc:                             # noqa: BLE001 — feeds are best-effort everywhere
        return 0, f"couldn't read the feeds: {exc}"
    if not titles:
        return 0, "no headlines available"

    if ask("ping") is None:                              # no model → no events, and say so plainly
        return 0, "no language model available (Ollama not running?) — headlines left unread"

    # ADR-157 — say so when the budget cut the read short. `extract` stops cleanly and keeps what it has,
    # which is right, but it stopped SILENTLY: a truncated run and a complete one printed the same sentence,
    # so a feed that outgrew the budget would look like a quiet news day. Timing the call is enough to tell.
    started = time.monotonic()
    events = extract_events(titles, players, ask, seen_at=datetime.now(UTC).isoformat(),
                            budget_seconds=budget_seconds)
    elapsed = time.monotonic() - started
    stored = store.upsert_headline_events(events)
    if elapsed >= budget_seconds:
        return stored, (f"{stored} events — ⚠ stopped at the {budget_seconds:.0f}s budget with "
                        f"{len(titles)} headlines offered, so some went unread")
    return stored, f"read {len(titles)} headlines in {elapsed:.0f}s → {stored} events"


def _headline_titles() -> list:
    """Titles from the same feeds the app shows — media headlines plus r/FantasyPL, each best-effort."""
    from src.api.feeds import parse_feed
    from src.api.media import media_headlines
    from src.api.reddit import RedditError, RedditRssClient

    titles = []
    try:
        for items in (media_headlines() or {}).values():
            titles += [i["title"] for i in items if i.get("title")]
    except Exception:                                    # noqa: BLE001
        pass
    try:
        titles += [p.get("title") or "" for p in parse_feed(RedditRssClient().get_subreddit_rss(), limit=100)]
    except (RedditError, Exception):                     # noqa: BLE001 — Reddit rate-limits; not fatal
        pass
    return [t for t in titles if t]
