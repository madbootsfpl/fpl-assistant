"""Ingestion — fetch FPL data, map it, and store it.

This coordinates three layers (client → mapping → storage) into the single
"refresh" operation. It is the only path in the app that reaches the network.
Keeping it in one module (rather than inside the CLI handler) honours ADR-003:
the CLI dispatches, the ingestion does the work.
"""

from src.api.client import FplClient
from src.api.clubelo import (
    ClubEloError,
    EloClient,
    map_elo_to_teams,
    parse_english_elo,
)
from src.models import Fixture, Player, Team
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
