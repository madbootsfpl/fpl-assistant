"""Matching a club's highlights video to a fixture (ADR-347).

⭐⭐ **The whole design is the verification.** There is no identifier to join on — FPL publishes no
highlights URL and `pulse_id` is 0 on all 380 fixtures — so the only thing tying a video to a match is the
**scoreline in its title**. That makes the match deterministic, and it makes the failure mode a *missing*
link rather than a wrong one, which is the only acceptable direction for this feature.
"""

import pytest

from src.api import highlights


@pytest.fixture
def store_with_a_played_match(tmp_path, monkeypatch):
    """A store whose only finished fixture is Chelsea 5-1 Bournemouth, wanting a highlight."""
    import shutil

    from src import config
    from src.storage import Storage

    target = tmp_path / "hl.db"
    shutil.copy(config.SEED_DB_PATH, target)
    target.chmod(0o644)
    monkeypatch.setattr(config, "SEED_DB_PATH", str(target))
    store = Storage(config.SEED_DB_PATH)

    clubs = {t["short_name"]: t["id"] for t in store.get_teams()}
    with store.conn:
        # ⭐ One candidate only, so a test asserting "nothing else was fetched" means what it says.
        store.conn.execute("UPDATE fixtures SET finished = 0, highlights_url = NULL")
        store.conn.execute(
            "UPDATE fixtures SET finished = 1, started = 1, team_h_score = 5, team_a_score = 1, "
            "team_h = ?, team_a = ? WHERE id = (SELECT MIN(id) FROM fixtures)",
            (clubs["CHE"], clubs["BOU"]))
    fixture_id = store.conn.execute("SELECT MIN(id) AS id FROM fixtures").fetchone()["id"]
    yield store, fixture_id
    store.close()

# ── reading a title ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("title, expected", [
    ("Chelsea 5-1 Bournemouth | HIGHLIGHTS | Premier League 2026/27",
     ("Chelsea", 5, 1, "Bournemouth")),
    # ⭐ Clubs write their own titles, so the shape varies and the parser must not assume one house style.
    ("Aston Villa 2-2 Brentford | Yarmoliuk and Ajer net on the road! | Premier League",
     ("Aston Villa", 2, 2, "Brentford")),
    ("Hull City 2-2 Everton | EXTENDED Premier League highlights",
     ("Hull City", 2, 2, "Everton")),
    ("Arsenal 2 - 1 Leeds United | Premier League highlights",
     ("Arsenal", 2, 1, "Leeds United")),
])
def test_a_scoreline_is_read_out_of_the_title(title, expected):
    assert highlights.parse_title(title) == expected


@pytest.mark.parametrize("title", [
    "Should You SELL Bruno For Saka? 🤔 | FPL Podcast 2026/2027",
    "Jorrel Hato Names FUNNIEST Chelsea Player",
    "",
])
def test_a_title_with_no_scoreline_yields_nothing(title):
    """⚠️ Club channels post far more than matches — podcasts, shorts, press conferences. ⭐ *Anything the
    parser cannot read is simply not a match*, which is the safe direction."""
    assert highlights.parse_title(title) is None


# ── accepting a video for a fixture ──────────────────────────────────────────────────────────────

def test_the_right_video_is_found():
    entries = [("Reading 0-2 Cobham Next Gen | HIGHLIGHTS | EFL Trophy", "u0"),
               ("Chelsea 5-1 Bournemouth | HIGHLIGHTS | Premier League", "u1")]
    assert highlights.match_fixture(entries, "Chelsea", "Bournemouth", 5, 1) == "u1"


def test_the_same_two_clubs_with_a_different_score_is_a_different_match():
    """🔴 **The check that makes this safe.** Two clubs meet more than once — a cup tie, a youth fixture,
    last season. ⭐⭐ *A title naming the right clubs with the wrong score is the wrong video behind a
    correct-looking scoreline*, which is worse than showing nothing."""
    entries = [("Chelsea 2-0 Bournemouth | U18 HIGHLIGHTS | 2026/27", "wrong")]
    assert highlights.match_fixture(entries, "Chelsea", "Bournemouth", 5, 1) is None


