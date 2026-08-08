"""Tests for Community Signals — Reddit RSS buzz (Sprint 067, ADR-059).

`community_buzz` is a pure counter (RSS text → most-mentioned players); `community_signals` orchestrates the
fetch and **degrades gracefully** — a failing client → `(None, message)`, never a raise. The Reddit client
is faked, so no network.
"""

from src.api.reddit import RedditError
from src.community import community_buzz, community_signals

_RSS = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><link href="https://reddit.test/haaland"/><title>Haaland or Isak this week?</title><content>captain Haaland</content></entry>
  <entry><link href="https://reddit.test/saka"/><title>Rate my team - is Saka worth it</title><content>Saka vs Haaland</content></entry>
</feed>"""

_PLAYERS = [{"id": 1, "web_name": "Haaland"}, {"id": 2, "web_name": "Isak"},
            {"id": 3, "web_name": "Saka"}, {"id": 4, "web_name": "Zzz"}]   # "Zzz" never mentioned


def test_community_buzz_ranks_by_mentions():
    buzz = community_buzz(_RSS, _PLAYERS, limit=5)
    assert [(r["web_name"], r["mentions"]) for r in buzz] == [("Haaland", 3), ("Saka", 2), ("Isak", 1)]
    assert all(r["web_name"] != "Zzz" for r in buzz)          # unmentioned players are dropped


def test_community_buzz_captures_the_posts():
    # each ranked player carries the distinct posts (title + link) that mention them
    buzz = community_buzz(_RSS, _PLAYERS, limit=5)
    haaland = next(r for r in buzz if r["web_name"] == "Haaland")
    assert len(haaland["posts"]) == 2                     # mentioned across both posts
    assert {p["link"] for p in haaland["posts"]} == {"https://reddit.test/haaland",
                                                      "https://reddit.test/saka"}
    assert all(p["title"] for p in haaland["posts"])      # each post carries its title
    isak = next(r for r in buzz if r["web_name"] == "Isak")
    assert [p["link"] for p in isak["posts"]] == ["https://reddit.test/haaland"]


def test_community_buzz_accepts_sqlite_rows():
    # the page passes store.get_players() → sqlite3.Row (no .get); community_buzz must handle it
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE p (id INTEGER, web_name TEXT)")
    conn.executemany("INSERT INTO p VALUES (?, ?)", [(1, "Haaland"), (2, "Saka")])
    rows = conn.execute("SELECT * FROM p").fetchall()
    buzz = community_buzz(_RSS, rows, limit=5)
    assert [(r["web_name"], r["mentions"]) for r in buzz] == [("Haaland", 3), ("Saka", 2)]


def test_community_buzz_counts_every_mentioning_post():
    # US-232 (the tester's bug): a player mentioned across N distinct posts counts N — not capped at 1
    rss = ('<feed xmlns="http://www.w3.org/2005/Atom">'
           + "".join(f'<entry><link href="https://r.test/{i}"/><title>Salah watch #{i}</title></entry>'
                     for i in range(4))
           + "</feed>")
    buzz = community_buzz(rss, [{"id": 1, "web_name": "Salah"}], limit=5)
    assert buzz[0]["mentions"] == 4 and len(buzz[0]["posts"]) == 4


def test_reddit_client_requests_the_configured_post_limit(monkeypatch):
    # US-232 (ADR-076): the client asks Reddit for ~100 posts (a bigger sample → meaningful counts)
    from src.api import reddit

    captured = {}

    class _Resp:
        text = "<feed/>"

        def raise_for_status(self):
            pass

    def _fake_get(url, **kw):
        captured["url"] = url
        return _Resp()

    monkeypatch.setattr(reddit.requests, "get", _fake_get)
    reddit.RedditRssClient().get_subreddit_rss()
    assert captured["url"] == "https://www.reddit.com/r/FantasyPL/.rss?limit=100"


def test_reddit_client_top_weekly_hits_the_top_week_url(monkeypatch):
    # US-292: the "top discussions this week" list fetches the top?t=week RSS variant.
    from src.api import reddit

    captured = {}

    class _Resp:
        text = "<feed/>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(reddit.requests, "get", lambda url, **kw: (captured.update(url=url) or _Resp()))
    reddit.RedditRssClient().get_top_weekly()
    assert captured["url"] == "https://www.reddit.com/r/FantasyPL/top/.rss?t=week"


def test_community_buzz_is_empty_safe():
    assert community_buzz("not xml at all", _PLAYERS) == []   # a parse error → [], no crash
    assert community_buzz("", _PLAYERS) == []
    assert community_buzz(_RSS, []) == []


def test_community_buzz_ignores_very_short_names():
    # web_names under 4 chars are skipped (noise) even if present in the text
    rss = '<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Cba is great</title></entry></feed>'
    assert community_buzz(rss, [{"id": 1, "web_name": "Cba"}]) == []


class _Boom:
    def get_subreddit_rss(self):
        raise RedditError("403")


class _Ok:
    def get_subreddit_rss(self):
        return _RSS


def test_community_signals_degrades_on_failure():
    rows, msg = community_signals(_PLAYERS, client=_Boom())
    assert rows is None and "unavailable" in msg              # a clear message, never a raise


def test_community_signals_returns_the_buzz_on_success():
    rows, msg = community_signals(_PLAYERS, client=_Ok())
    assert rows[0]["web_name"] == "Haaland" and "talked about" in msg
