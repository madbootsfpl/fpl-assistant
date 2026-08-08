"""Tests for the media-headlines feeds (Sprint 115, ADR-093).

Pure parsing + per-feed degrade — **no live network** (fixtures + a fake client). A display lens (never xP).
"""

from src.api.feeds import FeedError, parse_feed
from src.web_streamlit.media import media_headlines

_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>Fantasy Football Scout</title>
  <item><title>Scout: who to captain in GW1</title><link>https://ffs.example/captain</link>
        <pubDate>Fri, 15 Aug 2026 10:00:00 GMT</pubDate></item>
  <item><title>BBC-style: injury latest</title><link>https://ffs.example/injury</link>
        <pubDate>Fri, 15 Aug 2026 09:00:00 GMT</pubDate></item>
  <item><title>No link here</title></item>
</channel></rss>"""

_ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>YouTube — a creator</title>
  <entry><title>FPL GW1 team reveal</title>
         <link rel="alternate" href="https://youtube.example/v1"/>
         <published>2026-08-15T10:00:00+00:00</published></entry>
</feed>"""


def test_parse_feed_handles_rss_items():
    items = parse_feed(_RSS, limit=5)
    assert len(items) == 2                                       # the link-less item is skipped
    assert items[0] == {"title": "Scout: who to captain in GW1", "link": "https://ffs.example/captain",
                        "published": "Fri, 15 Aug 2026 10:00:00 GMT"}


def test_parse_feed_handles_atom_entries():
    items = parse_feed(_ATOM)
    assert items == [{"title": "FPL GW1 team reveal", "link": "https://youtube.example/v1",
                      "published": "2026-08-15T10:00:00+00:00"}]                # Atom <link href> + <published>


def test_parse_feed_respects_the_limit_and_is_empty_safe():
    assert len(parse_feed(_RSS, limit=1)) == 1
    assert parse_feed("<not xml") == [] and parse_feed("") == []               # junk / empty → no crash
    assert parse_feed("<rss><channel></channel></rss>") == []                  # no items → []


class _FakeClient:
    """A media client returning canned XML per URL, or raising a value that's an Exception."""
    def __init__(self, mapping):
        self.mapping = mapping

    def fetch(self, url):
        value = self.mapping[url]
        if isinstance(value, Exception):
            raise value
        return value


def test_media_headlines_skips_a_failing_or_empty_feed():
    feeds = [{"name": "Good", "url": "g"}, {"name": "Down", "url": "b"}, {"name": "Empty", "url": "e"}]
    client = _FakeClient({"g": _RSS, "b": FeedError("boom"), "e": "<rss><channel></channel></rss>"})
    out = media_headlines(feeds, limit_per_feed=5, client=client)
    assert "Good" in out and out["Good"][0]["title"] == "Scout: who to captain in GW1"
    assert "Down" not in out and "Empty" not in out            # a failed feed + an empty feed are omitted


def test_media_headlines_all_failing_returns_empty():
    feeds = [{"name": "A", "url": "a"}, {"name": "B", "url": "b"}]
    client = _FakeClient({"a": FeedError("x"), "b": FeedError("y")})
    assert media_headlines(feeds, client=client) == {}          # → the page shows the degrade note
