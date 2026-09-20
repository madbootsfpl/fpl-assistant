# Architectural Decision Record: The pipeline runs without you

**Decision ID:** ADR-211
**Date:** 2026-09-18
**Status:** ✅ **Gated and agreed 2026-09-18** (destination: Postgres · trigger: GitHub Actions · headlines: manual for now). **All six stages built (2a–2f).** ⏳ Outstanding is not code: a Supabase project, the Phase 1.5 RLS work, and the `FPL_DATABASE_URL` secret — until it exists both workflows are inert.
**Superseded By / Replaces:** Replaces the manual `reseed` → commit → redeploy path (ADR-053/056) as the way
data reaches users. Does **not** change any analytics.
**Deciders / Participants:** Tony Sheridan (Owner), Claude Code (Implementation)

---

### 📌 Context & Problem Statement

Today, new FPL data reaches users like this:

```text
you run `reseed` → a 956 KB SQLite file is committed to git → Cloud redeploys → testers see it
```

⭐ **The human is a load-bearing component.** Between commits, the deployed app serves whatever was last
pushed. For 25 testers who know you, fine. For an App Store product it is not — nobody is at a laptop at
2am, and App Review latency means you cannot patch your way out of a stale pipeline.

**And today gave a live demonstration of the cost.** ADR-210 shipped a table to record the transfer counters
before FPL resets them at each deadline. The GW5 deadline passed at 17:30Z with no refresh scheduled, so
**GW5's reading is gone permanently.** The observer existed; nothing ran it.

Phase 1's audit (`03_Architecture/Mobile_Platform_Audit.md`) named this the largest single piece of new work
in the mobile programme, and the one that — unsolved — makes the rest pointless.

---

### 🔬 Measured first

Everything below was timed against the live pipeline today, not estimated.

#### The refresh is three jobs, not one, and they differ by two orders of magnitude

| job | measured cost | needs | natural cadence |
|---|---|---|---|
| **Core refresh** — players · teams · fixtures · availability · transfer flow | **3.6 s** | FPL API only | minutes → hours |
| **Per-GW history backfill** (`history --backfill`) | **~3.3 min** (659 throttled calls @ 0.3 s) | FPL API, heavily | once per gameweek, after results |
| **Headline extraction** (`enrich_headlines`) | **64 s** | 🔴 **a local LLM** (Ollama `qwen3:8b` on `localhost:11434`) | daily-ish |

⭐ **The job that must run often is the cheap one.** A 3.6-second task can run every 15 minutes for nothing.
That single number removes most of the imagined infrastructure from this phase.

#### 🔴 Automating the *current* mechanism is ruled out by arithmetic

The obvious cheap step — keep `seed.db`, just schedule the commit — does not survive contact with a number:

| cadence | commits/yr | git history added per year |
|---|---|---|
| every 6 h | 1,460 | **~1.3 GB** |
| hourly | 8,760 | **~8.0 GB** |
| every 15 min | 35,040 | **~31.9 GB** |

A SQLite binary delta-compresses poorly, so each commit costs close to full size. ⭐ **This is decisive: the
*destination* has to change, not merely the trigger.** There is no cheap intermediate that keeps the committed
snapshot, so Phase 2 necessarily contains the Postgres migration.

#### The migration is smaller than it looks

`src/analytics` imports `Storage` **nowhere** (Phase 1 audit) — the coupling is one file, 966 lines, and
within it:

- **9 × `ON CONFLICT … DO UPDATE`** upserts — **portable to Postgres unchanged**
- 3 lines of connection/`row_factory` setup
- **4 uses of `PRAGMA table_info`** in `_migrate()` / `_rekey_history()` → `information_schema.columns`
- `sqlite3.Row` type hints — cosmetic

And the analytics already read rows through `_get(row, key)` helpers that handle **dict *or* Row**, so
psycopg's `dict_row` factory satisfies them without touching the engine.

---

### 💡 Options Considered

#### Destination

| option | verdict |
|---|---|
| **Commit `seed.db` on a schedule** | 🔴 **Rejected — 1.3–32 GB of git per year** (measured above) |
| Publish `seed.db` to object storage, app downloads on boot | Rejected: keeps a mechanism we throw away in Phase 3, and adds boot latency + a staleness window |
| **Postgres (Supabase), both clients read it** | ✅ **Chosen.** It is the Phase 3 destination anyway; the data is <10 MB against a 500 MB free tier; the port is one file |

