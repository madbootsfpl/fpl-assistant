# The external pipeline trigger (ADR-378)

A Cloudflare Worker whose only job is to call `workflow_dispatch` on `.github/workflows/data.yml` every
**10 minutes**, because GitHub's own cron does not fire at the rate it declares.

**Why it exists, in numbers.** Measured twice against the Actions API: `*/15` fired **6 times in 24 hours**
(6–7% of declared, 2026-09-26), and `0 * * * *` arrives a **median 3.9 h apart** (100 runs, 2026-10-30). The
cost is not cosmetic — `cadence()`'s pre-deadline branch promises *"four chances in the last hour"* and gets
roughly **one deadline in four**, so the app can show **team news four hours old in the hour when team news
decides the gameweek**.

⭐ **The worker is deliberately dumb and must stay that way.** It does not know when a deadline is. The
policy — live gameweek → 10 min · hour before a deadline → 15 min · ordinary → 1 h · overnight → 6 h — lives
in `src/pipeline.py` where it is testable, and `data.yml` says so: *"the schedule lives in Python, not in
this cron line, because the thing it depends on moves every week."* This supplies opportunities;
`refresh_due` decides. A tick with nothing to do exits in well under a second and makes no FPL request.

---

## Setup

**1 — Create a fine-grained GitHub token.** Least privilege, and the only step that cannot be scripted:

| field | value |
|---|---|
| Repository access | **Only select repositories** → `fpl-assistant` |
| Permissions | **Actions: Read and write** — nothing else |
| Expiry | your call; it must be rotated when it lapses |

⚠️ This token can start workflow runs in this repo. It **cannot** push code, read secrets, or touch any
other repository.

**2 — Check the Cloudflare token can write Workers.** ⚠️ The one `scripts/release_web.sh` uses is a
**Pages** token, and Workers is a separate scope — it fails with *"No access to the specified resource."* on
both `secret put` and `deploy`. Edit it at **dash.cloudflare.com/profile/api-tokens** and add:

- **Account → Workers Scripts → Edit**
- **Account → Account Settings → Read** (wrangler resolves the account through it)

⭐ *Edit* the existing token rather than minting a second: the value does not change, so nothing has to be
re-pasted and `release_web.sh` keeps working.

**3 — Deploy, then arm it. In that order:**

```bash
cd trigger
npx --yes wrangler@4 deploy                     # creates the worker — inert, no token yet
npx --yes wrangler@4 secret put GITHUB_TOKEN    # paste the PAT
```

⚠️ **Deploy first, because `secret put` needs the worker to exist.** Safe in that order precisely because
the worker is inert without its secret: the cron starts ticking immediately and logs
`no GITHUB_TOKEN — nothing dispatched` until step 3's paste lands.

⭐ Run both in a normal terminal, not through a tool — so the token never enters a transcript.

---

## Verifying it, rather than trusting it

🔴 **Cloudflare's cron is also best effort, and assuming otherwise is the mistake that produced this
directory.** Do not take the 10 minutes on faith.

- **Per-tick:** Cloudflare dashboard → the worker → *Logs*. A success logs `dispatched data.yml on master`.
- **End to end:** every refresh line already prints the settled crowd phase (ADR-377) —
  `… crowd GW9 @ 0.6h (ordinary hours).`
- **The actual test:** after two or three deadlines, re-run the coverage measurement and compare against the
  **26%** baseline in [ADR-377](../docs/06_Decisions/ADR-377-the-reading-we-keep.md). If coverage has not
  moved, Cloudflare is no better than GitHub and this should be deleted rather than kept as decoration.

## If it breaks

Nothing stops. `data.yml` keeps its hourly `schedule:` as a **backstop**, so a deleted, broken or
unconfigured worker returns the pipeline to exactly today's behaviour. ⭐ *A replacement for an unreliable
mechanism should not also be a single point of failure.* With no `GITHUB_TOKEN` the worker logs and does
nothing, the same shape as `data.yml` and `mirror.yml` without their secrets.

`tests/test_external_trigger.py` holds the cross-language contract: the workflow filename, the branch, the
`force` input, the cron interval against `pipeline.py`'s tightest, and the backstop's continued existence.
