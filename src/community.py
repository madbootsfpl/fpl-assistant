"""Community Signals — "most talked about" from Reddit RSS (Sprint 067, ADR-059).

Two parts: a **pure counter** (`community_buzz`) — an RSS feed + the players → a ranked "most mentioned"
list — and a thin **orchestrator** (`community_signals`) that fetches the public `r/FantasyPL` RSS via the
Reddit client and **degrades gracefully** (any 403 / 429 / timeout / parse error → `(None, a message)`,
never a raise). This is **mention frequency (buzz)**, not sentiment; a display lens, never xP.
"""

import re
import xml.etree.ElementTree as ET

from src.api.reddit import RedditError, RedditRssClient

_ATOM = {"a": "http://www.w3.org/2005/Atom"}
_MIN_NAME = 4        # ignore very short web_names (noise); count whole-word mentions only


def _feed_text(rss_text: str) -> str:
    """The lowercased title + content text of every entry in an Atom RSS feed (empty on a parse error)."""
    try:
        root = ET.fromstring(rss_text)
    except ET.ParseError:
        return ""
    parts = []
    for entry in root.findall("a:entry", _ATOM):
        parts.append(entry.findtext("a:title", default="", namespaces=_ATOM))
        parts.append(entry.findtext("a:content", default="", namespaces=_ATOM))
    return " ".join(parts).lower()


def community_buzz(rss_text: str, players, limit: int = 10) -> list:
    """Rank current players by how often they're mentioned in the RSS feed (ADR-059). Pure + empty-safe:
    a bad/empty feed → `[]`. Returns `[{**player, "mentions": n}]`, most-mentioned first (n ≥ 1)."""
    text = _feed_text(rss_text)
    if not text:
        return []
    scored = []
    for p in players:
        row = dict(p)        # players may be sqlite3.Row (no .get) — normalise once
        name = str(row.get("web_name") or "")
        if len(name) < _MIN_NAME:
            continue
        hits = len(re.findall(rf"\b{re.escape(name.lower())}\b", text))
        if hits:
            scored.append({**row, "mentions": hits})
    scored.sort(key=lambda r: r["mentions"], reverse=True)
    return scored[:limit]


def community_signals(players, limit: int = 10, *, client=None) -> tuple[list | None, str]:
    """Fetch r/FantasyPL RSS → the "most talked about" buzz list, or `(None, message)` on any failure
    (ADR-059 — degrade gracefully; the cloud IP may be blocked). `client` is injectable for tests."""
    client = client or RedditRssClient()
    try:
        rss = client.get_subreddit_rss()
    except RedditError:
        return None, "Community buzz is unavailable right now (Reddit didn't respond)."
    rows = community_buzz(rss, players, limit=limit)
    if not rows:
        return [], "No player mentions in the latest r/FantasyPL posts."
    return rows, f"Most talked about on r/FantasyPL — {len(rows)} players mentioned."
