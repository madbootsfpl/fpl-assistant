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


def test_every_channel_id_looks_like_one():
    for short, cid in highlights.CHANNELS.items():
        assert cid.startswith("UC") and len(cid) == 24, f"{short} has a malformed channel id"


def test_no_two_clubs_share_a_channel():
    """⚠️ A copy-paste between two rows of a hand-written dict is silent: both clubs would resolve, both
    would parse, and one of them would quietly answer with the other's matches. ⭐ *The score check cannot
    catch it, because the wrong club's feed is a perfectly valid feed.*"""
    seen = {}
    for short, cid in highlights.CHANNELS.items():
        assert cid not in seen, f"{short} and {seen[cid]} share channel id {cid}"
        seen[cid] = short


def test_all_twenty_clubs_are_covered():
    """📌 Nott'm Forest and Spurs were the last two missing, and the reason was **this machine**:
    youtube.com/@handle answers the EU consent wall from Ireland, so the handle resolver saw no channel
    for anyone. ⭐ *A blocked lookup reads exactly like an absent one* — the note recording it said "no
    official channel established", which is a claim about the clubs that the evidence never supported.

    ⚠️ Twenty is the size of the Premier League, so a missing club is a club whose matches silently get no
    link rather than an error anybody sees.
    """
    assert len(highlights.CHANNELS) == 20, sorted(highlights.CHANNELS)


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


# ── the club's own spelling of itself (ADR-352) ──────────────────────────────────────────────────

def test_forest_matches_the_name_forest_uses():
    """🔴 **A right channel behind a name that cannot match is worth nothing.** FPL writes *Nott'm
    Forest*; the club writes *Nottingham Forest*. ⚠️ Containment fails **both** ways, so every Forest
    fixture resolved to no link even with the official channel on the list — ⭐ *and "no link" is also
    what a missing channel looks like, which is where this hid.*"""
    entries = [("Crystal Palace 3-1 Nottingham Forest | Premier League Highlights 📺", "u")]
    assert highlights.match_fixture(entries, "Crystal Palace", "Nott'm Forest", 3, 1) == "u"


def test_the_alias_does_not_loosen_anything_else():
    """⚠️⚠️ **The temptation was a fuzzy ratio, and this is why it was refused.** Across all twenty feeds
    the spellings that match no FPL club are *Fenerbahce*, *LASK*, *PSG*, *Lille*, *Cobham Next Gen* —
    European and academy opponents that **must** keep failing. ⭐ *A matcher loosened until Forest fits
    is a matcher that fits PSG too.*"""
    assert highlights._looks_like("Nottingham Forest", "Nott'm Forest")
    for other in ["PSG", "Fenerbahce", "LASK", "Lille", "Cobham Next Gen", "Exeter City"]:
        assert not highlights._looks_like(other, "Nott'm Forest")
    # ⭐ The pair the original comment named, still safe.
    assert not highlights._looks_like("Man City", "Man Utd")


def test_an_archive_match_is_never_the_link_even_though_it_says_highlights():
    """🔴🔴 **The one case the score check cannot see.** Forest's archive series is branded *Classic
    Highlights* and carries a real scoreline, so it parses, names two Premier League clubs, and says
    *highlights* — ⚠️ *it would be taken by the preferred branch* the moment a current fixture ends 0-3
    at Selhurst. ⭐ The score is right and the match is twelve years old."""
    archive = ("Special Radosław Majewski Hat-Trick! 🪄 | Crystal Palace 0-3 Nottingham Forest | "
               "Classic Highlights 🎬")
    assert highlights.parse_title(archive), "the premise: this really does parse"
    assert highlights.match_fixture([(archive, "old")], "Crystal Palace", "Nott'm Forest", 0, 3) is None

    # ⭐ And it does not block the real one sitting beside it in the same feed.
    real = "Crystal Palace 0-3 Nottingham Forest | Premier League Highlights"
    assert highlights.match_fixture(
        [(archive, "old"), (real, "new")], "Crystal Palace", "Nott'm Forest", 0, 3) == "new"


def test_the_other_clubs_highlights_beat_this_clubs_dugout_cam(store_with_a_played_match):
    """🔴 **First club asked used to win, and the first club is the home one.** For *Crystal Palace 3-1
    Nott'm Forest*, Palace posted *"DUGOUT CAM 🎥 | Crystal Palace 3-1 Nottingham Forest"* and Forest
    posted the actual *Extended Highlights* — ⚠️⚠️ *the preference for a title saying "highlights" only
    ever applied within one club's feed*, so it could not see the better answer in the other one.

    ⭐ This is the ADR-347 failure again — the right match, the wrong video — and the fix is to judge
    both clubs' entries together rather than to stop at the first that answers.
    """
    store, fixture_id = store_with_a_played_match
    clubs = {t["short_name"]: t["id"] for t in store.get_teams()}
    with store.conn:
        store.conn.execute(
            "UPDATE fixtures SET team_h = ?, team_a = ?, team_h_score = 3, team_a_score = 1 WHERE id = ?",
            (clubs["CRY"], clubs["NFO"], fixture_id))

    feeds = _Feeds({
        "CRY": [("DUGOUT CAM 🎥 | Crystal Palace 3-1 Nottingham Forest", "https://youtu.be/dugout")],
        "NFO": [("Crystal Palace 3-1 Nottingham Forest | Premier League | Extended Highlights 🎬",
                 "https://youtu.be/real")],
    })

    assert highlights.fill(store, client=feeds) == 1
    row = store.conn.execute("SELECT highlights_url FROM fixtures WHERE id = ?", (fixture_id,)).fetchone()
    assert row["highlights_url"] == "https://youtu.be/real", "the dugout camera was stored as highlights"


def test_a_thriller_called_a_classic_is_still_a_highlights_package():
    """⚠️⚠️ **The guard is one observed phrase and not a list of words meaning "old", and this is the
    reason.** A club captioning a 3-3 *"A CLASSIC AT THE CITY GROUND"* has posted a genuine package —
    ⭐ *excluding the bare word would trade a wrong link for a missing one*, which is the trade ADR-347
    made in the other direction and had to undo.

    🔴 Without this the guard could be widened to `classic` and nothing would notice: the mutation
    survived, and a guard nothing stops from growing is a guard that eventually eats real links.
    """
    real = "A CLASSIC AT THE CITY GROUND 🔥 | Nott'm Forest 3-3 Spurs | Premier League Highlights"
    assert highlights.match_fixture([(real, "u")], "Nott'm Forest", "Spurs", 3, 3) == "u"
