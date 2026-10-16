# ADR-346 — The score, and what it did to your team

**Date:** 2026-10-16
**Status:** ✅ **Accepted and built** — service 2026-10-16, Flutter screen 2026-10-16.
**Raised by:** a tester — *"in the More tab, a live score from the current or last match or gameweek, and
when available a highlights clip of the goals, like a YouTube link, similar to flashscore.com"*
**Builds on:** ADR-298 (a played gameweek never changes), ADR-256 (the rate limit), ADR-211 (the pipeline)
**Splits from:** the highlights half, assessed and deferred below

---

## Context

The request has two halves with completely different shapes, and they are separated here because treating
them as one feature would hold the easy half hostage to the hard one.

⭐ **The data for scores is already free and already ours.** `GET /api/fixtures/` returns, per match:

```
team_h_score · team_a_score · minutes · started · finished · finished_provisional
stats[] → goals_scored, assists, bonus, cards — each with the FPL element id
```

Checked live on 2026-10-16: GW6 returned all ten matches finished, `CHE 5-1 BOU` with goals attributed to
Henderson ×2, João Pedro ×2, Rogers and Evanilson.

⚠️ **We do not store any of it.** `fixtures` holds `event`, `team_h`, `team_a`, the two difficulties,
`finished` and `kickoff_time`. No score, no minutes, no `started`.

### ⭐⭐ And there is a better feature than the one asked for

`/squad/gameweek` — the played-week view (ADR-298) — is the **2nd most-used endpoint in the app**: 18
installs, 195 calls, 10.8 per install. People already live on that screen.

Flashscore can show a score. ⭐ *Only we can show what it did to their team:* **CHE 5-1 BOU — your João
Pedro scored twice, 13 pts.** The `stats[]` block carries element ids, and the squad is already loaded, so
the join is free.

## Decision (proposed)

**Ship match scores, joined to the manager's own squad. Defer highlights.**

### The split that makes this work

⭐⭐ **A finished match is a fact; a live match is a feed.** They are fetched differently, and conflating
them is what would make this depend on a pipeline that cannot deliver it.

| | finished match | match in progress |
|---|---|---|
| source | pipeline → `fixtures` | fetched live on request |
| changes after? | **never** | every minute |
| cache | forever | ~60 s, server-side |
| precedent | ADR-298's *"one request per manager per gameweek, ever"* | `my-team` already fetches live |

🔴 **This is deliberately not a pipeline feature.** The pipeline fires at roughly a fifth of its declared
hourly cadence with a repeating 08:00–16:00 hole (Roadmap §2). ⭐ *A "live" score behind a scheduler that
skips Saturday morning would be a lie in the product.* So the live path bypasses it — and the finished
path does not care, because a played score never changes and one successful fetch is enough, ever.

### Schema

Add to `fixtures`: `team_h_score INTEGER`, `team_a_score INTEGER`, `minutes INTEGER`, `started INTEGER`.
⚠️ Nullable — a fixture that has not kicked off has no score, and `0-0` is a real result that must not be
confused with "not played".

### Contract

One endpoint, squad-scoped like the rest:

```
POST /api/v1/gameweek/scores   { manager_id?, gameweek? }
→ { gameweek, matches: [ { home, away, home_score, away_score, minutes,
                           started, finished, yours: [ {player, goals, assists, points} ] } ] }
```

⭐ `yours` is the whole point. Without it this is a worse flashscore.

### Rate limit

A new `"/gameweek/scores"` entry in `LIMITS`. ⚠️ The upstream is an **undocumented** API that can block a
noisy caller, and nine testers refreshing during a 15:00 kick-off is real traffic. The server-side cache is
the actual control: it makes the limit about *our* instance, not about how many people press refresh.

## The highlights half — assessed, deferred, and the evidence kept

📌 **Deferred, not refused.** The assessment is recorded because it took real work and the next attempt
should not repeat it.

**What was ruled out:**

- `pulse_id` is **0 on all 380 fixtures**, so there is no route to the official match page.
- UK digital highlights rights sit with BBC Sport for all 380 matches — ⚠️ *irrelevant here*: the owner and
  most testers are in **Ireland**, where the Premier League's own YouTube channel is visible (owner-checked
  2026-10-16). 🔴 New Zealand is unresolved — Sky holds **exclusive** rights there through 2027-28 and it
  cannot be tested from Ireland.
