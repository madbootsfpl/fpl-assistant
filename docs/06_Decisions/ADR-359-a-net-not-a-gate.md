# ADR-359 — A net, not a gate

**Date:** 2026-10-18
**Status:** Accepted
**Raised by:** the owner — *"noticed these emails showing CI failed, on checking they have happened for a while"*

---

## Context

**18 of the last 100 CI runs went red** (2026-09-26 → 2026-10-18), and the recent rate is worse: **8 of
the last 25**. Every one was fixed within minutes by the next commit. Every one sent an email first.

📌 **Nothing in CI is broken.** The run in the owner's screenshot is `04b873e`, pushed red by me that
morning. ⚠️ The email's *"CI on:pull_request"* header is the mobile app naming the workflow by its
declared triggers — `ci.yml` says `on: push, pull_request`, and **all 100 runs were pushes**. There are
no pull requests in this repository.

## ⭐⭐ The structural cause

```
branch protection on master:  404 — none configured
git hooks:                    none, samples only
```

**CI runs after the push.** A red build is a smoke alarm, not a lock on the door — so every failure
reaches `master`, notifies, and is repaired by the following commit. ⭐ *The emails are not noise; they
are the only thing doing the job, and they arrive after the fact by construction.*

## The failures, by cause

| cause | example | fixed at the root? |
|---|---|---|
| pushed carelessly | today's docs guard — pytest piped into `tail`, which **discards the exit code**, so the `&&` chain saw success | process, not code |
| environment difference | a SQLite `PRAGMA` in a test: green on 3.13 and 3.14, red on the Postgres job | ✅ ADR-355 |
| time-dependent | `test_xp_board` pinned to *"from GW6"*, red the week GW6 was played | partly |
| flaky | a live countdown inside an equality assertion | ✅ normalised |

## Decision

**A `pre-push` hook that costs ten seconds**, committed to `.githooks/` and activated with one
`git config core.hooksPath .githooks`.

It runs **ruff**, the **docs/orientation guards**, and **any test file changed in the commits being
pushed**. Measured at 9.1s, and it blocks: reproducing this morning's over-long status line, it fails
with the guard's own message.

### ⚠️⚠️ Called a net on purpose

📌 It does **not** run the full suite — five minutes is too long for every push, which is precisely why I
do not always run it. So **green here is not green on CI**, and in particular *nothing Postgres-only is
covered* — the environment class it cannot see is the one that bit yesterday.

⭐ `--no-verify` skips it, documented in the hook itself: *a hook you cannot skip is a hook you remove.*

### Rejected: branch protection with pull requests

It would gate properly, and `ci.yml` already answers `pull_request`. ⚠️ On a single-developer repository
it buys that by putting a branch and a PR in front of every one-line fix — ⭐ *friction that would be paid
on all 82 green pushes to catch the 18 red ones.*

## Consequences

✅ Of the eight recent failures, the hook would have caught the docs guard outright and the lint class
immediately. It would **not** have caught the Postgres-only one, and that is stated rather than hoped.

📌 **The honest other half: the largest single cause was me.** Two of the last three failures were mine,
and today's came from reading a pipeline's last line instead of its exit code. ⭐ *A hook is a weaker fix
than not doing that*, and it is the one this ADR cannot install.

⚠️ `.git/hooks/` is not version-controlled, so the hook only runs for a clone that has been pointed at it
— and an uninstalled hook looks exactly like a passing one. A test guards the README line that turns it
on, because that line is likelier to rot than the script.
