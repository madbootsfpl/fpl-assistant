"""Reddit RSS client — Community Signals' external source (ADR-059).

Fetches a subreddit's **public RSS** feed (no OAuth, no secret — the `.json` API 403s). Self-contained (its
own client + error type) so the FPL side is untouched, and **best-effort**: the caller degrades on failure
(a 403 / 429 / timeout → treat as "unavailable"). Cache + rate-limit-respect live at the caller (ADR-059).
"""

import time

import requests

from src import config
from src.api.retry import is_transient, with_retry


class RedditError(Exception):
    """Raised when the Reddit RSS feed can't be reached or returns an error status."""


class RedditRssClient:
    """A thin wrapper around a subreddit's public RSS endpoint (returns Atom XML)."""

    def __init__(
        self,
        url_template: str = config.REDDIT_RSS_URL,
        timeout: int = config.REDDIT_TIMEOUT,     # best-effort: a tight 5s budget (ADR-021)
        retries: int = 1,                         # fail fast — 2 attempts, then degrade
        backoff: float = 0.5,
        sleep=time.sleep,
    ):
        self.url_template = url_template
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.sleep = sleep

    def get_subreddit_rss(self, subreddit: str = config.REDDIT_SUBREDDIT,
                          *, limit: int = config.REDDIT_RSS_LIMIT) -> str:
        """Fetch a subreddit's RSS (Atom XML), the latest `limit` posts (Reddit's RSS max is 100 — a bigger
        sample makes the buzz count meaningful, ADR-076). Transient failures retry once (ADR-020); a
        permanent one (403/404/429) fails fast. On final failure raises `RedditError`, so the caller
        degrades."""
        url = f"{self.url_template.format(subreddit)}?limit={limit}"

        def fetch() -> str:
            response = requests.get(
                url, timeout=self.timeout, headers={"User-Agent": config.USER_AGENT}
            )
            response.raise_for_status()
            return response.text

        try:
            return with_retry(fetch, retries=self.retries, backoff=self.backoff, sleep=self.sleep)
        except requests.RequestException as exc:
            attempts = self.retries + 1 if is_transient(exc) else 1
            raise RedditError(f"Failed to fetch {url} after {attempts} attempt(s): {exc}") from exc
