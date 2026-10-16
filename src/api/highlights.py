"""Match highlights, from the clubs' own YouTube channels (ADR-347).

⭐⭐ **The hard part was never fetching, it was knowing a link is the right one.** FPL publishes no
highlights URL and `pulse_id` is 0 on all 380 fixtures, so there is no identifier to join on. What there
is, in every club's video title, is the **scoreline**:

    Chelsea 5-1 Bournemouth | HIGHLIGHTS | Premier League 2026/27

⭐ So the match is **deterministic, not a search**: parse `TeamA n-n TeamB`, and accept it only when both
clubs and **both goal counts** agree with the fixture we already stored. A title that does not parse, or
parses to a different score, yields nothing — ⚠️ *the failure mode is a missing link, never a wrong one.*

🔴🔴 **The channel list is an allow-list, and that is a rights decision rather than a convenience.**
Twelve of these are the channels the **Premier League links from its own channel page**; six more were
resolved by handle and then verified against their feed's actual contents. ⚠️⚠️ *Guessing handles is not
safe*: three guesses resolved to `ANIME VERSE`, `WEW` and a Nottingham Forest **fan** channel — and a fan
channel is exactly where an unlicensed re-upload lives. ⭐ *An allow-list of official channels is what keeps
this a link to the rights-holder rather than to whoever uploaded it first.*

📌 **All twenty clubs are on the list.** Nott'm Forest and Spurs were the last two, and the reason they
were missing turned out to be about this machine rather than about them: youtube.com/@handle answers an EU
consent wall from Ireland, so the handle resolver could not see any channel. ⭐ *A blocked lookup reads
exactly like an absent one*, and "could not be resolved" quietly became "does not exist" in the note that
recorded it.
"""

import re

from src.api.feeds import FeedError

#: Club short name → official YouTube channel id.
#:
#: ⭐ Provenance matters more than completeness here. **PL-linked** means the Premier League's own channel
#: page lists it; **verified** means the handle resolved and the feed's contents are that club's.
CHANNELS: dict[str, str] = {
    # ── linked by the Premier League itself ───────────────────────────────────────────────────────
    "ARS": "UCpryVRk_VDudG8SHXgWcG0w",
    "AVL": "UCICNP0mvtr0prFwGUQIABfQ",
    "BHA": "UCf-cpC9WAdOsas19JHipukA",
    "BOU": "UCeOCuVSSweaEj6oVtJZEKQw",
    "BRE": "UCAalMUm3LIf504ItA3rqfug",
    "CHE": "UCU2PacFf99vhb3hNiYDmxww",
    "COV": "UCch_NWdo3JWKngAyO9XlycA",
    "CRY": "UCWB9N0012fG6bGyj486Qxmg",
    "EVE": "UCtK4QAczAN2mt2ow_jlGinQ",
    "FUL": "UC2VLfz92cTT8jHIFOecC-LA",
    "HUL": "UC8MRV5E-Bi5qWomGjOF0ZQg",
    "IPS": "UCjNwxJec96lMWgCXjEDhXgQ",
    # ── resolved by handle, then verified against the feed's own contents ─────────────────────────
    "LEE": "UCyQcJHDN4uYfPa1DHzKVSnw",
    "LIV": "UC9LQwHZoucFT94I2h6JOcjw",
    "MCI": "UCkzCjdRMrW2vXLx8mvPVLdQ",
    "MUN": "UC6yW44UGJJBvYTlfC7CRg2Q",
    "NEW": "UCywGl_BPp9QhD0uAcP2HsJw",
    "SUN": "UCrw-7k6yJc0EMJdf-0BAkoQ",
    # ── named by a source that is not YouTube, then verified against the feed's own contents ───────
    # ⭐⭐ **The handle pages are unreachable from here**: youtube.com/@NFFC answers with the EU consent
    # wall (this project is operated from Ireland), so the resolver that found the six above cannot see
    # these two at all. ⚠️ *A blocked lookup reads exactly like a club that has no channel* — which is
    # what "could not be resolved from here" meant, and it was never a statement about the clubs.
    #
    # ⭐ So each id came from a source that names it outright, and neither is trusted on its own:
    #   NFO — linked from **nottinghamforest.co.uk** itself (`youtube.com/user/NFFCTube`), whose feed
    #         reports `author` *"Nottingham Forest FC"*.
    #   TOT — **Wikidata** P2397 on *Tottenham Hotspur F.C.*, whose feed reports `author`
    #         *"Tottenham Hotspur"*.
    # ⚠️⚠️ Both were then read: each feed carries this season's own matches in the exact
    # `Club n-n Club | … Highlights` shape the parser needs, which is the check that matters — ⭐ *a club
    # that cannot be parsed is on the list for nothing, and only its contents can say.*
    "NFO": "UCyAxjuAr8f_BFDGCO3Htbxw",
    "TOT": "UCEg25rdRZXg32iwai6N6l0w",
}

