# MadBoots — Phase 1 Architecture Audit

**Date:** 2026-09-18 · **Status:** 📋 For review — findings and recommendations, no structural code changes made
**Scope:** the existing codebase, database, auth, data pipeline, analytics, Streamlit app and deployment,
assessed against a target of **Streamlit web/desktop + a Flutter mobile client**, iPhone first.

> Every number in this document was measured against the working tree at `3bc3556` + ADR-210, not estimated.
> Where I could not verify something, it is marked **unverified** rather than assumed.

---

## 0. Executive summary

**The good news is larger than expected, and it is concentrated in one place.**

`src/analytics` — 7,525 lines, the entire xP/transfer/captain/optimiser engine — imports **nothing** but
`src.analytics.*` and `src.fpl_rules`. No storage, no Streamlit, no UI. It takes rows in and returns dicts
out. ⭐ **The engine is already a library.** It does not need extracting from Streamlit, because it was never
in Streamlit. That removes what I expected to be the largest refactor in the plan.

**And it is fast.** Measured on the live board (659 players):

| operation | time |
|---|---|
| load the whole board (players + fixtures + both histories) | **21 ms** |
| `decision_xp`, 5-gameweek horizon, all 659 players | **11 ms** |
| `suggest_transfers` for one squad | **18 ms** |
| `select_squad` (PuLP integer program — the heaviest thing in the app) | **94 ms** |

This has a direct architectural consequence: **§17's premise ("avoid expensive calculations per request")
is mostly false for this application.** There is no expensive calculation. A single small API instance can
serve the whole board's analytics per-request without a cache, a queue, or a worker pool. That deletes a
large amount of infrastructure from the plan.

**The bad news is also concentrated, and it is not where the plan looks.**

1. 🔴 **The Supabase database is effectively public.** Seven tables, one shared anon key, RLS either disabled
   or `using (true)`. Anyone holding the key can read, overwrite or delete **every user's squad and the entire
   tester email list**. That key currently lives in a server-side Streamlit secret; in a mobile app it ships
   inside the binary and is trivially extractable. **This is a blocker for shipping to strangers, and it is
   the reason the auth question is not deferrable.**
2. 🔴 **There is no data pipeline.** Data reaches users when *you* run `reseed` on your Mac and commit a
   956 KB binary to git. There is no scheduled ingestion anywhere in the repo — the only cron job is a
   mirror backup.
3. 🟠 **There is no API.** `src/web` is **104 lines** serving five HTML pages. `DIRECTION.md` calls it "the
   seed of that API"; it is a demo. The API is greenfield.
4. 🟠 **47% of `src/` is presentation that Flutter cannot reuse** — and it is where most of the last year went.

**Recommended sequence** (unchanged from your revision, with one insertion): audit → **RLS + identity** →
autonomous pipeline → API boundary → Flutter → iPhone MVP. The security item moves to the front because it
gates the pipeline design (what writes where, as whom) and because it is a live exposure today.

---

## 1. Current architecture

### 1.1 What the code actually is

| area | lines | reusable by Flutter? |
|---|---|---|
| `src/analytics` — the engine | **7,525** | ✅ **entirely**, unchanged |
| `src/web_streamlit` — the web UI | **10,204** | ❌ none |
| `src/ui` — text/markdown renderers (CLI + Streamlit) | 2,057 | ❌ none (but see §3.2) |
| `src/api` — the **FPL client** (fetching from FPL, not your API) | 447 | ✅ server-side |
| `src/web` — the "frozen FastAPI edge" | **104** | ⚠️ demo only |
| `src/storage.py` | 966 | ⚠️ SQLite-specific |
| `src/cli.py`, `ask.py`, `ingest.py`, `models/`, `config.py`, … | ~4,700 | partial |
| **total `src/`** | **26,037** | |
| tests | 25,142 (118 files, 1,898 tests) | — |

### 1.2 Data flow today

```text
FPL API ──► src/api/client ──► src/ingest.refresh ──► Storage (SQLite: data/fpl.db)
                                                              │
                                        `reseed` copies fpl.db ▼
                                                      data/seed.db
                                                              │
                                              👤 YOU: git commit + push
                                                              ▼
                                            Streamlit Community Cloud redeploys
                                                              ▼
                                                    testers see new data
```

