# Architectural Decision Record: The pipeline runs without you

**Decision ID:** ADR-211
**Date:** 2026-09-18
**Status:** ✅ **Gated and agreed 2026-09-18** (destination: Postgres · trigger: GitHub Actions · headlines: manual for now). **Stages 2a + 2b built** — see below. 2c–2f open.
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
  - [ ] 2c — scheduled refresh + validation + `data_status`; ⚠️ **prove the refusal path by feeding it a bad payload**
  - [ ] 2d — per-GW backfill
  - [ ] 2e — headline model decision, recorded
  - [ ] 2f — retire the manual deploy path
  - [ ] Mutation-test the validation guards

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

### 💡 The lesson (provisional — this is a proposal)

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