#### Where it runs

| option | verdict |
|---|---|
| **GitHub Actions cron** | ✅ **Chosen for v1** — free, already in use (`mirror.yml`), and a 3.6 s job is trivial. ⚠️ See the timing caveat below |
| A small always-on worker (Fly/Render) | Deferred. Correct if per-minute precision is ever needed; not yet justified |
| Supabase scheduled functions | Rejected for now — it would mean reimplementing the ingest in a second language |

⚠️ **The timing caveat, and it matters because of ADR-210.** GitHub's cron is best-effort and can be delayed
under load. Most of this pipeline does not care. **One part does:** the transfer counters must be read
*before* a deadline or that gameweek's value is unrecoverable.

⭐ **Mitigation — schedule redundantly rather than precisely:** fire the core refresh at **T-60, T-45, T-30 and
T-15** before each deadline and let the upsert keep whichever lands last. Four attempts at 3.6 s each cost
nothing and are robust to an hour of cron slop. *A cheap job does not need accurate scheduling; it needs
several chances.*

#### 🔴 The headline extraction — the one genuinely open question

`enrich_headlines` needs a language model, and the docstring already admits the consequence:

> *"extraction needs a language model, Streamlit Cloud has none… A snapshot built without a model simply
> carries no events, and every surface degrades to exactly what it said before."*

Today Cloud only has events because **your laptop bakes them into the seed**. Move the pipeline server-side
and they stop arriving. This is not cosmetic: reported-departure events feed the leavers logic on **six
surfaces** (ADR-151/153/155/156) and the ADR-210 exodus lede.

| option | trade-off |
|---|---|
| **(a) A hosted model API in the pipeline** | Small job (~112 headlines/run). Introduces the **first paid external dependency** and a key to manage. Needs its own evaluation of provider/model/cost — **not decided here** |
| **(b) Keep extraction manual on your Mac** | Everything else becomes autonomous; events refresh when you happen to run it. Honest and free, but leaves a human in one loop |
| **(c) Drop events entirely** | Rejected — it would retire six surfaces' worth of shipped behaviour |
| **(d) Self-host a model** | Rejected — cost and ops out of proportion to a 112-headline job |

⚠️ **This is the one place Phase 1's "£0 until real usage" assumption does not hold**, and it needs your call
rather than my default. 💡 **My recommendation: (b) first, (a) later** — get the pipeline autonomous for
everything that does not need a model, and treat the model question as its own small decision rather than
letting it block the 95% that is free.

---

### 🎯 Decision (proposed)

**Postgres as the destination, GitHub Actions as the trigger, three jobs at three cadences, and a validation
step that can refuse to publish.**

#### Cadence, justified rather than arbitrary

| context | interval | why |
|---|---|---|
| off-peak | 6 h | prices settle overnight; little else moves |
| ordinary weekday | 1 h | news and transfers trickle |
| **T-60 → deadline** | **4 attempts** (T-60/45/30/15) | team news and price changes cluster; ⭐ **and ADR-210's counters must be caught before the reset** |
| live gameweek | 10 min | scores and provisional points |
| after final whistle | once | trigger the per-GW backfill |

#### ⭐ Validation must be able to say no

Today the blast radius of a bad FPL response is your laptop. Server-side it is every user at once, so the
pipeline publishes only if the fetch passes:

- player count within a sane band of the last good run (**no mass disappearance**)
- fixtures present for the current and next gameweek
- not a wholesale zeroing of prices/ownership
- **on failure: keep the last good data and alert.** ⭐ *A pipeline that cannot decline is a pipeline that
  will eventually publish nonsense to everyone simultaneously.*

#### Freshness must be visible

A `data_status` row — last successful run, which gameweek, whether a gameweek is live, and whether the last
attempt failed — rendered in both clients. ⭐ *ADR-203 and ADR-210's lesson, applied to the pipeline itself:
a value without its observation time is not evidence.*

---

### ⚖️ Consequences & Trade-offs

**Positive**
- Data reaches users without you, which is the hard prerequisite for §9 of the mobile brief (**no app release
  for a data change**)
