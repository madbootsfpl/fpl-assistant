"""Client for the official Fantasy Premier League API.

This layer does exactly one job: make HTTP requests and return the raw JSON
data. It deliberately does not interpret, map or store anything — that belongs
to later layers (parser, storage). Keeping the network isolated here is the
"one-way data flow" rule from docs/03_Architecture/Architecture.md (§3).
"""

import requests

from src import config


class FplApiError(Exception):
    """Raised when the FPL API cannot be reached or returns an error status."""


class FplClient:
    """A thin wrapper around the FPL API endpoints we use.

    The base URL and timeout are injectable so tests can point the client at a
    fake, and so a future config change is a one-liner.
    """

    def __init__(
        self,
        base_url: str = config.FPL_BASE_URL,
        timeout: int = config.REQUEST_TIMEOUT,
    ):
        # Strip a trailing slash so joining with an endpoint path is predictable.
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_json(self, path: str):
        """GET one FPL endpoint and return its parsed JSON.

        Shared by the endpoint methods below so the network logic (timeout,
        User-Agent, error handling) lives in exactly one place. Any network or
        HTTP failure is re-raised as FplApiError, so callers get one clear,
        project-specific error type instead of a raw requests traceback.
        """
        url = self.base_url + path
        try:
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": config.USER_AGENT},
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as exc:
            raise FplApiError(f"Failed to fetch {url}: {exc}") from exc

    def get_bootstrap_static(self) -> dict:
        """Fetch the bootstrap-static payload (players, teams, gameweeks)."""
        return self._get_json(config.BOOTSTRAP_STATIC_PATH)

    def get_fixtures(self) -> list:
        """Fetch the fixtures payload (all matches)."""
        return self._get_json(config.FIXTURES_PATH)
