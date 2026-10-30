# ADR-378 — The tick comes from outside

**Decision ID:** ADR-378
**Date:** 2026-10-30
**Status:** ✅ **Accepted and built** — a Cloudflare Worker cron trigger calls `workflow_dispatch` every
**10 minutes**; GitHub's `schedule:` is kept as a **backstop**. ⏳ **Unverified by design:** Cloudflare's
cron is also best effort, and the measurement that decides this is two deadlines away.
**Superseded By / Replaces:** Closes the cadence defect [ADR-377](./ADR-377-the-reading-we-keep.md) left
open and quantified. Makes `src/pipeline.py`'s `cadence()` policy reachable for the first time since
[ADR-211](./ADR-211-the-pipeline-runs-without-you.md).
**Deciders / Participants:** Tony Sheridan (Owner, chose the approach), Claude Code (Implementation)

---

### 📌 The defect, measured twice

| when | cron declared | what actually fired |
|---|---|---|
| 2026-09-26 | `*/15 * * * *` | **6 runs in 24 hours** — 6–7% of declared |
| 2026-10-30 | `0 * * * *` | 100 runs at a **median 3.9 h** apart (mean 4.1, max 7.5) |

GitHub deprioritises scheduled runs on free runners. The repo had already concluded, correctly, that moving
`*/15` → hourly *"changes the documentation, not the data."* ⚠️ **What it did not do is notice that the
documentation it was fixing included a promise the code depends on.** `cadence()`:

> *"ADR-210's transfer counters reset at this deadline, and the reading before it cannot be recovered
> afterwards. **Four chances in the last hour** is the redundancy that makes cron's drift survivable."*

⭐⭐ **THOSE FOUR CHANCES NEVER EXISTED.** At a 3.9 h gap the expected coverage of the final hour is **~26%**,
and observed it was GW7 at **0.56 h** out and GW8 at **4.93 h**. A 15-minute *policy* cannot run more often
than the thing that invokes it.

**What that costs, in order of how much it matters:**

1. 🔴 **Team news and prices.** The pre-deadline interval exists because those *cluster* in the final hour. A
   manager checking an hour before the deadline can be reading **four-hour-old news** — a late injury flag
   arriving after they have picked. ⭐ *The same family as ADR-376's complaint: the app quietly confident and
   wrong.*
2. The crowd capture's phase swings by hours, so ADR-210's flows are not comparable across weeks.
3. The xP board runs up to 7.5 h stale (at least the staleness banner says so).

⭐ **And one thing it does NOT cost, checked rather than assumed: live scores.** `service/answers/scores.py`
fetches `get_fixtures` / `get_event_live` **directly from FPL at request time** behind a 60-second cache
(ADR-354/361/364), so the Scores screen the nine testers use was never on this clock.

---

### 🎯 The fix, and why it is shaped this way

A Cloudflare Worker (`trigger/`) with a cron trigger calls `workflow_dispatch` with `force: false`.

⭐⭐ **The worker is deliberately dumb and must stay that way.** It does not know when a deadline is and must
never learn: `data.yml`'s own comment is that *"the schedule lives in Python, not in this cron line, because
the thing it depends on moves every week."* The trigger supplies **opportunities**; `refresh_due` decides.
Teaching the worker about deadlines would move the policy out of the one place it is testable.

⚠️ `force` is **false**, always. Forcing would bypass the cadence gate 144 times a day and hammer FPL.

**Two constraints dissolved on inspection rather than being designed around:**
- The repo is **public**, so Actions minutes are unlimited and free. A dumb 10-minute tick costs nothing, and
  the "selective trigger that asks the API whether a refresh is due" I had sketched is **unnecessary
  complexity** — it would have duplicated policy to save a resource that is free.
- `workflow_dispatch` with a `force` input and `concurrency: data-pipeline` **already existed**, so no
  workflow plumbing and no pile-up risk.

**Why Cloudflare:** the account, the API token and `npx wrangler@4` are already in `scripts/release_web.sh`.
No new vendor. Rejected, with reasons:

