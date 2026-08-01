"""FPL Assistant entry point.

Proves the first vertical slice: fetch player data from the official FPL API and
report how many players came back. Storing that data (US-003) and displaying a
proper table (US-004) come next — see docs/05_Sprints/Sprint1.md.
"""

from src.api.client import FplApiError, FplClient


def main() -> None:
    print("⚽ FPL Assistant starting...")

    try:
        data = FplClient().get_bootstrap_static()
    except FplApiError as exc:
        print(f"Could not fetch FPL data: {exc}")
        return

    players = data.get("elements", [])
    teams = data.get("teams", [])
    print(f"Fetched {len(players)} players across {len(teams)} teams from the FPL API.")


if __name__ == "__main__":
    main()