- Flashscore's own terms say its video is *"not hosted on the Provider's servers"* and it is *"not
  responsible for the content of external Apps"*. ⭐ That is an **embed-and-disclaim** model run by a Malta
  company with ~100M users — replicable in code, not in legal posture.

**⭐⭐ What was ruled IN, against my own two earlier assessments:** club YouTube channels publish per-channel
RSS, free and keyless, and their titles carry the scoreline.

```
2026-10-10  [Chelsea]      Chelsea 5-1 Bournemouth      watch?v=mL-qGgJf6Ug
2026-10-10  [Aston Villa]  Aston Villa 2-2 Brentford    watch?v=7JCkPn7J-y4
2026-10-10  [Brentford]    Aston Villa 2-2 Brentford    watch?v=XLQm366y_90
2026-10-11  [Hull City]    Hull City 2-2 Everton        watch?v=nSkWXRgkjCI
```

**11 parseable links from 12 club feeds**, same day as the match, and the scorelines match FPL's fixture
data exactly. ⭐ So the match is **deterministic** — parse `TeamA n-n TeamB |`, verify score and both teams
against the stored fixture — reusing `src/api/feeds.py` (already best-effort per feed) and `names.py`.
⚠️ *I asserted twice that this would mean hand-pasting 380 links. It would not, and checking is what showed
that.*

**Why it still waits:** coverage is partial (Arsenal posted 15 videos, 13 saying "highlight", none of them
their own match), YouTube's feed caps at **15 entries** so a prolific club buries its highlight within
days — which makes it depend on the same polling cadence that is currently broken — and New Zealand is
untested. ⭐ **And it needs the stored fixture to match titles against, which is what this ADR builds.**

## Risks

| | |
|---|---|
| 🔴 Upstream blocking | An undocumented API, polled during matches. The 60 s cache is the control, not the rate limit. |
| 🟠 `0-0` vs not played | Nullable columns and `started`, never a score defaulting to zero. |
| 🟠 Provisional results | `finished_provisional` goes true before bonus is final. A score shown as settled before FPL settles it is wrong in the one direction people check. |
| 🟢 Analytics | **None touched.** No `decision_xp` change, no new analytics module. Display only. |

## Definition of Done

1. Automated tests, including a fixture that has not kicked off, a `0-0`, a provisional finish, and the
   squad join with a player who did not feature.
2. **A manual smoke test on a real match**, by the owner, on his own team. ⚠️ *ADR-344 recorded a probe
   against the demo squad and called that verification; it was not.*
3. Docs — Architecture, Roadmap, and this ADR moved to Accepted with what actually shipped.

## Not in scope

Highlights · notifications · live player points (FPL's `event/{gw}/live` is a different and larger
feature) · anything touching `decision_xp`.


---

## What shipped (2026-10-16)

**The service half, entirely.** `POST /api/v1/gameweek/scores` → `{gameweek, live, yours_known, matches[]}`,
with `fixtures` gaining `team_h_score`, `team_a_score`, `minutes` and `started` (nullable, migrated onto
existing databases). 13 new tests, five mutants each caught by the test that names the behaviour.

✅ **The Flutter screen too** — `lib/scores_view.dart`, reached from **More → Scores**, 7 widget tests
against the committed sample. ⚠️ Placed **second, behind Ask**: ADR-302 put Ask first on purpose and a new
row does not get to undo that quietly. It leads the remaining game rows because it is the only entry in
More you would open while a match is still on.

### 🔴 Two things the design missed, both found by running it against the real database

**1. Scores arrive before player history does.** `fixtures` is filled by the refresh; `player_history` by
the separate backfill. Against the live database GW6 had **ten scores and no history** — so `yours` was
empty for every match, which reads as *"none of your players featured"* when the truth is *"we do not know
yet"*. ⭐⭐ *An empty list cannot tell those apart, and they are opposite facts.* Hence `yours_known`, which
is not in the proposal above because nobody thought of it until the data did.

