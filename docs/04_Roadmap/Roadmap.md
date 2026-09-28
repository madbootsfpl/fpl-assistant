# MADBOOTS Roadmap

*Re-cut 2026-08-24 (post-GW1) into a single forward-looking page with an explicit **end-state vision**.
Everything known is pulled in — including things we may well decide **not** to build; a parked idea with a
recorded reason is worth more than a forgotten one. Phase 1 shipped as a **CLI** (ADR-002/003), not the
original web-first plan; that plan and its reconciliation live in git history and the per-sprint docs.
Previous consolidations: 2026-08-05 (Sprint 050), kept current through Sprint 172.*

**Status legend:** ✅ Done · ◑ Partial · ⬜ Not started · ⏳ Gated (waiting on data or a decision) · 🅾️ Declined

---

## Where we are — 2026-09-28, GW5 played

A mature FPL assistant: an analytics + optimisation core, a decision-support suite, a grounded
natural-language layer (`ask` + `chat`), a deployed Streamlit web app, a crowd/signals lens, and the two
differentiators — **Player DNA** (ADR-118) and **Team DNA** (ADR-119).

**3,005 Python tests · 481 Dart tests · 326 ADRs · CI green · live at madboots.streamlit.app / madboots.com.**
⚠️ *Counted 2026-09-28. The Dart half is listed separately because until ADR-322 it was not in CI at all — ⭐ a total that silently included 481 tests nothing ran was the more flattering number.*

⭐ **The shape of the work changed in September, and the roadmap below predates it.** Read the rest of this
page knowing three things:

1. **The product is in a closed beta with real testers**, not a solo tool. Several entries below are written
   as though the only user is the author.
2. **The data refreshes itself** (ADR-211). Squad data is in **Postgres**; a scheduled GitHub Action keeps it
   current. Any entry that assumes a manual `reseed` before a deadline is describing the old world.
   📅 *Exit criterion running: two weeks with no manual `reseed`, including a deadline and a live
   gameweek — **live since 2026-09-19, so it is met on or after 2026-10-03** if nothing needed a hand.*
   ⚠️ *Dated on 2026-09-21 because "two weeks" with no anchor cannot expire; it just keeps sounding
   current — the same rot ADR-212 found in a "(tomorrow)" that had been true in August.*
3. ✅ **Mobile shipped** — the first phase driven by user feedback rather than by what was next in the
   plan, and it is done: Flutter on **Android and iOS** from one codebase, nine testers, self-publishing
   releases (ADR-282/290). See [Mobile_Platform_Audit.md](../03_Architecture/Mobile_Platform_Audit.md)
   for the plan it came from. ⚠️ *This line read "the next phase is mobile" for three weeks after the app
   was on people's phones.*
   **Phase 1 ✅** the read surface is proven (Flutter reads the published board straight from Supabase — 667
   players, 162 KB, 511 ms). **Phase 2 ✅** the pipeline (ADR-211). **Phase 3 🟢 endpoints done:** all six
   squad endpoints are built and smoke-tested (ADR-219 → ADR-220), with Streamlit's Health tab as the web's
   in-process consumer. ⏳ **What remains of Phase 3 is auth** — Stage C, Supabase Auth and the identity
   migration; the endpoints take *ids in, analysis out*, so a **saved squad** is the different question.
   ✅ **Signals shipped 2026-09-22** (ADR-232), squad-scoped and ordered by evidentiary strength. ⭐ The
   *what-changed* view needed **no new data**: every signal carries a stable key and the **device** is the
   thing with a memory of this user.

   ✅ **The competitor-review pass is complete** (ADR-234 → ADR-238), run because the testers benchmark
   against Fantasy Football Hub and will phrase their feedback in its terms — ⭐ *getting ahead of the
   comparison is cheaper than answering it one report at a time.* Five changes: chip status from FPL's own
   history (234), the pitch reading three ways from one fetch (235), Boot Battle inside the transfer flow
   (236), player rows that expand into a card (237), and More as a directory with a value-showing filter
   (238). ⭐⭐ **What was NOT copied is the point**: no "AI" label — their AI-transfers feature is our Boot
   Battle and Player DNA under a fashionable name — and their help/feedback, which sends you back to a
   desktop, became a destination that sends from the phone.

   ✅ **The app runs on hardware other than this Mac** (ADR-239, 2026-09-22) — feature work stopped at the
   owner's call, because none of ADR-228…238 could be opened by anybody. ⭐⭐ The blocker was a `const`, not
   the signing: the API's address is now **runtime state with a compile-time default**, so the same build
   takes a LAN address today and a hosted URL later. The two silent-failure iOS keys are in and tested,
   and `scripts/serve_api.sh` binds `0.0.0.0` and prints the address to type in.
   📅 **Next, in the owner's order:** his own iPhone on **free provisioning** (£0, ⚠️ 7-day certificate,
   Wi-Fi only) → **poll the testers' handsets** → then the fork: **Apple £79/yr** for TestFlight, or the
   **Android** work. ⭐ Both need the API hosted; neither needs anything in ADR-239 redone.

   📌 **Still owed from that review:** tap two Players rows to Boot Battle them; the progressive-disclosure
   *"Add filter"* dropdown the owner liked in their custom transfers; and a **pitch badge for new signals**
   — ⚠️ held because *being told beats going to look* costs a round trip, and that has not been measured.

   ⚠️ **The audit's §4.2 was amended by building it** — Streamlit does *not* migrate onto the HTTP API; the
   contract is a Python module both transports share. ⭐ *A plan survives contact with the first endpoint,
   or it gets corrected in writing where the next reader will find it.*

---

# 📋 Everything open, in one list — **audited 2026-08-30**

Compiled by **reading the files and checking the code**, not from memory. Three entries were already done and
still marked open (noted inline below); the previous audit's own complaint about the homepage had likewise
outlived its problem. **Assume this list is stale before you assume the work is undone.**

## 🔒 Blocked on gameweeks — nothing to do but wait

⚠️ **Re-audited 2026-09-13 and the gate has moved.** It read *one* played round on 29 Aug, with `calibrate`
refusing (*"have 1, need ≥4"*); it now holds **4 played rounds and `calibrate` runs.** The 900-minute items are unchanged (**0 of 657** clear it — that is a ~GW10 bar, not a GW4 one), but
**the weight sitting is no longer blocked; it is due.** Two different gates were sharing one heading, and the
one that lifted first is the one nobody would notice lifting.

