# ADR-288 — The latency was not the one we were measuring

**Date:** 2026-09-24
**Status:** Accepted
**From:** the owner — *"lets sort the always-on vs scale-to-zero latency"*
**Revisits:** `Hosting_The_API.md` Step 4 (13.4s, 2026-09-23), which said to buy always-on

---

## The decision: **do not buy always-on**

The runbook had a threshold agreed in advance — *"10s or worse → set minimum instances to 1"* — and a
measurement that crossed it. That was the right way round, and the right answer on the day. It is the
wrong answer now, because the measurement no longer reproduces:

| | 2026-09-23 | 2026-09-24 |
|---|---|---|
| cold after idle | **13.4 s** | **0.4 s** (17 min) · **0.1 s** (45 min) |

⭐⭐ **The instance is not spinning down.** Two clean windows, nothing in the repo pinging it, on a Free
plan that is supposed to sleep after about fifteen minutes.

⚠️ **The likely reason is uncomfortable and worth saying**: a public HTTPS endpoint on a well-known
platform receives unsolicited traffic, and *any* request resets an idle timer. The service is being kept
awake by strangers knocking on the door. ⭐ *That is an accident, not an architecture* — it could stop
tomorrow, which is why the threshold stays on the books and the retry below is the insurance.

**Nothing is bought until a measurement asks for it.** ⭐ *A threshold agreed in advance is the only kind
that can overrule the person who set it* — including when it overrules them into not spending.

## ⚠️⚠️ What was actually failing: the deploy, not the sleep

Twice this evening the app showed *"Nothing answered."* Both were within two minutes of a `git push`.

**Every push redeploys the API, and during a redeploy there is a window with nothing serving.** That is
the latency the owner saw. It has nothing to do with scale-to-zero, and always-on would not have fixed
it.

And most of those redeploys had no reason to happen:

| tonight's pushes | |
|---|---|
| changed `src/`, `Dockerfile` or requirements | **2** |
| docs, ADRs, mobile code — nothing the image contains | **10** |

⭐⭐ **Ten of twelve deploys rebuilt and restarted a service whose code had not changed**, each one a
window in which a tester could open the app and be told it was broken.

📌 **The fix is a build filter, not a bill.** Render can be told to ignore paths that do not affect the
image. It costs nothing and removes five sixths of the windows. Left for the owner because it is a
dashboard setting on an account that is not mine.

## The two things shipped instead

**The error message was written for a different deployment.** One wording served both, and it was the
developer's: a tester whose server was waking up was told to check their Wi-Fi, grant a Local Network
permission, and see whether a shell script was running on a computer they do not own. ⭐ *An error
message that describes somebody else's setup is worse than no message — it sends the reader to fix
something that was never broken.*

It now branches on the address. Private ranges, `.local`, loopback, and plain HTTP on an explicit port —
the shape `scripts/serve_api.sh` produces — keep the developer advice. Everything else is told the truth.

**There was no way to retry.** The commonest failure in this app is also the most temporary, and the only
way out of the error screen was to force-quit it. ⚠️ *An error a second attempt would fix, with no way to
make a second attempt, is an error that reads as broken.*

## ⭐ Three mistakes worth keeping

**I was about to recommend spending money on a stale number.** The 13.4s was a year-old-in-dog-years
measurement — one day — and the instinct was to act on the decision already written down rather than
re-measure. ⚠️ *A runbook that records its own evidence invites you to trust the conclusion and skip the
evidence.*

**My first replacement message said "Pull down to try again."** There is no pull-to-refresh anywhere in
this app. ⭐⭐ *The fix for an instruction that describes something the screen cannot do was an
instruction that describes something the screen cannot do* — caught by looking, not by testing.

**A mutation survived because two rules both returned true.** Every local example in the tests was
`http://…:8078`, so the explicit-port rule answered first and deleting the entire private-range branch
changed nothing. ⭐ *Two rules that both return true make each other untestable, and the suite reports the
pair as covered.*

## What this does not do

- **No warming ping.** The runbook rejected one when a cold start was 13 seconds; it is not more
  attractive now that there is no cold start to warm. ⭐ *A cron that pretends to be always-on is the
  worst of both.*
- **No automatic retry.** The button is one tap and says why. An invisible retry would hide the fact that
  the service was asleep, and that fact is the one worth knowing if it ever becomes common.
- **The threshold stays.** If cold starts return — and they will if the accidental traffic stops — the
  rule already says what to do and the answer is one setting.