- ⭐ **It fixes a live problem first**: testers stop seeing commit-fresh data, before any mobile code exists
- ADR-210's transfer-flow log starts capturing complete gameweeks instead of whatever a manual run catches
- The Postgres migration is done once, and Phase 3's API inherits it

**Negative / limits**
- 🔴 **New ops burden, permanently.** A pipeline that runs unattended is a thing that can fail unattended.
  That is the real cost of this phase and it does not go away
- ⚠️ Headline events go stale under recommendation (b), until the model question is settled
- `seed.db` stays in the repo as a fallback during the cutover, so the old path remains until it is proven
- Supabase free tier **pauses inactive projects** — a scheduled job every hour incidentally prevents that,
  which is convenient but should not be relied on as the reason

---

### 🛠 Implementation & Migration — staged so nothing breaks

| stage | work | exit |
|---|---|---|
| **2a** | Postgres-backed `Storage` behind the existing interface; run the full suite against **both** backends | 1,898 tests green on Postgres |
| **2b** | Streamlit reads Postgres behind a flag; `seed.db` remains the fallback | the live app serves Postgres with no visible change |
| **2c** | Scheduled core refresh (GH Actions) + validation + `data_status` | a refresh runs unattended and a deliberately broken payload is **refused** |
| **2d** | Per-GW backfill job, triggered after results | a gameweek's history lands with no human |
| **2e** | Headline decision (a) or (b) | recorded, whichever way |
| **2f** | Retire the manual path | `reseed` becomes a local convenience, not the deploy route |

**Exit criterion for Phase 2** (from the audit): ⭐ **two weeks with no manual `reseed`, including a deadline
and a live gameweek.**

* **Action Items:**
  - [x] **GATE agreed 2026-09-18** — Postgres · GitHub Actions · headlines stay manual (option b)
  - [x] **2a — Postgres `Storage`; SQLite unchanged. 1,905 green on SQLite, 1,892 + 13 skipped on Postgres 17.2, and 0 of 659 xP values differ between backends**
  - [x] **2b — flagged cutover (`FPL_DATABASE_URL`), `seed.db` retained; the app renders on Postgres and `refresh` writes to it. 1,914 green on SQLite, 1,901 + 13 skipped on Postgres**
  - [x] **2c — scheduled refresh (`data.yml`, 15-min tick) + validation + `data_status`. ✅ Refusal proven on real Postgres: 662 players held, a 3-player payload refused, nothing written, `refreshed_at` unmoved. 11 mutants, 11 red**
  - [x] **2d — per-GW backfill (`backfill.yml`, hourly, gated on a completed gameweek missing history). ✅ Verified live; `_migrate` now portable, closing 2a's stated gap. 17 mutants red**
  - [x] **2e — headlines stay manual (option b), and the path to Postgres pinned: `cmd_refresh` hands ONE store to `enrich_headlines`, so a local refresh with the DSN carries them. Signals prints when they were last read**
  - [x] **2f — the manual route retired in code AND in copy: the sidebar no longer claims a redeploy is needed while reading Postgres; `reseed`'s help, docstring and DEPLOY.md state both eras**
  - [x] **Mutation-tested: 21 mutants across 2c–2f, 21 red** (2 survived a first pass — both guards that could not reach the case they described)

#### ✅ Always
- [ ] **Add a row to `docs/06_Decisions/ADR-000-index.md`.**

---

---

### ✅ Stage 2a — built 2026-09-18

**`Storage` now runs on Postgres, one body of SQL, proven by running the whole suite twice.**

| | tests |
|---|---|
| SQLite (default, unchanged) | **1,905 passed** |
| **Postgres 17.2** (`MADBOOTS_TEST_DSN=…`) | **1,892 passed · 13 skipped** |

The 13 are pinned by `test_storage_backends.py` and are the SQLite-legacy column/key migrations plus the
file-copy `reseed` — ⚠️ **"not applicable", not "handled"**, and named so a skip cannot pass for coverage
(ADR-178).

**And the numbers agree.** The same snapshot loaded into both backends, through the same `decision_xp`:
**0 of 659 players' xP differ** (tolerance 1e-9), identical top 5, and Postgres costs **30 ms against 28 ms**
for the whole board. ⭐ *The analytics cannot tell which backend they read* — which is the property the whole
phase depends on, since they are what must not change.

#### The seam — `src/db.py`, and what actually differed