**2. `finished` does not imply `started` in a database that predates `started`.** Every fixture stored
before this change has `started` NULL and `finished` already set, so a played match read as *"not started
but finished"* and `_which_gameweek` found no playable week at all. ⭐ Derived in code rather than
backfilled: cheaper, and it cannot drift.

### ⚠️ And one mistake this project had already written down

`yours` was first a flat dict of `id` + stats — ⭐ **the exact second-player-shape mistake
`gameweek_result` records making** (ADR-227), caught by `test_player_shape.py` the same way and within
minutes. It now carries a `player_summary` with the week beside it.

### 📌 Unrelated fragility found on the way, not fixed here

Running `ingest.refresh` against the local `data/fpl.db` turned **ten unrelated tests red** — the bank
suite, three API-contract samples, spent chips. That file is **gitignored**, and on SQLite
`_wants_the_snapshot` hands it to any test that opens the default store. ⚠️⚠️ *So those tests pass or fail
according to when the developer last ran a refresh, and CI — which has no `fpl.db` — can never see it.*
Restoring the file from the committed snapshot made all ten green again. ⭐ *A test that reads a gitignored
file is a test whose result belongs to one machine.* Worth its own gate; not taken here.


### 🔴 And a third, which only CI could see (2026-10-16)

The first CI run went red with **all 3,078 tests passing**. The failure was a session guard:

> *🔴 The test suite modified `data/seed.db`, which is committed to git.*

⭐⭐ **Adding a column means opening the committed snapshot now rewrites it.** `_migrate` runs
`ALTER TABLE fixtures ADD COLUMN …` on any database lacking the new columns, and the snapshot lacked them.

⚠️⚠️ **It could not fail locally, for a reason worth keeping.** A developer machine has
`data/fpl.db` — gitignored — so the migration landed there, invisibly. CI has no such file, so the same
code reached `seed.db`, which is in git. ⭐ *The same change was harmless on every machine that had run the
app and caught on the one that had not*, which is the only place it could have been caught.

**Fixed by bringing the snapshot up to the schema deliberately**, once, rather than letting every test run
do it by accident — the same move as the earlier *"refresh the committed seed so it agrees with itself"*.
Verified schema-only: eleven tables, **no row-count change anywhere**, and zero fixtures carrying a score.


---

## The screen (2026-10-16)

⭐ Both ambiguous pairs are resolved **in the widget**, not left to the reader: a score is drawn only when
`started`, so `0–0` and a kick-off time can never be confused; and the heading says *"your players not in
yet"* when `yoursKnown` is false, where an empty card would have claimed nobody featured.

### 🔴 Three defects the widget tests caught

1. **The heading row overflowed at 472 px** with the LIVE chip and the *not-in-yet* note together — a
   yellow-and-black stripe on a narrow phone, in front of a tester. Now `Flexible` with an ellipsis.
2. **A second `pumpWidget` reuses the existing `State`**, so a `late _future` never re-runs and the screen
   keeps showing the first body. ⭐⭐ *A test that pumps twice and asserts on the second was asserting on
   the first* — it passed for the wrong reason until a distinct key forced a fresh State.
3. **Two matches in one gameweek can share a scoreline.** The sample has two 3–0s and the assertion
   demanded exactly one — ⭐ *a uniqueness the data never owed the test.*

### ⭐ The sample had to be made real first

`spikes/018-flutter-read-slice/api-samples/gameweek-scores.json` was generated with every score `null`,
because the committed snapshot's `fixtures` carry none — so the one example a Dart author reads could not
show a score at all. ⚠️ **But `player_history` already knew them**: it stores `team_h_score` /
`team_a_score` on every appearance row. Backfilled from there — **50 fixtures, including a genuine
`LEE 0-0 CRY`**, which is precisely the case the screen exists to distinguish. ⭐ *The fixture now agrees
with itself, and the sample shows the feature rather than its type signature.*


---

## The layout the owner asked for (2026-10-16)

Two reports from the staged build, and they were different kinds of thing.

### 🔴 "It doesn't give the actual score"

