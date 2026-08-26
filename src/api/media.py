"""Media headlines from public RSS/Atom feeds (Sprint 115, ADR-093; moved to core by ADR-151).

**Why it moved.** This lived in `web_streamlit/` and had nothing web-specific in it — `config` plus
`api.feeds`, no Streamlit anywhere. That was invisible until refresh-time headline extraction needed the same
feeds and `test_core_never_imports_a_web_edge` failed: the core cannot import an edge (ADR-050/052), and the
guard was right — the function was misfiled, not the import.

Aggregates the configured public RSS/Atom feeds into `{source: [headlines]}`, **per-feed best-effort**: one
feed failing (403 / timeout / junk) is skipped, the rest still show. Display-only (never xP); the page caches
+ button-gates the call so a slow/blocked feed never delays load.
"""

from src import config
from src.api.feeds import FeedError, MediaFeedsClient, parse_feed


def media_headlines(feeds=None, *, limit_per_feed: int = config.MEDIA_FEED_LIMIT, client=None) -> dict:
    """`{source_name: [{title, link, published}, …]}` for the configured feeds. A feed that errors or parses to
    nothing is simply omitted. `client` is injectable for tests (no live network)."""
    feeds = config.MEDIA_FEEDS if feeds is None else feeds
    client = client or MediaFeedsClient()
    out = {}
    for feed in feeds:
        try:
            items = parse_feed(client.fetch(feed["url"]), limit=limit_per_feed)
        except FeedError:
            continue                          # skip this source; the others still show
        if items:
            out[feed["name"]] = items
    return out