Three things, each found by running it rather than reading it:

1. **Placeholders.** `?` → `%s` on the way through, so every statement is written once. ⚠️ **And a literal
   `%` must be escaped first** — psycopg parses placeholders in *every* statement, including ones with no
   parameters, so the `1%` inside a column comment in `CREATE TABLE player_transfer_flow` raised *"incomplete
   placeholder"* and the schema would not build.
2. **Rows.** `sqlite3.Row` allows named **and** positional access; `dict_row` allows only named, and `Storage`
   reads `fetchone()[0]` in six places. So PG rows are wrapped in a `Row` that matches `sqlite3.Row` —
   ⭐ *a row object that is nearly the same is how two backends quietly disagree.*
3. **Booleans.** `was_home` and `finished` are `INTEGER` columns receiving Python bools; SQLite stores them,
   Postgres refuses. Coerced in the adapter, with a test naming both columns so that adding a real boolean
   column is visibly a reason to revisit it.

#### 🐛 Two real bugs the port surfaced — in `Storage`, not in the tests

* ⚠️⚠️ **Player search was about to become case-sensitive.** `p.web_name LIKE ?` carried the comment *"LIKE is
  case-insensitive for names"* — true of SQLite, stated as though it were a property of SQL. On Postgres
  `LIKE` is case-**sensitive**, so `search haaland` would have found nobody. Now `LOWER(…) LIKE LOWER(?)`,
  exact on both. ⭐ **Second time in one day that a case-sensitivity assumption crossed an engine boundary** —
  the other is `beta_users` in `docs/SUPABASE_RLS.md`, where the same species of bug is load-bearing enough to
  dictate the security staging.
* **A missing table was caught by driver class.** `except sqlite3.OperationalError` implements ADR-151's
  "a snapshot older than this table must degrade, never raise" — and on Postgres that became a crash. Now a
  portable `db.MISSING_TABLE`. ⚠️ Postgres also **aborts the whole transaction** on any error, so the adapter
  rolls back before re-raising; without that, recovering from a missing table would poison the connection.

#### ⭐ The harness caught a design flaw, not just bugs

`is_postgres` was first derived from the **path string**. The Postgres test harness broke it on contact: the
suite asks for `:memory:` while `db.connect` is patched to return Postgres, so path and connection disagreed
and the SQLite-only migrations ran against Postgres. It now reads the **connection**.
⭐ *A derived fact should be read from the thing it describes — the path is a request, the connection is the
answer.*

#### Running it

```bash
pytest                                                   # SQLite, unchanged
MADBOOTS_TEST_DSN=postgresql://… pytest                  # the same suite on Postgres
```

CI now runs **both**, so the dual-backend claim is swept rather than asserted (ADR-184).

⚠️ **Stated limitation, carried forward:** Postgres has **no migration story**. Its schema is created fresh
from the current DDL, which is why `_migrate` / `_rekey_history` are skipped rather than ported. That is fine
until the first column is added while Postgres holds real data — **which will happen inside this phase**, and
is the first thing 2b must decide.

---

### ✅ Stage 2b — built 2026-09-18

**One environment variable moves the whole app onto Postgres.** `FPL_DATABASE_URL` sets `config.DATABASE_URL`,
which feeds `config.DB_PATH` — and since `src/db.py` already decides the backend from that string, all
**eighteen** `Storage()` call sites in the web app follow without one of them being edited.

| | tests |
|---|---|
| SQLite (unset — unchanged) | **1,914 passed** |
| Postgres 17.2 | **1,901 passed · 13 skipped** |

**Verified end-to-end, not just in tests:**

* Six pages rendered against Postgres with **no exception and `fallback_reason()` of None** — it genuinely
  read Postgres, not the seed.
* `FPL_DATABASE_URL=… python app.py refresh` wrote a live FPL fetch **straight into a fresh Postgres**:
  662 players · 380 fixtures · 662 availability rows · 662 ADR-210 transfer-flow rows, schema created from
  nothing. The pipeline's write path exists.

#### ⭐ The variable *is* the fallback

Unset it and the app is byte-for-byte what it was. That is deliberately simpler than an automatic runtime
failover — ⭐ *a failover that silently serves last month's snapshot while the pipeline is dead is the failure
this phase exists to remove.* Where a **configured** Postgres cannot be used, the app still renders from the
seed, and the sidebar shows a **warning** (not a caption — the freshness line is already a caption, and a
caption reads as routine) naming the reason.

