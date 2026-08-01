"""Ingestion — fetch FPL data, map it, and store it.

This coordinates three layers (client → mapping → storage) into the single
"refresh" operation. It is the only path in the app that reaches the network.
Keeping it in one module (rather than inside the CLI handler) honours ADR-003:
the CLI dispatches, the ingestion does the work.
"""

from src.api.client import FplClient
from src.models import Player, Team
from src.storage import Storage


def refresh(store: Storage, client: FplClient | None = None) -> tuple[int, int]:
    """Fetch the latest FPL data and store it locally.

    Returns (player_count, team_count). Raises FplApiError if the fetch fails —
    the caller decides how to report that. The `client` is injectable so tests
    can supply a fake instead of hitting the network.
    """
    client = client or FplClient()
    data = client.get_bootstrap_static()

    teams = [Team.from_api(t) for t in data.get("teams", [])]
    players = [Player.from_api(e) for e in data.get("elements", [])]

    store.save_teams(teams)      # teams first — players reference them
    store.save_players(players)

    return len(players), len(teams)