| item | unblocks at | note |
|---|---|---|
| In-season xMins share (ADR-125) — **the blend** | GW4-6 | ✅ **The Kinsky bug is CLOSED (ADR-173, 2026-09-02): 0.50 → 2.60 xP.** Reported 2026-08-18, open for 15 days — a role-change cold-start whose xMins was stuck at **0.18** from last season's 630 backup minutes while he was playing every minute. What remains gated here is the *blend* ADR-125 designed (weight in-season minutes against history by evidence). ADR-173 took the unambiguous cases instead — a player who has appeared in **every** completed gameweek — and left the ambiguous ones exactly where they were, so the sample-size objection this was deferred on is still intact and still waiting. |
| Market goals → attack/defence strength (**ADR-005 unblocked**) | ~GW10 | derive our own from per-fixture `xg`/`xgc`; **ranked above the weight tuning** — those tune terms we have, this adds one we lack |
| Scout's boards get current data | ~GW10 | 3 of 5 need 900 minutes and read **last season** until then |
| Ceiling / differential captaincy | GW4-6 | needs a variance distribution — the same wall the win-probability sim hit |
| DGW/BGW detection · **Evaluation & feedback loops** | in-season | Evaluation is the only item that says whether *any* of this helped |
| Tier 3 — the crowd backtest | with Evaluation | does following vs fading the crowd beat xP-only? |

## 👤 Needs you — I cannot do these  *(audited 2026-09-02)*

**Two of six were already done, and a third was never blocked on what it said.** Audited by checking the code
and the live site, not by re-reading the rows: `madboots.com` (closed 31 Aug), the **Squad Lab icon** (done
**2026-08-12**, and the *"needs the art"* it waited 21 days for was never required — 🧪 is an emoji), and the
**Maddie intro** (shipped and verified live today). Of the three that remain, **two had wrong numbers in
them** — the video row counted the series roadmap as a script and had not noticed §0 was shot, and the
uncommitted-files row said 4 when it is 6.

⚠️ **The failure mode here is not stale prose, it is a blocker that was never real.** *"Needs the art"* was
wrong the day it was written, and nothing re-reads a row that says someone else is the holdup. Re-audit this
list on sight, not on suspicion.

| item | why it matters |
|---|---|
| **Produce the video series** — **10** to shoot | ✅ **§0 (the Maddie intro) IS shot** — re-recorded and live 2026-09-02. What remains is **§§1, 2, 4-9, G, H = 10 scripts**, all current as of 2026-09-01 and none of them true before that (they described a nav that had moved three times). §8b (Ask) is retired, not pending. Suggested order in §3 — which is the roadmap table, **not a script**, and was being counted as one. ⚠️ **§G Scout must wait until ~GW10** or keep its voiceover off "this season": four of its five boards need 900 minutes and **0 of 651 players** clear that bar. Record **both CTA tails** (acquisition + in-app) in the same session. |
| **Use the Admin ▸ Ask experiment** a few times | its decision point is the GW4-6 sitting; *"I never opened it"* is a valid answer |
| The **3** uncommitted files in your tree | 2 sprint lesson docs (Sprint57, Sprint62) + `spikes/015-soccerdata/compare_npxg.py`, kept out of every commit deliberately. **Was 6** — `Sprint61_Lessons_Learnt.md` and the two `.jpeg`s it embeds were committed 2026-09-02, because the images were the owner's own design references and untracked, so git held no copy and the doc's links pointed at files on one machine. ⚠️ An earlier version of this row called them *"mentioned nowhere"* — inferred from filenames that look like camera output, never grepped for. |

## 🟢 Buildable now — nothing blocking

### 📱 Mobile — named and not built *(2026-09-24)*

⭐ Listed so none of it reads as finished. None is blocked; each is a decision or a slice of work.

- 🔴 **GitHub runs 7% of the scheduled pipeline ticks** *(measured 2026-09-25)*. `data.yml` declares
  `*/15 * * * *` and fired **5 times in 24 hours** — 47 in seven days against 672 implied. `backfill.yml`
  declares hourly and manages roughly one run in five hours. ⚠️⚠️ So *"the data refreshes itself"*
  (ADR-211) is true at a granularity of **~5 hours, not 15 minutes**, and nothing in the product says so:
  ⭐ *the staleness banner only fires when a completed gameweek has no rows at all*, never when the rows
  are five hours old. That matters most where the data moves fastest — price changes land ~02:30 UK, so a
  morning reader can be looking at yesterday's prices. 📌 **Needs a decision, not effort**: make the cron
  honest and teach `behind` about age, or drive the tick from something that actually keeps time and use
  GitHub only as the worker. ⚠️ *A schedule the platform ignores is a schedule that lies in the
  documentation as well as in the file.*
- 🔴 **The mobile API is unauthenticated and uncapped** *(named 2026-09-24, ADR-283)*. `FPL_USER_CAP` and
  `beta_users` live in `src/web_streamlit/` and have never applied to the app. That was fine while
  distribution meant *"I send you a file"*; ⚠️ **a public Android download button makes it a decision rather
  than a default.** Rate limits are what stand there today — `/squad/build` 20/min is the one that matters,
  being the only endpoint whose CPU a stranger controls. ⭐ Watch the **slowest 5% on `/squad/build`** in the
  platform panel, not the user count. Belongs with accounts (ADR-259), still parked.

### 📱 Who is actually testing the mobile app? — **answered 2026-09-24 as LOAD, not people (ADR-280)**

⭐ The owner settled it the moment it was raised: *"I am not interested in personal information"* — so the API now records **platform · version · a random install id · endpoint · duration**, and never the manager id, the IP or the body. The counting question below is closed; the **accounts** question (ADR-259) remains parked.

<details><summary>the original finding, kept</summary>

The owner, after putting the APK on a tablet: *"how do I know who is testing, does that information route
back to our admin stats on the desktop?"*

**Answer today: no, and for a structural reason.**

| | Desktop | Mobile |
|---|---|---|
| Identity | an **email**, from the beta allow-list (`beta_users`) | **none** — there is no sign-in |
| Signal | `last_seen` on sign-in · `updated_at` when a squad is saved | **nothing is sent** |
| Admin panel | 👥 Tester activity: active / dormant / lapsed / never | absent |

⚠️ The mobile app sends **zero telemetry** — a grep for `track(` / analytics in `mobile/lib/` returns only
the mantra copy. The desktop's roster (ADR-142) is built entirely on the email allow-list, and the phone
has no email because it deliberately has no accounts (ADR-259, still open).