FEED = "https://www.youtube.com/feeds/videos.xml?channel_id={cid}"

#: ⚠️ YouTube's channel feed serves **fifteen** entries and no more — which is also the cap on how far
#: back this can reach. ⭐ *A club that posts several times a day buries its own highlight within days*,
#: so this is polled while matches are recent rather than relied on as an archive.
FEED_ITEMS = 15

#: `Chelsea 5-1 Bournemouth | HIGHLIGHTS | …` — and the same shape without a trailing pipe.
#:
#: ⚠️ Club names carry spaces, dots and apostrophes (*Nott'm Forest*, *Man Utd*), so the name groups are
#: deliberately loose and the **score** is what makes the match strict.
TITLE = re.compile(r"([A-Za-z .'&]+?)\s+(\d+)\s*-\s*(\d+)\s+([A-Za-z .'&]+?)\s*(?:\||$)")

#: ⚠️⚠️ **A club's archive series publishes an old match with a real scoreline in the title**, and
#: Forest's is branded *Classic Highlights*:
#:
#:     Special Radosław Majewski Hat-Trick! 🪄 | Crystal Palace 0-3 Nottingham Forest | Classic Highlights
#:
#: 🔴 That parses, names two Premier League clubs, and says *highlights* — so it would be taken by the
#: **preferred** branch the moment a current fixture happens to end 0-3 at Selhurst. ⭐⭐ *The score check
#: was supposed to make a wrong link impossible, and an old match between the same two clubs is exactly
#: the case it cannot see* — the scoreline is right, and the match is twelve years old.
#:
#: 📌 Deliberately the one phrase actually observed, across all twenty feeds, rather than a list of words
#: that might mean "old". ⚠️ *Excluding the word "classic" alone would drop a genuine package captioned
#: "A CLASSIC AT THE CITY GROUND"* — a wrong link traded for a missing one, which is the trade ADR-347
#: made in the other direction and had to undo. The real discriminator is the upload **date** against
#: kickoff, which this module already parses and throws away; see ADR-352.
ARCHIVE = re.compile(r"classic highlights", re.I)


#: FPL's spelling → the club's own, for the one club where **neither name contains the other**.
#:
#: 🔴 **A right channel is worth nothing behind a name that cannot match.** Forest's own videos say
#: *Nottingham Forest* and FPL says *Nott'm Forest*; containment fails both ways, so every Forest match
#: resolved to no link even once the channel was on the list. ⭐ *The symptom of a missing alias and the
#: symptom of a missing channel are the same symptom* — no link — which is why this hid behind that.
#:
#: ⚠️⚠️ **One entry, from evidence, not a spelling table.** Every club spelling observed across all
#: twenty feeds was checked against every FPL name: `Nott'm Forest` is the only FPL name nothing matched.
#: The other misses are *Fenerbahce*, *LASK*, *PSG*, *Cobham Next Gen* — European and academy opponents
#: that **must** keep failing. ⭐ *A matcher loosened until Forest fits is a matcher that fits PSG too.*
ALIASES = {"nott'm forest": "nottingham forest"}


def _canon(name: str) -> str:
    return ALIASES.get(name.lower().strip(), name.lower().strip())


def _looks_like(a: str, b: str) -> bool:
    """Is this title's club name the same club? ⭐ Containment either way, because a club writes itself
    *Leeds United* where FPL says *Leeds* — ⚠️ and never a fuzzy ratio, which would let *Man City* match
    *Man Utd* on a bad day."""
    a, b = _canon(a), _canon(b)
    return bool(a) and bool(b) and (a in b or b in a)


def parse_title(title: str):
    """`('Chelsea', 5, 1, 'Bournemouth')` from a video title, or None."""
    m = TITLE.search(title or "")
    if not m:
        return None
    return m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4).strip()