⚠️ **The human is a load-bearing component.** Between your commits, the deployed app serves whatever you last
pushed. The `data: GW4 update` / `data: post GW4 update` commits in the log are this mechanism.

### 1.3 Auth and user state today

Two unrelated systems, both inside the Streamlit layer:

- **Identity:** Streamlit's native `st.login()` (Google OIDC, Authlib). Off unless `[auth]` is in secrets.
  Admission is by allow-list against `beta_users`; a non-listed sign-in is written to `beta_waitlist`.
- **User data:** seven Supabase tables reached over **PostgREST** with a single `FPL_STORE_KEY` anon key.
  The squad is keyed by `sha256(email)` (`auth.user_key`), so raw addresses are not stored in `squads`.

⚠️ **Supabase Auth is not in use.** Supabase is a database with an open door, not an identity provider here.
That distinction is the whole of §4 below.

### 1.4 Deployment

| piece | where | cost |
|---|---|---|
| Streamlit app | Community Cloud, `madboots.streamlit.app` | £0 |
| Landing page | Cloudflare Pages, `madboots.com` (static, outside the repo at `~/madboots-site/`) | £0 |
| Database (FPL data) | committed `data/seed.db` in the repo | £0 |
| Database (user data) | Supabase free tier | £0 |
| CI | GitHub Actions — ruff + pytest on 3.13/3.14 | £0 |
| Scheduled jobs | **one**: `mirror.yml`, a repo backup at 04:17 UTC. **No data job.** | £0 |

---

## 2. Database review

### 2.1 FPL data — SQLite, 956 KB

| table | rows | cols |
|---|---|---|
| `players` | 659 | 41 |
| `player_history` (per-GW, this season) | 2,547 | 28 |
| `player_history_past` (past seasons) | 2,097 | 16 |
| `fixtures` | 380 | 8 |
| `player_availability` (ADR-203) | 670 | 6 |
| `player_transfer_flow` (ADR-210, new today) | 0 | 7 |
| `teams` | 20 | 7 |
| `headline_events` | 14 | 5 |

**⚠️ There are no indexes at all** beyond implicit primary keys. Irrelevant at 956 KB and 6,400 rows;
it must not be carried into Postgres unexamined.

**Growth is negligible.** A full season of per-GW history is 659 × 38 ≈ 25,000 rows. Even with per-gameweek
availability and transfer-flow snapshots, the entire FPL dataset stays comfortably inside Supabase's 500 MB
free tier for **years**. 💡 *Database size is not a cost driver for this product and should not shape the
architecture.*

### 2.2 User data — Supabase, seven tables

| table | key | RLS | holds |
|---|---|---|---|
| `squads` | `handle` (or `sha256(email)`) | `using (true)` | the user's 15 players, jsonb |
| `beta_users` | `email` | `using (true)` | **raw tester emails** (allow-list) |
| `beta_waitlist` | email | **disabled** | raw emails of non-admitted sign-ins |
| `user_prefs` | `user_key` | policies per ADR-147 | manager id, league id |
| `player_watchlist` | — | **disabled** | watchlist rows |
| `maddie_videos` | — | public read | marketing video links |
| `events` | identity | — | anonymous usage analytics (ADR-100) |

### 2.3 🔴 The security finding, stated plainly

The docs are candid that this is deliberate — `CLOUD_SQUADS.md` says *"a handle isn't security — this is a
hobby beta on public FPL data"*, and for a hobby beta among people you know, that judgement was correct.

It does not survive the move to an app store, for three reasons:

1. **The anon key becomes client-side.** Today it is a Streamlit server-side secret. In Flutter it is compiled
   into the binary and can be extracted from the IPA in minutes. That is *expected* for a Supabase anon key —
   the whole design assumes RLS is doing the protecting. **Here RLS is not protecting anything.**
2. **`beta_users` and `beta_waitlist` hold raw email addresses** with open read. That is a personal-data
   exposure with GDPR weight, independent of the app question.
