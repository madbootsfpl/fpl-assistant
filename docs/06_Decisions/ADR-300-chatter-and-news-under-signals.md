# ADR-300 — Chatter and News under Signals

**Date:** 2026-09-25
**Status:** ✅ **Chatter built** (2026-09-25). 🔴 **News not built** — the recommendation below stands
and was accepted.
**From:** the owner — *"Signals: can we add in the Headlines — FPL analysis & football news as well as the
Community chatter, maybe stick under one or two new sub tabs under Signals called Chatter and/or News. Can
we have images rather than just links. Thoughts?"*

---

## Chatter already exists, and the phone cannot reach it

⭐⭐⭐ **`src/community.py` has been in this repo since Sprint 067 (ADR-059).** It fetches `r/FantasyPL`'s
public RSS, counts whole-word player mentions against the squad index, and returns a ranked *most talked
about* list. It degrades on 403 / 429 / timeout / parse error to `(None, message)` and never raises.

⚠️⚠️⚠️ **Correction (2026-09-26): it was wired to *nothing*.** This ADR said *"wired to Streamlit and to
nothing else"*, and that was wrong — I assumed it rather than checking. `git log -S community_signals`
says: it shipped on the **web** in Sprint 068, sat on the Trending page through US-345 (10 Aug 2026), and
was dropped by **ADR-150** on 26 Aug when Signals and Trending were reorganised. From that day until the
Chatter endpoint was written it was **called by no caller on any surface** — a month of dead code that no
test noticed, because nothing that still ran touched it.

⭐⭐ *A feature does not have to be deleted to be lost.* It was removed from the one screen that used it,
and the code stayed exactly where it was, passing its own unit tests, reachable by nobody.

**Cost to surface it:** one endpoint, one model, one sub-tab. No new dependency, no new source, no new
failure mode — the degradation path is already written and already tested.

⭐ It also fits what Signals **is**. The tab's existing promise is *"what changed that you should know
about"*, and *"forty people are arguing about Mbeumo today"* is that, in the one currency Signals already
trades in: attention. ⚠️ Worth keeping the existing framing on it — **mention frequency, not sentiment** —
because *a count of names is not an opinion about players, and a screen that blurs the two is inventing
analysis it did not do.*

## News is a different kind of thing, and I would not build it

🔴 **This is the half I would push back on**, and the reason is not effort.

⚠️⚠️⚠️ **It changes what the product is.** Everything in this app answers *"what should I do about my
squad?"* from numbers it computed and can explain — the landing page says **"Analytics decide. Logic
explains."** A headline feed answers *"what is happening in football?"*, which is a question a hundred
apps already answer better, and it is the first surface here that would carry text nobody could hold this
app accountable for. ⭐ *A tool people open to decide something is a different product from one they open
to browse, and the second is much harder to stop becoming.*

**Three concrete costs, on top of the philosophical one:**

1. ⚠️ **Someone else's words and pictures.** Republishing headlines with thumbnails means hot-linking
   images from publishers who have not agreed to it, at whatever scale this grows to. Fine at nine
   testers; ⭐ *a decision that is fine at nine and not at nine hundred is a decision worth making at
   nine.*
2. ⚠️ **A feed is a liability the pipeline does not have.** Every other source here is FPL or Reddit, both
   with a known shape and a written degradation path. A news feed is an editorial firehose — 🔴 *the first
   time it carries something distasteful next to a manager's squad, the app published it.*
3. ⚠️ **It never says it was wrong.** Signals exists because *"the server says what exists; only the device
   knows what is new"* (ADR-232/256). Headlines do not expire, cannot be marked seen in any meaningful
   way, and would sit at the top of the tab going stale.

⭐ **What I would do instead, if the want behind this is real:** the actual need is probably *"tell me
when something happened to a player I own"* — which is what Signals already does from **price, minutes,
status and ownership**, and could do better from **team news** without importing a newspaper. ⚠️ *The
feature to build is the one the request is reaching for, not the one it names.*

## Images

⚠️ **Worth separating from the tabs.** A Reddit entry carries no reliable thumbnail; a club-badge or
player-mugshot beside each row is **already in hand** (`shirt_url`, the mugshots the player sheet uses)
and costs nothing new. ⭐ *An image that identifies the subject is worth more than one that decorates the
page*, and it is the one this app can supply without asking anyone's permission.

## Recommendation

| | |
|---|---|
| **Chatter** | ✅ Build. One endpoint away, fits the tab, degrades already. |
| **News** | 🔴 Do not build — see above. Happy to be overruled, but this one is a fork in what the product is. |
| **Images** | ✅ Build with Chatter, from **our own** badges and mugshots. |

📌 **If the answer is "build News anyway"**, the version I would argue for is *narrow*: team-news and
injury headlines **only**, filtered to clubs in your squad, with the source named on every row — ⚠️ *which
is a Signals feature wearing a News label, and that is rather the point.*


---

## What building Chatter found

⭐⭐ **The estimate held: it was one endpoint.** `community_signals` needed no change at all — the service
wraps it, flags rows against the squad, and hands back the same player shape every other answer uses.

⚠️⚠️ **The gating question was answered before any UI existed.** `src/community.py` has warned since
ADR-059 that *"the cloud IP may be blocked"*, and a tab that is permanently empty in production is not a
feature. So the service half shipped first and was called **from Render**: Reddit answers. ⭐ *The order
of work was chosen so the expensive half could be abandoned cheaply.*

⚠️⚠️⚠️ **It needed a cache, and `RedditRssClient`'s own docstring said so** — *"cache + rate-limit-respect
live at the caller"* — and mine had none. Two taps a minute apart were two fetches, and the second came
back *"Reddit didn't respond"* the first time I tried it. ⭐ *A tab that fails when you open it twice is a
tab people conclude is broken.* Ten minutes, keyed on **nothing**: `player_ids` only flag and `limit` only
slices, so one fetch serves every caller. A failure is never cached — *caching an outage makes a blip into
a symptom.*

**Four mutants survived honestly, and each led somewhere:**

- Two were **fixture** gaps: a two-entry feed cannot show a post cap being applied, and a cache test that
  warms the cache with the generous case cannot see a stingy fetch. ⭐ *A branch the test data cannot
  reach is not being tested.*
- One was a **genuine redundancy**: the freshness check also tested `rows is not None`, which made the
  "only cache a success" rule unfalsifiable. ⚠️ *Defence in depth on a rule nobody can break is defence
  against nothing, and it hides which line is doing the work.* One guard now, and both mutations die.
- One was a **real gap in the UI test**: I asserted the word *"yours"* and never the outline, which is
  what the eye actually finds first.

⭐ **And the player-shape sweep demanded the new endpoint before I remembered to add it** — the guard that
exists because *"a guard that requires manual registration is a guard that will be forgotten."*

📌 **Looks like a bug, is not:** the initials fallback appears more on this screen than anywhere else. The
Premier League CDN 403s for players it holds no photo of — new signings, mostly — and ⭐ *those are exactly
the players a subreddit has suddenly started talking about.* Measured: Brobbey, Barry and Tzolakis 403;
Haaland, Palmer and Isak 200.

## What shipped

**Service:** `chatter()` + `ChatterRequest` + `POST /api/v1/chatter`, with a ten-minute shared cache.

**App:** `chatter_view.dart` — a fourth scope on the Signals bar, each row carrying its mugshot, its
count, the threads behind it, and an outline if he is yours.

**Tests:** 12 service, 5 widget, mutation-tested **9/9** and **8/8**.
