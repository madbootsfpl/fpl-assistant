"""Ingestion — fetch FPL data, map it, and store it.

This coordinates three layers (client → mapping → storage) into the single
"refresh" operation. It is the only path in the app that reaches the network.
Keeping it in one module (rather than inside the CLI handler) honours ADR-003:
the CLI dispatches, the ingestion does the work.
"""

import time

from src import config
from src.api.client import FplApiError, FplClient
from src.api.clubelo import (
    ClubEloError,
    EloClient,
    map_elo_to_teams,
    parse_english_elo,
)
from src.models import Fixture, Player, PlayerGameweek, PlayerSeason, Team
from src.storage import Storage


def refresh(
    store: Storage,
    client: FplClient | None = None,
    elo_client: EloClient | None = None,
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

    # Teams first: both players and fixtures reference them (FK enforcement is on).
    store.save_teams(teams)
    store.save_players(players)
    store.save_fixtures(fixtures)

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