Two failures are told apart and both land there: unreachable, and *reachable but holding no MadBoots schema*
— a DSN pointing at the wrong database.

#### ⭐⭐ Two asymmetries that turned out to be the design

**A reader never creates the schema.** On SQLite the database *is* the app's own cache and bootstrapping it is
right; on Postgres it is a shared database the pipeline owns. A reader running `CREATE TABLE IF NOT EXISTS`
against an unexpected DSN would build eight empty tables and render *"no data"* — **reporting an empty league
instead of a misconfiguration.** So a reader probes (one query, not eight DDL round trips) and declines to
invent a schema; `ensure_schema=True` is how the pipeline says it means to.

**A reader may degrade; a writer must not.** ⚠️ Caught while wiring `cmd_refresh`, not by a failing test: the
reader path was written first and inheriting it for writers looked obviously right. It is not — **the fallback
target is the committed `data/seed.db`**, so a degrading `refresh` would write live FPL data *into the
repository's snapshot* and print success. Writers now raise. ⭐ *The safe direction to fail differs by what the
caller is for.*

#### 🐛 And the guard that swept for the wrong construct

`translate` rewrites `?` → `%s`. `test_storage_backends.py` guarded that by looking for a `?` inside a
**quoted literal** — the failure I imagined. The real one was a `?` inside a **SQL comment**: the new
`CREATE TABLE data_status` carried *"did the last attempt pass validation?"*, translation turned it into a
bind, and psycopg refused the statement — *"1 placeholders but 0 parameters were passed"* — so the schema
would not build.

⚠️ **I wrote that comment twenty minutes after writing the guard meant to catch exactly this.**
⭐⭐ *A guard against a claim must sweep for the claim, not for the version of it you thought of* (ADR-184,
third time). The guard now asserts what actually matters — **every `?` surviving translation is a real bind
parameter** — and was mutation-tested by restoring the naive translation, which turns it red.

#### `data_status` — freshness as a value

The sidebar read the SQLite file's **mtime**, and a Postgres table has no mtime. More than that, an mtime
records when something *wrote*, never whether the write was any good — which is the distinction an unattended
pipeline turns on. So a one-row `data_status` table carries `refreshed_at` (last **successful** publish),
`attempted_at` (last run, success or not), `ok` and `note`. ⭐ *Recording only successes would make a dead
pipeline indistinguishable from a quiet one* — ADR-203's `last_seen_at` reasoning, in the place it matters
most. **Nothing writes it until 2c**; readers degrade to "unknown".

#### ⚠️ The open question, stated rather than guessed

**Performance against a real Supabase is unmeasured.** Against a *local* Postgres the overhead is about
**35 ms per page** fixed (two connections plus a schema probe), with the data-heavy Players board costing more
(5.8 s against 4.4 s). Over the network to Supabase each connection is plausibly far dearer.

The obvious mitigation — caching the connection in `st.cache_resource` — is **deliberately not built**, because
it would be infrastructure for a latency nobody has measured. 📅 **Trigger: on the first Supabase deploy,
compare page timings against the seed; if the added cost exceeds ~200 ms per rerun, cache the connection.**

---

### ✅ Stage 2c — built 2026-09-18

**The pipeline runs, decides, and refuses.** `app.py pipeline` is one tick; `.github/workflows/data.yml` runs
it every 15 minutes, inert until `FPL_DATABASE_URL` is set.

| | tests |
|---|---|
| SQLite | **1,933 passed** |
| Postgres 17.2 | **1,920 passed · 13 skipped** |

#### ✅ The exit criterion, demonstrated on real Postgres

```text
1. first tick, empty database   → Published 662 players, 20 teams, 380 fixtures (bootstrapping)
2. immediately again            → Nothing to do — ordinary hours — next due in 0:59:57
3. FPL "returns" three players  → REFUSED — only 3 players; count collapsed 662 → 3.
                                  The last good data still stands.
   players before 662 · after 662   ← nothing was written
4. refreshed_at did NOT move · attempted_at did · ok=0 · note carries the reason
```

#### ⭐ Three judgements a person made implicitly, now written down