def videos(short_name: str, *, client=None) -> list[tuple[str, str]]:
    """`[(title, url)]` from one club's channel feed. ⚠️ Empty on any failure — never raises."""
    cid = CHANNELS.get(short_name)
    if not cid:
        return []
    try:
        from src.api.feeds import MediaFeedsClient, parse_feed
        raw = (client or MediaFeedsClient()).fetch(FEED.format(cid=cid))
        # ⚠️ **The whole feed, not `MEDIA_FEED_LIMIT`.** That default is sized for the headlines ticker,
        # where five recent items is the point. Here every discarded entry is a match that silently has
        # no highlight — ⭐ *and YouTube only serves fifteen, so there is nothing to protect against.*
        return [(e.get("title", ""), e.get("link", "")) for e in parse_feed(raw, limit=FEED_ITEMS)]
    except (FeedError, Exception):   # noqa: B014 - every failure degrades the same way
        return []


def match_fixture(entries, home: str, away: str, home_score: int, away_score: int) -> str | None:
    """The URL whose title names **this** fixture, preferring one that says it is highlights.

    ⭐⭐ Both clubs **and both scores** must agree. ⚠️ *A title naming the right two clubs with the wrong
    score is a different match between them* — a cup tie, a youth fixture, last season — and accepting it
    would put the wrong video behind a correct-looking scoreline.

    🔴 **Matching the fixture is not the same as matching the video, and the first version only did the
    first.** Arsenal 2-1 Leeds resolved to *"FRIMMY AND MO GILLIGAN'S PITCHSIDE REACTIONS | Alternative
    Commentary"* — the right match, on the right official channel, and not the highlights. ⭐ *A reader
    who taps "Highlights" and gets comedians has been told something untrue by the label.*

    ⚠️ So it is a **preference, not a requirement**: seven of eight real links said *highlights* and the
    eighth did not — *"Aston Villa 2-2 Brentford | Yarmoliuk and Ajer net on the road!"* is a genuine
    highlights package whose title never uses the word. ⭐ Requiring it would trade a wrong video for a
    missing one; preferring it fixes the first without causing the second.
    """
    fallback = None
    for title, url in entries:
        if ARCHIVE.search(title or ""):
            continue
        parsed = parse_title(title)
        if not parsed:
            continue
        h, hs, aws, a = parsed
        if (hs, aws) != (home_score, away_score):
            continue
        if not (_looks_like(h, home) and _looks_like(a, away)):
            continue
        if "highlight" in title.lower():
            return url
        fallback = fallback or url
    return fallback


def fill(store, *, client=None, limit: int = 20) -> int:
    """Find and record highlights for recently-finished fixtures. Returns how many were added.

    ⭐⭐ **One feed per club, not one per fixture.** Ten matches touch twenty clubs, and asking each club
    once answers every fixture it played in — ⚠️ *a lookup per fixture would fetch the same feed twice
    for the same match.*

    ⭐ Only the clubs involved in fixtures that still want a link are fetched, so a weekend with nothing
    outstanding makes **no requests at all** and the cost falls to zero on its own.

    ⚠️ Best-effort throughout: a feed that fails is skipped and the fixture simply keeps waiting.
    """
    wanting = store.fixtures_wanting_highlights()[:limit]
    if not wanting:
        return 0

    clubs = {t["id"]: t for t in store.get_teams()}
    feeds: dict[str, list] = {}
    added = 0
    for f in wanting:
        home, away = clubs.get(f["team_h"]), clubs.get(f["team_a"])
        if not home or not away:
            continue
        # ⭐⭐ **Both clubs' entries, judged together.** 🔴 This used to take the first club that
        # returned anything, and the first club is the home one: for *Crystal Palace 3-1 Nott'm Forest*,
        # Palace's feed offered *"DUGOUT CAM 🎥 | Crystal Palace 3-1 Nottingham Forest"* and Forest's
        # offered the actual *Extended Highlights* — and the dugout camera won, because it was asked
        # first and the loop stopped as soon as something answered.
        #
        # ⚠️⚠️ *The preference for a title that says "highlights" only ever applied within one club's
        # feed*, so it could not see the better answer sitting in the other one. ⭐ Concatenating first
        # makes the preference mean what it says. Still one fetch per club — `feeds` caches.
        entries = []
        for side in (home, away):
            short = side["short_name"]
            if short not in feeds:
                feeds[short] = videos(short, client=client)
            entries += feeds[short]

        url = match_fixture(entries, home["name"], away["name"],
                            f["team_h_score"], f["team_a_score"])
        if url and url != f["highlights_url"]:
            # ⭐ Only a *change* is written and counted. A recent fixture is re-examined every tick,
            # and ⚠️ *reporting "1 highlight" each time for the same video would be a number that
            # never settles.*
            store.set_highlights(f["id"], url)
            added += 1
    return added