def test_the_clubs_must_be_the_right_way_round():
    """⚠️ `Leeds 1-0 Arsenal` is not `Arsenal 1-0 Leeds`. ⭐ Home and away decide what the score means."""
    entries = [("Leeds United 2-1 Arsenal | Premier League highlights", "u")]
    assert highlights.match_fixture(entries, "Arsenal", "Leeds", 2, 1) is None


def test_a_club_names_itself_more_fully_than_fpl_does():
    """⭐ FPL says *Leeds*; the club says *Leeds United*. Containment either way, ⚠️ never a fuzzy score —
    which would let *Man City* match *Man Utd* on a bad day."""
    entries = [("Arsenal 2-1 Leeds United | Premier League highlights", "u")]
    assert highlights.match_fixture(entries, "Arsenal", "Leeds", 2, 1) == "u"


def test_man_city_is_not_man_utd():
    entries = [("Liverpool 0-3 Man City | Premier League highlights", "u")]
    assert highlights.match_fixture(entries, "Liverpool", "Man Utd", 0, 3) is None


def test_the_highlights_video_wins_over_another_about_the_same_match():
    """🔴 **Matching the fixture is not matching the video, and the first version only did the first.**
    Arsenal 2-1 Leeds resolved live to *"FRIMMY AND MO GILLIGAN'S PITCHSIDE REACTIONS | Alternative
    Commentary"* — the right match, the right official channel, and not the highlights. ⭐ *A reader who
    taps "Highlights" and gets comedians has been told something untrue by the label.*
    """
    entries = [
        ("FRIMMY AND MO GILLIGAN'S REACTIONS | Alternative Commentary | Arsenal 2-1 Leeds United", "chat"),
        ("Arsenal 2-1 Leeds United | Premier League highlights", "real"),
    ]
    assert highlights.match_fixture(entries, "Arsenal", "Leeds", 2, 1) == "real"


def test_a_highlights_package_that_never_says_the_word_is_still_taken():
    """⚠️ A **preference, not a requirement**: seven of eight real links said *highlights* and the eighth
    did not. ⭐ *Requiring the word would trade a wrong video for a missing one.*"""
    entries = [("Aston Villa 2-2 Brentford | Yarmoliuk and Ajer net on the road! | Premier League", "u")]
    assert highlights.match_fixture(entries, "Aston Villa", "Brentford", 2, 2) == "u"


# ── the allow-list ───────────────────────────────────────────────────────────────────────────────

def test_a_club_not_on_the_allow_list_is_never_fetched_at_all():
    """🔴🔴 **The allow-list is a rights decision, not a lookup table.** ⚠️ Resolving channels by guessing
    handles produced `ANIME VERSE`, `WEW` and a Nottingham Forest **fan** channel — ⭐ *and a fan channel
    is exactly where an unlicensed re-upload lives.*

    ⚠️⚠️ **Asserting the result is empty is not enough, and the mutation proved it.** Removing the
    allow-list check entirely left this passing: an unknown club got a made-up channel id, the fetch
    failed, and `[]` came back for the wrong reason. ⭐ *What must be true is that nothing was requested* —
    so the double records calls and the test reads the record.
    """
    class _Recording:
        def __init__(self): self.urls = []
        def fetch(self, url):
            self.urls.append(url)
            return "<feed/>"

    spy = _Recording()
    assert highlights.videos("NOT-A-CLUB", client=spy) == []
    assert spy.urls == [], f"a club off the list was fetched anyway: {spy.urls}"

    # 📌 The two clubs whose official channel could not be established from here.
    assert "NFO" not in highlights.CHANNELS and "TOT" not in highlights.CHANNELS


def test_every_channel_id_looks_like_one():
    for short, cid in highlights.CHANNELS.items():
        assert cid.startswith("UC") and len(cid) == 24, f"{short} has a malformed channel id"


# ── filling fixtures ─────────────────────────────────────────────────────────────────────────────

class _Feeds:
    """A stand-in for the RSS client that records which feeds were asked for."""

    def __init__(self, by_club): self.by_club, self.asked = by_club, []

    def fetch(self, url):
        cid = url.split("channel_id=")[-1]
        short = next(s for s, c in highlights.CHANNELS.items() if c == cid)
        self.asked.append(short)
        # ⚠️ `<title>` as well as `<media:title>` — a real YouTube feed carries both, and `parse_feed`
        # reads the Atom one. ⭐ *A double that omits what the parser actually uses tests the double.*
        items = "".join(
            f"<entry><title>{t}</title><media:title>{t}</media:title>"
            f'<link rel="alternate" href="{u}"/></entry>'
            for t, u in self.by_club.get(short, []))
        return ('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom" '
                f'xmlns:media="http://search.yahoo.com/mrss/">{items}</feed>')