**When.** ⭐ *The schedule is Python, not cron, because the thing it depends on moves every week.* GitHub
cannot know when Saturday's deadline is; the fixtures can. So the workflow ticks dumbly every 15 minutes and
`cadence()` decides: a gameweek in play → 10 min · **the hour before a deadline → 15 min** (four chances, the
redundancy that makes cron's drift survivable, because ADR-210's counters reset at that deadline and the
reading before it cannot be recovered) · ordinary → 1 h · overnight → 6 h. A tick with nothing to do costs
**0.19 s** and makes no FPL request.

**Whether.** ⚠️ `validate()` runs **before the first write, for every caller** — once storing *is* publishing,
a check that runs afterwards is not a check, and the last good copy is already gone. Deliberately **not** an
optional argument: an opt-out on a shared helper is how one call site behaves differently from every other
(ADR-181), and the caller that would have forgotten is the manual refresh, run by a person, against the
database everything else reads.

⚠️ **The bounds are a smoke alarm, not a thermostat, and that is their whole provenance** (ADR-199 asks; the
honest answer is *declared, not measured*). They catch an empty, truncated or zeroed payload — **not**
ordinary movement. A real January window must pass, because a check that blocks good data is worse than one
that stores slightly odd data. 📅 Revisit if one ever fires on a payload that turns out to have been fine —
that, not a date, is the evidence a bound is wrong.

**Saying so.** `data_status` on every attempt: `refreshed_at` moves only on a publish, `attempted_at` on every
run. ⭐ *Recording only successes would make a dead pipeline indistinguishable from a quiet one.*

#### 🐛 Two things the build caught

* ⚠️ **I shipped `--no-headlines` in the workflow for a flag that does not exist.** The YAML was valid, the
  command was not, and nothing would have failed until the first scheduled tick — in production, unattended.
  ⭐ *A workflow file is code that no test runs by default.* There is now a test that parses the command out
  of the YAML and puts it through the real argument parser; mutation-tested by restoring the bug.
  (Headlines are absent from this path **by construction**, not by flag — `pipeline.run` never reaches
  `enrich_headlines`, so there is nothing to remember to pass.)
* ⚠️ **Five existing ingest tests failed the moment validation went in — on 2-player payloads.** That is the
  validation working: they had been exercising the ingest path on a response production cannot produce. The
  **fixture was padded, not the check loosened** — ⭐ *a fixture that models less than reality will confirm a
  broken mechanism*, and this is the seventh time that has cost something this month.

**11 mutants, 11 red** — including "validation never refuses", "a refusal moves `refreshed_at`", "the
pre-deadline window is ignored", and the `--no-headlines` bug itself.

#### ⚠️ Cost, stated

96 ticks a day. Fine on a public repo (free Actions minutes); on a **private** one an uncached install would
dominate, so the workflow caches pip and the tick itself is 3.6 s. 📅 If this repo is private, check the
minutes after a week — the mitigation is a smaller requirements set for the pipeline, not a coarser cadence,
because the pre-deadline window is the part that must not slip.

---

### ✅ Stage 2d — built 2026-09-18

**A gameweek's history lands with no human.** `app.py pipeline --backfill`, driven by
`.github/workflows/backfill.yml` on an hourly tick — a different job on a different clock from the core
refresh: ~659 throttled requests (3–5 minutes) once per gameweek, against the refresh's 3.6 seconds every few
minutes. Its own workflow, because a five-minute job has no business holding the 15-minute tick's concurrency
group.

| | tests |
|---|---|
| SQLite | **1,941 passed · 1 skipped** |
| Postgres 17.2 | **1,929 passed · 13 skipped** |

#### ✅ Demonstrated end to end on real Postgres

```text
1. core refresh, empty database  → Published 662 players, 20 teams, 380 fixtures
2. is a gameweek missing?        → due=True — no stored history for GW[1, 2, 3, 4]
3. a real throttled backfill     → 5 players · 24 past seasons · 25 gameweek rows · 0 failures
                                   rounds now carrying a scoreline: [1, 2, 3, 4, 5]
4. data_status                   → backfilled_at set, backfilled_event 5
                                   core refresh verdict untouched (ok=1, refreshed_at unchanged)
```

#### ⭐⭐ "Done" is asked with the analytics' own definition