3. **RLS cannot be fixed without real identities.** A policy like `using (auth.uid() = owner_id)` requires
   Supabase Auth to have issued that `uid`. The current `sha256(email)` key comes from Streamlit's OIDC
   session and means nothing to Postgres. ⭐ **This is why the auth migration and the RLS fix are one piece of
   work, not two** — and why §4 of your plan cannot simply be deferred.

**Recommendation:** treat this as the first work item after the audit, ahead of the pipeline. It is a live
exposure, it is cheap to fix for the *current* web app (tighten policies, stop open-reading emails), and the
*full* fix (Supabase Auth + owner-scoped RLS) is a hard prerequisite for any mobile client.

---

## 3. Gap analysis

### 3.1 Reusable unchanged ✅

- **The whole of `src/analytics`.** Verified: its only `src.*` imports are `src.analytics.*` and
  `src.fpl_rules`. It is pure, takes rows and dicts, returns dicts. This is the crown jewels — 210 ADRs of
  reasoning — and it moves to the server untouched.
- **`src/api`** (the FPL client, retry/throttle) and **`src/models`** — server-side ingestion, unchanged.
- **`src/ingest.py`** — the refresh logic itself is sound; only its *trigger* and *destination* change.
- **The test suite.** 1,898 tests over the engine keep their value entirely.

### 3.2 ⭐ The most useful finding for the API

**The analytics already return JSON-shaped data.** `src/ui` is a *separate* text renderer layered on top —
so the structured layer an API needs already exists beneath it. Measured:

```text
decision_xp(...)   → list[dict] with keys {id, web_name, team, position, xp, by_gameweek,
                     rate, rate_source, minutes_weight, ep_next, difficulty, …}
                   → json.dumps() succeeds unmodified ✅
```

**But not everything:**

```text
gameweek_plan(...) → {captain, lineup, transfer, transfers, flags, timing, cliff, …}
                   → json.dumps() FAILS: lineup.start / lineup.bench carry raw sqlite3.Row ❌
```

**Implication:** the API needs a thin **serialisation boundary** (Pydantic response models) — not to
restructure the analytics, but to convert player *rows* into player *DTOs* at the edge. This is a
well-bounded job, perhaps a day, and it is the right place to draw the public contract anyway (§5 of your
brief: "do not expose internal implementation details"). ⚠️ Doing it *properly* also decouples the API from
`sqlite3.Row`, which is what makes the Postgres migration cheap.

### 3.3 Needs building 🔨

| # | item | size | notes |
|---|---|---|---|
| 1 | **Owner-scoped identity + RLS** | M | Supabase Auth; migrate `sha256(email)` keys to `auth.uid()`; rewrite every policy |
| 2 | **Autonomous ingestion** | **L** | scheduled refresh → validate → analytics → Postgres. *The largest new system.* |
| 3 | **SQLite → Postgres** for FPL data | M | `Storage` is the only coupling point (966 lines); analytics never touch it |
| 4 | **FastAPI service** + DTO layer | M | greenfield; `src/web`'s 104 lines are not a foundation |
| 5 | **Flutter app** | **L** | complete UI rebuild |
| 6 | **Release/ops** | M | crash reporting, store listings, account deletion, CI for mobile builds |

### 3.4 Not reusable, and it is a lot ❌

`src/web_streamlit` (10,204 lines) and `src/ui` (2,057) do not port. That is the pitch (ADR-084), player
cards, Player/Team DNA (ADR-118/119), Scout (ADR-167), Signals (ADR-150), the shared components (ADR-163),
the responsive fixes, the theming — roughly **a year of UI sprints**.

⭐ **This is the honest cost of the plan and it should be stated once, clearly: you are building a second
product that shares a brain.** Not a port. The brain is excellent and free; the body is new.

---

## 4. API review — what genuinely needs FastAPI

Your §4 instinct was right, and the measured timings sharpen the boundary into something simple:

> **If the operation's input is the whole board, precompute it. If its input is a user's squad, compute it
> live in FastAPI.**

### 4.1 Direct Flutter → Supabase (no API) ✅

Board-wide values that are identical for every user, written by the pipeline once per refresh:

- players, teams, fixtures, gameweek state and deadlines
- **per-player xP over each horizon** (`decision_xp` output — this is board-wide and precomputable)
- the stat boards: xG, over/under, DefCon, clean sheets, set pieces, price predictions
- Player DNA / Team DNA percentiles
- Signals: crowd exodus, trending, headline events
- the user's own rows: squad, watchlist, preferences (under owner-scoped RLS)

**This is the majority of the app's read surface**, and it wants no API at all — PostgREST with RLS serves it.

> ### 📍 Status, 2026-09-20 — one of these now exists
>
> ⚠️ **When this section was written, none of the derived boards were in the database.** They were computed
> in Python at read time, which a Flutter client cannot do — so §4.1 described a read surface that was not
> there. It read as a description and was a requirement.
>
> ✅ **Per-player xP is now published by the pipeline** (ADR-213): one row per player carrying a horizon-8
> board with **unrounded** per-gameweek values, so any horizon 1–8 is derivable exactly. Validated before it
> replaces the last good board, and pinned by a test that recomputes and compares.
>
> ✅ **Team DNA is now published too** (ADR-214) — 20 clubs, eight percentile axes each.
>
> 🔴 **The rest are empty, not deferred.** Measured at GW5: over/under and DefCon reliability gate at 900
> minutes and the board's maximum is **450**; worth-noticing returns nothing; Player DNA returns a profile
> for every player whose peer pool is **one player or none**, so every percentile is the no-peers default.
> 📅 Re-measured on or after **2026-11-01**. ⬜ `trending` is not published at all — it is `ORDER BY` on a
> column the client already holds.
>
> ⚠️ A published board is anchored to the gameweeks it covers (`first_event`), because the window moves at
> every deadline. A client that ignores that will misread it as current.

### 4.2 Flutter → FastAPI ✅

> ⚠️ **Amended by [ADR-219](../06_Decisions/ADR-219-one-contract-two-transports.md), which built the first
> of these.** The endpoints below are right; *"Streamlit migrates onto the same API"* is not. The contract
> lives in `src/service/` as plain functions — FastAPI wraps them for Flutter, Streamlit imports them
> in-process — because a separately-hosted service turns every squad analysis the web app renders into a
> round trip, on the app spike 017 had just taken from 3,026 ms to 20 ms. ⭐ *A contract with one consumer
> is still a guess; the guarantee is bought back with a test that the HTTP body equals the in-process
> answer serialised.* ✅ **All six are now built** — `analysis` (ADR-219), then `transfers`, `captain`,
> `gameweek-plan`, `route` and `build` (ADR-220). ⚠️ Building the five found that ADR-209's transfer
> tie-break had reached the engine and only four of its ten call sites, including the web app's own
> Transfer tab.

Operations whose input is *this user's fifteen players*, which cannot be precomputed:

| endpoint | engine call | measured |
|---|---|---|
| `POST /api/v1/squad/analysis` | `analyse_squad` + `decision_xp` | ~30 ms |
| `POST /api/v1/squad/transfers` | `suggest_transfers` / `suggest_transfer_plan` | ~18 ms |
| `POST /api/v1/squad/captain` | `captain_picks` | ~15 ms |
| `POST /api/v1/squad/gameweek-plan` | `gameweek_plan` (the assembler) | ~35 ms |
| `POST /api/v1/squad/route` | `route_to_player` (ADR-207) | ~20 ms |
| `POST /api/v1/squad/build` | `select_squad` (PuLP) | **~94 ms** |

⚠️ **Send the squad as a list of player ids and let the server load the board.** Do not have Flutter upload
player rows — that would put the client in the position of defining the engine's input, which is exactly how
two implementations of the same rule appear (this codebase has three ADRs about that: 123, 127, 181).

### 4.3 Verdict on FastAPI

**Required — but small.** Roughly six endpoints, all thin wrappers over existing pure functions plus a DTO
layer. It is *not* a proxy in front of Supabase, and it should not become one.

