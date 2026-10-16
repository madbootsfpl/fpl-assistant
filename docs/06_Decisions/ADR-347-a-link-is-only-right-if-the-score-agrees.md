# ADR-347 — A link is only right if the score agrees

**Date:** 2026-10-16
**Status:** ✅ Accepted and built
**Completes:** the half ADR-346 deferred
**Asked for:** *"lets do the video clip first before shipping"*

---

## Context

ADR-346 deferred highlights and recorded why: no identifier to join on (`pulse_id` is **0** on all 380
fixtures), partial coverage, YouTube's 15-entry feed cap, and an untested New Zealand. It also recorded the
finding that overturned two earlier assessments of mine — **club channels publish free, keyless RSS whose
titles carry the scoreline.**

## The two problems, and only one was technical

### ⭐⭐ Matching: the score is the join key

There is no id tying a video to a fixture. There is a **scoreline in the title**:

```
Chelsea 5-1 Bournemouth | HIGHLIGHTS | Premier League 2026/27
```

So the match is **deterministic**: parse `TeamA n-n TeamB`, and accept only when both clubs *and both goal
counts* agree with the fixture already stored.

⚠️ **The score is what makes it strict, and it has to be.** Two clubs meet more than once — a cup tie, a
youth fixture, last season. `Chelsea 2-0 Bournemouth | U18 HIGHLIGHTS` names the right two clubs and is the
wrong video; ⭐ *the wrong video behind a correct-looking scoreline is worse than no video.* Club names are
matched loosely in both directions (FPL says *Leeds*, the club says *Leeds United*) and never by a fuzzy
ratio, which would let **Man City** match **Man Utd** on a bad day.

### 🔴🔴 Sourcing: the allow-list is a rights decision

**Resolving channels by guessing handles is not safe.** Of twenty guesses, three resolved to the wrong
channel — `ANIME VERSE`, `WEW`, and a Nottingham Forest **fan** channel. ⭐⭐ *A fan channel is exactly
where an unlicensed re-upload lives*, and a plausible-looking wrong channel is worse than a missing one
because nothing about it reads as wrong.

So `CHANNELS` is an allow-list with recorded provenance:

| how | clubs |
|---|---|
| **Linked by the Premier League itself** | 12 |
| Resolved by handle, then **verified against the feed's own contents** | 6 |
| ⚠️ **Not established** | **NFO, TOT** — their matches get no link |

📌 Notably the PL links mostly the smaller clubs; Liverpool, Man Utd, Man City and Spurs are not on its
featured list, which is about featuring and not about authenticity.

## Measured coverage

**7 of 10 GW6 matches**, six days after they were played, with 18 of 20 clubs — and **two of the three
misses are the two clubs that have no channel**. ⭐ Taken daily rather than six days late, and with all
twenty, it would be higher. ⚠️ *This is a "when available" feature and the UI says so by drawing nothing
when there is nothing.*

## Decisions

**Both clubs are asked.** ⭐ Measured: Arsenal did not post its own GW6 match and **Leeds did** — asking
only the home side would have thrown away coverage.

**One feed per club, not per fixture**, and only for clubs in fixtures that still want a link. A weekend
with nothing outstanding makes **no requests at all**.

**A found link is never re-fetched.** `fixtures_wanting_highlights` shrinks to nothing on its own — the
same economics as a played score.

**Written outside `save_fixtures`**, which rebuilds a row from FPL's payload and has never heard of
highlights. ⚠️ *A refresh would otherwise blank the link on every tick.*

**Last in the pipeline and never fatal.** It reaches twenty other people's feeds; a failure there must not
touch a refresh that has already succeeded.

**The whole feed, not `MEDIA_FEED_LIMIT`.** That default is six, sized for the headlines ticker. Here every
discarded entry is a match that silently has no highlight.

## The client

A link, not an embed: **"Highlights on YouTube"**, drawn only when one exists. ⚠️ *It names the
destination* — `test_help_link.py` exists in this repo because tapping a row and landing in another app is
a surprise unless it was announced.

⚠️⚠️ **It took its own row after two attempts at sharing one.** Side by side with the points it overflowed
the card by 27 px; constrained with `Flexible` it was squeezed to 114 px for 267 px of words. ⭐ *A row
needing a compromise from both children is a row with one child too many* — and the label cannot shrink,
because naming the destination is the point.

## 🔴 A test that passed for the wrong reason

`test_only_known_clubs_are_fetched` asserted `videos("NOT-A-CLUB") == []` — and **survived a mutation that
removed the allow-list check entirely**: an unknown club got a made-up channel id, the fetch failed, and
`[]` came back for the wrong reason. ⭐⭐ *The thing that must be true is that nothing was requested*, so
the double now records calls and the test reads the record. It is the rights-critical behaviour in the
whole feature, and the first version of its test could not see it.

## 🔴 Found by opening the links, not by testing them (2026-10-16)

The first production run found **8 of 10** GW6 matches — and the two misses were exactly MUN v TOT and
CRY v NFO, the two clubs with no channel. ⭐ *Every gap explained by the allow-list, none by the matcher.*

⚠️⚠️ **Then I opened them.** Seven were the highlights. The eighth, Arsenal 2-1 Leeds, was
*"FRIMMY AND MO GILLIGAN'S PITCHSIDE REACTIONS 🤣 | Alternative Commentary"* — the right match, on
Arsenal's own official channel, and **not the highlights**.

⭐⭐ **Matching the fixture is not matching the video, and the first version only did the first.** A reader
who taps *"Highlights"* and gets comedians has been told something untrue by the label.

**Fixed as a preference, not a requirement.** Seven of eight real titles said *highlights*; the eighth —
*"Aston Villa 2-2 Brentford | Yarmoliuk and Ajer net on the road!"* — is a genuine package whose title
never uses the word. ⭐ *Requiring it would trade a wrong video for a missing one.* So a highlights-titled
match wins, and anything else is kept as a fallback.

### And the wrong link would have been permanent

🔴 `fixtures_wanting_highlights` returned only fixtures with **no link**, so once the reaction video was
stored nothing would ever have looked again. ⚠️ *A link that is never re-checked is a wrong link kept for
ever* — and this is not a freak case: a club posts a reaction clip before its highlights package, and
whichever existed when the pipeline happened to run is what got stored.

Now a fixture played in the **last three days** is re-examined whatever it holds, and only a *change* is
written. ⭐ It converges and then the window closes — re-checking every played fixture for ever would fetch
twenty feeds a tick to change nothing.

## Still open

⏳ **New Zealand is untested.** A YouTube link resolves per viewer's territory and cannot be checked from
Ireland. 📌 One tester opening one link answers it.

⏳ **NFO and TOT** need an official channel id each — two links, two minutes, by someone who can confirm
them.
