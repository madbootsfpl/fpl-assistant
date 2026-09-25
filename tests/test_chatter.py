"""Chatter — r/FantasyPL mention counts, on the phone at last (ADR-300, built on ADR-059).

⭐⭐⭐ **Almost none of this is new code, and that is the point of the ADR.** `community_signals` has
counted whole-word mentions against the squad index since Sprint 067 — resolving shared `web_name`s
properly (ADR-152) and degrading on any 403 / 429 / timeout — and was reachable only from Streamlit.

These pin what the *service* adds: the player shape, the owned flag, the caps, the cache, and the promise
that a dark Reddit is an empty list rather than an error.
"""

from __future__ import annotations

import pytest

from src.service import ChatterRequest, chatter
from src.service import answers as answers_mod


def feed(a: str, b: str, threads: int = 5) -> str:
    """A feed where `a` appears in **many** threads and `b` in one.

    ⚠️⚠️ **The first version had two entries, and two mutants survived on that alone** — the post cap and
    the wide fetch were both unreachable, because a fixture that never produces enough cannot show a cap
    being applied. ⭐ *A branch the test data cannot reach is not being tested*, however many assertions
    point at it.
    """
    entries = [
        f"<entry><title>{a} thread {n}</title><content>{a} {a}</content>"
        f'<link href="https://reddit.com/{n}"/></entry>'
        for n in range(threads)
    ]
    entries.append(
        f"<entry><title>Captain {b}?</title><content>{b}</content>"
        f'<link href="https://reddit.com/b"/></entry>'
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<feed xmlns="http://www.w3.org/2005/Atom">' + "".join(entries) + "</feed>"
    )


class FakeReddit:
    """The RSS client, with a feed we control — or a failure."""

    def __init__(self, xml: str | None = None, raises: bool = False):
        self._xml, self._raises = xml, raises
        self.calls = 0

    def get_subreddit_rss(self) -> str:
        self.calls += 1
        if self._raises:
            from src.api.reddit import RedditError

            raise RedditError("blocked")
        return self._xml


@pytest.fixture(autouse=True)
def _cold_cache():
    """⚠️ Every test starts cold. ⭐ *A cache shared between tests is a test that passes because of the
    one before it* — and this module's cache is deliberately global, so it must be reset explicitly."""
    answers_mod._CHATTER.update(rows=None, note="", until=0.0)
    yield
    answers_mod._CHATTER.update(rows=None, note="", until=0.0)


@pytest.fixture(scope="module")
def two_names():
    """Two real `web_name`s from the committed fixture, long enough to be counted (`_MIN_NAME`)."""
    from src.storage import Storage

    store = Storage()
    try:
        names = [p["web_name"] for p in store.get_players()
                 if len(p["web_name"]) > 5 and p["web_name"].isalpha()]
    finally:
        store.close()
    return names[0], names[1]


def feed_for(two_names, threads: int = 5) -> str:
    a, b = two_names
    return feed(a, b, threads)


def test_the_most_mentioned_player_comes_first(two_names):
    a, _b = two_names
    out = chatter(ChatterRequest(), client=FakeReddit(feed_for(two_names)))

    assert out["rows"], out["note"]
    assert out["rows"][0]["player"]["web_name"] == a
    assert out["rows"][0]["mentions"] > out["rows"][-1]["mentions"]


def test_every_row_is_the_same_player_shape_as_every_other_answer(two_names):
    """⚠️ *A flattened player here would be a second player shape* — `test_player_shape.py` refused one
    within minutes the last time, and it was right to."""
    out = chatter(ChatterRequest(), client=FakeReddit(feed_for(two_names)))

    for row in out["rows"]:
        assert set(row) == {"player", "photo", "mentions", "owned", "posts"}
        assert row["player"]["web_name"] and row["player"]["position"]
        # ⭐ Our own mugshot, not a thumbnail from the feed.
        assert row["photo"].startswith("http")


def test_the_ids_flag_rows_and_never_narrow_the_sweep(two_names):
    """⭐ The contract the global signals scope already uses: *the subreddit talks about whoever it talks
    about.* ⚠️ Filtering here would make a tab called "what is everyone talking about" answer a different
    question."""
    a, _b = two_names
    everyone = chatter(ChatterRequest(), client=FakeReddit(feed_for(two_names)))
    answers_mod._CHATTER.update(rows=None, until=0.0)

    owned_id = next(r["player"]["id"] for r in everyone["rows"]
                    if r["player"]["web_name"] == a)
    flagged = chatter(ChatterRequest(player_ids=[owned_id]),
                      client=FakeReddit(feed_for(two_names)))

    assert len(flagged["rows"]) == len(everyone["rows"]), "the ids filtered the sweep"
    assert [r["owned"] for r in flagged["rows"]].count(True) == 1
    assert next(r for r in flagged["rows"] if r["owned"])["player"]["id"] == owned_id