⭐⭐ **But the server already receives everything needed and records none of it.** Every squad endpoint is
called with a `manager_id`, so the API could answer *"which managers used the app this week, and which
screens"* **without a single client change and without accounts** — it simply does not log it.

**The cheap version, if wanted:** record `(manager_id, endpoint, timestamp)` server-side and add a panel
beside the existing one. ⚠️ *A manager id is public and is their own, but this is still tracking* — it
should be said out loud in the app rather than discovered, which is the same rule the feedback relay
follows (ADR-231).

📌 **Deliberately not decided here.** It is a product question — *how much do you want to know about
testers who never asked to be measured?* — and it is entangled with the accounts question (ADR-259) that
is already parked. Named so it is not rediscovered.

</details>

*(**Sprint 61's design notes audited 2026-09-02** — the two screenshots the owner attached four days ago were
read and checked against the app. **📅 Fixtures: fully shipped**, and better than the reference in one respect
— the ticker is a badge × gameweek grid with a **difficulty digit** beside the colour, which the mockup is
colour-only. Its one real gap, a **sort control**, is now built (*Easiest run* · *Team A–Z*, easiest still the
default). **🧩 My Squad: the card already matched** — name · price · opponent · xP · armband · bench roles —
and its one real gap, the **vice-captain**, is now built end to end, including the `is_vice_captain` the
manager-ID import had been discarding. **Deliberately not built:** whole-card colour-by-points, which trades a
readable number for a hue on the surface ADR-135 taught us not to over-density. **Still open:** bank + free
transfers on the My Squad strip — we hold both numbers, but that strip was cut 5 → 3 once already (US-404) for
slivering on mobile, so it wants a gate, not enthusiasm.)*

