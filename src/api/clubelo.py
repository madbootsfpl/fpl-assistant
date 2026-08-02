"""ClubElo client — the project's second (external) data source (ADR-010).

Fetches team Elo ratings as CSV, parses the English top-division clubs, and maps them
to FPL teams. It is self-contained (its own client, error type, parse/map) so the FPL
side is untouched, and it is *best-effort*: callers handle failure gracefully.
"""

import csv
import datetime
import io

import requests

from src import config

# The 6 clubs whose ClubElo name differs from FPL's `name` (14 others match exactly).
CLUBELO_TO_FPL = {
    "Coventry": "Coventry City",
    "Forest": "Nott'm Forest",
    "Hull": "Hull City",
    "Ipswich": "Ipswich Town",
    "Man United": "Man Utd",
    "Tottenham": "Spurs",
}


class ClubEloError(Exception):
    """Raised when ClubElo cannot be reached or returns an error status."""


class EloClient:
    """A thin wrapper around the ClubElo dated endpoint (returns CSV)."""

    def __init__(
        self,
        base_url: str = config.CLUBELO_BASE_URL,
        timeout: int = config.REQUEST_TIMEOUT,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def get_elo_csv(self, date: str | None = None) -> str:
        """Fetch the Elo ratings CSV for `date` (defaults to today)."""
        date = date or datetime.date.today().isoformat()
        url = f"{self.base_url}/{date}"
        try:
            response = requests.get(
                url, timeout=self.timeout, headers={"User-Agent": config.USER_AGENT}
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            raise ClubEloError(f"Failed to fetch {url}: {exc}") from exc


def parse_english_elo(csv_text: str) -> dict:
    """Parse ClubElo CSV → {club_name: elo} for English top-division clubs only."""
    elo_by_club = {}
    for row in csv.DictReader(io.StringIO(csv_text)):
        if row.get("Country") == "ENG" and row.get("Level") == "1":
            elo_by_club[row["Club"]] = float(row["Elo"])
    return elo_by_club


def map_elo_to_teams(elo_by_club: dict, teams) -> tuple[dict, list]:
    """Map ClubElo club names to FPL team ids.

    `teams` are mappings with `id` and `name` (e.g. bootstrap-static `teams`).
    Returns ({team_id: elo}, unmapped) — the resolved Elo plus any ClubElo club that
    couldn't be placed (so the caller can report it loudly without dropping it silently).
    """
    id_by_name = {t["name"]: t["id"] for t in teams}
    elo_by_team: dict = {}
    unmapped: list = []
    for club, elo in elo_by_club.items():
        fpl_name = CLUBELO_TO_FPL.get(club, club)
        team_id = id_by_name.get(fpl_name)
        if team_id is None:
            unmapped.append(club)
        else:
            elo_by_team[team_id] = elo
    return elo_by_team, unmapped
