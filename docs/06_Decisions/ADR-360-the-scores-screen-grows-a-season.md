# ADR-360 — The Scores screen grows a season

**Date:** 2026-10-18
**Status:** 🚪 **Proposed — this is the gate.** Nothing is built until this is agreed.
**Supersedes the parking in:** ADR-358
**Mockup:** `https://claude.ai/artifact/5WB1oNori2ZmGkBY2NQYx9` (real GW7 data throughout)

---

## Context

Two pieces of tester feedback land on the same screen:

1. *"wants more stats like flashscore"* — ADR-358 parked this with the finding that the **timeline is not
   buildable**: FPL publishes no minutes, no substitutions, no VAR, no lineups.
2. *"can this information and view persist across gameweeks, just like we have for previous matches and
   future ones?"*

They are one build, so they get one gate.

## 🔴 What the data actually supports

Checked live, not assumed:

| | past gameweeks | in play | future gameweeks |
|---|---|---|---|
| fixtures, clubs, kick-off times | ✅ | ✅ | ✅ **already served** |
| score + per-fixture stats | ✅ **GW1 onward, indefinitely** | ✅ | ✗ does not exist |
| whose squad it was | ✅ FPL picks (ADR-350) | ✅ caller's squad | ⚠️ caller's squad *today* |
| highlights | ⚠️ **GW1–GW5 gone for ever** | — | ✗ n/a |

⭐⭐ **The endpoint already takes a gameweek.** `gameweek/scores` has accepted `{"gameweek": N}` since
ADR-346; GW8 returns its ten fixtures with kick-off times right now. ⚠️ *This is a navigation feature, not
a data feature*, which is most of why it is cheap.

📌 **I was wrong about forwards in the first pass** and the owner was right to push: I said a future week
"is a fixture list, which is what FDR already is". It is not — FDR is **team-level**; this is *your
players, match by match*, which is the same join ADR-346 calls the feature.

## Decision 1 — the card: a summary, and one dropdown

**Closed:** scoreline · state · scorers · assists.
**Open — one dropdown, four blocks:** cards · your players and what they earned · the bonus race (BPS) ·
the highlights video.

⭐ Nothing repeats between the halves — the duplication the owner rejected in the first Scores rework
(*"its duplicated and not well laid out"*).

### ⚠️⚠️ Assists are listed, never paired

FPL publishes goals and assists as **two lists it links to nothing**. Brentford's pairing was forced (one
goal, one assist); Liverpool's was not — Wirtz and Barcola each set up one of Munoz and Isak and the data
cannot say which. 🔴 *The first mockup printed "Munoz (Wirtz)"* — **the ADR-351 mistake, three days after
ADR-351**. Assists sit on their own row so both sides start on the same line however many goals each
scored.

### ⚠️ Every glyph is drawn, none typed

`result_pitch.dart` already pays for this lesson: *"the first version used emoji and Android substituted
its own: 🅰 came out as a white A on a **red** box — on a screen whose other feature is red cards."*
📌 But `scores_view.dart` builds its scorer line as a **string** — `'⚽' * a.goals` — so adopting the drawn
ball turns that string into a `Row` of widgets. A shape change, not a find-and-replace.

## Decision 2 — the week selector, both directions

`‹ GW7 › ` across the top, **GW1 to the final gameweek**.

* **Backwards** — the full card, with the squad *as it was that week* (ADR-350 already fetches it).
* **Forwards** — the same card with no score: clubs, kick-off time, and **which of your players are in it**.

⭐ The forward view needs one small server addition: `yours` is computed from `player_history`, which does
not exist before a match. For an unplayed fixture it comes from **player → team → fixture** instead.
⚠️ And it is the squad *as it stands today*, which a transfer will change — the card should say so rather
than imply a locked team.

## Risks, named rather than discovered

🔴 **GW1–GW5 will never have highlights.** The clubs' feeds hold fifteen entries and had moved on before
ADR-357 fixed the lookup. A tester scrolling back will find a gap that looks exactly like a bug: the card
has to say *"no highlights for this match"*, not simply omit the row.

⚠️ **The open card is ~1080px — taller than a phone.** It scrolls. If that proves wrong, the cheap fix is
collapsing the bonus race by default or moving the video above it. 📌 *Watch what testers reach for.*

⚠️ **Bonus is provisional for up to ~96 minutes** (measured, ADR-356). The bonus race is at its most
useful exactly then, and at its most likely to change under the reader. It needs the provisional marker.

## Out of scope, deliberately

- the Flashscore timeline — **not deferred, impossible**: no minutes, no subs, no VAR, no lineups (ADR-358)
- buying a second data provider
- `data_checked` and the settled-week caching question (ADR-356 left it alone on purpose)

## Definition of done

Automated tests · a manual smoke test on the owner's phone · this ADR updated with what changed · and
⭐ **a check that scrolling back to GW1 is honest about the missing highlights**, because that is the one
state no test will think to look at.