**True, and not a screen bug.** The live API returned `null` for every score. The cause is the one the
architecture review measured and could not then justify caring about:

⭐⭐ **The scheduled pipeline had not run since the code that writes scores shipped.** Last run 08:46 on
`c51dec5`; the service landed ~11:30; it was 13:30. That five-hour hole is exactly the **08:00–16:00 blind
spot** recorded in Roadmap §2 — ⚠️ *measured a week earlier with no evidence it cost anything, and here is
the evidence.* A manual `workflow_dispatch` filled it and the scores appeared: `ARS 2-1 LEE`,
`CHE 5-1 BOU`, `SUN 0-2 BHA`.

📌 **Nothing in this ADR fixes that.** It is a cadence problem with its own open decision, and this is the
first thing it has visibly broken.

### ⭐ The layout

The owner's mock-up put the two clubs on the outside with crests and full names, the score between them
with a status word beneath, **each of your players under the club he actually played for**, and a *"Your
fantasy impact"* total at the foot.

⭐⭐ **The side-split is the part that earns the redesign.** A name under a scoreline does not say who he
was playing *for*; a name under a crest does — and a pinned widget test now asserts it by **horizontal
position** relative to the score, because that is what the reader is actually using to decide.

Server changes: a `clubs` **sidecar map** (short name → name + badge, carried once rather than per match,
the shape `my-team` uses for `kits`) and a `status` string. ⭐ *"Full time" / a minute / nothing is one
judgement, and three clients making it separately is three chances to disagree about whether a match is
over.*

### ⚠️ One place the mock-up was more cautious than it needed to be

It footnoted *"gameweek points are not necessarily points earned in this individual match"* — true of a
gameweek total, and **this is not one**: `player_history` is keyed by **fixture** (ADR-129), so the number
shown was earned in that match. The card says **"in this match"** and means it.

### 🔴 And a test that passed for the wrong reason

The impact total was first asserted against the committed sample, whose one scoring match holds **9 pts and
0 pts** — so *"the first player's points"* and *"the sum"* are the same number, and a mutation replacing
one with the other **survived**. ⭐ *A test whose data cannot distinguish the bug from the fix is a test
that passes for the wrong reason.* Rewritten against a hand-built body with two scorers, where the total
matches neither alone.


---

## 🔴 The first rendering was wrong, and the screenshot said why (2026-10-16)

Build 42 on the phone produced a card that was **duplicated and truncated**, and the owner's two sentences
named both causes precisely: *"its duplicated"* and *"having 'your player' adds no value if thats all we
show."*

| fault | why it was wrong |
|---|---|
| **Every name tagged `· Your player`** | ⭐⭐ True of **everything in the block**, so it said nothing — and it cost the width that truncated the names themselves: *"João Pedro · Your pl…"*, *"B.Fernandes · Your …"*. ⚠️ *A label true of everything on screen is not a label.* |
| **Names listed twice** | Under the clubs, then again in *"Your fantasy impact"*. Arsenal drew *Raya · Gabriel · Konsa* and then *Calvert-Lewin · Raya · Gabriel · Konsa*. Same facts, no new one. |
| **Per-player points missing** | The card showed **11 pts** for four players and never said which earned it — ⭐ *the one number a reader wants when three of his are in the same match.* |
| **`1 pts`** | Noticed by every reader, fixed by none. |
| **`did not play` in green** | Green reads as good news. |

### The layout, chosen by the owner from three

⭐ **Compact — names only.** Crest and club on the outside, score between with its status beneath, your
players' **names** under their own club, and **one total** at the foot. Goals ride along as `⚽` because
they are the one event compact enough to earn the width; nothing else does.

A match with none of yours is **just a scoreline** — no divider, no total, no *"none of yours"*. ⚠️ *A card
that explains its own emptiness spends four lines saying nothing happened.*

📌 **Not chosen, and worth remembering why:** a per-player scorecard showing each man's own points. It
answers *"which of my four earned the 11?"*, which this layout cannot — the trade the owner made is density
over attribution, and if that question starts being asked, that is the design waiting.

### ⭐ Three mutants, each caught

The `· Your player` tag restored · `pts` at one point · the total drawn for a match with nobody in it.
