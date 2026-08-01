"""FPL Assistant entry point.

First vertical slice: fetch player data from the FPL API, store it locally in
SQLite, and report the counts. Displaying a proper player table (US-004) comes
next — see docs/05_Sprints/Sprint1.md.
"""

from src import config
from src.api.client import FplApiError, FplClient
from src.models import Player, Team
from src.storage import Storage
from src.ui.table import render_player_table


def main() -> None:
    print("⚽ FPL Assistant starting...")

    try:
        data = FplClient().get_bootstrap_static()
    except FplApiError as exc:
        print(f"Could not fetch FPL data: {exc}")
        return

    teams = [Team.from_api(t) for t in data.get("teams", [])]
    players = [Player.from_api(e) for e in data.get("elements", [])]

    store = Storage()
    store.save_teams(teams)      # teams first — players reference them
    store.save_players(players)

    print(
        f"Stored {store.count_players()} players and "
        f"{store.count_teams()} teams in {config.DB_PATH}."
    )

    # Read back from the local database (not the API) and show the top players.
    print()
    print(render_player_table(store.get_players()))
    store.close()


if __name__ == "__main__":
    main()