| option | why not |
|---|---|
| Supabase `pg_cron` + `pg_net` | free and already there, but puts a GitHub token **inside the database** `sql/setup.sql` was hardened to lock down. ⭐ *Muddying a security boundary to save a dependency we already have is a bad trade.* |
| Render cron job | a paid feature, and free web services spin down so an in-process scheduler is not dependable |
| a second repo's `schedule:` | same platform, same deprioritisation |
| third-party cron services | hands a workflow-triggering token to a vendor we do not control |

### ⚠️ The interval was wrong first, and a test caught it

I scoped **15 minutes** from `INTERVAL_PRE_DEADLINE` and **forgot `INTERVAL_LIVE` is 10**. A 15-minute tick
leaves the live-gameweek policy unreachable — ⭐⭐ *the same class of bug this worker exists to fix,
reintroduced one layer up.*

`test_the_cron_is_at_least_as_often_as_the_tightest_policy_interval` reads **both** constants from
`src/pipeline.py` and compares them to the cron in `wrangler.toml`, so tightening a policy interval later
fails loudly instead of silently going unserved. The cron is **`*/10`** — 144 dispatches a day.

---

### 🔴 Kept: the backstop

`data.yml`'s hourly `schedule:` stays, and `test_the_backstop_schedule_is_still_there` pins it.

⭐⭐ **A REPLACEMENT FOR AN UNRELIABLE MECHANISM SHOULD NOT ALSO BE A SINGLE POINT OF FAILURE.** A deleted,
broken or unconfigured worker returns the pipeline to exactly today's behaviour rather than stopping it. The
worker is also **inert without its secret** — the same shape as `data.yml` and `mirror.yml` — so a fork never
sees it fail every ten minutes.

---

### 🧪 Definition of Done

**1 — Automated tests.** 8 new in `tests/test_external_trigger.py`. ⭐ **A Worker cannot be unit-tested from
pytest and does not need to be** — it is one `fetch` with no branching worth asserting. What rots is the
**contract between two files in different languages**: a hard-coded workflow filename, branch and input name
that a rename would not tell it about. ⚠️ *A trigger dispatching a workflow that no longer exists fails
silently every ten minutes, and the only symptom is data quietly going stale.*

**8 deliberate defects, all caught:** workflow renamed · wrong branch · `force: true` · no longer inert
without its secret · cron slower than the tightest policy · backstop schedule deleted · `workflow_dispatch`
removed · the `force` input renamed.

⭐ One test initially **skipped** (no `origin/HEAD` on this clone) and was given a second source, because *a
skipped test guards nothing.*

**2 — Manual smoke test.** `node --check trigger/worker.js` parses; the workflow still parses as YAML with
both triggers present. ⚠️ **Not yet deployed** — it needs a token only the owner can mint (`trigger/README.md`).

**3 — Docs.** This ADR, `trigger/README.md`, `data.yml`'s header rewritten so the next reader does not read
`schedule:` as the cadence (ADR-294's lesson), index, PROJECT_STATUS, README counts.

---

### 📊 Consequences

**Good:** `cadence()`'s policy becomes reachable for the first time. Team news before a deadline is the win
that matters; ADR-210's flows become phase-comparable, which unblocks the flow half of the sentiment work.

**Costs / limits:**
- 🔴 **Unverified, and deliberately labelled so.** Cloudflare's cron is also best effort. ⭐ *Assuming a
  platform meets its declared cadence is the exact mistake that produced this ADR*, so the claim here is
  "plausibly better", not "fixed". The test is the ADR-377 coverage measurement re-run after two or three
  deadlines against the **26%** baseline. **If it has not moved, delete this rather than keep it as
  decoration.**
- ⚠️ **Needs a token the owner must mint and rotate.** Not deployed until then; until it is, nothing changes.
- ⚠️ 144 runs/day makes the Actions tab and `gh run list` noisy, and ADR-377's own cadence measurement reads
  that list — ⭐ *the instrument that found this will need its query adjusted once the fix lands.*
- ⚠️ A new deployable with no CI. If it rots, the crowd-phase line is the alarm.

---

### 🔗 Links

- [ADR-377](./ADR-377-the-reading-we-keep.md) — where this defect was quantified and left open
- [ADR-211](./ADR-211-the-pipeline-runs-without-you.md) — the pipeline this ticks
- [ADR-210](./ADR-210-a-threshold-reads-the-distribution-it-describes.md) — the log whose phase this fixes
- `trigger/` — `worker.js` · `wrangler.toml` · `README.md`