`backfill_due` calls **`minutes.completed_gameweeks`** — the same function `in_season_share`, the backtest and
ADR-203's availability log use. A round counts as held only when its rows carry a **scoreline**.

⚠️ Had the pipeline invented its own test — *"are there rows for round N?"* — it would have passed, and been
wrong: FPL writes a player's per-gameweek row when the fixture is merely **scheduled** (ADR-125/129), so the
pipeline would have found rows, concluded the work was done, and left the analytics with a gameweek they
cannot see. ⭐ **The pipeline's "done" has to be the consumer's "have".**

A gameweek also counts as complete only when **all** its fixtures have finished — a Saturday round with a
Monday night game still to come is not ready.

#### ⭐ The migration gap, closed rather than deferred again

2a said plainly: *"Postgres has no migration story… that stops being fine the first time a column is added
while it holds real data."* 2d adds two columns to `data_status`, so it stopped being fine.

`_migrate` now runs on **both** backends. The only part that was ever SQLite-specific was asking a table for
its columns (`PRAGMA table_info` vs `information_schema`), which `db.columns` answers on either. Verified on a
Postgres table created in the old shape: the columns appear and **the row survives** — it adds, never
rebuilds. ⚠️ `_rekey_history` stays SQLite-only, and correctly: a Postgres database has never held the old
primary key it repairs.

#### 🐛 Three things caught, two of them by mutation

* ⚠️ **`COALESCE` on `note` broke clearing.** Giving the backfill its own stamps meant `set_data_status` had
  to merge rather than overwrite — and merging `note` meant a **successful refresh could no longer clear a
  previous failure's reason**, so the app would have gone on showing yesterday's refusal. ⭐ *A field cleared
  by writing None cannot be merged with COALESCE.* The note now follows the verdict: a write carrying `ok`
  owns it, a write without one leaves it.
* ⚠️ **A guard that could not reach its own case.** The test protecting the refresh's note from the backfill
  set `note=None` first — so a mutation that let the backfill clobber it with None destroyed nothing and
  stayed green. ⭐ *A guard only tests the case its fixture can reach.* It now starts from a live refusal.
* ⚠️ **The Postgres migration was proved by a script I ran by hand, and disabling it broke no test.**
  ⭐ *Verifying something once is not testing it.* There is now a real test, skipped without a Postgres and
  always run by CI's postgres job.

**17 mutants, 17 red** across 2c and 2d.

---

### ✅ Stages 2e + 2f — built 2026-09-19. **Phase 2 complete.**

| | tests |
|---|---|
| SQLite | **1,946 passed · 1 skipped** |
| Postgres 17.2 | **1,934 passed · 13 skipped** |

#### 2e — the one manual input, and the gap in it

The gate chose option (b): headline extraction stays manual, because it needs a language model and the
scheduled runner has none. ⚠️ **But that decision had an unexamined hole**: extraction writes to whatever
`Storage()` resolves to, and after the cutover the app reads Postgres — so events extracted on the owner's
Mac would have landed in a local SQLite cache nobody reads.

⭐ **It turned out to already work, for a reason worth pinning rather than rediscovering.** `cmd_refresh`
opens **one** store and hands that same store to `enrich_headlines`, so
**`FPL_DATABASE_URL=… python app.py refresh`** on a machine with Ollama writes players *and* headlines
straight into Postgres. No separate push step, no second code path. A test now pins it, because 'tidying'
the headline call onto its own `Storage()` would silently split the destination in two — and ⚠️ **the symptom
would be *no news*, which looks exactly like *no news*.**

**So the Signals page now prints when headlines were last read.** Every other freshness signal in this phase
is surfaced; leaving the one manual input silent would be the exception that mattered most.
⭐ *Stale headlines do not look stale.*

#### 2f — retiring a path means retiring what the product says about it

`reseed` does **not** go away. What changes is its job, and the app had a sentence about that job baked in:

> *"🌐 A data snapshot — updates when the app is redeployed."*

True before the cutover, **false after it** — the pipeline refreshes the database through the day. ⭐ *That is
a sentence the app says about itself while behaving differently*, which is exactly the shape ADR-184 was
written about. The sidebar now tells the truth in both states, and a test asserts both branches.