def test_a_fixture_gets_the_link_and_is_not_asked_about_twice(store_with_a_played_match):
    store, fixture_id = store_with_a_played_match
    feeds = _Feeds({"CHE": [("Chelsea 5-1 Bournemouth | HIGHLIGHTS", "https://youtu.be/x")]})

    assert highlights.fill(store, client=feeds) == 1
    row = store.conn.execute("SELECT highlights_url FROM fixtures WHERE id = ?", (fixture_id,)).fetchone()
    assert row["highlights_url"] == "https://youtu.be/x"

    # ⭐ A found link never changes, so the fixture drops off the list and the feeds go quiet.
    feeds.asked.clear()
    assert highlights.fill(store, client=feeds) == 0
    assert feeds.asked == [], "a fixture that already has a link must not refetch anything"


def test_either_club_can_be_the_one_that_posted(store_with_a_played_match):
    """⭐ Measured: Arsenal did not post its own GW6 match and **Leeds did**. ⚠️ *Asking only the home club
    would have thrown away a third of the coverage.*"""
    store, _ = store_with_a_played_match
    feeds = _Feeds({"BOU": [("Chelsea 5-1 Bournemouth | HIGHLIGHTS", "https://youtu.be/away")]})
    assert highlights.fill(store, client=feeds) == 1


def test_a_recent_fixture_can_have_a_worse_link_replaced(store_with_a_played_match):
    """🔴 **A link that is never re-checked is a wrong link kept for ever.** Live, Arsenal 2-1 Leeds
    resolved to *"Alternative Commentary"* — right match, right channel, wrong video — and with the
    original rule nothing would ever have looked again. ⭐ A short window lets the real package replace
    it, then closes."""
    store, fixture_id = store_with_a_played_match
    from datetime import UTC, datetime
    with store.conn:
        store.conn.execute("UPDATE fixtures SET highlights_url = ?, kickoff_time = ? WHERE id = ?",
                           ("https://youtu.be/reaction", datetime.now(UTC).isoformat(), fixture_id))

    feeds = _Feeds({"CHE": [("Chelsea 5-1 Bournemouth | HIGHLIGHTS", "https://youtu.be/real")]})
    assert highlights.fill(store, client=feeds) == 1
    row = store.conn.execute("SELECT highlights_url FROM fixtures WHERE id = ?", (fixture_id,)).fetchone()
    assert row["highlights_url"] == "https://youtu.be/real"

    # ⭐ And it settles: the same video found again is not a change, so the count stops moving.
    assert highlights.fill(store, client=feeds) == 0


def test_an_old_fixture_is_left_alone_once_it_has_a_link(store_with_a_played_match):
    """⚠️ The window closes. ⭐ *Re-checking every played fixture for ever would fetch twenty feeds a tick
    to change nothing.*"""
    store, fixture_id = store_with_a_played_match
    with store.conn:
        store.conn.execute("UPDATE fixtures SET highlights_url = ?, kickoff_time = ? WHERE id = ?",
                           ("https://youtu.be/old", "2026-08-01T14:00:00Z", fixture_id))

    feeds = _Feeds({"CHE": [("Chelsea 5-1 Bournemouth | HIGHLIGHTS", "https://youtu.be/new")]})
    assert highlights.fill(store, client=feeds) == 0
    assert feeds.asked == [], "an old fixture with a link must not be looked up again"


def test_a_feed_that_fails_leaves_the_fixture_waiting(store_with_a_played_match):
    """⚠️ Best-effort throughout: somebody else's outage must not fail a pipeline tick."""
    store, fixture_id = store_with_a_played_match

    class _Broken:
        def fetch(self, url): raise RuntimeError("youtube is down")

    assert highlights.fill(store, client=_Broken()) == 0
    row = store.conn.execute("SELECT highlights_url FROM fixtures WHERE id = ?", (fixture_id,)).fetchone()
    assert row["highlights_url"] is None
