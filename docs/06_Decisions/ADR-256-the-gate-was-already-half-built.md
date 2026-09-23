# ADR-256 — The gate was already half-built

**Date:** 2026-09-23
**Status:** Accepted
**Gate for:** hosting the JSON API, so the app works for someone who is not the owner
**Builds on:** ADR-211 (Postgres), ADR-219 (the contract), ADR-239 (the address is runtime config)

---

## Context

Hosting has been *"the only thing between all of this and a tester"* for ten ADRs. The research turned up
that most of it was already done.

⭐⭐⭐ **`Storage` already speaks Postgres.** `db_path` takes a file path **or** a `postgresql://` DSN, and
one environment variable selects it. The GitHub Actions already write to Supabase through the session
pooler. So there is no data layer to build, no migration, and no second source of truth — hosting is
*"run uvicorn somewhere with `FPL_DATABASE_URL` set"*.

### Measured before deciding

| | |
|---|---|
| peak memory under real requests | **87 MB** |
| warm responses | **41–188 ms** |
| dependencies the API loads | **193 MB** — of which **71 MB is `pulp`** |
| the app's full requirements | **481 MB** |
| container image | **234 MB** |
| container cold start | **0.9–1.1s**, three runs |
| first real request after a cold boot | **66 ms** |

## Decision

**Scale-to-zero, on a slim container image.**

⭐ **Because it is reversible.** Scale-to-zero and always-on are the *same image* and differ by a platform
setting; the data lives in Supabase; the app talks to a URL. Switching is one number and a redeploy — so
the choice is not a commitment, and guessing at a usage profile you can go and observe is the wrong way to
spend a decision.

⚠️ **The asymmetry, named:** you learn scale-to-zero was wrong when a tester hits a cold start at a
deadline. The mitigation is Step 4 of the runbook — **measure it before any tester has the URL.**

### 📌 A warming ping was designed and deliberately not built

The plan was to keep the instance awake around deadlines using the existing 15-minute schedule. Then the
cold start came back at **~1 second**. ⭐ *Building it anyway would have been building for a fear the
measurement contradicts* — and if Step 4 comes back slow, always-on is the simpler answer than a cron
pretending to be one.

### A rate limit, because a public API needs a cost control before it is public

Every endpoint is unauthenticated, which is defensible for *ids in, analysis out* over public FPL data —
the CORS comment already says so, and that **`feedback` reaches a human** and **`build` runs an LP solver
whose CPU a stranger would be choosing**. Those two get strict limits; everything else is generous, because
⚠️ *a limit that catches ordinary use is a limit that gets removed rather than fixed.*

⭐ **Sliding window, not fixed** — a fixed window lets twice the allowance through across a boundary.
⭐ **Bucketed by rule, not by path** — otherwise the real limit is the default multiplied by the endpoint
count. ⚠️ **Health is never limited**: it is what the platform polls, and throttling it would make the
service look unhealthy under exactly the load the limit exists for.

⚠️⚠️ **It is a cost control, not a security boundary.** `X-Forwarded-For` is trivially forged by anyone
talking to the service directly. That is written in the source *and* asserted by a test, so nobody later
mistakes it for authentication.

## ⚠️⚠️ What running the image found, that reading it never would

**`/health` answered `200 {"ok": true}` while every real request 500-ed.** With no DSN the container falls
back toward the committed seed, which is excluded from the image, and failed on a permission error three
steps downstream.

⭐⭐⭐ **A platform polling that health check would have kept the instance in rotation**, and the failure
would have reached a tester as *"the app is broken."* Health now answers *can this instance serve?* — a
different question from *is the process alive?*, and only the first is worth reporting. It carries the
reason, and the reason **names the missing secret** rather than the permission error it causes: *a health
reason that describes a symptom sends whoever reads it to the wrong file.*

**The container reported `"version": "unknown"`.** `requirements-api.txt` deliberately omits `-e .`, so
`importlib.metadata` had nothing to read — and the phone's own connection check asserts that field is
non-empty. It falls back to `pyproject.toml` now. ⭐ *A deployment that cannot say which build it is cannot
be diagnosed.*

**And the tests had the same bug twice.** Two mutations survived — a hard-coded port and a shipped seed
database — because the assertions grepped the whole Dockerfile and `.dockerignore`, **including the
comments that explain those very rules**. ⭐ *A grep for a string finds the paragraph saying it is not
there.* Comments are stripped before every such check now.

## Consequences

⭐ **The runbook marks every step `✅ executed` or `🔴 not executed`**, and a test enforces it. ADR-249's
runbook was written from knowledge and broke four times on first use; this one has a build, a container, a
Postgres round trip and three cold-start timings behind its first half, and is honest that the second half
is still a plan. ⚠️ *An unverified instruction is not a defect; an unverified instruction presented as a
verified one is.*

📌 **Still owed at deploy time**, and all of it is the owner's to do: the account, the secret, the domain,
and hiding the Settings server field before a tester build.

## Verification

* **19 tests** across the limiter and the image, including the default allowance being large enough for a
  tester moving between tabs, and health being able to report that it *cannot* serve.
* **7/7 mutations killed** on the limiter — a fixed window, per-path buckets, the proxy header ignored,
  the wrong forwarded hop, health being limited, no `Retry-After`, and feedback given the generous default.
* **7/7 on the image** — the web stack creeping in, `pulp` dropped, the seed shipped, a hard-coded port,
  binding to localhost, running as root, and health returning to a constant.
* **3/3 on the runbook guard**, which now covers **every** document in `03_Architecture`, not the one that
  broke.
