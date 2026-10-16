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

## Still open

⏳ **New Zealand is untested.** A YouTube link resolves per viewer's territory and cannot be checked from
Ireland. 📌 One tester opening one link answers it.

⏳ **NFO and TOT** need an official channel id each — two links, two minutes, by someone who can confirm
them.
