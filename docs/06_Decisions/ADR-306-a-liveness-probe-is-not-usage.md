# ADR-306 — A liveness probe is not usage

**Date:** 2026-09-26
**Status:** ✅ **Built**, and the open question is answered — see the end.
**From:** the owner's first look at his own stats panel (ADR-305), which arrived as a screenshot.

---

## What the panel said

```
/api/v1/health          955 · 96%
/api/v1/admin/usage      23 ·  2%
/api/v1/squad/my-team     6 ·  1%
/api/v1/ask               1 ·  0%
```

⚠️⚠️⚠️ **96% of the table was a machine checking whether the machine was up.** The whole of the real
traffic — six squad loads, one Ask — sat underneath it rounded to *0%* and *1%*.

⭐ `usage.py` exists to answer one question, in the owner's own words: *"the distribution & number using
the apps… to make sure that we are scaled enough."* Something polling a URL is not a person, and counting
it makes the number that matters unreadable.

## The fix

⭐ `/health` is dropped at the **recorder**, not in the panel — *the cheapest place to drop something is
before it exists*, and a row written then filtered still costs a write, a table row and a read.

⚠️ **An exact path, not a substring.** A mutation replacing the set membership with `'health' in path`
survived every test, because nothing asked for a path that merely contains it — ⭐ *a rule that matches by
coincidence will one day silence an endpoint somebody wanted*, invisibly.

## The question the number actually raised

⚠️⚠️ **955 probes is one every few minutes, and that may quietly be the reason ADR-288 declined
always-on.**

That ADR revisited a **13.4s** cold start, found it *"no longer reproduced"*, and attributed the original
figure to the deploy window — fixed with a build filter. The measurement behind it was *45 minutes idle,
then 0.1s*. ⭐ **But a service polled every few minutes is never idle**, and Render's free tier spins down
on inactivity. So *"45 minutes idle"* may never have been idle at all.

📌 **Today's reading is consistent with warm**: `/health` **0.16s**, a real endpoint **1.1s**. Neither
looks like a container starting.

⭐⭐ *This is the session's pattern again, pointing the other way*: ADR-288 recorded that the screenshots
keep being right and the reasoning keeps being wrong — and here a **measurement** was right about what it
measured and wrong about what it meant, because nobody asked what else was touching the service.

🔴 **Open, and only the owner can answer it: is something pinging `/health` on purpose?** An uptime
monitor, a cron, a `repository_dispatch` — anything on a ~10-minute clock.

- **If yes** — the service is effectively always-on for free, which is a good outcome ⚠️ *that nobody
  wrote down and nothing protects.* It should be named somewhere, because the day it lapses the 13.4s
  comes back and the cause will look like a mystery.
- **If no** — the probes are the platform's own, they are not keeping anything warm, and ADR-288's
  conclusion stands on its own feet.

⚠️ **And this change removes the evidence either way**, which is worth saying plainly: once `/health` is
uncounted, the panel can no longer show whether the pinger is alive. ⭐ *That is the right trade for a
usage table and the wrong one for a dependency* — if warmth is load-bearing, it deserves to be
**deliberate** (always-on, or a documented ping) rather than an accident visible only as noise in a
different report.


---

## Answered (2026-09-26): nothing is pinging it on purpose

The owner: *"no, nothing is pinging it that I am aware of."*

⭐ **So the probes are the platform's own**, and ADR-288's conclusion stands on its own feet: the 13.4s
was the deploy window, the build filter removed five sixths of those, and always-on stays declined.

⚠️ **The residual is smaller and different in kind.** If Render's own checks are what keeps the container
warm, that is **platform behaviour, not a dependency this project created** — there is nothing to
document, nothing to renew, and nothing that lapses because somebody forgot it. ⭐ *A risk you do not own
is a risk you cannot drop*, which is the opposite of the case I was worried about.

📌 **What to watch instead**, now that the panel no longer shows the probes: the **P95** on that same
screen. A container starting shows up there as a single slow request among fast ones — ⭐ *the slow tail is
where a cold start hides*, and it is already on display for exactly that reason.
