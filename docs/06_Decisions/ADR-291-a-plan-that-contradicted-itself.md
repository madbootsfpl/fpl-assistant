# ADR-291 — A plan that contradicted itself

**Date:** 2026-09-25
**Status:** Accepted
**From:** the owner, on iOS — `draft bench ids not in the draft squad: [496]`, on every launch

---

## The app would not open

The screen showed a server validation error and nothing else. The saved plan that caused it was re-sent
on the next launch, and the next. ⚠️⚠️ *A saved plan that cannot be sent and cannot be cleared is an app
that will not open.*

## The bug: two halves of one object, from two sources

`Draft.swap()` built the XI from the draft and the bench from the **team**:

```dart
final current = existing?.playerIds ?? basePlayerIds;   // the draft
final next  = [for (final id in current)  id == outId ? inId : id];
final bench = [for (final id in benchIds) id == outId ? inId : id];   // ⚠️ the team
```

So a **second** transfer rebuilt the bench from the original squad and resurrected the player the first
transfer had sold. Reproduced exactly, with the owner's own id:

```
after transfer 1   squad has 496: false     bench: [12, 13, 14, 900]
after transfer 2   squad: […, 900]          bench: [12, 13, 14, 496]
STRAY BENCH IDS: [496]
```

⭐⭐ **`replace()` — the substitution path, twenty lines away — had always done it correctly**, taking
`existing?.benchIds ?? benchIds`. ⚠️ *Two halves of one object derived from two sources will disagree;
the only question is when.*

## ⚠️ The fix that would not have helped

Correcting `swap()` stops new bad drafts being written and says **nothing about the one already on the
owner's phone.** That draft is on disk, and every launch would re-send it.

So a self-contradictory draft is now a staleness reason of its own: dropped, with a sentence, like a plan
whose gameweek has passed. ⭐ It is checked **first** — before manager, gameweek and squad — because *the
other three ask whether the plan still applies; this one asks whether it was ever sendable*, and a stuck
phone must not stay stuck until the gameweek turns.

The message does not explain the bug. ⭐ *"Please make it again" is the only instruction that helps, and
it is the whole of what a reader can act on.*

4/4 mutations killed, including moving the consistency check below the manager check — which leaves the
stuck phone stuck and passes every other test.

## ⚠️ And the publish step left something in the repo

The first `wrangler pages deploy` wrote `.wrangler/cache/pages.json` into the working tree, and the
release commit's `git add -A` swept it in. It holds the **Cloudflare account id** — an identifier, not a
credential; it appears in every Cloudflare API URL and cannot authenticate anything — but it is not ours
to publish, and this repo is public.

⭐ **`test_no_credential_file_is_tracked` caught it**, which is the guard working — but on the next full
suite run, *after* the push. ⚠️⚠️ *Untracked is not enough when the next command is `git add -A`*, so the
fix is a rule in `.gitignore` rather than vigilance, and a second test now pins that rule.

📌 **The token was never written** — checked, not assumed. No rotation is needed, and an account id
cannot be rotated.

## What this does not do

- **No history rewrite.** The account id is in one pushed commit on a public repo. It is low-value and
  force-pushing a shared history is the owner's call, not a cleanup to perform quietly.
- **No revalidation of other draft operations.** `replace()`, `applySquad()` and the Lab were read and
  take their bench from the draft already; ⭐ the new consistency check now covers all of them anyway,
  which is the point of putting it in `checkAgainst` rather than in `swap`.
