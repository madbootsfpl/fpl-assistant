# ADR-352 — A channel behind a name that cannot match

**Date:** 2026-10-16
**Status:** Accepted
**Asked for:** the two missing channel ids (ADR-347 left Nott'm Forest and Spurs off the allow-list)
**Extends:** ADR-347 (highlights, matched by the one thing that can verify them)

---

## Context

ADR-347 shipped highlights for eighteen of twenty clubs and recorded the other two as *"no official
channel established"*. That note was wrong about why.

⭐⭐ **`youtube.com/@handle` answers the EU consent wall from Ireland.** The resolver that found six
channels by handle cannot see *any* channel from this machine — it reads 584KB of consent UI and finds no
`channelId`. ⚠️ *A blocked lookup reads exactly like an absent one*, and the note recording it turned
"could not be resolved here" into a claim about the clubs.

Both ids came from sources that name them outright, neither trusted alone:

| | id | named by | feed `author` |
|---|---|---|---|
| NFO | `UCyAxjuAr8f_BFDGCO3Htbxw` | **nottinghamforest.co.uk** itself (`youtube.com/user/NFFCTube`) | *Nottingham Forest FC* |
| TOT | `UCEg25rdRZXg32iwai6N6l0w` | **Wikidata** P2397 on *Tottenham Hotspur F.C.* | *Tottenham Hotspur* |

Both feeds were then read, which is the check that matters: each carries this season's matches in the
exact `Club n-n Club | … Highlights` shape the parser needs.

## 🔴 And then Forest still resolved to nothing

**FPL writes `Nott'm Forest`. The club writes `Nottingham Forest`.** `_looks_like` is containment either
way, and neither string contains the other — so every Forest fixture produced no link with the official
channel sitting on the list. ⭐⭐ *The symptom of a missing alias and the symptom of a missing channel are
the same symptom*, which is how this hid behind the thing it was blamed on.

**Decision: one alias, from evidence.** Every club spelling observed across all twenty feeds was checked
against every FPL name. `Nott'm Forest` is the **only** FPL name nothing matched; the other misses are
*Fenerbahce*, *LASK*, *PSG*, *Lille*, *Cobham Next Gen*, *Exeter City* — European and academy opponents
that **must** keep failing. ⚠️⚠️ *A matcher loosened until Forest fits is a matcher that fits PSG too*,
so this is a one-entry alias and not a fuzzy ratio.

## 🔴🔴 Two defects the alias switched on

Both were latent. Making Forest matchable made them reachable, so they belong to this change.

**An archive match with a real scoreline.** Forest's archive series is branded *Classic Highlights*:

```
Special Radosław Majewski Hat-Trick! 🪄 | Crystal Palace 0-3 Nottingham Forest | Classic Highlights
```

It parses, names two Premier League clubs, and says *highlights* — so the **preferred** branch would take
it the moment a current fixture ends 0-3 at Selhurst. ⭐⭐ *The score check was meant to make a wrong link
impossible, and an old match between the same two clubs is the one case it cannot see*: the scoreline is
right and the match is twelve years old.

⚠️ Excluded on the **one phrase actually observed** across all twenty feeds, not a list of words meaning
"old". Excluding the bare word would drop a genuine package captioned *"A CLASSIC AT THE CITY GROUND"* —
a wrong link traded for a missing one, which is the trade ADR-347 made in the other direction and had to
undo. 📌 A test pins the narrowness, because the mutation widening the guard survived until it existed.

**The first club asked won, and the first club is the home one.** For *Crystal Palace 3-1 Nott'm Forest*,
Palace posted *"DUGOUT CAM 🎥 | Crystal Palace 3-1 Nottingham Forest"* and Forest posted the actual
*Extended Highlights* — and the dugout camera won, because `fill` stopped at the first club that answered.
⚠️⚠️ *The preference for a title saying "highlights" only ever applied within one club's feed*, so it
could not see the better answer in the other one. ⭐ This is the ADR-347 failure exactly — the right match,
the wrong video — surviving inside the fix for it.

Both clubs' entries are now judged together, which also makes `fill` shorter. Still one fetch per club.

## Consequences

✅ Twenty of twenty clubs, and a test asserts the count rather than listing the absences.

📌 **Not retroactive.** YouTube serves fifteen feed entries, so GW1–GW5 Forest and Spurs matches are past
recovering — checked against the real feeds, all nine resolve to nothing. GW6's *Man Utd 1-1 Spurs* and
*Crystal Palace 3-1 Nott'm Forest* both resolve now.

## ⏳ Deferred: the date window is the real discriminator

A highlights package is published within days of kickoff; an archive upload is not. `parse_feed` already
returns `published` and `videos()` **throws it away**. A window around kickoff would retire the textual
guard and also cover the two hazards this change leaves standing — ⚠️ *Fulham's women's results and
Chelsea's academy games parse to real scorelines between real clubs*, and today only the opponent's name
saves them. 📌 That changes a shipped matching rule, so it wants its own gate rather than a quiet ride on
this one.
