# ADR-346 — The score, and what it did to your team

**Date:** 2026-10-16
**Status:** 📌 **Proposed — a gate, not a build.** Nothing here is implemented.
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