💡 **It could be deferred for a read-only first slice** (browse players, fixtures, your squad) — but the moment
the app does the thing MadBoots is *for* (captain, transfers, the week's plan), it is needed. I would build it
in Phase 3 rather than pretend it can wait.

---

## 5. The data pipeline — the real work

### 5.1 What has to change

```text
  TODAY                                    TARGET
  ─────                                    ──────
  you, on a Mac                            a scheduled job
  → SQLite file                            → validate
  → git commit (956 KB binary)             → run analytics
  → Cloud redeploy                         → write Postgres
  → testers see it                         → every client reads it live
```

Your §9 requirement — *data changes must never require an app release* — is correct and is the single
constraint that most shapes this build. ⚠️ **It is also the requirement the current architecture most
violates**, since today a data change requires a *deploy*.

### 5.2 Recommended shape (deliberately boring)

- **Trigger:** a scheduled job. GitHub Actions cron is free and already in use (`mirror.yml` proves the
  pattern), but ⚠️ its schedule is best-effort and can be delayed under load — acceptable for hourly data,
  **not** for a pre-deadline or live-gameweek refresh. A small always-on worker (Fly.io / Render free-ish
  tier) is the more honest choice if live gameweeks matter.
- **Cadence, justified rather than arbitrary** (your §10 asks for this):
  - **off-peak:** every 6 h — prices settle overnight, little else moves
  - **match-day / live gameweek:** every 5–10 min for scores and provisional points
  - **deadline day, T-6h → T:** every 15 min — team news and price changes cluster here
  - **transfer counters:** ⭐ ADR-210 established these *accumulate across the week and reset at each
    deadline*, so the pipeline must record the **end-of-cycle** reading before each deadline or that week's
    data is unrecoverable. The new `player_transfer_flow` table already does this — it is the pattern the
    rest of the pipeline should follow.
- **Freshness must be visible.** Publish a `data_status` row (last refresh, which gameweek, whether live) and
  render it in both clients. ⭐ *This codebase's own lesson (ADR-203, ADR-210): a value without its
  observation time is not evidence.*
- **Validation before publish, and it must be able to say no.** A bad FPL response should leave the last good
  data in place rather than blanking 659 players for every user at once. This is new — today the blast radius
  of a bad refresh is your laptop.

### 5.3 Why this goes before Flutter

It is the largest unknown; it is a hard prerequisite for §9; it fixes a *live* problem (your testers see
commit-fresh data today); and if you decide you do not want to own this operational burden, you will have
learned the decisive fact before writing any Dart. ⭐ **Prove the thing that can kill the plan, first.**

---

## 6. Flutter review

### 6.1 Recommendations

| decision | recommendation | why |
|---|---|---|
| **State management** | **Riverpod** | compile-safe DI, trivial to test, good async/caching primitives. Bloc is more ceremony than a read-mostly analytics client needs |
| **Navigation** | `go_router` | deep links (a shared player/squad link) fall out for free |
| **Local cache** | **Drift** (SQLite) | ⭐ you already think in SQLite tables; the shapes map almost 1:1, and it gives real offline reads |
| **Networking** | `dio` + generated models | interceptors for auth refresh and ETag handling (§10) |
| **Models** | generate from the OpenAPI schema FastAPI already emits | one contract, no hand-written duplicates |
| **Responsive** | layout by breakpoint from day one, ship phone only | §11's architecture, §5's scope |

### 6.2 The product shape

Do **not** port the 7-tab Streamlit IA. On a phone, MadBoots is about four questions:

1. **This week** — captain, flags, the one recommended move, confidence
2. **My squad** — the pitch, xP, who to bench
3. **Transfers** — routes in and out, the longer view
4. **Players** — search, compare, the card

Everything else (DNA radars, Scout boards, Leagues, H2H) is a second release. ⭐ *The mobile app should be
the decision layer; the web app stays the exploration layer.* That is a real product distinction, not a
limitation — and it matches the positioning: **the analytics decide, you make the call.**

---

## 7. Infrastructure and cost

### 7.1 Required now

| item | option | cost |
|---|---|---|
| Postgres + auth | Supabase free tier | **£0** (500 MB; you need <10 MB) |
| FastAPI host | Fly.io / Render small instance | **£0–5/mo** |
| Scheduler | GH Actions cron, or the same worker | £0 |
| Streamlit | unchanged | £0 |
| **Apple Developer Program** | required to ship | **£79/yr** |
| Google Play | later | £20 once |
| Crash reporting | Sentry free tier | £0 |

**Realistic run cost for the iPhone MVP: under £10/month plus the Apple fee.** The measured performance is why
— no cache layer, no queue, no worker pool, no read replicas. ⚠️ *Do not let the architecture diagram talk you
into infrastructure the timings say you do not need.*

### 7.2 Scaling triggers (not now)

- Supabase free tier pauses inactive projects and caps bandwidth → **paid tier (~£20/mo) at real usage**
- FastAPI single instance is fine to ~thousands of daily users at these timings; scale horizontally when
  p95 latency degrades, not before
- The first genuine cost driver will be **push notifications** at volume, not compute

### 7.3 App Store obligations the brief omits

- 🔴 **Sign in with Apple is mandatory** (Guideline 4.8) if you offer Google sign-in. Your §14 lists Apple as
  "potential" — it is required. Supabase Auth supports it; it needs the Apple Developer setup.
- 🔴 **In-app account deletion is mandatory** (since June 2022) for any app with accounts.
- 🟠 **Guideline 4.2 (minimum functionality)** — a thin data viewer risks rejection. MadBoots is far richer
  than that, but the *first* submission must not be a stub.
- 🟠 **Privacy nutrition labels** — you collect email and usage analytics; declare both.
- 🟠 Every code change is now **1–3 days from merge to user**, permanently, and you will support multiple app
  versions against one API. §5's versioning discipline stops being optional.

---

## 8. Risks

| # | risk | severity | mitigation |
|---|---|---|---|
| 1 | **Open RLS + anon key in a shipped binary** | 🔴 **critical** | fix before any client ships; owner-scoped policies on real `auth.uid()` |
| 2 | **Raw emails readable with the anon key** | 🔴 high | tighten now, independent of mobile |
| 3 | **Pipeline unreliability** — stale or blank data with no human watching | 🔴 high | validate-before-publish; visible freshness; alerting |
| 4 | **Auth migration breaks the live beta** | 🟠 high | dual-run; migrate `sha256(email)` → `auth.uid()` with a mapping table; keep the Streamlit path working throughout |
| 5 | ⚠️ **Opportunity cost — the analytics stop** | 🟠 **high** | see below |
| 6 | Two clients drift into two behaviours | 🟠 med | one engine, one API contract; ⭐ this codebase already has ADR-123/127/181 on exactly this failure |
| 7 | App Review rejection | 🟡 med | Apple sign-in + account deletion **before** first submission |
| 8 | Postgres migration touches `Storage`'s 966 lines | 🟡 med | analytics never import `Storage` — the blast radius is one file |

### ⚠️ Risk 5 deserves its own paragraph

This is a solo project with a live season, a live beta, 1,898 tests, 210 ADRs, and an **ML Phase 1 decision
pre-registered for on/after 2026-10-26** (ADR-204). The plan above is months of work in which the analytics —
the actual differentiator — mostly stops.

Nothing in the brief says **what gets paused**. I would write that down before Phase 2 starts, because it is
the decision most likely to be regretted. My suggestion: let the **GW8 ML review happen on schedule** (it is
a day's work, its date was pre-registered, and skipping it breaks the project's own rule that a decline needs
a date), and accept that in-season analytics work otherwise pauses.

💡 **Timing note:** GW5 is tonight. A realistic first submission is the back half of the season at the
earliest. That is *fine* — but it argues for building the pipeline now, while data questions are fresh, and
shipping the app for the run-in or next season rather than rushing it mid-campaign.

---

## 9. Migration plan

**Phase 1 — Audit** ✅ *this document*

**Phase 1.5 — Secure the existing system** 🔴 *new; days, not weeks*
Owner-scoped RLS, stop open-reading emails, rotate the anon key. Protects today's users regardless of what
happens next. Independent of mobile.

**Phase 2 — The autonomous pipeline** *the big one*
Scheduled ingestion → validation → analytics → Postgres. FPL data moves from a committed `seed.db` to a live
database. **Streamlit cuts over to it first** — proving the pipeline against the client you already have, with
users who will tell you when it breaks. Exit criterion: *two weeks with no manual `reseed`, including a
deadline and a live gameweek.*

**Phase 3 — API boundary** — 🟢 *the endpoints are done; auth is not*
✅ **All six squad endpoints and the DTO layer are built** (ADR-219 → ADR-220). ⏳ Supabase Auth + identity
migration (risked, dual-run) — **not started**, and it is what remains of this phase. ⭐ These endpoints take
*ids in, analysis out*, so there is no user row to protect; a **saved squad** is the different question.

⚠️ Streamlit does **not** migrate onto the HTTP API — see the amendment at §4.2. It imports the same contract
in-process, and Health is its first consumer, so the contract is exercised by a real client before Flutter
exists. ⭐ *A contract with one consumer is a guess* — the principle stands; the transport changed.

**Phase 4 — Flutter foundation** — auth, networking, Riverpod, Drift cache, navigation, theme, responsive
scaffolding for all four form factors, phone-only rendering.

**Phase 5 — Vertical slice** — sign in → my squad → player → xP, on a real iPhone.

**Phase 6 — iPhone MVP** — the four core screens, crash reporting, account deletion, Apple sign-in, submission.

**Phase 7+ — iPad → Android phone → Android tablet**, no architectural change.

---

## 10. Your §23 questions, answered

| question | answer |
|---|---|
| **What stays in Streamlit?** | The whole web/desktop UI. It is the exploration surface and it keeps its Python-native strengths. |
| **What moves into reusable services?** | Almost nothing needs moving — `src/analytics` is *already* a standalone library. Only `Storage` changes (SQLite → Postgres) and a DTO layer is added. |
| **What belongs in Supabase?** | All board-wide precomputed data, plus user squads/watchlists/preferences under owner-scoped RLS. |
| **What can Flutter read directly?** | Everything in the line above. This is the majority of the read surface. |
| **What genuinely requires FastAPI?** | Anything taking the user's squad as input: analysis, transfers, captain, gameweek plan, route, squad build. ~6 endpoints. |
| **What stays server-side?** | The engine, all ML, the FPL API credentials, the pipeline. Flutter never computes FPL logic. |
| **What belongs in Flutter?** | Presentation, navigation, local cache, offline degradation. Nothing else. |
| **What should be cached locally?** | Squad, fixtures, player list, last-known analytics, watchlist — via Drift, with a visible "as of" stamp. |
| **How should live data refresh?** | ETag/`If-None-Match` on board-wide reads; cadence by context (6 h → 15 min → 5 min); Supabase realtime only for genuinely live gameweek scores. |
| **What infrastructure is actually required?** | Supabase, one small API instance, a scheduler, Sentry. **That is all** — the measured timings rule out the rest. |
| **What can remain free?** | Everything except the £79/yr Apple fee, until real usage arrives. |
| **What waits for scale?** | Paid Supabase, horizontal API scaling, a CDN, push at volume, ML serving infrastructure. |

---

## 11. ML architecture note

Per your instruction, ML stays server-side and independent of the client. The current state supports this
easily: ML Phase 0 is complete (ADR-201/202/203), Phase 1 is **held pending the GW8 review** (ADR-204), and
nothing in the app consumes a model today. When a model does ship, it writes its outputs into the same
Postgres tables the pipeline already populates — so **retraining or replacing a model never touches the
mobile app**, exactly as §8 requires. No mobile-side inference, now or planned.

---

## 12. Recommendation

**Proceed — with the security fix first and the pipeline before Flutter.**

The plan is sound, the engine is in far better shape than a year-old hobby codebase has any right to be, and
the measured performance means this can be built and run for under £10/month. The two things I would change
from the brief as written are already in your revision, plus one insertion:

1. 🔴 **Phase 1.5 — fix RLS and the email exposure now.** It is a live issue, it is cheap, and it is a hard
   prerequisite for a shipped client.
2. **Pipeline before Flutter**, cutting Streamlit over to it first so it is proven by real users.
3. **Write down what pauses.** The ML review on 2026-10-26 should survive; most other in-season analytics work
   will not.

⭐ **The thing to protect throughout is the engine.** It is 7,525 lines, it imports nothing, it is covered by
1,898 tests, and it is the only part of MadBoots that would be genuinely hard to rebuild. Every architectural
decision below it should be judged on whether it keeps that layer pure.
