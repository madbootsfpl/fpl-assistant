"""Community Signals — "most talked about" from Reddit RSS (Sprint 067, ADR-059).

Two parts: a **pure counter** (`community_buzz`) — an RSS feed + the players → a ranked "most mentioned"
list — and a thin **orchestrator** (`community_signals`) that fetches the public `r/FantasyPL` RSS via the
Reddit client and **degrades gracefully** (any 403 / 429 / timeout / parse error → `(None, a message)`,
never a raise). This is **mention frequency (buzz)**, not sentiment; a display lens, never xP.
"""


import xml.etree.ElementTree as ET

from src.analytics.names import build_index, find_mentions
from src.api.reddit import RedditError, RedditRssClient

_ATOM = {"a": "http://www.w3.org/2005/Atom"}
_MIN_NAME = 4        # ignore very short web_names (noise); count whole-word mentions only


def _entries(rss_text: str) -> list:
    """Each Atom entry as `{title, link, text}` (text = lowercased title + content, for matching);
    `[]` on a parse error. The title + link let the UI show *which* posts drive a player's buzz."""
    try:
        root = ET.fromstring(rss_text)
    except ET.ParseError:
        return []
    out = []
    for entry in root.findall("a:entry", _ATOM):
        title = entry.findtext("a:title", default="", namespaces=_ATOM)
        content = entry.findtext("a:content", default="", namespaces=_ATOM)
        link_el = entry.find("a:link", _ATOM)
        out.append({"title": title, "link": link_el.get("href") if link_el is not None else "",
                    "text": f"{title} {content}".lower()})
    return out


def _id(row):
    try:
        return row["id"]
    except (KeyError, IndexError, TypeError):
        return None


def community_buzz(rss_text: str, players, limit: int = 10) -> list:
    """Rank current players by how often they're mentioned in the RSS feed (ADR-059). Pure + empty-safe:
    a bad/empty feed → `[]`. Returns `[{**player, "mentions": n, "posts": [{title, link}]}]`,
    most-mentioned first (n ≥ 1); `posts` are the distinct entries mentioning that player."""
    entries = _entries(rss_text)
    if not entries:
        return []
    # ADR-152 — resolve names properly rather than regexing each `web_name` independently. Doing it the naive
    # way was wrong three ways on live data: 14 web_names are shared (a bare "Palmer" credited BOTH Cole
    # Palmer and a backup keeper, which is why the board listed Palmer twice at 30 mentions), 90 web_names sit
    # inside a *different* player's full name ("James Maddison out for two weeks" credited Reece James), and
    # ambiguity was silently resolved rather than dropped.
    index = build_index(players)
    by_id = {_id(p): dict(p) for p in players}
    hits, posts = {}, {}
    for e in entries:
        for pid, n in find_mentions(e["text"], index).items():
            hits[pid] = hits.get(pid, 0) + n
            posts.setdefault(pid, []).append({"title": e["title"], "link": e["link"]})
    scored = [{**by_id[pid], "mentions": n, "posts": posts[pid]} for pid, n in hits.items() if pid in by_id]
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