def test_a_dark_reddit_is_an_empty_list_and_a_sentence(two_names):
    """⚠️⚠️ **Reddit blocks datacentre IPs and rate-limits.** ⭐ *A tab that can go dark must have
    something true to draw when it does* — and it must not raise, because it sits beside signals that are
    working."""
    out = chatter(ChatterRequest(), client=FakeReddit(raises=True))

    assert out["rows"] == []
    assert "unavailable" in out["note"].lower()
    assert out["measures"] == "mentions"


def test_a_failure_is_not_cached(two_names):
    """⚠️⚠️ **Caching an outage makes a blip into a symptom.** A blocked request must not blank the tab
    for the whole TTL — the next caller tries again."""
    dark = FakeReddit(raises=True)
    assert chatter(ChatterRequest(), client=dark)["rows"] == []

    live = FakeReddit(feed_for(two_names))
    assert chatter(ChatterRequest(), client=live)["rows"], "the failure was cached"
    assert live.calls == 1


def test_a_second_caller_within_the_window_does_not_refetch(two_names):
    """⭐⭐ **`RedditRssClient`'s own docstring says cache lives at the caller**, and the first version of
    this had none: two taps a minute apart were two fetches, and the second came back *"Reddit didn't
    respond."* ⚠️ *A tab that fails when you open it twice is a tab people conclude is broken.*"""
    live = FakeReddit(feed_for(two_names))
    first = chatter(ChatterRequest(limit=3), client=live)
    second = chatter(ChatterRequest(limit=3), client=live)

    assert live.calls == 1, f"fetched {live.calls} times"
    assert [r["player"]["id"] for r in first["rows"]] == \
           [r["player"]["id"] for r in second["rows"]]


def test_one_fetch_serves_every_limit(two_names):
    """⭐ The cache is keyed on **nothing**: `limit` slices a wide fetch rather than changing it.

    ⚠️⚠️ **Narrow first, and the order is the test.** Asking wide first filled the cache with every row,
    so a fetch that obeyed the caller's `limit` passed anyway — ⭐ *a cache test that warms the cache with
    the generous case cannot see a stingy fetch.*
    """
    live = FakeReddit(feed_for(two_names))
    narrow = chatter(ChatterRequest(limit=1), client=live)
    wide = chatter(ChatterRequest(limit=25), client=live)

    assert live.calls == 1
    assert len(narrow["rows"]) == 1
    assert len(wide["rows"]) == 2, (
        f"the cached fetch holds {len(wide['rows'])} rows — it was narrowed to the first caller's "
        f"limit, so everyone after them sees a shorter list than they asked for"
    )
    assert narrow["rows"][0]["player"]["id"] == wide["rows"][0]["player"]["id"]


def test_the_posts_behind_a_count_are_carried_but_capped(two_names):
    """⭐ The count is the number; the posts are the evidence for it. ⚠️ Capped at three — *a row that
    scrolls is a row that has stopped being a summary.*"""
    out = chatter(ChatterRequest(), client=FakeReddit(feed_for(two_names)))

    top = out["rows"][0]
    assert top["posts"], "a mention with no post behind it cannot be checked"
    # ⭐ The feed puts him in **five** threads, so three is a cap being applied rather than a coincidence
    # of the fixture — ⚠️ which is exactly what the two-entry version could not tell.
    assert top["mentions"] >= 10, "the fixture is too small to show a cap"
    assert len(top["posts"]) == 3, f"{len(top['posts'])} posts — the cap is not being applied"
    for post in top["posts"]:
        assert post["title"] and post["link"].startswith("http")


@pytest.mark.parametrize("limit", [0, 26, -1])
def test_an_absurd_limit_is_refused(limit):
    """⚠️ A display list, not a dataset."""
    with pytest.raises(ValueError):
        chatter(ChatterRequest(limit=limit), client=FakeReddit("<feed/>"))


def test_the_answer_says_what_it_measures(two_names):
    """⚠️⚠️ **Mention frequency, not sentiment** — ADR-059's framing, carried onto the phone. ⭐ *A count
    of names is not an opinion about players*, and a screen that blurs the two is inventing analysis it
    did not do."""
    out = chatter(ChatterRequest(), client=FakeReddit(feed_for(two_names)))

    assert out["measures"] == "mentions"
    assert "talked about" in out["note"]