`reseed`'s own help, its docstring and `DEPLOY.md` now state the two eras explicitly: before the cutover it
**is** the deploy route and nothing else reaches testers; after it, it maintains the **fallback** the app
shows when Postgres cannot be read — ⚠️ *a very stale fallback is a poor fallback*, so it stays worth running
occasionally. It targets SQLite explicitly, so `FPL_DATABASE_URL` never redirects it.

#### 🐛 And the sweep was wrong again, in the same way

The guard for the retired claim required the word **"reseed" on the same line** as the claim — and missed the
exact regression it exists for, because the `help=` string on `p_reseed` never contains that word; the
*variable name* does. ⭐⭐ *Sweep for the claim, not for a word you expect to sit beside it.* **Second time in
this ADR alone**, after the `?`-in-a-SQL-comment guard in 2b.

**21 mutants across 2c–2f, 21 red** — 2 of them survived a first pass and both were guards that could not
reach the case they described.

---

### 📋 Phase 2 status

**Built:** 2a Postgres backend · 2b flagged cutover · 2c scheduled refresh + validation · 2d per-gameweek
backfill · 2e headlines (decided manual, path pinned) · 2f manual route retired in code and copy.

**⏳ Outstanding, and it is not code:** a Supabase project, the Phase 1.5 RLS work, and the
`FPL_DATABASE_URL` secret. Until that secret exists **both workflows are inert and the app is byte-for-byte
what it was** — so nothing shipped here changes today's deploy, and `reseed` → commit → push remains the way
to update it.

📅 **The exit criterion can only start once the secret is set: two weeks with no manual `reseed` needed,
including a deadline and a live gameweek.** ⚠️ *"No reseed needed"* — not *"no reseed permitted"*. Needing one
is the failure signal, not a rule broken.

---

### ✅ LIVE ON PRODUCTION — 2026-09-20

**The pipeline runs, and the app reads it.** `FPL_DATABASE_URL` is set as a GitHub Actions secret (the
schedule) and a Streamlit secret (the app), both pointing at the Supabase **session pooler** — `pooler.
supabase.com:5432`, IPv4, because ⚠️ *the direct connection is IPv6-only on most projects and GitHub Actions
cannot reach it.*

| check | result |
|---|---|
| a scheduled run reached the database | `data_status.ok = true`, attempted 3 minutes earlier |
| the app is on Postgres, not the seed | sidebar reads **"🔄 Updated automatically"** |
| and it is *really* Postgres | **667 players** in the app · **659** in `seed.db` |

⭐ **That player count is the proof the caption alone is not.** A caption says what the code believes; two
different numbers say which database answered.

⚠️ **The nine FPL tables land in `public`, so PostgREST exposed them** — closed with `revoke all … from anon`
straight after populating. The data is public information, so this is surface rather than secrecy, and the
app reads it over the **direct Postgres connection**, never PostgREST.

⚠️ **A first run took four minutes**, almost all of it installing Streamlit, PuLP and FastAPI — against a
**3.6-second** refresh. Free on a public repo, but 96 ticks a day of that is waste, and the fix is the one
already named: a smaller requirements set for the pipeline, not a coarser cadence.

📅 **The exit criterion now starts: two weeks with no manual `reseed` needed, including a deadline and a live
gameweek.** ⚠️ *Needed*, not *permitted* — needing one is the failure signal. GW6 is 2026-10-10, which makes
the next three weeks a quiet window to find out.

### 💡 The lesson

> **An observer that has to be run by hand is not an observer, it is a habit.**

ADR-203 built the availability log and ADR-210 built the transfer-flow log, both on the principle that *the
observer must be in place before the thing it observes*. Both are correct, and both were still defeated on
2026-09-18 by the simplest possible failure: **nobody ran the refresh before the deadline.**

⭐ *Recording machinery and scheduling machinery are different problems, and building the first one well does
nothing about the second.*

---

### 🔗 References & Related Artifacts
- **The audit that scoped this:** `docs/03_Architecture/Mobile_Platform_Audit.md` §5
- **What the pipeline must not lose:** [ADR-210](./ADR-210-a-threshold-reads-the-distribution-it-describes.md) · [ADR-203](./ADR-203-availability-is-recorded-as-it-passes.md)
- **The path it replaces:** ADR-053 / ADR-056 — the committed snapshot
- **The security work alongside it:** `docs/SUPABASE_RLS.md` (Phase 1.5)
