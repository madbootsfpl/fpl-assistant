# ADR-360 — The Scores screen grows a season

**Date:** 2026-10-18
**Status:** ✅ **Agreed 2026-10-18 — building.** The server is done; the screen is not (see *State of the build*).
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

### ⭐ How far forward? Measured: the whole season is there, and that is not the answer

All **380 fixtures carry a gameweek and a kick-off time**, GW1 to GW38 — zero unscheduled, zero flagged
provisional today. So forwards is not "the next week", it is **thirty-one gameweeks**.

⚠️⚠️ **The fixtures stay meaningful at any distance; the join does not.** *"Which of your players are in
it"* uses the squad you hold **today**, and by GW20 that is a guess dressed as a fact — the same shape of
mistake as ADR-350, which credited a past week to a squad that had since changed.

**Decision: forward navigation stops at the house horizon — five gameweeks.** ⭐ Not a new number:
`analyse`, `board`, `dead_slot` and `explain` all already default to `horizon: int = 5`. Beyond that, team
-level fixture browsing is what **FDR already is**, and it is genuinely the right screen for it.

📌 `provisional_start_time` exists on every fixture and is zero everywhere today, but TV picks do move
kick-offs. The store does not carry that field, so a time can change under a reader with nothing marking
it — ⚠️ at three to five weeks out that is the normal case, not the edge case.

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

## 🔴 The hazard that changed the plan mid-build

**`yours[].player` was briefly an id into `people`** — the sidecar describing each man once, which is what
`clubs` beside it has always done. Eleven men travel twice in the payload without it.

⚠️⚠️ **Build 45 parses that field as an object** (`json['player'] as Map<String, dynamic>`), and Render
deploys on push. Shipping the server alone would have thrown on the Scores screen for all nine testers
**the moment it deployed**, before any of them could update.

⭐⭐ *An additive change reaches an old client harmlessly; a changed field does not.* So `events` and
`bonus_race` reference `people` by id and `yours` keeps its shipped shape. The inconsistency is deliberate
and costs about 2 KB — it can go the next time that field changes shape for another reason.

## State of the build

**Done, green, and safe to deploy on its own:**

* `player_history` already held goals, assists, cards, saves, bonus and BPS **keyed by fixture** — so the
  whole card is one local query. ⭐ *No schema change, no upstream call, and GW1 works.*
* `events` (goals · assists · cards), `bonus_race`, and a `people` sidecar; a forward week reports **who
  of yours is involved**, from team membership rather than from history that does not exist yet.
* The drawn ball and boot moved out of `result_pitch.dart` into `event_icons.dart` so both screens use
  one shape. ⚠️ The Scores line still builds `'⚽' * goals` into a **string** — that is the next edit, and
  it is a `Row`, not a find-and-replace.
* 30 server tests, five mutants each caught. Payload 12.7 → **30.6 KB** wire, between `my-team` and
  `ticker`.

**🔴 Caught by counting bytes:** the first sidecar named every player with a history row — all 667 across
a gameweek, **126 KB** — because the id was added before checking whether he had done anything.
⭐ *That is the ADR-227 payload sin inside the change that cites it.*

**Not built yet:** the card itself (summary + one dropdown) and the week bar. The new fields are parsed
by the client and not yet drawn, so the screen is exactly as it shipped.

## Definition of done

Automated tests · a manual smoke test on the owner's phone · this ADR updated with what changed · and
⭐ **a check that scrolling back to GW1 is honest about the missing highlights**, because that is the one
state no test will think to look at.