*(**US-435 — the merged golden page — shipped 2026-08-31**, ADR-171. That was the last open item of the
17-item UX review; the review is now fully closed. New follow-up from building it: **`llm.narrate` never sets
`"think": False`** while `llm.extract` does, which is most of the 27 s a narrated answer costs locally — its
own ADR, because narration and extraction were split deliberately (ADR-151/157). The **ADR index backfill is
DONE** (2026-08-31) — it had stopped at 122 while 171 ADRs existed; all 49 added, re-sorted ascending, and
`tests/test_adr_index.py` now fails if an ADR is ever filed without a row.

**The marketing scripts are current for the first time** (2026-08-31 → 09-01): every one of §§1-9 predated the
app it described — six sign-offs closed on the retired *"The AI explains"* mantra, §8 was a full script for
**Ask** (retired, ADR-168), Squad Lab and AI Tips were destinations (ADR-166/171), and **five shipped
differentiators had no marketing at all**. All re-cut; §8 replaced with **Leagues & Head-to-Head**; the Ask
draft archived as §8b with its GW4-6 trigger; **§G Scout** and **§H Team DNA** newly drafted. Also measured
rather than assumed: **Maddie reads at ~119 wpm**, not the ~150 the drafts assumed, so every stated duration
*and every beat timecode* was optimistic by 25-70% — all recomputed. §§4-5 became **~90s YouTube pieces**
(owner's call) rather than being cut down; they are searched for, so they compound instead of decaying.)*

- **Multi-GW transfer-path planner** ◑ — the timing arithmetic shipped (ADR-132); the *path search* was declined on evidence and would need a real branching market to be worth revisiting.
- **Player-card advanced stats** (Key Passes, Shots in the Box) and **shot maps / event data** — both need an external source; FPL does not carry them. A source decision, not a build.
- **Reddit aggregate sentiment** — needs the Reddit API + a Cloud secret. RSS gives a *count*, not sentiment.
- **Pundit / video NLP** — research-heavy; the ADR-151 extraction pipeline is the obvious base.
- **Session/cookie auth** for `/my-team/{id}/` · **source versioning** · **cache TTLs** · **auth polish** — infrastructure, no user pull yet.
- **PuLP 4.0 migration** ◑ — variables migrated, `PULP_CBC_CMD` deliberately kept.

## 🅾️ Declined on evidence — do not re-propose without new data

Each was measured, and the number is in the ADR so the question does not reopen from scratch.

| item | the number that killed it |
|---|---|
| Win-probability sim (ADR-161) | one starter's points have **sd 3.51**; a 3-differential H2H has gap **sd ≈ 8.6** against typical margins of 2-5 pts → *"it's close"*, every week |
| Multi-GW path search (ADR-132) | the best sell was the **same player in all six gameweeks**; the market yielded **one** beneficial move — a tree with one branch |
| Chip-sequence ranking (ADR-143) | worth **0.3 xP**; the legality defect it hid (two chips advised for one gameweek, **28% of squads**) was the real find |
| Cache `decision_xp` for tap lag (2026-08-28) | **7 ms of a 56 ms** render, inside an interaction dominated by a websocket round-trip; a stale entry would show **wrong xP** |
| Attack/Defence FDR from FPL's own fields (ADR-005) | `strength_attack_home` is **0** after GW1 and always has been — hence deriving our own instead |
| Player clashes (ADR-145) | would have fired for **100% of squads every week** |

## ⏸️ Parked with a trigger

- **`decision_xp` fixture sensitivity** — two features came back smaller than expected because the multiplier is only ±20% (ADR-006). Revisit *with* the weight calibration, not before, and **not to make a chart look better**.
- **Donations / funded community project** — ⏸️ **PARKED 2026-09-17 by the owner**: *"let's pause on donations, we can hold to see if it becomes a reality."* The original framing (2026-09-06) was explicitly *"not to make money but to gather funding to support scale, interest and diversity in thought"* — so the reason to want money was **scale**, and scale currently costs nothing: Streamlit Community Cloud's free tier, a 50-user cap, no paid dependency. ⭐ **A funding question with no cost behind it is a question about identity, not about money**, and those are better answered by the thing actually happening. **Verified nothing is live before parking**: no `FUNDING.yml`, no sponsor or donate link in the app or at `~/madboots-site`. ⚡ **TRIGGER — whichever comes first:** (a) running the app **stops being free** (free tier exceeded, or the user cap has to rise past what it supports), or (b) **someone offers unprompted**. ✅ **What does NOT unwind:** AGPL-3.0, `NOTICE` and `CONTRIBUTING` stand on their own — they are about the **code being shared back** and about how people contribute, neither of which was a money decision. ⚠️ **What this does change:** the **FPL terms** question (ADR-205) was *elevated* by donations, not created by them — parking returns it to the posture it has always had, a personal project reading a public API, which is the same posture every refresh has used since day one. It stops being a thing to resolve and goes back to being a thing to know.
- **MADBOOTS rebrand infra changeover** (ADR-103) — repo transfer + domain, to do all together. The site source lives at `~/madboots-site`, which is the strongest argument for folding it into the repo.

---

**GW1 (2026-08-21) has been played and the season is live.** The data-hardening flip is done: per-GW history is
backfilled (609 players), and the season-to-date surfaces that reset at rollover now fall back to last season
until they can answer for themselves (ADR-126). What remains gated is **calibration** — the weights stay 0 until
`calibrate` clears its ≥4-gameweek guard at ~GW4-6.

GW1 cost us **nine-plus bugs of one species**: code that had shipped correct-looking and had **never executed
under real data** — a flag that only lies mid-gameweek, a `max()` that only misbehaves once `points_per_game`
is non-zero, `.get()` on a `sqlite3.Row` in a loop that had always been empty, a primary key that held until a
double gameweek, and *three separate cases* of a missing value rendering as a confident zero. Preseason green
tests proved much less than they appeared to.

Two habits came out of it and are now standing practice: **audit before a first occurrence** (a deliberate
DGW/BGW pass found three more bugs *ahead* of the event — repeat it before the first blank and the first chip
deadline), and **prototype before building** (it changed or shrank four features — ADR-125, 130, 131, 132 —
each time because a measurement contradicted a plausible assumption).

---

## ✅ Delivered — the condensed trail

*Kept compact on purpose; the full record is in `docs/05_Sprints/` and the [ADR index](../06_Decisions/ADR-000-index.md).*

**Core engine (CLI).** FPL API client + SQLite cache (upsert, generic migrations); ClubElo as a best-effort
second source. Custom FDR (overall + Elo), pts/£m value, **xP over a multi-week horizon**, xG/xA/xGI/xGC,
over/under-performance, DefCon, clean-sheet solidity. **One xP recipe** (`decision_xp`, ADR-041) shared by the
optimiser and the decision layer — so a squad built on xP has no phantom free transfers. **xMins v0** (ADR-038)
weights xP default-on at every decision edge. An **ILP squad selector** (PuLP) — best XI or full 15, formations,
declared bench, include/exclude, archetypes (ADR-043/044), bench-aware builds (ADR-045).

**Decision support.** `captain` (ADR-029) · `transfer` ranked by XI-gain (ADR-046) + a coordinated plan
(ADR-035) · `analyse` with a per-GW breakdown (ADR-032) · a grounded **gameweek plan** (ADR-070) · a v0
**chip-timing advisor** (ADR-082) · a **price-change predictor** (ADR-092) · **set-piece takers** (ADR-081).

**Grounded language layer.** `ask` — eight intents, all *analytics-decide, LLM-narrates*, every answer
**verified** against the data (✓/⚠, ADR-037); `chat` (ADR-047) with follow-ups; an FPL **rules** assistant over a
curated KB (ADR-085). The LLM is optional — absent, it degrades to decision + facts.

**The web edge.** A thin FastAPI slice (ADR-050, now **frozen** as the lean "also-serves-HTTP" reference) → a
measured **Streamlit spike + decision** (ADR-051) → the app we grow (ADR-052), **deployed** to Community Cloud
(ADR-053). A CSS **pitch view** (ADR-084), a **countdown** banner (ADR-086/088), the **My Squad / 🧪 Squad Lab**
IA split (ADR-105), a **player-actions panel** (ADR-108), a **per-GW xP toggle** (ADR-121), **scrollable stat
boards** with honest sort (ADR-116), a ⭐ **Watchlist** (ADR-117), **compare two players** (ADR-110).

**The differentiators.** **Player DNA** (ADR-118, S168-171) — AI Verdict → 8-axis percentile radar → AI Insights
→ performance trend, on Players ▸ Card and My Squad. **Team DNA** (ADR-119, S172) — the same fingerprint for a
club, via Fixtures ▸ 🧬 Team DNA and the My Squad ▸ Health "Your teams" strip.

**Crowd & signals (Phase 6, Tiers 1-2).** Crowd/momentum ingestion + `crowd_flags` (ADR-057), a Trending page,
an FPL **news lens**, **manager-ID import** (ADR-058), Reddit **RSS buzz** (ADR-076), **media headlines**
(ADR-093) — all degrade-gracefully, display-only.

**Product & ops.** MADBOOTS rebrand (ADR-103) · Google auth + per-user persistence (ADR-106) · cross-device
squads (ADR-094) · beta gate, waitlist and self-service unsubscribe (ADR-087/102/122) · anonymous usage
analytics (ADR-100) · the calibration harness (ADR-101).

**Post-GW1 (2026-08-24).** "Upcoming" fixtures cut by **gameweek deadline**, not FPL's `finished` flag
(ADR-123) · the cold-start xP rate shrinks by **evidence, not value** (ADR-124) · the full **per-GW history
backfill** · the gated boards, Team DNA key-players and Player DNA all **fall back to last season** rather than
showing nothing (ADR-126) · in-season xMins **deferred** with its trap recorded (ADR-125).

---

**Decision surfaces, from the rival-feature review onward.** Squad Risk Monitor and squad-grade DNA (ADR-130) ·
the pool-wide **value frontier** (ADR-138) · a forward gameweek planner, *"a plan, not a panic"* (ADR-131) ·
player clashes (ADR-141/145) · captain margin (ADR-144) · **league import and elite comparison** (ADR-141/161/162)
· transfer advice that names the dead slot (ADR-046/136) · pricing the rebuild (ADR-185) · the competitive layer
(ADR-082/141/161/177) · one 📡 **Signals** page (ADR-146/150) with *"my squad only"* reaching Community Signals
(ADR-149) · price arrows using the colour channel (ADR-140) · a loaded league persisting across sessions and
devices (ADR-106/142/147/148).

**Where the advice was wrong, and the rules that came out of it.** Two defenders at one club are one bet twice
(ADR-145/189) · a defender plays for a team (ADR-186/188) · **spend the transfers you hold** (ADR-035/186/187/191)
· bank to afford, not only to stack (ADR-186) · one recipe means every caller (ADR-041/151/173/181) · the same
build twice is the same squad (ADR-183) · name the two halves (ADR-182) · Squad Lab's three build modes were
really two (ADR-137) · sweep for the claim, not the places you remember (ADR-168/184). ⭐ **Multi-gameweek
planning was measured and closed** (ADR-132/185/186/187) — the search space was empty.

**Shape and interaction.** *Plan in the Lab, play on the pitch* (ADR-132/161/178) and *one week on the pitch,
every week in the Lab* (ADR-133/178/179) · the player-actions panel (ADR-108) · My Squad v2, tap-the-pitch
(ADR-108/133) · actions on the entity as a density change (ADR-133/135/158) · the card opens on a **tap**, not a
hover (ADR-133/139) · the Fixtures IA restructure (ADR-134) · the accent belongs to the theme (ADR-114/180) · the
🧪 Squad Lab icon (`0898efc` — ⚠️ its *"needs the art"* blocker was never real; 🧪 is an emoji) · homepage copy,
audited 2026-08-27 against `docs/08_Marketing/Homepage_Copy.md`.

**Data hardening, delivered.** Per-gameweek history ingestion (ADR-128) · rolling 3-/6-GW form windows and trend
views (ADR-159) · a per-season price sparkline (ADR-160) · the price-change predictor (ADR-092).

**The ML track, through its gate.** Phase 0a retention (ADR-201) · Phase 0b the baseline (ADR-202) ·
**availability recorded as it passes** (ADR-202/203) · 📌 **Phase 1's gate was run and the answer was "not
yet"** (ADR-173/204/205) — re-decided after GW8, on or after 2026-10-26.

**Mobile, and the platform under it.** Self-hosted Android distribution (ADR-282) · swipe through the season
(ADR-298) · the tablet's portrait pitch (ADR-285) · mini-league sub-tabs (ADR-287) · the Lab's other two modes,
which were already built (ADR-272/294) · ⭐ the **LLM intent classifier declined on measurement**
(ADR-168/307/308/309).

**Auth, ops and the guards.** Cross-device persistence, Google auth, remember-me, analytics, the beta gate and
self-service unsubscribe (ADR-087/094/099/100/106/122) · the admin tester-activity roster (ADR-120) · ⭐ **three
guards that already existed** — 481 Dart tests nothing ran, a PuLP pin in a file the deploy does not install, a
staleness test skipping its own subject (ADR-221/294/310/322) · the solver imported where it is called rather
than everywhere (ADR-322/323) · the two 2,400-line modules split along seams they already had (ADR-324/325) · and
the three orienting documents cut from **697 KB to 152 KB** — the ADR index (509→94 KB),
`PROJECT_STATUS.md` (84.5→5 KB, 86% of it a sprint log inside one line) and **this file** (103→53 KB, 46%
of which was delivered work sitting in sections meant to say what is next), all three now guarded by a
size ceiling because every prose guard passed the whole time they grew (ADR-105/326).

**The 2026-08-24 "next up", all three delivered.** Player DNA sparklines + W-D-L form dots and Team DNA's real
clean-sheet rate and team form (ADR-128) · the `_percentile` **midrank fix** (ADR-127) — a goalkeeper had read
*Goal Threat 96th percentile on a raw 0.00*, because a pool of ties was ranked as if it were ordered.

**Owner actions, closed.** `madboots.com` deployed **2026-08-31** (⚠️ the next edit to that file re-opens the
same manual step — it is outside the repo) · the Maddie intro re-recorded **2026-09-02**, dropping the *"AI
clarifies the data"* claim ADR-168 removed · the community archive's licence **resolved by reading the file**
(ADR-205) · the 🧪 Squad Lab icon, which had sat on this list for **21 days blocked on art nobody had to make**.
📊 **`history --backfill` run 2026-09-01:** 626 players, **2,071 season rows**, **1,236 per-GW rows** (was 609),
no failures; GW1 and GW2 carry scorelines and the per-GW sums match the aggregate; reseeded and pushed
(`2980ce9`). ⚠️ ClubElo had been 502 since 2026-09-01 and last-known Elo persists on `teams.elo` (Arsenal reads
2063.8); blast radius is **one CLI flag**, `fdr --type elo` — the FDR page and `decision_xp` both pin
`source="fpl"`, so nothing a deployed user sees depends on it.

## 🎯 The end state — what MadBoots is trying to be

**A tool that tells you what to do and shows its working — and admits what it doesn't know.**

The market splits into **solvers** (fplapex — optimise hard, explain nothing) and **viz tools** (aceanalyst —
show everything, decide nothing). MadBoots straddles both *and* narrates. The nearest neighbour in philosophy is
**fplanalyser** — grounded and narrative, squad grades, plain-English verdicts, "a plan not a panic".

⚠ **Recalibration (2026-08-19):** *"we explain, they don't"* is a weak claim against fplanalyser — they explain
well too. The real edge is **execution + the DNA visuals + free/honest positioning + the full workflow in one
place.** Own the *explain + DNA + honesty* lane; don't try to out-solver a solver.

### Where we actually stand (2026-08-25)

This stopped being a list of things to borrow. We have now shipped against three of the four, and **twice
declined to copy a rival's feature because our own measurements said it wouldn't work here**:

| rival | their signature | where we are |
|---|---|---|
| **fplanalyser** | Squad Risk Monitor · Squad-grade DNA · forward planner | **all three shipped** (ADR-130/131). The planner is **deliberately different**: their projected-points-vs-average framing is *noise* on our numbers (a squad's per-GW xP varies ±3%), so ours leads with fixture **exposure**, which swings 2→7. |
| **fplapex** | multi-GW transfer path · chip-sequence scan · competitive layer | Path search **declined on evidence** (ADR-132): the best sell was the same player in all six gameweeks and the market yielded *one* beneficial move — a tree with one branch. Shipped the **timing arithmetic** instead. **Chip scan resolved** (ADR-143): the ranking declined on evidence (worth 0.3 xP), the legality defect it hid — two chips advised for one gameweek, 28% of squads — fixed. Competitive layer **partly** shipped as 🏆 Leagues (ADR-141): the *differentials* half is live (effective ownership vs global, captain split, chips, movers). **H2H and the win-probability sim are still open** — see the detailed item. |
| **FFH** | the rich player card · click-a-player menu | Card beaten on our own metrics (xP · value · ownership tier · DefCon · set-pieces — none of which they show). **Tap-the-pitch live and Cloud-verified** (ADR-133). |
| **aceanalyst** | pool-wide value-frontier scatter | **Shipped** (ADR-138) — and made ours: the hover carries a tested *verdict*, not a coordinate. Building it also exposed an xMins blind spot no ranked surface had surfaced, because a frontier promotes cheap-and-high numbers rather than burying them. |

**The divergences are the position, not a shortfall.** Anyone can copy a screenshot; what is hard to copy is
having measured *whether the thing behind the screenshot works on your own data* — and having written down the
answer. Both declines are recorded with the numbers that produced them, and both carry a **checkable trigger**
for revisiting (ADR-132's is explicit: if the best move ever differs by gameweek, or three-plus beneficial moves
co-exist, the tree becomes well-posed).

**The honesty half is no longer a slogan.** When a board can't answer it says so and names the season it is
showing instead (ADR-126). When a pool can't rank a player it says that rather than drawing a shape (ADR-133's
radar guard). When a tester can't be assessed the roster shows "—" rather than 100% risk (ADR-130). When a
projection barely moves, the card says so rather than letting a 3% wobble read as a forecast (ADR-131). That is
**six or so places enforced by tests**, and it is the one lane none of the four compete in.

**In full, the end state is:**
1. **A decision engine** — one xP recipe, calibrated on real returns, with a multi-gameweek transfer path and a
   full chip-sequence plan.
2. **An explanation layer** — every recommendation carries a grounded *why* (Edge / Risk), verified against the
   data, never the model's imagination.
3. **A DNA layer** — player, team and squad fingerprints that make a shape legible at a glance.
4. **A triage layer** — what needs your attention this week, and how much you'd regret ignoring it.
5. **An honest layer** — degrade visibly, label the source, never render a guess as a measurement.
6. **An interaction layer** — tap a shirt, not a dropdown (see *Interaction*, below).

---

## ⏳ Data Hardening — gated on ~GW4-6

Prep is done and dormant (Sprint 069, ADR-060); the harness is built (Sprint 138, ADR-101) and the flip is
scripted in the **[GW1_RUNBOOK](../GW1_RUNBOOK.md)**. `calibrate` prints its own countdown — currently
*"have 1, need ≥4"*. **The harness recommends; the owner commits.** One weight at a time (ADR-101).

- ⏳ **`FORM_WEIGHT` calibration** — the main season signal; first of the three.
- ⏳ **`SET_PIECE_WEIGHT` calibration** (ADR-096) — then revisit the tier guard against observed returns.
- ⏳ **`DEFCON_MAGNIFIER_WEIGHT` calibration** (ADR-097).
- ⏳ **PARKED QUESTION — should `decision_xp` be more fixture-sensitive?** Two features came back smaller than
  the roadmap described for the same underlying reason: the fixture multiplier is ±20% at its extremes
  (ADR-006), so a squad's per-gameweek projection varies by **±3%** (ADR-131) and one player's best transfer is
  **the same in every gameweek** (ADR-132). That is a deliberate property of a smooth metric, not a bug — but
  it is worth *measuring* rather than assuming. Belongs in this sitting because `calibrate` can answer it:
  sweep the multiplier as a weight and see whether a sharper one improves rank correlation. **Do not change it
  to make a chart look better** — that is the one thing both ADRs refused.
- ⏳ **In-season minutes in the xMins share** (ADR-125) — deliberately paired to the same sitting: same
   threshold, same data. ⚠ Whoever builds it must not infer "played" from a per-GW row's presence — **FPL
   writes the row when the fixture is scheduled, not played**, so a naive minutes share zeroes two whole clubs
   for the two days their gameweek is in flight.
- ◑ **Attack/Defence FDR split** (ADR-005) — **decided 2026-08-28: derive our own** (owner ask; see the
   Backlog's *"Market goal projections"* entry). Still blocked at source — `strength_attack_home` and friends
   are **0 after GW1** and FPL never populates them — but the *"much bigger piece of work"* that clause pointed
   at got smaller: **ADR-128 put `xg` and `xgc` per player per FIXTURE in the per-GW table**, and aggregated by
   team that *is* attack and defence strength from results. Prompted by the owner asking whether we could pull
   Spreadex's per-team projected goals. **Measured first: their CS% column is not independent data** — it is
   `exp(−opponent's projected goals) + 2.9pp`, sd **0.6pp** across all 20 teams, so the market publishes ONE
   number and the rest is arithmetic. **Scraping the bookmaker is declined** (no public API, against their
   terms, their commercial product); a licensed odds API stays as the fallback if our derived number proves
   poor. ⏳ **GW4-6** — but ranked **above** the form / set-piece / DefCon weight calibrations in that batch:
   those tune terms we already have, this adds one we are missing. A real clean-sheet probability replaces
   `defcon_magnifier`'s FDR-1-5 proxy and reprices every defender and keeper (4 points each, half a squad).

---

## 🖱 Interaction — the FFH-style click layer

**The thread the owner explicitly did not want lost.** Testers keep describing Fantasy Football Hub's
interaction: *"FFH pops a menu on **clicking** a player — full card · substitute · captain."*

- 🅾️ **Drag-and-drop to reorder the bench** (ADR-084) — rejected; the ⬆/⬇ controls do the job without JS.

---

## 📊 Analysis & decision features

**Competitive-inspired (⭐ = the data already exists, near-term feasible):**

- ◑ **Multi-GW transfer-path planner** — the **timing arithmetic** shipped (ADR-132, Sprint 184: use it /
  bank it / take the hit); the **path search itself is declined on evidence** — the best sell was the same
  player in all six gameweeks and the market yielded one positive-gain move, so the tree had one branch. A
  checkable trigger to revisit is recorded in the ADR. *(original line, for the trail)* — plan several
  gameweeks ahead as a path/tree, pricing **hits (−4 now vs rolling)** against total xPts. **MadBoots spin:** a
  grounded *why* per move (Edge/Risk each step). Reuses `suggest_transfers` + `by_gameweek`. Pairs with the
  per-GW xP toggle (US-422). *(A coordinated greedy plan already shipped, Sprint 033 — this is the real one.)*
- ◑ **Full chip-sequence scan** *(fplapex)* — the **ranking is declined on evidence** (ADR-143, Sprint 197);
  the **legality defect** it would have hidden is fixed. Measured over 200 random legal squads on live data:
  two chips want the same gameweek **28% of the time** (so not a one-branch tree), but resolving it optimally
  is worth **0.3 xP median / 1.5 worst** — the same order as ADR-131's ±3% noise. A precise ordering on
  numbers that cannot carry one. **What was real:** the app was advising two chips in one gameweek, which FPL
  forbids and `fpl_rules` explicitly states — contradicting its own knowledge base. Chips now take distinct
  gameweeks, the one with the least at stake moves, and it says what that cost (0.0 xP median). *Third
  sequence/tree feature killed by a measurement here — our projections are smooth, and smooth projections make
  optimal ordering worthless.* *(A v0 chip-timing advisor shipped — Sprint 096, ADR-082.)*
- ⬜ **Ceiling / "differential" captaincy** — `captain` ranks by *mean* xP; add a variance/ceiling lens for when
  you need a differential rather than the safe pick.
- ⬜ **DGW/BGW detection** — sharpens the chip advisor; in-season data.
- ⬜ **Probabilistic xMins (the full ML model)** — per-fixture expected-minutes *probabilities* from schedule
  density, European congestion, rotation profiles. Needs in-season per-GW minutes to train, external
  European-fixture data, and a real ML effort. The rigorous successor to xMins v0 — **Phase 5, genuinely far off.**
- ⬜ **Evaluation & feedback loops** — did the suggested captain beat the template? Golden-gameweek regression;
  xP calibration; captain hit-rate; net season points. *Critical before fully trusting recommendations* — and
  the only item that tells us whether any of the above actually helped.

---

## 🤖 Learned prediction — the ML track  *(agreed 2026-09-16)*

The plan the owner brought in (a LightGBM stack over FPL + understat features) was validated and **re-ordered
before starting**: the model was not the first problem. Four phases, each with its own gate.

- ⏳ **Phase 2 — points, only if minutes pays.** Deliberately last. If a learned minutes model cannot beat
  0b's baseline, a learned points model on the same data will not either, and we will have found that out for
  the price of the smaller question.

**Standing constraint:** the deployed app has **no model** ([ADR-168](../06_Decisions/ADR-168-retire-ask-and-the-promise-with-it.md)),
so anything learned must ship as **numbers computed offline and stored**, not as inference at request time.
And whatever ships keeps the ADR-199 rule: ⭐ *a constant is measured, or declared unmeasured with a reason.*

### 📅 The scheduled review — **once GW8 is played: on or after 2026-10-26**

Written down with its criteria now, because ⭐ *a plan with no review date is a plan that gets followed past
the point it stopped being right* — and this one has a standing reason to drift: **every week that passes
adds a gameweek**, so "not enough data yet" is always true and never actionable.

**The trigger is a date, not a feeling** — and the date is read off the fixture list, not estimated: GW8's
last match kicks off **2026-10-25T16:30Z**. By then the cache holds ~8 gameweeks (~5,100 player-gameweeks at
the current 637 rows a week), which
is the first point at which a walk-forward split has enough on both sides of it to mean anything.

**What the review must answer — all four, in writing:**
1. **Has the baseline moved?** Re-run ADR-202 on 8 gameweeks (ρ 0.605 · MAE 24.0 · start call 70.1%).
   ⚠️ **Score it both ways**: with today's availability (comparable to ADR-202, leak and all) and with
   ADR-203's log (correct, but a different measurement). ⭐ *Two numbers that measure different things must
   not be plotted as one line.*
   A baseline taken once is a snapshot; the ML case rests on the gap between it and a model, so it needs
   to be a line. ⚠️ GW4 was anomalous for every forecaster — four rounds cannot tell that apart from noise.
2. **ADR-192's cold-start constant — still not set.** ADR-202 confirmed the direction (**+39.1 minutes**
   optimistic, start calls at **49.2%**) and found that correcting it makes the *ranking* worse at every
   value. The one real harm — a no-history player in a top-20 recommendation, who scored 0 — happened
   **once in 80 slots**, and n = 1 is not a rate. Eight gameweeks give ~160 slots. Decide it there.
3. **Has the licensing question been answered** (archive in, or archive permanently out)? This decides
   whether Phase 1 is *"train on 11 seasons"* or *"wait for GW20"*, and they are different projects.
4. **Apply ADR-204's pre-registered rule to the blend.** The gate was run on 2026-09-17 and came back
   **+0.4 SE against a +1 SE bar**, with hit@20 up +2.1 SE. Re-fit `k` on the 8 gameweeks — never carry the
   old one over — then ship if ρ ≥ +1 SE, or hit@20 ≥ +2 SE with ρ not falling. **If neither, Phase 1 is
   declined for the season.** ⭐ *A decline needs a date the same way a feature does.*

⚠️ **The review may conclude "not yet" — but it may not conclude it twice without changing something.** If
GW8 says wait, the next review sets a *different* gate, or the ML track is parked with a trigger like anything
else in this document.

---

## 🗣 Crowd, signals & the language layer

Tiers 1 and 2 shipped (ADR-057/058/059/093) — crowd flags, a Trending page, an FPL news lens, manager-ID
import, Reddit RSS buzz, media headlines. Momentum boards are live now that GW1 has run.

- ⬜ **Tier 3 — the crowd backtest**: does following vs fading the crowd beat xP-only? Ties into *Evaluation*.
- ⬜ **Reddit r/FPL aggregate sentiment** — needs the Reddit API + a Cloud secret (RSS buzz is a *count*, not
  sentiment).
- ⭐ 🚧 **Read the headlines we already fetch** (ADR-151, proposed; spike 206) — *owner question, 2026-08-26:
  could ML give Signals a sentiment score?* **Measured and declined as framed:** 112 headlines, **6,227 chars**,
  titles only, no labels — and the text is *reported fact with named journalists*, not opinion, so there is no
  sentiment to score. **But the Watkins → Al-Hilal story was already in the feed**, reduced to "13 mentions" —
  the exact story behind ADR-146's unexplained exodus. So: **extraction, not classification.** Rules scored
  **58% precision** with dangerous errors (two negations read as injuries; *Enzo Maresca*, a manager, matched
  as a player); local `qwen3:8b` zero-shot fixed 4 of 5 and **failed silent every time**. Design: the model
  **proposes**, the app **verifies** (closed `kind` set + resolve to exactly one `web_name`, drop otherwise) —
  the same shape as ADR-037's grounding check, so the "analytics decide" rule holds. ⬜ Prereq: fix
  `community_buzz`'s surname collision ("Palmer" listed twice). ❌ Not building: a sentiment score, a trained
  model, or a Signals+Trending blend — **blending needs weights, weights need the evaluation loop**.
- ⬜ **Pundit / video NLP** — LLM-summarise FPL YouTube / articles into structured signals. Research-heavy.
- 🔴 **Pin what affects output, and decide PuLP 4 — ADR-310 (2026-09-26).** CI had been **red for 24 days** and the eighth root cause was not a test at all: **PuLP 4.0.0 removes `PULP_CBC_CMD`**, and Render installs the same `requirements.txt`, so the **next deploy would have removed the solver in production**. Pinned to 3.3.2 — ⭐ *the solver decides which fifteen players the app recommends*, so moving to **HiGHS** is a gated change with a re-validation of the optimiser's output, not a version bump. 📌 Still unpinned and on the same argument: **`pandas`, `numpy`**. ⚠️ And `config.DB_PATH` / `config.SQUADS_PATH` still resolve from whether a **gitignored** file exists, which is what made a laptop and a runner different machines in four of the eight causes — *fixed per test, mechanism still there.*
- ⏳ **Voice input, and the Ask sequence behind it — ADR-309 (gate, 2026-09-26).** The owner asked for a **microphone**; a full conversational design came back with it and was checked against the code. 🔴 **Its premise is wrong where it costs most**: there is **no LLM in the shipped product** — `app.py:721` silences the narrator deliberately (Ollama is `localhost`; Render has none), so every Ask answer on all three platforms is pure analytics today. The gap is an **inference host** (£; **27-86 s** narration measured against **120 ms** without), not wiring. ⭐⭐ **Two of the design's own later phases are already built and client-locked**: the **gameweek briefing** (routes today, and richer than the mockup — each flag costed in points, the replacement each bench would field, its own ceiling explained) and `converse()`'s *why* / *next* / *what about* (ADR-047), which the phone cannot reach because `ask_question` calls `answer()`. ⭐⭐⭐ **Agreed order: mic → surface the briefing → plumb context → harden name resolution for dictation — none of which needs an AI decision at all**; then the host, then a fallback router (gated, above). ⚠️ The real work in voice is that **STT will mangle player names** ("Semenyo", "Ndiaye", "Cunha") — ADR-152's index absorbs it, and ADR-308 already leans on that; 🔴 plus **iOS may ship audio to Apple**, and *a plugin default is not a decision.* ✗ **TTS declined** — *audio cannot be skimmed*, and the briefing's value **is** its structure.
- ◑ **More `ask` intents / an LLM intent classifier** — **promoted 2026-08-30 by the first Admin-Ask
  evaluation (ADR-168 §🔬).** The owner asked *"what's my best strategy for FPL"* with Ollama **running** and
  got the catch-all list: `route()` matched none of the 16 intents, and it contains **no LLM reference** — so
  the same reply comes back with or without a model. **The ceiling is the router, not the narration**, and
  routing is the half a language model is actually good at. A hosted model dropped in as-is would buy a nicer
  paragraph on questions that already work and still fall through on that one. Decide at the GW4-6 sitting.
- 🅾️ **X/Twitter signals** — paid/restricted. Skipped.
- 🅾️ **Betting/odds as a lens** (ADR-093) — declined *as a lens*; a possible **Tier-3 modelling input** later,
  never a display.

---

## 🔬 Data sources we've evaluated and declined

Kept so the reasoning isn't re-litigated:

- 🅾️ **soccerdata / npXG** (ADR-016, Sprint 015) — matching works (~95% FPL↔Understat) and npXG is real, **but**
  the value is narrow (penalties score points in FPL, so penalty-inclusive xG is the relevant signal) and the
  cost is high: 14 → 72 packages including a selenium/pandas stack, scraping fragility, a season-alignment trap.
  **Revisit only if a decision-driving need appears that FPL can't meet** — and prefer a *lightweight direct
  Understat fetch* over the full library. Evidence: `spikes/015-soccerdata/`.
- ⬜ **Player-card "advanced" stats — Key Passes + Shots in the Box** — FFH shows them; they're not in the FPL
  API but *are* reachable from a free Understat/FBref fetch (per-shot coords → "in box"; KP direct). Same
  decision as above — **its own sprint and data-source ADR** if the card wants them.
- ⬜ **Shot map / zones / event-data bars** (Player + Team DNA 🔴 deferred) — same dependency, same gate.
- 🅾️ **Big Chances / Big Chances Created** — Opta-proprietary and paid. Not planned.

---

## 🛠 Infrastructure, ops & tech debt

- ⬜ **Session/cookie auth for user-specific data** (`/my-team/{id}/`) — unlocks a manager-ID fetch inside
  `analyse`/`transfer`. Native `st.login()` is the product-path upgrade above the current gate.
- ⬜ **Source versioning** — formalise "version all external sources"; confidence scoring on fallback.
- ⬜ **Cache TTLs.**
- ⬜ **Deferred auth polish** — a confirm dialog on Log out; a signed/opaque "remember me" token instead of the
  raw value (deferred as over-engineering for a hobby beta; revisit only if the raw cookie value becomes a
  concern).
- ◑ **PuLP 4.0 migration** (ADR-066) — variables migrated; `PULP_CBC_CMD` deliberately kept (COIN_CMD needs an
  external CBC that fails locally *and* on the read-only Cloud). Revisit only if we adopt `pulp[cbc]`.

---

## 🧯 Standing risks

- **Season-rollover and first-occurrence bugs.** Six in two days at GW1. A deliberate **DGW/BGW audit**
  (2026-08-24) then found three more *before* the event: a primary-key collision that silently halved a double
  gameweek, the fixture ticker hiding a double's second fixture, and the player card double-counting one — all
  three fixed (ADR-129). Auditing ahead of a first occurrence works — worth repeating before the
  first blank gameweek and the first chip deadline.
- **`ep_next` is load-bearing early.** The cold-start rate leans on it (ADR-104/124) until real evidence
  accrues; an FPL quirk in it propagates.
- **Streamlit Cloud can serve a stale build** after a push — Reboot from the ⋮ menu.
- **ClubElo is intermittent** — best-effort by design (ADR-010), degrades to last-known.

---

## Guiding principles (unchanged)

- **The CLI stays the engine** — new surfaces (web) are edges over the same analytics; generic core, policy
  at the edge.
- **Analytics decide; the LLM only narrates** — grounded, verified, optional.
- **FPL is the source of truth**; external sources degrade gracefully.
- **Learn by building, sprint by sprint** — a gate (ADR) per feature; simple over clever.
- **Degrade visibly.** An empty board beats a wrong one; a labelled fallback beats both. Never render a missing
  value as a confident zero — that lesson cost six bugs in two days.
