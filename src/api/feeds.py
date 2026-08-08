"""Media-headlines feeds — a generic best-effort RSS/Atom client + parser (Sprint 115, ADR-093).

The `RedditRssClient` shape (ADR-059): our User-Agent, a tight timeout, retry-once, raise on failure — the
caller caches + button-gates + degrades. A **display lens** (never xP). `parse_feed` handles **both** RSS
(`<item>`) and Atom (`<entry>`, e.g. YouTube) with the stdlib — **no new dependency** — and is empty-safe on
junk (a bad feed degrades, never crashes).
"""

import time
import xml.etree.ElementTree as ET

import requests

from src import config
from src.api.retry import with_retry

_ATOM = "{http://www.w3.org/2005/Atom}"


class FeedError(Exception):
    """Raised when a media feed can't be reached or returns an error status."""


class MediaFeedsClient:
    """A thin best-effort wrapper over a public RSS/Atom URL (returns the raw XML text)."""

    def __init__(self, timeout: int = config.MEDIA_FEED_TIMEOUT, retries: int = 1, backoff: float = 0.5,
                 sleep=time.sleep):
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self.sleep = sleep

    def fetch(self, url: str) -> str:
        """Fetch a feed's XML (best-effort). A transient failure retries once (ADR-020); anything else raises
        `FeedError` so the caller degrades (skip this feed)."""
        def _get():
            resp = requests.get(url, headers={"User-Agent": config.USER_AGENT}, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text

        try:
            return with_retry(_get, retries=self.retries, backoff=self.backoff, sleep=self.sleep)
        except requests.RequestException as exc:
            raise FeedError(f"could not fetch feed {url}: {exc}") from exc


def _text(el) -> str:
    return (el.text or "").strip() if el is not None else ""


def _first(entry, rss_tag: str, atom_tag: str) -> str:
    """The RSS child (`rss_tag`) else the Atom child (`atom_tag`) text, or ''."""
    return _text(entry.find(rss_tag)) or _text(entry.find(f"{_ATOM}{atom_tag}"))


def _link(entry) -> str:
    """The item link — RSS `<link>text` or Atom `<link href=…>` (prefer rel='alternate')."""
    rss = _text(entry.find("link"))
    if rss:
        return rss
    links = entry.findall(f"{_ATOM}link")
    for a in links:                                    # Atom: an alternate link is the human page
        if a.get("rel", "alternate") == "alternate" and a.get("href"):
            return a.get("href")
    return links[0].get("href", "") if links else ""


def parse_feed(xml: str, limit: int = config.MEDIA_FEED_LIMIT) -> list:
    """Parse an RSS/Atom feed → up to `limit` `{title, link, published}` dicts, newest-first as the feed gives
    them. Handles RSS `<item>` and Atom `<entry>`; empty-safe (bad XML / no items → `[]`)."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return []
    entries = root.findall(".//item") or root.findall(f".//{_ATOM}entry")
    out = []
    for e in entries[:limit]:
        title = _first(e, "title", "title")
        link = _link(e)
        published = _first(e, "pubDate", "published") or _first(e, "pubDate", "updated")
        if title and link:                             # skip a malformed entry, keep the rest
            out.append({"title": title, "link": link, "published": published})
    return out
