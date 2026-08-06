"""Client for the official Fantasy Premier League API.

This layer does exactly one job: make HTTP requests and return the raw JSON
data. It deliberately does not interpret, map or store anything — that belongs
to later layers (parser, storage). Keeping the network isolated here is the
"one-way data flow" rule from docs/03_Architecture/Architecture.md (§3).
"""

import time

import requests

from src import config
from src.api.retry import is_transient, with_retry


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
        retries: int = 2,          # required source: retry hard before giving up (ADR-021)
        backoff: float = 0.5,
        sleep=time.sleep,
    ):
        # Strip a trailing slash so joining with an endpoint path is predictable.
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.sleep = sleep

    def _get_json(self, path: str):
        """GET one FPL endpoint and return its parsed JSON.

        Shared by the endpoint methods below so the network logic (timeout,
        User-Agent, retry, error handling) lives in exactly one place. FPL is the
        *required* source, so a transient failure is retried (ADR-021); on exhaustion
        any network or HTTP failure is re-raised as FplApiError — fatal, since there is
        no graceful degradation for FPL.
        """
        url = self.base_url + path

        def fetch():
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": config.USER_AGENT},
            )
            response.raise_for_status()
            return response.json()

        try:
            return with_retry(
                fetch, retries=self.retries, backoff=self.backoff, sleep=self.sleep
            )
        except requests.RequestException as exc:
            attempts = self.retries + 1 if is_transient(exc) else 1
            raise FplApiError(
                f"Failed to fetch {url} after {attempts} attempt(s): {exc}"
            ) from exc

    def get_bootstrap_static(self) -> dict:
        """Fetch the bootstrap-static payload (players, teams, gameweeks)."""
        return self._get_json(config.BOOTSTRAP_STATIC_PATH)

    def get_fixtures(self) -> list:
        """Fetch the fixtures payload (all matches)."""
        return self._get_json(config.FIXTURES_PATH)

    def get_entry(self, entry_id: int) -> dict:
        """A manager's public entry metadata (name, `current_event`, overall rank) — Sprint 064/ADR-058."""
        return self._get_json(config.ENTRY_PATH.format(entry_id))

    def get_entry_picks(self, entry_id: int, gameweek: int) -> dict:
        """A manager's squad picks for `gameweek` (public **after** that GW's deadline; 404 before)."""
        return self._get_json(config.ENTRY_PICKS_PATH.format(entry_id, gameweek))

    def get_element_summary(self, element_id: int) -> dict:
        """Fetch one player's element-summary (ADR-027).

        Contains `fixtures`, this-season per-GW `history`, and `history_past`
        (past-season summaries). One call per player — the caller throttles a bulk
        backfill (see ingest.backfill_history).
        """
        return self._get_json(config.ELEMENT_SUMMARY_PATH.format(element_id))
