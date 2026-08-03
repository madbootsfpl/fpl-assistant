"""Retry-with-backoff for best-effort HTTP fetches (ADR-020).

Source-agnostic: wrap any callable that performs a `requests` GET, and transient failures
(gateway errors, timeouts, dropped connections) are retried with exponential backoff before
propagating. Permanent failures (4xx) raise immediately — a retry wouldn't help. The `sleep`
callable is injectable so tests run instantly and can assert the backoff.
"""

import time

import requests

# Gateway / unavailable errors — transient, worth a retry (ClubElo's 502 lives here).
RETRYABLE_STATUS = frozenset({502, 503, 504})


def is_transient(exc: Exception) -> bool:
    """True if `exc` is worth retrying (a momentary blip), False if permanent."""
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code in RETRYABLE_STATUS
    return False


def with_retry(fetch, *, retries: int = 2, backoff: float = 0.5, sleep=time.sleep):
    """Call `fetch()`, retrying transient failures with exponential backoff.

    Makes up to `retries + 1` attempts. A transient error backs off (`backoff · 2**attempt`)
    and retries; a permanent error — or the last transient one — propagates unchanged for the
    caller to wrap. Returns `fetch()`'s result on success.
    """
    for attempt in range(retries + 1):
        try:
            return fetch()
        except requests.RequestException as exc:
            if is_transient(exc) and attempt < retries:
                sleep(backoff * (2 ** attempt))
                continue
            raise
